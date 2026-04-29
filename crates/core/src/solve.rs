//! End-to-end pwn solve orchestration.

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::case::PwnCase;
use crate::provider::{ModelRequest, ModelResponse, infer_with_fallback, load_provider_config};
use crate::worker_client::PwnWorkerClient;
use crate::workflow::{PWN_STEP_SCHEMA_VERSION, WorkflowRunOutcome, start_pwn_workflow};
use crate::{VantaError, VantaResult};

/// Current solve analysis schema version.
pub const SOLVE_ANALYSIS_SCHEMA_VERSION: &str = "vanta.pwn.analysis.v1";

/// Result of running pwn solve orchestration.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct SolveOutcome {
    /// Run identifier.
    pub run_id: String,
    /// Run directory path.
    pub run_dir: PathBuf,
    /// Workspace directory path.
    pub workspace_dir: PathBuf,
    /// Model provider used.
    pub provider: String,
    /// Whether model fallback was used.
    pub fallback_used: bool,
    /// Whether GDB dynamic verification was requested.
    pub gdb_used: bool,
}

/// Run the local pwn solve workflow.
pub fn solve_case(project_root: impl AsRef<Path>, case: &PwnCase) -> VantaResult<SolveOutcome> {
    let run = start_pwn_workflow(project_root, case)?;
    let mut worker = PwnWorkerClient::start()?;
    let capabilities = call_and_write(
        &mut worker,
        &run,
        "worker.capabilities",
        "capability-check.json",
        serde_json::json!({}),
    )?;
    let static_scan = call_and_write(
        &mut worker,
        &run,
        "pwn.static_scan",
        "static-scan.json",
        case_params(case),
    )?;
    let pattern_match = worker.call(
        "pwn.pattern_match",
        serde_json::json!({"static_scan": static_scan}),
    )?;
    append_tool_event(&run, "pwn.pattern_match", "ok", &pattern_match)?;
    let model_response = first_model_pass(case, &capabilities, &static_scan, &pattern_match)?;
    let gdb_used = maybe_dynamic_verify(&mut worker, &run, case, &model_response)?;
    let poc_draft = call_and_write(
        &mut worker,
        &run,
        "pwn.poc_draft",
        "poc-draft.json",
        case_params(case),
    )?;
    let final_response = final_model_pass(case, &static_scan, &poc_draft, &model_response)?;
    write_analysis(&run, &model_response, &final_response, gdb_used)?;
    write_facts(&run, &final_response)?;
    Ok(SolveOutcome {
        run_id: run.run_id,
        run_dir: run.run_dir,
        workspace_dir: run.paths.workspace_dir,
        provider: final_response.provider,
        fallback_used: final_response.fallback_used || model_response.fallback_used,
        gdb_used,
    })
}

fn first_model_pass(
    case: &PwnCase,
    capabilities: &Value,
    static_scan: &Value,
    pattern_match: &Value,
) -> VantaResult<ModelResponse> {
    let config = load_provider_config()?;
    let request = ModelRequest {
        system_prompt: system_prompt(),
        user_prompt: format!(
            "请基于以下 CTF pwn case 和 IDA/static evidence 给出漏洞假设、需要的证据和下一步动作。\ncase:\n{}\ncapabilities:\n{}\nstatic_scan:\n{}\npattern_match:\n{}",
            json_string(&case.summary())?,
            json_string(capabilities)?,
            json_string(static_scan)?,
            json_string(pattern_match)?
        ),
    };
    infer_with_fallback(&config, &request)
}

fn final_model_pass(
    case: &PwnCase,
    static_scan: &Value,
    poc_draft: &Value,
    previous: &ModelResponse,
) -> VantaResult<ModelResponse> {
    let config = load_provider_config()?;
    let request = ModelRequest {
        system_prompt: system_prompt(),
        user_prompt: format!(
            "请整合现有证据，输出面向用户的 CTF pwn 解题分析摘要、可信假设、是否还需要 GDB、PoC 草案注意事项。\ncase:\n{}\nstatic_scan:\n{}\npoc_draft:\n{}\nprevious_model_analysis:\n{}",
            json_string(&case.summary())?,
            json_string(static_scan)?,
            json_string(poc_draft)?,
            previous.text
        ),
    };
    infer_with_fallback(&config, &request)
}

fn maybe_dynamic_verify(
    worker: &mut PwnWorkerClient,
    run: &WorkflowRunOutcome,
    case: &PwnCase,
    model_response: &ModelResponse,
) -> VantaResult<bool> {
    if !model_requests_gdb(&model_response.text) {
        write_planned_skip(
            run,
            "dynamic-verify.json",
            "model did not request GDB evidence",
        )?;
        return Ok(false);
    }
    let breakpoint = call_and_write(
        worker,
        run,
        "pwn.breakpoint_plan",
        "breakpoint-plan.json",
        case_params(case),
    )?;
    append_tool_event(run, "pwn.breakpoint_plan", "ok", &breakpoint)?;
    let dynamic = call_and_write(
        worker,
        run,
        "pwn.dynamic_verify",
        "dynamic-verify.json",
        case_params(case),
    )?;
    append_tool_event(run, "pwn.dynamic_verify", "ok", &dynamic)?;
    Ok(true)
}

