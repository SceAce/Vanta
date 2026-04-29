//! Vanta core runtime primitives.

pub mod workspace;

pub use workspace::{
    InitOutcome, SessionEvent, VantaError, VantaResult, Workspace, WorkspacePaths, WorkspaceStatus,
    init_workspace, workspace_status,
};
