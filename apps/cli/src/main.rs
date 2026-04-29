//! Vanta command-line entry point.

use std::env;
use std::path::PathBuf;

use anyhow::{Context, Result, bail};
use vanta_core::{init_workspace, workspace_status};

fn main() -> Result<()> {
    let command = Command::parse(env::args().skip(1).collect())?;
    run(command)
}

#[derive(Debug, Eq, PartialEq)]
enum Command {
    Init { path: PathBuf, mode: String },
    Status { path: PathBuf },
    Help,
}

impl Command {
    fn parse(args: Vec<String>) -> Result<Self> {
        match args.first().map(String::as_str) {
            None => Ok(Self::Help),
            Some("init") => parse_init(&args[1..]),
            Some("status") => parse_status(&args[1..]),
            Some("--help" | "-h" | "help") => Ok(Self::Help),
            Some(other) => bail!("未知命令 `{other}`。运行 `vanta help` 查看可用命令。"),
        }
    }
}

fn run(command: Command) -> Result<()> {
    match command {
        Command::Init { path, mode } => {
            let outcome = init_workspace(&path, &mode).context("初始化 Vanta workspace 失败")?;
            let action = if outcome.created { "created" } else { "loaded" };
            println!(
                "workspace {action}: {}",
                outcome.paths.workspace_dir.display()
            );
            println!("mode: {}", outcome.workspace.mode);
            println!("schema: {}", outcome.workspace.schema_version);
            Ok(())
        }
        Command::Status { path } => {
            let status = workspace_status(&path);
            println!("project: {}", status.paths.project_root.display());
            println!("workspace: {}", status.paths.workspace_dir.display());
            println!("exists: {}", status.exists);
            Ok(())
        }
        Command::Help => {
            print_help();
            Ok(())
        }
    }
}

fn parse_init(args: &[String]) -> Result<Command> {
    let mut path = PathBuf::from(".");
    let mut mode = String::from("ctf");
    let mut index = 0;

    while index < args.len() {
        match args[index].as_str() {
            "--mode" => {
                let value = args
                    .get(index + 1)
                    .context("`--mode` 需要一个值：ctf、research 或 malware")?;
                mode = validate_mode(value)?;
                index += 2;
            }
            value if value.starts_with("--") => {
                bail!("未知参数 `{value}`。运行 `vanta help` 查看用法。");
            }
            value => {
                path = PathBuf::from(value);
                index += 1;
            }
        }
    }

    Ok(Command::Init { path, mode })
}

fn parse_status(args: &[String]) -> Result<Command> {
    let path = match args {
        [] => PathBuf::from("."),
        [single] => PathBuf::from(single),
        _ => bail!("`vanta status` 最多接受一个路径参数。"),
    };
    Ok(Command::Status { path })
}

fn validate_mode(value: &str) -> Result<String> {
    match value {
        "ctf" | "research" | "malware" => Ok(value.to_owned()),
        other => bail!("未知 mode `{other}`。允许值：ctf、research、malware。"),
    }
}

fn print_help() {
    println!(
        "\
Vanta

Usage:
  vanta init [path] [--mode ctf|research|malware]
  vanta status [path]
  vanta help

Examples:
  vanta init ./challenge
  vanta init ./challenge --mode research
  vanta status ./challenge"
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_init_defaults_to_current_dir_and_ctf() -> Result<()> {
        let command = Command::parse(vec![String::from("init")])?;
        assert_eq!(
            command,
            Command::Init {
                path: PathBuf::from("."),
                mode: String::from("ctf")
            }
        );
        Ok(())
    }

    #[test]
    fn parse_init_accepts_mode_and_path() -> Result<()> {
        let command = Command::parse(vec![
            String::from("init"),
            String::from("./chall"),
            String::from("--mode"),
            String::from("research"),
        ])?;
        assert_eq!(
            command,
            Command::Init {
                path: PathBuf::from("./chall"),
                mode: String::from("research")
            }
        );
        Ok(())
    }

    #[test]
    fn parse_rejects_unknown_mode() {
        let result = Command::parse(vec![
            String::from("init"),
            String::from("--mode"),
            String::from("unknown"),
        ]);
        assert!(result.is_err());
    }
}
