//! Model provider configuration and inference fallback.

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::{VantaError, VantaResult};

/// Current provider config schema version.
pub const PROVIDER_CONFIG_SCHEMA_VERSION: &str = "vanta.providers.v1";

/// Default provider config file name under VANTA_HOME.
pub const PROVIDER_CONFIG_FILE: &str = "providers.json";

/// Provider configuration stored only in the user-local Vanta home.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct ProviderConfig {
    /// Config schema version.
    pub schema_version: String,
    /// Default profile name.
    pub default_profile: String,
    /// OpenAI-compatible provider config.
    #[serde(default)]
    pub openai_compatible: Option<OpenAiCompatibleConfig>,
    /// Local llama process fallback config.
    #[serde(default)]
    pub local_llama_process: Option<LocalLlamaProcessConfig>,
}

/// OpenAI-compatible chat completion provider config.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct OpenAiCompatibleConfig {
    /// Base URL such as http://127.0.0.1:8000 or https://api.openai.com.
    pub base_url: String,
    /// Model name.
    pub model: String,
    /// Optional API key file path under user control.
    #[serde(default)]
    pub api_key_path: Option<PathBuf>,
    /// Request timeout in seconds.
    #[serde(default = "default_timeout_seconds")]
    pub timeout_seconds: u64,
}

/// Local CUDA llama process config.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct LocalLlamaProcessConfig {
    /// Command argv with placeholders: {model_path}, {prompt_file}, {output_file}.
    pub command: Vec<String>,
    /// Local model file path.
    pub model_path: PathBuf,
    /// Process timeout in seconds.
    #[serde(default = "default_local_timeout_seconds")]
    pub timeout_seconds: u64,
}

/// Model inference request.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct ModelRequest {
    /// System instruction.
    pub system_prompt: String,
    /// User prompt.
    pub user_prompt: String,
}

/// Model inference response.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct ModelResponse {
    /// Provider used for the response.
    pub provider: String,
    /// Model name or path summary.
    pub model: String,
    /// Text returned by the model.
    pub text: String,
    /// Whether fallback was used.
    pub fallback_used: bool,
}

/// Provider availability summary.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
pub struct ProviderStatus {
    /// Path checked for provider config.
    pub config_path: PathBuf,
    /// Whether provider config exists.
    pub config_exists: bool,
    /// Whether OpenAI-compatible config is present.
    pub openai_configured: bool,
    /// Whether local llama process config is present.
    pub local_llama_configured: bool,
    /// Human-readable default profile.
    pub default_profile: Option<String>,
}

impl ProviderConfig {
    /// Build local llama fallback-only config.
    pub fn local_llama(command: Vec<String>, model_path: PathBuf) -> Self {
        Self {
            schema_version: PROVIDER_CONFIG_SCHEMA_VERSION.to_owned(),
            default_profile: "local".to_owned(),
            openai_compatible: None,
            local_llama_process: Some(LocalLlamaProcessConfig {
                command,
                model_path,
                timeout_seconds: default_local_timeout_seconds(),
            }),
        }
    }
}

/// Return the configured Vanta home directory.
pub fn vanta_home() -> VantaResult<PathBuf> {
    if let Ok(value) = env::var("VANTA_HOME") {
        return Ok(PathBuf::from(value));
    }
    let home = env::var("HOME").map_err(|_source| {
        VantaError::Validation("HOME is not set; set VANTA_HOME for Vanta config".to_owned())
    })?;
    Ok(PathBuf::from(home).join(".vanta"))
}

/// Return the default provider config path.
pub fn provider_config_path() -> VantaResult<PathBuf> {
    Ok(vanta_home()?.join(PROVIDER_CONFIG_FILE))
}

/// Read provider config from the user-local Vanta home.
pub fn load_provider_config() -> VantaResult<ProviderConfig> {
    let path = provider_config_path()?;
    let text = fs::read_to_string(&path).map_err(|source| VantaError::Io {
        path: path.clone(),
        source,
    })?;
    let config: ProviderConfig =
        serde_json::from_str(&text).map_err(|source| VantaError::Json {
            path: path.clone(),
            source,
        })?;
    validate_provider_config(&config)?;
    Ok(config)
}

/// Write provider config to the user-local Vanta home.
pub fn write_provider_config(config: &ProviderConfig) -> VantaResult<PathBuf> {
    validate_provider_config(config)?;
    let home = vanta_home()?;
    create_dir_all(&home)?;
    let path = home.join(PROVIDER_CONFIG_FILE);
    write_json_pretty(&path, config)?;
    Ok(path)
}

/// Return provider status without contacting remote providers.
pub fn provider_status() -> VantaResult<ProviderStatus> {
    let path = provider_config_path()?;
    if !path.exists() {
        return Ok(ProviderStatus {
            config_path: path,
            config_exists: false,
            openai_configured: false,
            local_llama_configured: false,
            default_profile: None,
        });
    }
    let config = load_provider_config()?;
    Ok(ProviderStatus {
        config_path: path,
        config_exists: true,
        openai_configured: config.openai_compatible.is_some(),
        local_llama_configured: config.local_llama_process.is_some(),
        default_profile: Some(config.default_profile),
    })
}

