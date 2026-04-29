//! Case schema loading, validation, and canonical writing.

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::{VantaError, VantaResult, WorkspacePaths};

/// Current pwn case schema version.
pub const CASE_SCHEMA_VERSION: &str = "vanta.pwn.case.v1";

/// ASLR behavior for dynamic workflow steps.
#[derive(Debug, Clone, Default, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum AslrPolicy {
    /// Preserve the host/user default ASLR behavior.
    #[default]
    Preserve,
    /// Disable ASLR only for the current local run when supported.
    DisableForRun,
    /// Require ASLR to be enabled before dynamic execution.
    RequireEnabled,
}

/// Case safety mode.
#[derive(Debug, Clone, Default, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum CaseMode {
    /// CTF target mode.
    #[default]
    Ctf,
    /// Authorized research mode.
    Research,
    /// Malware handling mode.
    Malware,
}

/// Remote service metadata. Connecting still requires runtime permission.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct RemoteTarget {
    /// Remote host name or address.
    pub host: String,
    /// Remote TCP port.
    pub port: u16,
    /// Whether TLS is expected.
    #[serde(default)]
    pub tls: bool,
    /// Human-readable authorization or challenge description.
    #[serde(default)]
    pub description: String,
}

/// User-provided pwn case definition.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct PwnCase {
    /// Case schema version.
    #[serde(default = "default_case_schema_version")]
    pub schema_version: String,
    /// Target ELF path.
    pub binary_path: PathBuf,
    /// Optional libc path.
    #[serde(default)]
    pub libc_path: Option<PathBuf>,
    /// Optional dynamic loader path.
    #[serde(default)]
    pub ld_path: Option<PathBuf>,
    /// Program arguments.
    #[serde(default)]
    pub args: Vec<String>,
    /// Environment variables for target execution.
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    /// Optional stdin fixture or literal input.
    #[serde(default)]
    pub stdin: Option<String>,
    /// Optional remote target metadata.
    #[serde(default)]
    pub remote: Option<RemoteTarget>,
    /// ASLR policy.
    #[serde(default)]
    pub aslr: AslrPolicy,
    /// Per-step timeout in seconds.
    #[serde(default = "default_timeout_seconds")]
    pub timeout_seconds: u64,
    /// Retry limit for deterministic dynamic steps.
    #[serde(default = "default_retry_limit")]
    pub retry_limit: u32,
    /// Deterministic workflow seed.
    #[serde(default)]
    pub seed: u64,
    /// Case safety mode.
    #[serde(default)]
    pub mode: CaseMode,
}

/// Normalized validation summary.
#[derive(Debug, Clone, Serialize, Eq, PartialEq)]
pub struct CaseSummary {
    /// Case schema version.
    pub schema_version: String,
    /// Target ELF path.
    pub binary_path: PathBuf,
    /// Whether libc is configured.
    pub has_libc: bool,
    /// Whether ld is configured.
    pub has_ld: bool,
    /// Argument count.
    pub args_count: usize,
    /// Environment variable count.
    pub env_count: usize,
    /// Whether remote metadata exists.
    pub has_remote: bool,
    /// ASLR policy.
    pub aslr: AslrPolicy,
    /// Timeout seconds.
    pub timeout_seconds: u64,
    /// Retry limit.
    pub retry_limit: u32,
    /// Deterministic seed.
    pub seed: u64,
    /// Case mode.
    pub mode: CaseMode,
}

impl PwnCase {
    /// Build a minimal case draft for a binary path.
    pub fn draft(binary_path: impl Into<PathBuf>) -> Self {
        Self {
            schema_version: CASE_SCHEMA_VERSION.to_owned(),
            binary_path: binary_path.into(),
            libc_path: None,
            ld_path: None,
            args: Vec::new(),
            env: BTreeMap::new(),
            stdin: None,
            remote: None,
            aslr: AslrPolicy::Preserve,
            timeout_seconds: default_timeout_seconds(),
            retry_limit: default_retry_limit(),
            seed: 0,
            mode: CaseMode::Ctf,
        }
    }