fn call_and_write(
    worker: &mut PwnWorkerClient,
    run: &WorkflowRunOutcome,
    method: &str,
    file_name: &str,
    params: Value,
) -> VantaResult<Value> {
    let result = worker.call(method, params)?;
    write_step_result(run, file_name, method, &result)?;
    append_tool_event(run, method, "ok", &result)?;
    Ok(result)
}

fn write_step_result(
    run: &WorkflowRunOutcome,
    file_name: &str,
    step: &str,
    result: &Value,
) -> VantaResult<()> {
    let artifact = serde_json::json!({
        "schema_version": PWN_STEP_SCHEMA_VERSION,
        "step": step,
        "status": result.get("status").and_then(Value::as_str).unwrap_or("ok"),
        "summary": result.get("summary").and_then(Value::as_str).unwrap_or("worker result recorded"),
        "result": result
    });
    write_json_pretty(&run.run_dir.join(file_name), &artifact)
}

fn write_planned_skip(run: &WorkflowRunOutcome, file_name: &str, summary: &str) -> VantaResult<()> {
    let artifact = serde_json::json!({
        "schema_version": PWN_STEP_SCHEMA_VERSION,
        "step": "pwn.dynamic_verify",
        "status": "skipped",
        "summary": summary
    });
    write_json_pretty(&run.run_dir.join(file_name), &artifact)
}

fn write_analysis(
    run: &WorkflowRunOutcome,
    first: &ModelResponse,
    final_response: &ModelResponse,
    gdb_used: bool,
) -> VantaResult<()> {
    let value = serde_json::json!({
        "schema_version": SOLVE_ANALYSIS_SCHEMA_VERSION,
        "run_id": run.run_id,
        "provider": final_response.provider,
        "model": final_response.model,
        "fallback_used": first.fallback_used || final_response.fallback_used,
        "gdb_used": gdb_used,
        "first_pass": first.text,
        "final": final_response.text
    });
    write_json_pretty(&run.run_dir.join("analysis.json"), &value)
}

fn write_facts(run: &WorkflowRunOutcome, final_response: &ModelResponse) -> VantaResult<()> {
    let value = serde_json::json!({
        "schema_version": "vanta.facts.v1",
        "items": [{
            "kind": "pwn.solve.analysis",
            "run_id": run.run_id,
            "provider": final_response.provider,
            "summary": final_response.text
        }]
    });
    write_json_pretty(&run.paths.facts_file, &value)
}

fn append_tool_event(
    run: &WorkflowRunOutcome,
    tool: &str,
    status: &str,
    output: &Value,
) -> VantaResult<()> {
    let value = serde_json::json!({
        "schema_version": "vanta.tool-runs.v1",
        "run_id": run.run_id,
        "tool": tool,
        "status": status,
        "output_summary": compact_value(output)
    });
    append_jsonl(&run.paths.tool_runs_file, &value)
}

fn case_params(case: &PwnCase) -> Value {
    serde_json::json!({"case": case})
}

fn system_prompt() -> String {
    "你是 Vanta Pwn 的本地分析模型。只帮助授权 CTF pwn 解题。优先基于 IDA 伪代码和静态证据给出结论；只有需要动态证据时明确写出 need gdb。不要要求连接未授权真实目标，不要输出或索要 API key。".to_owned()
}

fn model_requests_gdb(text: &str) -> bool {
    let normalized = text.to_ascii_lowercase();
    ["need gdb", "use gdb", "dynamic", "debug", "调试", "动态"]
        .iter()
        .any(|needle| normalized.contains(needle))
}

fn compact_value(value: &Value) -> Value {
    if let Some(summary) = value.get("summary") {
        return serde_json::json!({"summary": summary});
    }
    serde_json::json!({"type": value_type(value)})
}

fn value_type(value: &Value) -> &'static str {
    match value {
        Value::Null => "null",
        Value::Bool(_) => "bool",
        Value::Number(_) => "number",
        Value::String(_) => "string",
        Value::Array(_) => "array",
        Value::Object(_) => "object",
    }
}

fn json_string<T: Serialize>(value: &T) -> VantaResult<String> {
    serde_json::to_string_pretty(value).map_err(|source| VantaError::Json {
        path: "solve-prompt-json".into(),
        source,
    })
}

fn write_json_pretty<T: Serialize>(path: &Path, value: &T) -> VantaResult<()> {
    let text = serde_json::to_string_pretty(value).map_err(|source| VantaError::Json {
        path: path.to_path_buf(),
        source,
    })?;
    fs::write(path, format!("{text}\n")).map_err(|source| VantaError::Io {
        path: path.to_path_buf(),
        source,
    })
}

fn append_jsonl<T: Serialize>(path: &Path, value: &T) -> VantaResult<()> {
    let line = serde_json::to_string(value).map_err(|source| VantaError::Json {
        path: path.to_path_buf(),
        source,
    })?;
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|source| VantaError::Io {
            path: path.to_path_buf(),
            source,
        })?;
    writeln!(file, "{line}").map_err(|source| VantaError::Io {
        path: path.to_path_buf(),
        source,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_gdb_need_from_model_text() {
        assert!(model_requests_gdb("We need GDB to confirm the crash."));
        assert!(model_requests_gdb("需要动态调试确认偏移。"));
        assert!(!model_requests_gdb("Static evidence is enough."));
    }
}