/// Run inference with OpenAI-compatible provider first, then local llama fallback.
pub fn infer_with_fallback(
    config: &ProviderConfig,
    request: &ModelRequest,
) -> VantaResult<ModelResponse> {
    if let Some(openai) = &config.openai_compatible {
        match infer_openai_compatible(openai, request) {
            Ok(mut response) => {
                response.fallback_used = false;
                return Ok(response);
            }
            Err(_error) => {
                if let Some(local) = &config.local_llama_process {
                    return infer_local_llama(local, request, true);
                }
                return Err(VantaError::Http(format!(
                    "openai_compatible provider failed and local_llama_process is not configured: {_error}"
                )));
            }
        }
    }
    if let Some(local) = &config.local_llama_process {
        return infer_local_llama(local, request, config.openai_compatible.is_some());
    }
    Err(VantaError::Validation(
        "no model provider configured in $VANTA_HOME/providers.json".to_owned(),
    ))
}

fn infer_openai_compatible(
    config: &OpenAiCompatibleConfig,
    request: &ModelRequest,
) -> VantaResult<ModelResponse> {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(config.timeout_seconds))
        .build()
        .map_err(|source| VantaError::Http(source.to_string()))?;
    let mut builder = client
        .post(openai_chat_url(&config.base_url))
        .json(&openai_body(config, request));
    if let Some(key) = read_api_key(config.api_key_path.as_ref())? {
        builder = builder.bearer_auth(key);
    }
    let response = builder
        .send()
        .map_err(|source| VantaError::Http(source.to_string()))?;
    if !response.status().is_success() {
        return Err(VantaError::Http(format!(
            "provider returned {}",
            response.status()
        )));
    }
    let value: Value = response
        .json()
        .map_err(|source| VantaError::Http(source.to_string()))?;
    Ok(ModelResponse {
        provider: "openai_compatible".to_owned(),
        model: config.model.clone(),
        text: extract_openai_text(&value)?,
        fallback_used: false,
    })
}

fn infer_local_llama(
    config: &LocalLlamaProcessConfig,
    request: &ModelRequest,
    fallback_used: bool,
) -> VantaResult<ModelResponse> {
    let temp_dir = unique_temp_dir()?;
    create_dir_all(&temp_dir)?;
    let prompt_file = temp_dir.join("prompt.txt");
    let output_file = temp_dir.join("output.txt");
    fs::write(
        &prompt_file,
        format!("{}\n\n{}", request.system_prompt, request.user_prompt),
    )
    .map_err(|source| VantaError::Io {
        path: prompt_file.clone(),
        source,
    })?;
    let argv = render_local_command(config, &prompt_file, &output_file)?;
    run_local_command(&argv, config.timeout_seconds)?;
    let text = read_local_output(&output_file)?;
    let _ignored = fs::remove_dir_all(&temp_dir);
    Ok(ModelResponse {
        provider: "local_llama_process".to_owned(),
        model: config.model_path.display().to_string(),
        text,
        fallback_used,
    })
}

fn run_local_command(argv: &[String], _timeout_seconds: u64) -> VantaResult<()> {
    let program = argv
        .first()
        .ok_or_else(|| VantaError::Validation("local llama command is empty".to_owned()))?;
    let status = Command::new(program)
        .args(&argv[1..])
        .status()
        .map_err(|source| VantaError::Process(source.to_string()))?;
    if status.success() {
        return Ok(());
    }
    Err(VantaError::Process(format!(
        "local llama exited with {status}"
    )))
}

fn render_local_command(
    config: &LocalLlamaProcessConfig,
    prompt_file: &Path,
    output_file: &Path,
) -> VantaResult<Vec<String>> {
    if config.command.is_empty() {
        return Err(VantaError::Validation(
            "local llama command is empty".to_owned(),
        ));
    }
    Ok(config
        .command
        .iter()
        .map(|item| {
            item.replace("{model_path}", &config.model_path.display().to_string())
                .replace("{prompt_file}", &prompt_file.display().to_string())
                .replace("{output_file}", &output_file.display().to_string())
        })
        .collect())
}

fn validate_provider_config(config: &ProviderConfig) -> VantaResult<()> {
    if config.schema_version != PROVIDER_CONFIG_SCHEMA_VERSION {
        return Err(VantaError::Validation(format!(
            "unsupported provider schema_version `{}`",
            config.schema_version
        )));
    }
    if config.openai_compatible.is_none() && config.local_llama_process.is_none() {
        return Err(VantaError::Validation(
            "at least one provider must be configured".to_owned(),
        ));
    }
    Ok(())
}

fn openai_chat_url(base_url: &str) -> String {
    format!("{}/v1/chat/completions", base_url.trim_end_matches('/'))
}

fn openai_body(config: &OpenAiCompatibleConfig, request: &ModelRequest) -> Value {
    serde_json::json!({
        "model": config.model,
        "messages": [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt}
        ],
        "temperature": 0.2
    })
}

