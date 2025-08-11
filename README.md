# prich: Prompt Rich LLM Templates with Pre/Postprocessing for Any Workflow

```
  ██████╗ ██████╗ ██╗ ██████╗██╗  ██╗  Prompt Rich Templating CLI Engine
  ██╔══██╗██╔══██╗██║██╔════╝██║  ██║  For LLM Prompts and Shell Commands
  ██████╔╝██████╔╝██║██║     ███████║  with Multi-Step Processing Pipelines
  ██╔═══╝ ██╔══██╗██║██║     ██╔══██║
  ██║     ██║  ██║██║╚██████╗██║  ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝
```

**prich** is a lightweight CLI tool for creating, managing, executing, and sharing reusable LLM prompt pipelines for *any* use case-development, data analysis, content generation, and more. With Jinja2 templating, flexible scripting (in any language), and shareable template packages, **prich** shines for teams collaborating on standardized LLM workflows. Share templates via files, git, or cloud storage, and streamline tasks like code review, git diff analysis, or CSV data insights.

### **NOTE**: Tool is still under development so there could be potential issues.

## Why prich?
- **Any Prompt, Any Domain**: Build prompts for coding (e.g., code review), data analysis (e.g., CSV summaries), content creation, or customer support, with commands to prepare data (e.g., parse CSVs, clean text).
- **Team Collaboration**: Share template packages via git repos - just add `.prich` folder with your shared templates, file transfers, or cloud storage (e.g., Google Drive, Dropbox), ensuring consistent LLM outputs across teams.
- **Simple and Hackable**: Intuitive CLI and YAML configs make it easy to craft dynamic prompts, with support for Python, shell, or any scripting language.
- **Portable**: Isolated virtual environments (default and custom venvs) ensure dependency safety and portability; or use standard commands like git, cat, etc.

#### [See prich templates repository for examples](https://github.com/oleks-dev/prich-templates/blob/main/templates/README.md)

## Key Features
- **Modular Prompts**: Define prompts with Jinja2 templates and per-template YAML configs.
- **Flexible Pipelines**: Chain preprocessing, postprocessing, and llm steps (e.g., parse CSVs, list files) using any language or shell command.
- **Team-Friendly Sharing**: Package templates with dependencies for easy sharing via files, git, or cloud storage.
- **Secure venv Management**: Default (`.prich/venv/`) and custom Python venvs (e.g., `.prich/templates/code_review/scripts/venv`) isolate dependencies.
- **Simple CLI**: Commands like `prich run` and `prich install` streamline workflows.

## Execution Example

```commandline
➜ prich run summarize-git-diff --review
prich v0.1.0 - CLI for reusable rich LLM prompts with script pipelines
Template: Summarize git diff 1.0, Args: provider=llama3.1-8b, review=True
Generate a summary and review of differences between local code and remote or committed states.

Step #1: Run git diff working vs last commit ("when" expression "working_vs_last_commit or (not working_vs_last_commit and not working_vs_remote and not committed_vs_remote and not remote_vs_local)" is True)
Execute command git diff HEAD

Step #2: Get current branch ("when" expression "not working_vs_last_commit" is True)
Execute command git rev-parse --abbrev-ref HEAD

Step #6: Ask to summarize the diff
LLM Response:
**Summary**

The changes made to the `README.md` file are significant, with a substantial addition of content related to configuring and using different providers for LLM (Large Language Model) processing. The new section covers supported providers, including 
`echo`, `openai`, `mlx_local`, `ollama`, and `stdin_consumer`. Each provider has its own configuration options and rendering modes.

**Review**

The changes are well-structured and easy to follow, with clear headings and concise descriptions for each provider. The use of code blocks and YAML syntax makes it straightforward to understand the configuration options for each provider.

Some notable improvements include:

* **Expanded documentation**: The new section provides detailed information on configuring providers, including supported models, rendering modes, and configuration options.
* **Improved readability**: The addition of clear headings, concise descriptions, and code blocks enhances the overall readability of the document.
* **Increased flexibility**: The introduction of multiple providers allows users to choose the best option for their specific use case.

However, there are a few minor suggestions for improvement:

* **Consistency in formatting**: While the new section is well-formatted, some sections (e.g., `provider_type`) have inconsistent indentation or spacing.
* **Clarification on usage**: Some providers (e.g., `stdin_consumer`) could benefit from additional guidance on how to use them effectively.

Overall, the changes are a significant improvement to the document, providing valuable information for users and contributors.
```

## Installation
### **Set up prich**:
    
Until prich is published on PyPI, you can install it directly from GitHub:  
 
**Recommended: Use `pipx`**
```bash
pipx install git+https://github.com/oleks-dev/prich
```