    /// Validate semantic constraints after deserialization.
    pub fn validate(&self) -> VantaResult<()> {
        validate_schema_version(&self.schema_version)?;
        validate_binary_path(&self.binary_path)?;
        validate_optional_path(self.libc_path.as_ref(), "libc_path")?;
        validate_optional_path(self.ld_path.as_ref(), "ld_path")?;
        validate_env(&self.env)?;
        validate_remote(self.remote.as_ref())?;
        validate_runtime_limits(self.timeout_seconds, self.retry_limit)
    }

    /// Return an evidence-friendly normalized summary.
    pub fn summary(&self) -> CaseSummary {
        CaseSummary {
            schema_version: self.schema_version.clone(),
            binary_path: self.binary_path.clone(),
            has_libc: self.libc_path.is_some(),
            has_ld: self.ld_path.is_some(),
            args_count: self.args.len(),
            env_count: self.env.len(),
            has_remote: self.remote.is_some(),
            aslr: self.aslr.clone(),
            timeout_seconds: self.timeout_seconds,
            retry_limit: self.retry_limit,
            seed: self.seed,
            mode: self.mode.clone(),
        }
    }
}

/// Load and validate a case file from JSON or YAML.
pub fn load_case(path: impl AsRef<Path>) -> VantaResult<PwnCase> {
    let path = path.as_ref();
    let text = read_text(path)?;
    let case = parse_case(path, &text)?;
    case.validate()?;
    Ok(case)
}

/// Write the canonical workspace case artifact as JSON.
pub fn write_canonical_case(paths: &WorkspacePaths, case: &PwnCase) -> VantaResult<PathBuf> {
    let path = paths.pwn_dir.join("case.json");
    write_json_pretty(&path, case)?;
    Ok(path)
}

/// Write a case draft to the requested path.
pub fn write_case_draft(path: impl AsRef<Path>, case: &PwnCase) -> VantaResult<()> {
    write_json_pretty(path.as_ref(), case)
}

fn parse_case(path: &Path, text: &str) -> VantaResult<PwnCase> {
    match path.extension().and_then(|value| value.to_str()) {
        Some("yaml" | "yml") => parse_yaml(path, text),
        _ => serde_json::from_str(text).map_err(|source| VantaError::Json {
            path: path.to_path_buf(),
            source,
        }),
    }
}

fn parse_yaml(path: &Path, text: &str) -> VantaResult<PwnCase> {
    serde_yaml::from_str(text).map_err(|source| VantaError::Yaml {
        path: path.to_path_buf(),
        source,
    })
}

fn validate_schema_version(schema_version: &str) -> VantaResult<()> {
    if schema_version == CASE_SCHEMA_VERSION {
        return Ok(());
    }
    Err(VantaError::Validation(format!(
        "unsupported case schema_version `{schema_version}`"
    )))
}

fn validate_binary_path(path: &Path) -> VantaResult<()> {
    if path.as_os_str().is_empty() {
        return Err(VantaError::Validation(
            "binary_path must be non-empty".to_owned(),
        ));
    }
    if !path.is_file() {
        return Err(VantaError::Validation(format!(
            "binary_path `{}` is not a file",
            path.display()
        )));
    }
    Ok(())
}

fn validate_optional_path(path: Option<&PathBuf>, label: &str) -> VantaResult<()> {
    if let Some(value) = path
        && !value.is_file()
    {
        return Err(VantaError::Validation(format!(
            "{label} `{}` is not a file",
            value.display()
        )));
    }
    Ok(())
}

fn validate_env(env: &BTreeMap<String, String>) -> VantaResult<()> {
    for key in env.keys() {
        if is_sensitive_env_key(key) {
            return Err(VantaError::Validation(format!(
                "env key `{key}` looks sensitive and cannot be saved in a case"
            )));
        }
    }
    Ok(())
}