fn extract_openai_text(value: &Value) -> VantaResult<String> {
    let text = value
        .get("choices")
        .and_then(Value::as_array)
        .and_then(|choices| choices.first())
        .and_then(|choice| choice.get("message"))
        .and_then(|message| message.get("content"))
        .and_then(Value::as_str);
    text.map(str::to_owned).ok_or_else(|| {
        VantaError::Http("chat completion missing choices[0].message.content".to_owned())
    })
}

fn read_api_key(path: Option<&PathBuf>) -> VantaResult<Option<String>> {
    let Some(path) = path else {
        return Ok(None);
    };
    let text = fs::read_to_string(path).map_err(|source| VantaError::Io {
        path: path.clone(),
        source,
    })?;
    Ok(Some(text.trim().to_owned()))
}

fn read_local_output(path: &Path) -> VantaResult<String> {
    fs::read_to_string(path).map_err(|source| VantaError::Io {
        path: path.to_path_buf(),
        source,
    })
}

fn unique_temp_dir() -> VantaResult<PathBuf> {
    let mut path = env::temp_dir();
    path.push(format!(
        "vanta-llama-{}-{}",
        std::process::id(),
        time::OffsetDateTime::now_utc().unix_timestamp_nanos()
    ));
    Ok(path)
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

fn default_timeout_seconds() -> u64 {
    30
}

fn default_local_timeout_seconds() -> u64 {
    120
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::io::{Read, Write};
    use std::net::TcpListener;
    use std::thread;

    use super::*;

    #[test]
    fn local_llama_command_uses_prompt_and_output_files() -> anyhow::Result<()> {
        let root = unique_test_dir("local_llama_command_uses_prompt_and_output_files")?;
        let output_text = root.join("model-output.txt");
        fs::write(&output_text, "local answer")?;
        let config = LocalLlamaProcessConfig {
            command: vec![
                "sh".to_owned(),
                "-c".to_owned(),
                format!("cp {} {{output_file}}", output_text.display()),
            ],
            model_path: root.join("model.gguf"),
            timeout_seconds: 10,
        };
        let request = ModelRequest {
            system_prompt: "sys".to_owned(),
            user_prompt: "user".to_owned(),
        };

        let response = infer_local_llama(&config, &request, true)?;

        assert_eq!(response.provider, "local_llama_process");
        assert_eq!(response.text, "local answer");
        assert!(response.fallback_used);
        fs::remove_dir_all(root)?;
        Ok(())
    }

    #[test]
    fn openai_failure_falls_back_to_local_llama() -> anyhow::Result<()> {
        let root = unique_test_dir("openai_failure_falls_back_to_local_llama")?;
        let output_text = root.join("model-output.txt");
        fs::write(&output_text, "fallback answer")?;
        let config = ProviderConfig {
            schema_version: PROVIDER_CONFIG_SCHEMA_VERSION.to_owned(),
            default_profile: "default".to_owned(),
            openai_compatible: Some(OpenAiCompatibleConfig {
                base_url: "http://127.0.0.1:9".to_owned(),
                model: "bad".to_owned(),
                api_key_path: None,
                timeout_seconds: 1,
            }),
            local_llama_process: Some(LocalLlamaProcessConfig {
                command: vec![
                    "sh".to_owned(),
                    "-c".to_owned(),
                    format!("cp {} {{output_file}}", output_text.display()),
                ],
                model_path: root.join("model.gguf"),
                timeout_seconds: 10,
            }),
        };

        let response = infer_with_fallback(&config, &sample_request())?;

        assert_eq!(response.text, "fallback answer");
        assert!(response.fallback_used);
        fs::remove_dir_all(root)?;
        Ok(())
    }

    #[test]
    fn openai_compatible_parses_chat_completion() -> anyhow::Result<()> {
        let listener = TcpListener::bind("127.0.0.1:0")?;
        let addr = listener.local_addr()?;
        let handle = thread::spawn(move || {
            if let Ok((mut stream, _addr)) = listener.accept() {
                let mut buffer = [0_u8; 2048];
                let _read = stream.read(&mut buffer);
                let body = r#"{"choices":[{"message":{"content":"remote answer"}}]}"#;
                let response = format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                    body.len(),
                    body
                );
                let _write = stream.write_all(response.as_bytes());
            }
        });
        let config = OpenAiCompatibleConfig {
            base_url: format!("http://{addr}"),
            model: "mock".to_owned(),
            api_key_path: None,
            timeout_seconds: 2,
        };

        let response = infer_openai_compatible(&config, &sample_request())?;

        assert_eq!(response.text, "remote answer");
        handle
            .join()
            .map_err(|_error| anyhow::anyhow!("mock server failed"))?;
        Ok(())
    }

    fn sample_request() -> ModelRequest {
        ModelRequest {
            system_prompt: "sys".to_owned(),
            user_prompt: "user".to_owned(),
        }
    }

    fn unique_test_dir(name: &str) -> anyhow::Result<PathBuf> {
        let mut root = std::env::temp_dir();
        root.push(format!("vanta-provider-{name}-{}", std::process::id()));
        if root.exists() {
            fs::remove_dir_all(&root)?;
        }
        fs::create_dir_all(&root)?;
        Ok(root)
    }
}
