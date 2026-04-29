//! Pwn workflow artifact primitives.

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

use crate::case::{PwnCase, write_canonical_case};
use crate::workspace::{
    TOOL_RUNS_SCHEMA_VERSION, WorkspacePaths, append_session_event, init_workspace,
};
use crate::{VantaError, VantaResult};

/// Current pwn run schema version.
pub const PWN_RUN_SCHEMA_VERSION: &str = "vanta.pwn.run.v1";

/// Current pwn step artifact schema version.
pub const PWN_STEP_SCHEMA_VERSION: &str = "vanta.pwn.step.v1";

/// Current local knowledge pattern schema version.
pub const PWN_PATTERNS_SCHEMA_VERSION: &str = "vanta.pwn.patterns.v1";

/// A deterministic run artifact summary.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct PwnRun {
    /// Run schema version.
    pub schema_version: String,
    /// Run identifier.
    pub run_id: String,
    /// UTC creation timestamp.
    pub created_at: String,
    /// Canonical case artifact path.
    pub case_artifact: PathBuf,
    /// Deterministic seed.
    pub seed: u64,
    /// ASLR policy recorded for this run.
    pub aslr_policy: String,
    /// Step names in execution order.
    pub steps: Vec<String>,
}

/// A workflow step artifact.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct WorkflowStepArtifact {
    /// Step schema version.
    pub schema_version: String,
    /// Step name.
    pub step: String,
    /// Step status.
    pub status: String,
    /// Compact summary.
    pub summary: String,
    /// Artifact paths produced by the step.
    pub artifacts: Vec<String>,
    /// Evidence candidate refs or paths.
    pub evidence_candidates: Vec<String>,
    /// Optional structured failure.
    pub failure: Option<WorkflowFailure>,
}

/// Standard workflow failure shape.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct WorkflowFailure {
    /// Failure taxonomy category.
    pub category: String,
    /// Human-readable message.
    pub message: String,
    /// Evidence ref or path.
    pub evidence_ref: String,
    /// Suggested next action.
    pub suggested_next_action: String,
}

/// Result of initializing a pwn run.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct WorkflowRunOutcome {
    /// Workspace paths.
    pub paths: WorkspacePaths,
    /// Run id.
    pub run_id: String,
    /// Run directory path.
    pub run_dir: PathBuf,
}

/// Initialize workspace paths and write deterministic first-run artifacts.
pub fn start_pwn_workflow(
    project_root: impl AsRef<Path>,
    case: &PwnCase,
) -> VantaResult<WorkflowRunOutcome> {
    let init = init_workspace(project_root, mode_label(case))?;
    ensure_pwn_workflow_dirs(&init.paths)?;
    ensure_patterns_file(&init.paths)?;
    let canonical_case = write_canonical_case(&init.paths, case)?;
    let run_id = build_run_id(case.seed)?;
    let run_dir = init.paths.pwn_dir.join("runs").join(&run_id);
    create_dir_all(&run_dir)?;
    write_run_file(&run_dir, &run_id, &canonical_case, case)?;
    write_initial_step_artifacts(&run_dir)?;
    append_tool_runs(&init.paths, &run_id)?;
    append_session_event(
        &init.paths.session_file,
        "pwn.workflow.start",
        "pwn workflow started",
    )?;
    Ok(WorkflowRunOutcome {
        paths: init.paths,
        run_id,
        run_dir,
    })
}

fn ensure_pwn_workflow_dirs(paths: &WorkspacePaths) -> VantaResult<()> {
    create_dir_all(paths.pwn_dir.join("runs"))?;
    create_dir_all(paths.pwn_dir.join("knowledge"))
}

fn ensure_patterns_file(paths: &WorkspacePaths) -> VantaResult<()> {
    let path = paths.pwn_dir.join("knowledge").join("patterns.json");
    if path.exists() {
        return Ok(());
    }
    let value = serde_json::json!({
        "schema_version": PWN_PATTERNS_SCHEMA_VERSION,
        "patterns": ["ret2win", "ret2libc", "fmtstr", "tcache_poisoning"]
    });
    write_json_pretty(&path, &value)
}

