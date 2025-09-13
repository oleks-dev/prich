# prich: Prompt Rich LLM Templates with Pre/Postprocessing for Any Workflow

```
  ██████╗ ██████╗ ██╗ ██████╗██╗  ██╗  Prompt Rich Templating CLI Engine
  ██╔══██╗██╔══██╗██║██╔════╝██║  ██║  For LLM Prompts and Shell Commands
  ██████╔╝██████╔╝██║██║     ███████║  with Multi-Step Processing Pipelines
  ██╔═══╝ ██╔══██╗██║██║     ██╔══██║
  ██║     ██║  ██║██║╚██████╗██║  ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝
```
![Tests](https://oleks-dev.github.io/prich/badges/tests.svg)
![Coverage](https://oleks-dev.github.io/prich/badges/coverage.svg)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Documentation: prich](https://img.shields.io/badge/documentation-prich-blue?logo=materialformkdocs)](https://oleks-dev.github.io/prich)
[![Templates: prich](https://img.shields.io/badge/templates-prich-blue?logo=github)](https://github.com/oleks-dev/prich-templates)

**prich** is a lightweight CLI tool for creating, managing, executing, and sharing reusable LLM prompt pipelines for *any* use case-development, data analysis, content generation, and more. With Jinja2 templating, flexible scripting (in any language), and shareable template packages, **prich** shines for teams collaborating on standardized LLM workflows. Share templates via files, git, or cloud storage, and streamline tasks like code review, git diff analysis, or CSV data insights.

### **NOTE**: Tool is still under development so there could be potential issues.

## Why prich?
- **Any Prompt, Any Domain**: Build prompts for coding (e.g., code review), data analysis (e.g., CSV summaries), content creation, or customer support, with commands to prepare data (e.g., parse CSVs, clean text).
- **Team Collaboration**: Share template packages via git repos - just add `.prich` folder with your shared templates, file transfers, or cloud storage (e.g., Google Drive, Dropbox), ensuring consistent LLM outputs across teams.
- **Simple and Hackable**: Intuitive CLI and YAML configs make it easy to craft dynamic prompts, with support for Python, shell, or any scripting language.
- **Portable**: Isolated virtual environments (default and custom venvs) ensure dependency safety and portability; or use standard commands like git, cat, etc.

## Quick Demo
![Demo](demo.gif)

#### [Documentation Site](https://oleks-dev.github.io/prich)  

#### [See prich templates repository](https://github.com/oleks-dev/prich-templates/blob/main/templates/README.md)  

## Key Features
- **Modular Prompts**: Define prompts with Jinja2 templates and per-template YAML configs.
- **Flexible Pipelines**: Chain preprocessing, postprocessing, and llm steps (e.g., parse CSVs, list files) using any language or shell command.
- **Team-Friendly Sharing**: Package templates with dependencies for easy sharing via files, git, or cloud storage.
- **Secure venv Management**: Default (`.prich/venv/`) and custom Python venvs (e.g., `.prich/templates/code_review/scripts/venv`) isolate dependencies.
- **Simple CLI**: Commands like `prich run` and `prich install` streamline workflows.

> **Supported LLMs**: Ollama API, OpenAI API, MLX LM, STDIN (different cli tools like q chat, mlx_lm.generate, etc.)

## Quick Start
> prich requires **python 3.10+**

1. Install `prich` tool `pipx install git+https://github.com/oleks-dev/prich` (see `Installation`)
2. Initialize config (use global for the start): `prich init --global`
3. Create simple example template (`prich create <template_id> --global`): `prich create my-template -g`
4. Run template (`prich run <template_id>`): `prich run my-template`
> Note: By default prich will set up and use echo provider which just outputs the rendered template  
> To use it with LLM see `Configure .prich/config.yaml` and follow it to add your LLM provider

Optionally you can also run for the start:  
* Run template with help flag (`prich run <template_id> --help`): `prich run my-template --help`
* See installed templates: `prich list`
* See templates available for installation from the remote repo: `prich list --remote`

See [Quick Start](https://oleks-dev.github.io/prich/tutorials/quickstart/)

## Installation
See [Install & update](https://oleks-dev.github.io/prich/how-to/install/#install-prich)

## Install Templates  
See [Install templates](https://oleks-dev.github.io/prich/how-to/install-templates/)

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

## Shell Completion  
`prich` supports autocompletion for **zsh**, **bash**, and **fish**.

See [How-To Install](docs/how-to/install.md)

## Shell Completion  
`prich` supports autocompletion for **zsh**, **bash**, and **fish**.

See [How-To - Install & update - Shell Completion](https://oleks-dev.github.io/prich/how-to/install/#shell-completion)


## Template Reference  
See [Template - Content](https://oleks-dev.github.io/prich/reference/template/content/)


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
    instructions: |
      Assistant is a senior engineer who provides detailed code explanation.
    input: |
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

## Validate Templates  
Validation of templates help to detect yaml schema issues.

There are several commands that you can execute the check the templates:  

* Validate all available templates. Add `-l`/`--local` or `-g`/`--global` for validation of only local (current folder) or global templates.
  ```shell
  prich validate
  prich validate --global
  prich validate --local
  ```

* Validate one template by template id
  ```shell
  prich validate --id <template_id>
  prich validate --id code-review
  ```

* Validate selected yaml file
  ```shell
  prich validate --file <template_yaml_file>
  prich validate --file ./.prich/templates/my-template/my-template.yaml
  ```


## Advanced Features

- **Pipeline Steps**: Use Python, shell, LLM, or any language for pipeline steps (e.g., parse CSVs with pandas, clean text with awk).

- **Conditional Expressions**: Use Jinja2 style conditional expressions to execute or skip pipeline steps

- **Custom Python Venvs**: Templates like code_review use dedicated venvs for dependency isolation.


## Configure .prich/config.yaml
See [Config - Settings](https://oleks-dev.github.io/prich/reference/config/settings/)


### Supported Providers  
See [Config - Providers](https://oleks-dev.github.io/prich/reference/config/providers/)


## Contributing  
Want to create templates for data analysis, content generation, or other domains? Fork the repo, add a template package, or submit a PR! See CONTRIBUTING.md for guidelines.


## License  
MIT License. See LICENSE for details.


---
**prich**: Simplify any LLM prompt pipeline and collaborate effortlessly!