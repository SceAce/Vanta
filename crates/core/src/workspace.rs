//! Workspace and transcript primitives for Vanta.

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

/// Current workspace metadata schema version.
pub const WORKSPACE_SCHEMA_VERSION: &str = "vanta.workspace.v1";

/// Current facts schema version.
pub const FACTS_SCHEMA_VERSION: &str = "vanta.facts.v1";

/// Current tool run schema version.
pub const TOOL_RUNS_SCHEMA_VERSION: &str = "vanta.tool-runs.v1";

/// Current session event schema version.
pub const SESSION_EVENT_SCHEMA_VERSION: &str = "vanta.session-event.v1";

/// Vanta core result alias.
pub type VantaResult<T> = Result<T, VantaError>;

/// Errors returned by Vanta core operations.
#[derive(Debug, thiserror::Error)]
pub enum VantaError {
    /// Filesystem operation failed.
    #[error("filesystem operation failed for {path}: {source}")]
    Io {
        /// Path involved in the failed operation.
        path: PathBuf,
        /// Original IO error.
        source: std::io::Error,
    },

    /// JSON serialization or parsing failed.
    #[error("json operation failed for {path}: {source}")]
    Json {
        /// Path involved in the failed operation.
        path: PathBuf,
        /// Original JSON error.
        source: serde_json::Error,
    },

    /// Timestamp formatting failed.
    #[error("timestamp formatting failed: {0}")]
    TimeFormat(#[from] time::error::Format),
}

/// Paths used by a Vanta workspace.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct WorkspacePaths {
    /// Root directory selected by the user or command.
    pub project_root: PathBuf,
    /// Hidden Vanta workspace directory.
    pub workspace_dir: PathBuf,
    /// Workspace metadata file.
    pub workspace_file: PathBuf,
    /// Session transcript JSONL file.
    pub session_file: PathBuf,
    /// Facts JSON file.
    pub facts_file: PathBuf,
    /// Tool run JSONL file.
    pub tool_runs_file: PathBuf,
    /// Pwn-specific workspace directory.
    pub pwn_dir: PathBuf,
}

impl WorkspacePaths {
    /// Build workspace paths from a project root.
    pub fn new(project_root: impl AsRef<Path>) -> Self {
        let project_root = project_root.as_ref().to_path_buf();
        let workspace_dir = project_root.join(".vanta");
        let pwn_dir = workspace_dir.join("pwn");

        Self {
            project_root,
            workspace_file: workspace_dir.join("workspace.json"),
            session_file: workspace_dir.join("session.jsonl"),
            facts_file: workspace_dir.join("facts.json"),
            tool_runs_file: workspace_dir.join("tool-runs.jsonl"),
            workspace_dir,
            pwn_dir,
        }
    }
}

/// Vanta workspace metadata.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct Workspace {
    /// Metadata schema version.
    pub schema_version: String,
    /// Workspace type name.
    pub workspace_type: String,
    /// Workspace mode: ctf, research, or malware.
    pub mode: String,
    /// UTC creation timestamp.
    pub created_at: String,
    /// UTC update timestamp.
    pub updated_at: String,
}

/// Result of an init operation.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct InitOutcome {
    /// Workspace paths.
    pub paths: WorkspacePaths,
    /// Workspace metadata.
    pub workspace: Workspace,
    /// Whether the metadata file was created during this call.
    pub created: bool,
}

/// Current workspace status.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct WorkspaceStatus {
    /// Workspace paths.
    pub paths: WorkspacePaths,
    /// Whether workspace metadata exists.
    pub exists: bool,
}

/// Transcript event written to session.jsonl.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct SessionEvent {
    /// Session event schema version.
    pub schema_version: String,
    /// Event type.
    pub event_type: String,
    /// UTC event timestamp.
    pub timestamp: String,
    /// Human-readable event message.
    pub message: String,
}

/// Initialize or inspect Vanta workspace state.
pub fn init_workspace(project_root: impl AsRef<Path>, mode: &str) -> VantaResult<InitOutcome> {
    let paths = WorkspacePaths::new(project_root);
    create_workspace_dirs(&paths)?;

    let created = !paths.workspace_file.exists();
    let workspace = if created {
        let now = utc_now()?;
        let workspace = Workspace {
            schema_version: WORKSPACE_SCHEMA_VERSION.to_owned(),
            workspace_type: "vanta-workspace".to_owned(),
            mode: mode.to_owned(),
            created_at: now.clone(),
            updated_at: now,
        };
        write_json_pretty(&paths.workspace_file, &workspace)?;
        workspace
    } else {
        read_json(&paths.workspace_file)?
    };

    ensure_json_file(&paths.facts_file, FACTS_SCHEMA_VERSION)?;
    ensure_json_file(&paths.tool_runs_file, TOOL_RUNS_SCHEMA_VERSION)?;
    append_session_event(
        &paths.session_file,
        "workspace.init",
        "workspace initialized",
    )?;

    Ok(InitOutcome {
        paths,
        workspace,
        created,
    })
}