> This installs prich in an isolated environment, ideal for CLI tools.  
> Make sure pipx is installed (`pip install pipx && pipx ensurepath`).

**Alternative: Use `uv`**
```bash
uv venv prich-env
source prich-env/bin/activate
uv pip install git+https://github.com/oleks-dev/prich
```

**Manual**
```bash
git clone https://github.com/oleks-dev/prich.git
cd prich
python -m venv .venv
source .venv/bin/activate
pip install .
```

**Help**  
To display possible commands 
```bash
prich --help
```

### **Initialize prich**:
**prich** uses nodejs-like home/local folder configurations for flexible usage of the configs and templates per project.  

   - Local folder based
       ```bash
       prich init
       ```
       > Creates `.prich/` with a default preprocessing venv (`.prich/venv/`) and config file.  

   - Global user folder based
       ```bash
       prich init -g
       ```
     
       > Creates `~/.prich/` with a default preprocessing venv (`~/.prich/venv/`) and config file.

## Install Templates

There are several ways to install templates. You can install them from remote repository or from local zip archive or template folder.
For local option download or clone a template package (e.g., csv_analysis_template/) as a folder or a zip file and install it:

### Install template from remote GitHub Template Repository
Templates are stored in this [github prich-templates repository](https://www.github.com/oleks-dev/prich-templates)

- **List Available Remote Templates for Installation**

    ```bash
    prich list --remote
    ```

    ```bash
    prich list --remote --tag code --tag review
    ```

- **Install Template from *prich-templates* Repository**

    ```bash
    prich install <template_id> --remote
    ```

    ```bash
    prich install <template_id> --remote --global
    ```


### Install from a local template zip file:

```bash
prich install <template-zip-file>.zip
```

### Install from a local template folder:

```bash
prich install <template-folder>
```

```bash
prich install ./code-review
```

This copies files, sets up venvs, and installs dependencies - if python is used there.


## Usage

- **List Templates**:  
    List both globally (home folder) and locally (current folder) installed templates where local templates overloads any same global
    ```bash
    prich list
    ```

    List only globally (home folder) installed templates
    ```bash
    prich list -g
    ```

    List only locally (current folder) installed templates
    ```bash
    prich list -l
    ```

    Output:
    ```
    - git-diff: Analyze and summarize git changes
    - code-review: Review Python files for code quality
    - csv-analysis: Analyze CSV data and generate business insights
    ```

- **Run a Template**:  
    See template help description and args
    ```bash
    prich run code-review --help
    ```

    Run template
    ```bash
    prich run code-review --file myscript.py
    ```

## Team Collaboration

**prich** is designed for teams to share and standardize LLM prompts across workflows:

- **Share Templates in your repository**:  
    Store `.prich/` folder with templates in your repository and work on them together.  
    For templates with python scripts you can add `venv` folders to `.gitignore` and ask team to install venvs personally:

    ```bash
    prich venv-install <template_name>
    ```

    or to re-install:

    ```bash
    prich venv-install <template_name> --force
    ```


- **Share Templates as files**:
    Package templates in a git repo, shared drive, or cloud storage (e.g., Google Drive, Dropbox)
    You can use complete template folder or compress it into a zip archive.  
    Team members install templates:

    ```bash
    git clone https://github.com/your-team/team-prich-templates.git
    prich install team-prich-templates/csv-analysis
    prich install team-prich-templates/code-review.zip
    ```

    Or download from cloud storage and install via `prich install`.

- **Standardize Workflows**:
Use shared templates to ensure consistent LLM outputs, whether for code reviews (“Add docstrings”) or business insights (“Focus marketing on Laptops”).

- **Cross-Functional Use**:
Developers, data analysts, marketers, or support teams can use prich for their prompts, with templates tailored to each domain.


## Template Creation Guide

See [templates_guide.md](templates_guide.md)

## Example Templates

```yaml
id: "explain-code"
name: "Explain Code"
schema_version: "1.0"
version: "1.0"
author: "prich"
description: Provide detailed code explanation
tags: ["code"]
steps:
  - name: "Ask to explain code"
    type: llm
    prompt:
      system: |
        Assistant is a senior engineer who provides detailed code explanation.
      user: |
        Explain what this{% if lang %} {{ lang }}{% endif %} code does:
        File: {{ file }}
        ```{% if lang %}{{ lang.lower() }}{% endif %}
        {{ file | include_file }}
        ```
usage_examples:
  - "explain-code --file mycode.py"
  - "explain-code --file ./mycode.py --lang python"
  - "explain-code --file ./proj/mycode.js --lang javascript"
variables:
  - name: file
    description: File to review
    cli_option: --file
    required: true
    type: str
  - name: lang
    description: Code language (ex. Python, JavaScript, Java)
    cli_option: --lang
    required: false
    default: null
    type: str
```

```yaml
id: "summarize-git-diff"
name: "Summarize git diff"
schema_version: "1.0"
version: "1.0"
author: "prich"
description: Generate a summary and review of differences between local code and remote or committed states.
tags: ["code", "git", "diff", "review"]
steps:
  - name: "Run git diff working vs last commit"
    when: "working_vs_last_commit or (not working_vs_last_commit and not working_vs_remote and not committed_vs_remote and not remote_vs_local)"
    type: command
    call: "git"
    args: ["diff", "HEAD"]
    output_variable: "git_diff"

  - name: "Get current branch"
    when: "not working_vs_last_commit"
    type: command
    call: "git"
    args: ["rev-parse", "--abbrev-ref", "HEAD"]
    output_variable: "current_branch"

  - name: "Run git diff working vs remote"
    when: "working_vs_remote"
    type: command
    call: "git"
    args: ["diff", "origin/{{current_branch}}"]
    output_variable: "git_diff"

  - name: "Run git diff committed vs remote"
    when: "committed_vs_remote"
    type: command
    call: "git"
    args: ["diff", "origin/{{current_branch}}..HEAD"]
    output_variable: "git_diff"

  - name: "Run git diff remote vs local"
    when: "remote_vs_local"
    type: command
    call: "git"
    args: ["diff", "HEAD..origin/{{current_branch}}"]
    output_variable: "git_diff"

  - name: "Ask to summarize the diff"
    type: llm
    prompt:
      system: |
        Assistant is a senior engineer who makes a git diff summarization{% if review %} and detailed review{% endif %} in natural language.
      user: |
        Summarize {% if review %} and review {% endif %}the following:
        ```text
        {{ git_diff }}
        ```
usage_examples:
  - "summarize-git-diff"
  - "summarize-git-diff --review"
  - "summarize-git-diff --working-vs-last-commit"
  - "summarize-git-diff --working-vs-last-commit --review"
  - "summarize-git-diff --working-vs-remote"
  - "summarize-git-diff --committed-vs-remote"
  - "summarize-git-diff --remote-vs-local"
variables:
  - name: working_vs_last_commit
    description: "Unstaged working changes"
    cli_option: --working-vs-last-commit
    required: false
    type: bool
  - name: working_vs_remote
    description: "All uncommitted + unpushed vs remote"
    cli_option: --working-vs-remote
    required: false
    type: bool
  - name: committed_vs_remote
    description: "Only unpushed commits"
    cli_option: --committed-vs-remote
    required: false
    type: bool
  - name: remote_vs_local
    description: "Changes on remote not in local"
    cli_option: --remote-vs-local
    required: false
    type: bool
  - name: review
    description: "Make deeper review additionally"
    cli_option: --review
    required: false
    type: bool
```

## Advanced Features

- **Pipeline Steps**: Use Python, shell, LLM, or any language for pipeline steps (e.g., parse CSVs with pandas, clean text with awk).

- **Conditional Expressions**: Use Jinja2 style conditional expressions to execute or skip pipeline steps

- **Custom Python Venvs**: Templates like code_review use dedicated venvs for dependency isolation.

## Configure .prich/config.yaml

### Settings
```python
settings:
  default_provider: "llama3.1-8b"
  editor: "vim"
```
* `default_provider`: Name of the provider from providers that would be used by default in all templates if not overloaded with the `--provider <provider_name>` argument.
* `editor`: Editor execution command used in by some commands (default: `vi`)

### Supported Providers
`provider_type`:
* `echo` - Just output rendered prompt as is without any LLM processing, could be used to save or send to LLM later  
  Structure:
    ```python
      provider_type: Literal["echo"]
      mode: Optional[str]  # Prompt Provider Mode (for prompt templates)
    ```
  Example:
    ```yaml
      show_prompt:
        provider_type: "echo"
        mode: "flat"
    ```
* `openai` - HTTP provider to work with OpenAI API compatible model providers  
  Structure:
    ```python
      provider_type: Literal["openai"]
      configuration: dict  # Configuration params (like api_key and base_url)
      options: dict  # Optional params (like model)
    ```
  Example:
    ```yaml
      openai-gpt4o:
        provider_type: "openai"
        configuration:
          api_key: "${OPENAI_API_KEY}"
          base_url: "https://openai.com/api"
        options:
          model: "gpt-4o"
    ```
* `mlx_local` - (for mac) Use MLX LM library with your local model  
  Structure:  
    ```python
      provider_type: Literal["mlx_local"]
      model_path: str  # Path to a local file with a model
      mode: Optional[str]  # Prompt Provider Mode (for prompt templates)
      max_tokens: Optional[int] = None  # The maximum number of tokens. Use -1 for an infinite generator. Default: 256
      temp: Optional[float] = None  # The temperature for sampling, if 0 the argmax is used. Default: 0
      top_p: Optional[float] = None  # Nulceus sampling, higher means model considers more less likely words.
      min_p: Optional[float] = None  # The minimum value (scaled by the top token's probability) that a token probability must have to be considered.
      min_tokens_to_keep: Optional[int] = None  # Minimum number of tokens that cannot be filtered by min_p sampling.
      top_k: Optional[int] = None  # The top k tokens ranked by probability to constrain the sampling to.
    ```
  Example:
    ```yaml
      mlx-mistral-7b:
        provider_type: "mlx_local"
        mode: "mistral-instruct"
        model_path: "~/.cache/huggingface/hub/models--mlx-community--Mistral-7B-Instruct-v0.3-4bit/snapshots/a4b8f870474b0eb527f466a03fbc187830d271f5"
        max_tokens: 3000
    ```
* `ollama` - HTTP provider to work with Ollama models  
  Structure:
    ```python
      provider_type: Literal["ollama"]
      model: str  # ollama model name
      mode: Optional[str]  # Prompt Provider Mode (for prompt templates)
      base_url: Optional[str] = None  # ollama url
      options: Optional[dict] = None  # additional model options
      stream: Optional[bool] = None  #  if false the response will be returned as a single response object, rather than a stream of objects
      suffix: Optional[str] = None  # the text after the model response
      template: Optional[str] = None  # custom prompt template
      raw: Optional[bool] = None  # if true no formatting will be applied to the prompt. You may choose to use the raw parameter if you are specifying a full templated prompt in your request to the API
      format: Optional[dict | str] = None  #  the format to return a response in. Format can be json or a JSON schema
      think: Optional[bool] = None  # (for thinking models) should the model think before responding?
    ```
  Examples:
    ```yaml
      llama3.1-8b:
        provider_type: ollama
        model: "llama3.1:8b"
        stream: false
        options:
          num_predict: 2000
    ```
    ```yaml
      qwen3-8b:
        provider_type: ollama
        model: "qwen3:8b"
        stream: true
        think: true
        options:
          num_predict: 3000
    ```
  Use `raw: true` and `mode: ...` for custom provider prompt mode format:  
    ```yaml
      qwen3-8b-raw:
        provider_type: ollama
        model: "qwen3:8b"
        mode: flat
        raw: true
        stream: true
        think: false
        options:
          num_predict: 3000
    ```
* `stdin_consumer` - STDIN provider to work with local models that support STDIN (for example with `q chat`)
  Structure:
    ```python
      provider_type: Literal["stdin_consumer"]
      mode: Optional[str]  # Prompt Provider Mode (for prompt templates)
      call: Optional[str] = None  # command call for shell execution
      args: Optional[List[str]] = None  # arguments for shell execution
      stdout_strip_prefix: Optional[str] = None  # strip prefix string from the response
      stdout_slice_start: Optional[int] = None  # slice stdout from character number
      stdout_slice_end: Optional[int] = None  # slice stdout to character number
    ```
  Example:
    ```yaml
      qchat:
        provider_type: stdin_consumer
        mode: flat
        call: q
        args:
          - chat
          - --no-interactive
    ```

### Provider Mode `mode`  
Use to specify how the prompt would be constructed for the LLM, you can modify or add your own as needed in the `config.yaml` - `provider_modes`.
There are three fields available that are used in the template prompts. It could be `prompt` for plain string or `system` and `user` for instructions and query, or just `user` for a query.

* `plain`
```text
{prompt}
```
* `flat`
```text
### System:
{system}

### User:
{user}

### Assistant:
```
```text
### User:
{user}

### Assistant:
```
* `chatml`
```json
[
  {"role": "system", "content": system},
  {"role": "user", "content": user}
]
```
```json
[
  {"role": "user", "content": user}
]
```

* `mistral-instruct` and `llama2-chat`
```text
<s>[INST]
{system}

{user}
[/INST]
```
```text
<s>[INST]
{user}
[/INST]
```
* `anthropic`
```text
Human: {system}

{user}

Assistant:
```
```text
Human: {user}

Assistant:
```

## Contributing

Want to create templates for data analysis, content generation, or other domains? Fork the repo, add a template package, or submit a PR! See CONTRIBUTING.md for guidelines.


## License

MIT License. See LICENSE for details.



---
**prich**: Simplify any LLM prompt pipeline and collaborate effortlessly!