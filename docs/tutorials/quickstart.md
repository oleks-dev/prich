# Quickstart

This gets you from zero to a runnable template, then switches to a real provider.

## 1) Install prich

**Recommended (isolated):**

```bash
pipx install git+https://github.com/oleks-dev/prich
```

Alternative with uv:

```bash
uv venv prich-env
source prich-env/bin/activate
uv pip install git+https://github.com/oleks-dev/prich
```

Or clone + `pip install .`

## 2) Initialize

Use a global home for shared templates/config:
```bash
prich init --global
# creates ~/.prich and ~/.prich/venv
```

Project-local variant:
```bash
prich init
# creates ./.prich and ./.prich/venv
```

(You can have both; locals override globals by merging.)

## 3) Create Template  
Global:  
```bash
prich create my-template --global
# creates ./.prich/templates/my-template/my-template.yaml
```

Project-local variant:  
```bash
prich create my-template
# creates ~/.prich/templates/my-template/my-template.yaml
```

List what you have:  
```bash
prich list
# returns list of global overridden by project-local specific
prich list --global
# returns list of global
prich list --local
# returns list of local
```

## 4) Run it  
```bash
prich run my-template --help
# see what options are available for the template
prich run my-template
# run without options
```

By default, prich uses the echo provider (shows rendered prompt without calling an LLM).

## 5) Point to a real provider  
Open ~/.prich/config.yaml (or ./.prich/config.yaml).  
Define one or more providers (see Reference → Providers). Examples:

- Ollama (local):  
```yaml
llama3.1-8b:
  provider_type: ollama
  model: "llama3.1:8b"
  stream: false
  options:
    num_predict: 2000
```

- OpenAI-compatible HTTP:  
```yaml
openai-gpt4o:
  provider_type: openai
  configuration:
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"   # use your endpoint
  options:
    model: "gpt-4o"
```

- MLX LM (mac, local):  
```yaml
mlx-mistral-7b:
  provider_type: "mlx_local"
  model_path: "/path/to/model"
  mode: flat
  max_tokens: 3000
```

- STDIN bridge (e.g., q chat):  
```yaml
qchat:
  provider_type: stdin_consumer
  mode: plain
  call: q
  args: ["chat", "--no-interactive"]
```
> Note: All provider fields and modes are detailed in the Providers reference.


And set your default provider:

```yaml
settings:
  default_provider: "llama3.1-8b"  # example
  editor: "vim"
```


## 6) Try a real example

You can install from a remote repo or local folder/zip:
```bash
# Discover remote templates
prich list --remote
prich list --remote --tag code --tag review

# Install one
prich install summarize-git-diff --remote
```

Then run it, e.g.:
```bash
prich run summarize-git-diff --review
```
The template will execute shell steps (like git diff) and then call your configured LLM provider.

> Tip: For team repos with Python helpers, ignore venv in VCS and ask teammates to run:
> prich venv-install (or --force to rebuild).
 
