//! Vanta command-line entry point.

use std::env;
use std::path::PathBuf;

use anyhow::{Context, Result, bail};
use vanta_core::{
    ProviderConfig, PwnCase, init_workspace, load_case, provider_status, solve_case_with_reporter,
    workspace_status, write_case_draft, write_provider_config,
};

fn main() -> Result<()> {
    let command = Command::parse(env::args().skip(1).collect())?;
    run(command)
}

#[derive(Debug, Eq, PartialEq)]
enum Command {
    Init {
        path: PathBuf,
        mode: String,
    },
    Status {
        path: PathBuf,
    },
    CaseInit {
        binary: PathBuf,
        output: PathBuf,
    },
    CaseValidate {
        path: PathBuf,
    },
    ModelStatus,
    ModelInitLocal {
        model_path: PathBuf,
        command: String,
    },
    Solve {
        path: PathBuf,
    },
    Help,
}

impl Command {
    fn parse(args: Vec<String>) -> Result<Self> {
        match args.first().map(String::as_str) {
            None => Ok(Self::Help),
            Some("init") => parse_init(&args[1..]),
            Some("status") => parse_status(&args[1..]),
            Some("case") => parse_case_command(&args[1..]),
            Some("model") => parse_model_command(&args[1..]),
            Some("solve") => parse_solve(&args[1..]),
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
        Command::CaseInit { binary, output } => {
            let case = PwnCase::draft(binary);
            write_case_draft(&output, &case).context("写入 case 草案失败")?;
            println!("case draft: {}", output.display());
            Ok(())
        }
        Command::CaseValidate { path } => {
            let case = load_case(&path).context("校验 case 失败")?;
            let summary = serde_json::to_string_pretty(&case.summary())?;
            println!("{summary}");
            Ok(())
        }
        Command::ModelStatus => {
            let status = provider_status().context("读取模型 provider 状态失败")?;
            let summary = serde_json::to_string_pretty(&status)?;
            println!("{summary}");
            Ok(())
        }
        Command::ModelInitLocal {
            model_path,
            command,
        } => {
            let config = ProviderConfig::local_llama(local_llama_command(&command), model_path);
            let path = write_provider_config(&config).context("写入本机模型配置失败")?;
            println!("provider config: {}", path.display());
            Ok(())
        }
        Command::Solve { path } => {
            let case = load_case(&path).context("加载 case 失败")?;
            let root = project_root_for_case_file(&path);
            let outcome = solve_case_with_reporter(root, &case, |message| {
                eprintln!("[vanta solve] {message}");
            })
            .context("运行 pwn solve workflow 失败")?;
            println!("run: {}", outcome.run_id);
            println!("workspace: {}", outcome.workspace_dir.display());
            println!("artifacts: {}", outcome.run_dir.display());
            println!("provider: {}", outcome.provider);
            println!("fallback_used: {}", outcome.fallback_used);
            println!("gdb_used: {}", outcome.gdb_used);
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

fn parse_case_command(args: &[String]) -> Result<Command> {
    match args.first().map(String::as_str) {
        Some("init") => parse_case_init(&args[1..]),
        Some("validate") => parse_case_validate(&args[1..]),
        Some(other) => bail!("未知 case 子命令 `{other}`。允许值：init、validate。"),
        None => bail!("`vanta case` 需要子命令：init 或 validate。"),
    }
}

fn parse_case_init(args: &[String]) -> Result<Command> {
    let mut binary: Option<PathBuf> = None;
    let mut output = PathBuf::from("case.json");
    let mut index = 0;
    while index < args.len() {
        match args[index].as_str() {
            "--output" | "-o" => {
                output = PathBuf::from(args.get(index + 1).context("`--output` 需要一个输出路径")?);
                index += 2;
            }
            value if value.starts_with("--") => bail!("未知参数 `{value}`。"),
            value => {
                binary = Some(PathBuf::from(value));
                index += 1;
            }
        }
    }
    let binary = binary.context("`vanta case init` 需要 binary 路径")?;
    Ok(Command::CaseInit { binary, output })
}

fn parse_case_validate(args: &[String]) -> Result<Command> {
    match args {
        [single] => Ok(Command::CaseValidate {
            path: PathBuf::from(single),
        }),
        [] => bail!("`vanta case validate` 需要 case.json 或 case.yaml 路径。"),
        _ => bail!("`vanta case validate` 只接受一个 case 文件路径。"),
    }
}

fn parse_model_command(args: &[String]) -> Result<Command> {
    match args.first().map(String::as_str) {
        Some("status") => Ok(Command::ModelStatus),
        Some("init-local") => parse_model_init_local(&args[1..]),
        Some(other) => bail!("未知 model 子命令 `{other}`。允许值：status、init-local。"),
        None => bail!("`vanta model` 需要子命令：status 或 init-local。"),
    }
}

fn parse_model_init_local(args: &[String]) -> Result<Command> {
    let mut model_path: Option<PathBuf> = None;
    let mut command: Option<String> = None;
    let mut index = 0;
    while index < args.len() {
        match args[index].as_str() {
            "--command" => {
                command = Some(
                    args.get(index + 1)
                        .context("`--command` 需要本地 llama 可执行程序路径")?
                        .clone(),
                );
                index += 2;
            }
            value if value.starts_with("--") => bail!("未知参数 `{value}`。"),
            value => {
                model_path = Some(PathBuf::from(value));
                index += 1;
            }
        }
    }
    Ok(Command::ModelInitLocal {
        model_path: model_path.context("`vanta model init-local` 需要 model path")?,
        command: command.context("`vanta model init-local` 需要 --command")?,
    })
}

fn parse_solve(args: &[String]) -> Result<Command> {
    match args {
        [single] => Ok(Command::Solve {
            path: PathBuf::from(single),
        }),
        [] => bail!("`vanta solve` 需要 case.json 或 case.yaml 路径。"),
        _ => bail!("`vanta solve` 只接受一个 case 文件路径。"),
    }
}

fn local_llama_command(command: &str) -> Vec<String> {
    vec![
        command.to_owned(),
        "--model".to_owned(),
        "{model_path}".to_owned(),
        "--prompt-file".to_owned(),
        "{prompt_file}".to_owned(),
        "--output-file".to_owned(),
        "{output_file}".to_owned(),
        "--gpu-layers".to_owned(),
        "-1".to_owned(),
    ]
}

fn project_root_for_case_file(path: &std::path::Path) -> PathBuf {
    path.parent()
        .filter(|parent| !parent.as_os_str().is_empty())
        .unwrap_or_else(|| std::path::Path::new("."))
        .to_path_buf()
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
  vanta case init <binary> [--output case.json]
  vanta case validate <case.json|case.yaml>
  vanta model status
  vanta model init-local <model.gguf> --command <llama-program>
  vanta solve <case.json|case.yaml>
  vanta help

Examples:
  vanta init ./challenge
  vanta init ./challenge --mode research
  vanta status ./challenge
  vanta case init ./chall
  vanta case validate ./case.yaml
  vanta model status
  vanta model init-local ./model.gguf --command llama-cli
  vanta solve ./case.json"
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

    #[test]
    fn parse_case_init_accepts_output() -> Result<()> {
        let command = Command::parse(vec![
            String::from("case"),
            String::from("init"),
            String::from("./chall"),
            String::from("--output"),
            String::from("case.json"),
        ])?;
        assert_eq!(
            command,
            Command::CaseInit {
                binary: PathBuf::from("./chall"),
                output: PathBuf::from("case.json")
            }
        );
        Ok(())
    }

    #[test]
    fn parse_solve_accepts_case_path() -> Result<()> {
        let command = Command::parse(vec![String::from("solve"), String::from("case.yaml")])?;
        assert_eq!(
            command,
            Command::Solve {
                path: PathBuf::from("case.yaml")
            }
        );
        Ok(())
    }

    #[test]
    fn parse_model_init_local_accepts_command() -> Result<()> {
        let command = Command::parse(vec![
            String::from("model"),
            String::from("init-local"),
            String::from("model.gguf"),
            String::from("--command"),
            String::from("llama-cli"),
        ])?;
        assert_eq!(
            command,
            Command::ModelInitLocal {
                model_path: PathBuf::from("model.gguf"),
                command: String::from("llama-cli")
            }
        );
        Ok(())
    }
}
