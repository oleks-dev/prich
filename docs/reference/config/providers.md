# Providers `providers`

prich supports multiple provider backends. You can set a `settings.default_provider`, assign provider to a specific template using `settings.provider_assignments` (see Template Provider Assignments), and override it per run with `--provider <provider-name>`.

> Currently `prich` supports `OpenAI`, `Ollama`, and `MLX LM` providers, plus `STDIN Consumer` and simple `echo` output.

## Echo `echo`

Render the prompt but **do not** call a model (good for debugging, CI dry-runs, copy-paste into other tool, or pipe to stdin).

```yaml
show_prompt:
  provider_type: "echo"
  mode: "flat"      # see "Modes"
```

## OpenAI-compatible HTTP `openai`

Generic HTTP client for OpenAI and compatible services.

```yaml
openai-gpt4o:
  provider_type: "openai"
  configuration:                    # would be sent as OpenAI(**configuration)
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"   # <— use a real endpoint
  options:                          # would be sent as client.chat.completions.create(**options)
    model: "gpt-4o"
```

## Ollama HTTP (using /generate endpoint) `ollama`

Local server (using http://localhost:11434 by default)

```yaml
qwen3-8b:
  provider_type: "ollama"
  model: "llama3.1:8b"
  stream: true
  options:
    num_predict: 3000
```

Advanced/raw prompt control:  
> NOTE: Use `raw: true` and `mode: ...` for custom provider prompt mode format:  
```yaml
qwen3-8b-custom:
  provider_type: "ollama"
  model: "qwen3:8b"    # model name installed in your Ollama
  mode: "flat"         # optional [str] name of prich config provider prompt template mode (see config.yaml `provider_modes`)
  base_url: "http://localhost:11434"  # optional [str] - Ollama server URL 
  think: true          # optional [bool] - for thinking models only to enable/disable
  stream: true         # optional [bool] - stream output
  suffix: ""           # optional [str]
  raw: true            # optional [bool] - send prompt without default model prompt template, use with `mode: "..."`
  format: "json"       # optional [dict | str] - "json" or json schema for specific output format
  options:             # optional [dict] - model options (vary depending on used model)
    num_predict: 5000
```

## STDIN consumer (bridge to CLIs) `stdin_consumer`

Send prompts to a command via STDIN and read STDOUT (e.g., q chat, mlx_lm.generate).

#### Q Chat  
```yaml
qchat:
  provider_type: "stdin_consumer"
  mode: "flat"
  call: "q"                      # executable file
  args: ["chat", "--no-interactive"]  # optional arguments
  strip_output_prefix: "> "      # optional [str] - strip prefix text from step output
  slice_output_start: 0          # optional [int] - slice step output text starting from N
  slice_output_end: -1           # optional [int] - slice step output text ending at N (negative counts from the back)
```

#### MLX LM Generate  
```yaml
  mlx-mistral-7b-cli:
    provider_type: stdin_consumer
    mode: plain
    call: "mlx_lm.generate"
    args:
      - "--model"
      - "/Users/guest/.cache/huggingface/hub/models--mlx-community--Mistral-7B-Instruct-v0.3-4bit/snapshots/a4b8f870474b0eb527f466a03fbc187830d271f5"
      - "--prompt"
      - "-"
    output_regex: "^==========\\n((?:.|\\n)+)\\n\\=\\=\\=\\=\\=\\=\\=\\=\\=\\=(?:.|\\n)+$"
```
