//! JSON-RPC stdio client for the Python pwn worker.

use std::env;
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};

use serde_json::Value;

use crate::{VantaError, VantaResult};

/// Environment variable used to override the pwn worker command.
pub const PWN_WORKER_COMMAND_ENV: &str = "VANTA_PWN_WORKER_COMMAND";

/// Persistent JSON-RPC client for one pwn worker process.
pub struct PwnWorkerClient {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
    next_id: u64,
}

impl PwnWorkerClient {
    /// Start the configured Python pwn worker process.
    pub fn start() -> VantaResult<Self> {
        let argv = worker_command();
        let program = argv
            .first()
            .ok_or_else(|| VantaError::Validation("pwn worker command is empty".to_owned()))?;
        let mut command = Command::new(program);
        command.args(&argv[1..]);
        command.env("PYTHONPATH", worker_pythonpath());
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|source| VantaError::Process(source.to_string()))?;
        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| VantaError::Process("pwn worker stdin is unavailable".to_owned()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| VantaError::Process("pwn worker stdout is unavailable".to_owned()))?;
        Ok(Self {
            child,
            stdin,
            stdout: BufReader::new(stdout),
            next_id: 1,
        })
    }

    /// Call one worker method and return its JSON result.
    pub fn call(&mut self, method: &str, params: Value) -> VantaResult<Value> {
        let request_id = self.next_id;
        self.next_id += 1;
        let request = serde_json::json!({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        });
        self.write_request(&request)?;
        let response = self.read_response()?;
        parse_rpc_response(response, request_id)
    }

    fn write_request(&mut self, request: &Value) -> VantaResult<()> {
        let line = serde_json::to_string(request).map_err(|source| VantaError::Json {
            path: "pwn-worker-jsonrpc-request".into(),
            source,
        })?;
        writeln!(self.stdin, "{line}").map_err(|source| VantaError::Process(source.to_string()))?;
        self.stdin
            .flush()
            .map_err(|source| VantaError::Process(source.to_string()))
    }

    fn read_response(&mut self) -> VantaResult<Value> {
        let mut line = String::new();
        let read = self
            .stdout
            .read_line(&mut line)
            .map_err(|source| VantaError::Process(source.to_string()))?;
        if read == 0 {
            return Err(VantaError::Process("pwn worker closed stdout".to_owned()));
        }
        serde_json::from_str(&line).map_err(|source| VantaError::Json {
            path: "pwn-worker-jsonrpc-response".into(),
            source,
        })
    }
}

impl Drop for PwnWorkerClient {
    fn drop(&mut self) {
        let _ignored = self.child.kill();
        let _ignored = self.child.wait();
    }
}

/// Return the worker command argv.
pub fn worker_command() -> Vec<String> {
    env::var(PWN_WORKER_COMMAND_ENV)
        .map(|value| split_command(&value))
        .unwrap_or_else(|_error| {
            vec![
                "uv".to_owned(),
                "run".to_owned(),
                "python".to_owned(),
                "-m".to_owned(),
                "vanta_pwn_worker.server".to_owned(),
            ]
        })
}

fn parse_rpc_response(response: Value, request_id: u64) -> VantaResult<Value> {
    if response.get("id").and_then(Value::as_u64) != Some(request_id) {
        return Err(VantaError::Process(
            "pwn worker returned mismatched id".to_owned(),
        ));
    }
    if let Some(error) = response.get("error") {
        let message = error
            .get("message")
            .and_then(Value::as_str)
            .unwrap_or("pwn worker request failed");
        return Err(VantaError::Process(message.to_owned()));
    }
    response
        .get("result")
        .cloned()
        .ok_or_else(|| VantaError::Process("pwn worker response missing result".to_owned()))
}

fn split_command(value: &str) -> Vec<String> {
    value.split_whitespace().map(str::to_owned).collect()
}

fn worker_pythonpath() -> String {
    let worker_path = "tools/pwn-worker/src";
    match env::var("PYTHONPATH") {
        Ok(existing) if !existing.is_empty() => format!("{worker_path}:{existing}"),
        _ => worker_path.to_owned(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_rpc_result() -> anyhow::Result<()> {
        let value = serde_json::json!({"jsonrpc":"2.0","id":7,"result":{"ok":true}});

        let result = parse_rpc_response(value, 7)?;

        assert_eq!(result["ok"], true);
        Ok(())
    }

    #[test]
    fn rejects_rpc_error() {
        let value = serde_json::json!({
            "jsonrpc":"2.0",
            "id":7,
            "error":{"code":-1,"message":"failed"}
        });

        assert!(parse_rpc_response(value, 7).is_err());
    }
}