fn validate_remote(remote: Option<&RemoteTarget>) -> VantaResult<()> {
    if let Some(target) = remote {
        if target.host.trim().is_empty() {
            return Err(VantaError::Validation(
                "remote.host must be non-empty".to_owned(),
            ));
        }
        if target.port == 0 {
            return Err(VantaError::Validation(
                "remote.port must be non-zero".to_owned(),
            ));
        }
    }
    Ok(())
}

fn validate_runtime_limits(timeout_seconds: u64, retry_limit: u32) -> VantaResult<()> {
    if timeout_seconds == 0 {
        return Err(VantaError::Validation(
            "timeout_seconds must be greater than 0".to_owned(),
        ));
    }
    if retry_limit > 10 {
        return Err(VantaError::Validation(
            "retry_limit must be 10 or lower for MVP workflows".to_owned(),
        ));
    }
    Ok(())
}

fn is_sensitive_env_key(key: &str) -> bool {
    let normalized = key.to_ascii_uppercase();
    ["API_KEY", "TOKEN", "SECRET", "PRIVATE_KEY", "PASSWORD"]
        .iter()
        .any(|needle| normalized.contains(needle))
}

fn read_text(path: &Path) -> VantaResult<String> {
    fs::read_to_string(path).map_err(|source| VantaError::Io {
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

fn default_case_schema_version() -> String {
    CASE_SCHEMA_VERSION.to_owned()
}

fn default_timeout_seconds() -> u64 {
    10
}

fn default_retry_limit() -> u32 {
    1
}

#[cfg(test)]
mod tests {
    use std::fs;

    use super::*;

    #[test]
    fn json_and_yaml_case_parse_to_same_summary() -> anyhow::Result<()> {
        let root = unique_test_dir("json_and_yaml_case_parse_to_same_summary")?;
        let binary = root.join("chall");
        fs::write(&binary, b"elf")?;
        let json = root.join("case.json");
        let yaml = root.join("case.yaml");
        fs::write(
            &json,
            format!(r#"{{"binary_path":"{}"}}"#, binary.display()),
        )?;
        fs::write(&yaml, format!("binary_path: {}\n", binary.display()))?;

        assert_eq!(load_case(json)?.summary(), load_case(yaml)?.summary());

        fs::remove_dir_all(root)?;
        Ok(())
    }

    #[test]
    fn defaults_are_stable() -> anyhow::Result<()> {
        let root = unique_test_dir("defaults_are_stable")?;
        let binary = root.join("chall");
        fs::write(&binary, b"elf")?;
        let json = root.join("case.json");
        fs::write(
            &json,
            format!(r#"{{"binary_path":"{}"}}"#, binary.display()),
        )?;

        let case = load_case(json)?;

        assert_eq!(case.seed, 0);
        assert_eq!(case.aslr, AslrPolicy::Preserve);
        assert_eq!(case.timeout_seconds, 10);
        assert_eq!(case.retry_limit, 1);
        assert_eq!(case.mode, CaseMode::Ctf);

        fs::remove_dir_all(root)?;
        Ok(())
    }

    #[test]
    fn sensitive_env_key_is_rejected() -> anyhow::Result<()> {
        let root = unique_test_dir("sensitive_env_key_is_rejected")?;
        let binary = root.join("chall");
        fs::write(&binary, b"elf")?;
        let json = root.join("case.json");
        fs::write(
            &json,
            format!(
                r#"{{"binary_path":"{}","env":{{"API_TOKEN":"x"}}}}"#,
                binary.display()
            ),
        )?;

        assert!(load_case(json).is_err());

        fs::remove_dir_all(root)?;
        Ok(())
    }

    fn unique_test_dir(name: &str) -> anyhow::Result<PathBuf> {
        let mut root = std::env::temp_dir();
        root.push(format!("vanta-case-{name}-{}", std::process::id()));
        if root.exists() {
            fs::remove_dir_all(&root)?;
        }
        fs::create_dir_all(&root)?;
        Ok(root)
    }
}