fn write_run_file(
    run_dir: &Path,
    run_id: &str,
    case_artifact: &Path,
    case: &PwnCase,
) -> VantaResult<()> {
    let run = PwnRun {
        schema_version: PWN_RUN_SCHEMA_VERSION.to_owned(),
        run_id: run_id.to_owned(),
        created_at: utc_now()?,
        case_artifact: case_artifact.to_path_buf(),
        seed: case.seed,
        aslr_policy: format!("{:?}", case.aslr),
        steps: workflow_steps(),
    };
    write_json_pretty(&run_dir.join("run.json"), &run)
}

fn write_initial_step_artifacts(run_dir: &Path) -> VantaResult<()> {
    for (name, file_name) in step_files() {
        let artifact = WorkflowStepArtifact {
            schema_version: PWN_STEP_SCHEMA_VERSION.to_owned(),
            step: name.to_owned(),
            status: "planned".to_owned(),
            summary: "created by Rust orchestration; worker execution is delegated by runtime"
                .to_owned(),
            artifacts: Vec::new(),
            evidence_candidates: Vec::new(),
            failure: None,
        };
        write_json_pretty(&run_dir.join(file_name), &artifact)?;
    }
    Ok(())
}

fn append_tool_runs(paths: &WorkspacePaths, run_id: &str) -> VantaResult<()> {
    let event = serde_json::json!({
        "schema_version": TOOL_RUNS_SCHEMA_VERSION,
        "run_id": run_id,
        "tool": "pwn.workflow",
        "status": "planned",
        "steps": workflow_steps()
    });
    append_jsonl(&paths.tool_runs_file, &event)
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

fn step_files() -> Vec<(&'static str, &'static str)> {
    vec![
        ("worker.capability_check", "capability-check.json"),
        ("pwn.static_scan", "static-scan.json"),
        ("pwn.breakpoint_plan", "breakpoint-plan.json"),
        ("pwn.dynamic_verify", "dynamic-verify.json"),
        ("pwn.poc_draft", "poc-draft.json"),
    ]
}

fn workflow_steps() -> Vec<String> {
    step_files()
        .into_iter()
        .map(|(name, _file)| name.to_owned())
        .collect()
}

fn build_run_id(seed: u64) -> VantaResult<String> {
    let compact = utc_now()?.replace([':', '-'], "");
    Ok(format!("run-{compact}-seed-{seed}"))
}

fn mode_label(case: &PwnCase) -> &'static str {
    match case.mode {
        crate::case::CaseMode::Ctf => "ctf",
        crate::case::CaseMode::Research => "research",
        crate::case::CaseMode::Malware => "malware",
    }
}

fn create_dir_all(path: impl AsRef<Path>) -> VantaResult<()> {
    let path = path.as_ref();
    fs::create_dir_all(path).map_err(|source| VantaError::Io {
        path: path.to_path_buf(),
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

fn utc_now() -> VantaResult<String> {
    OffsetDateTime::now_utc()
        .format(&Rfc3339)
        .map_err(VantaError::TimeFormat)
}

#[cfg(test)]
mod tests {
    use std::fs;

    use crate::case::PwnCase;

    use super::*;

    #[test]
    fn workflow_creates_run_artifacts() -> anyhow::Result<()> {
        let root = unique_test_dir("workflow_creates_run_artifacts")?;
        let binary = root.join("chall");
        fs::write(&binary, b"elf")?;
        let case = PwnCase::draft(binary);

        let outcome = start_pwn_workflow(&root, &case)?;

        assert!(outcome.run_dir.join("run.json").exists());
        assert!(outcome.run_dir.join("static-scan.json").exists());
        assert!(outcome.paths.pwn_dir.join("case.json").exists());
        assert!(
            outcome
                .paths
                .pwn_dir
                .join("knowledge")
                .join("patterns.json")
                .exists()
        );

        fs::remove_dir_all(root)?;
        Ok(())
    }

    fn unique_test_dir(name: &str) -> anyhow::Result<PathBuf> {
        let mut root = std::env::temp_dir();
        root.push(format!("vanta-workflow-{name}-{}", std::process::id()));
        if root.exists() {
            fs::remove_dir_all(&root)?;
        }
        fs::create_dir_all(&root)?;
        Ok(root)
    }
}