/// Return workspace status without mutating the filesystem.
pub fn workspace_status(project_root: impl AsRef<Path>) -> WorkspaceStatus {
    let paths = WorkspacePaths::new(project_root);
    let exists = paths.workspace_file.exists();
    WorkspaceStatus { paths, exists }
}

/// Append a session event to a JSONL transcript.
pub fn append_session_event(
    session_file: impl AsRef<Path>,
    event_type: &str,
    message: &str,
) -> VantaResult<()> {
    let session_file = session_file.as_ref();
    let parent = session_file.parent().unwrap_or_else(|| Path::new("."));
    create_dir_all(parent)?;

    let event = SessionEvent {
        schema_version: SESSION_EVENT_SCHEMA_VERSION.to_owned(),
        event_type: event_type.to_owned(),
        timestamp: utc_now()?,
        message: message.to_owned(),
    };
    let line = serde_json::to_string(&event).map_err(|source| VantaError::Json {
        path: session_file.to_path_buf(),
        source,
    })?;
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(session_file)
        .map_err(|source| VantaError::Io {
            path: session_file.to_path_buf(),
            source,
        })?;
    writeln!(file, "{line}").map_err(|source| VantaError::Io {
        path: session_file.to_path_buf(),
        source,
    })
}

fn create_workspace_dirs(paths: &WorkspacePaths) -> VantaResult<()> {
    create_dir_all(&paths.workspace_dir)?;
    create_dir_all(paths.pwn_dir.join("crashes"))?;
    create_dir_all(paths.pwn_dir.join("payloads"))?;
    create_dir_all(paths.pwn_dir.join("exploits"))?;
    create_dir_all(paths.pwn_dir.join("reports"))?;
    create_dir_all(paths.pwn_dir.join("gdb"))?;
    create_dir_all(paths.pwn_dir.join("ida"))
}

fn ensure_json_file(path: &Path, schema_version: &str) -> VantaResult<()> {
    if path.exists() {
        return Ok(());
    }
    let value = serde_json::json!({
        "schema_version": schema_version,
        "items": []
    });
    write_json_pretty(path, &value)
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> VantaResult<T> {
    let text = fs::read_to_string(path).map_err(|source| VantaError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    serde_json::from_str(&text).map_err(|source| VantaError::Json {
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

fn create_dir_all(path: impl AsRef<Path>) -> VantaResult<()> {
    let path = path.as_ref();
    fs::create_dir_all(path).map_err(|source| VantaError::Io {
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

    use super::*;

    #[test]
    fn init_workspace_creates_expected_files() -> anyhow::Result<()> {
        let root = unique_test_dir("init_workspace_creates_expected_files")?;

        let outcome = init_workspace(&root, "ctf")?;

        assert!(outcome.created);
        assert!(outcome.paths.workspace_file.exists());
        assert!(outcome.paths.session_file.exists());
        assert!(outcome.paths.facts_file.exists());
        assert!(outcome.paths.tool_runs_file.exists());
        assert!(outcome.paths.pwn_dir.join("crashes").exists());
        assert_eq!(outcome.workspace.schema_version, WORKSPACE_SCHEMA_VERSION);

        fs::remove_dir_all(root)?;
        Ok(())
    }

    #[test]
    fn workspace_status_does_not_create_workspace() -> anyhow::Result<()> {
        let root = unique_test_dir("workspace_status_does_not_create_workspace")?;

        let status = workspace_status(&root);

        assert!(!status.exists);
        assert!(!status.paths.workspace_dir.exists());

        fs::remove_dir_all(root)?;
        Ok(())
    }

    fn unique_test_dir(name: &str) -> anyhow::Result<PathBuf> {
        let mut root = std::env::temp_dir();
        root.push(format!("vanta-{name}-{}", std::process::id()));
        if root.exists() {
            fs::remove_dir_all(&root)?;
        }
        fs::create_dir_all(&root)?;
        Ok(root)
    }
}
