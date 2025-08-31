```
  ██████╗ ██████╗ ██╗ ██████╗██╗  ██╗  Prompt Rich Templating CLI Engine
  ██╔══██╗██╔══██╗██║██╔════╝██║  ██║  For LLM Prompts and Shell Commands
  ██████╔╝██████╔╝██║██║     ███████║  with Multi-Step Processing Pipelines
  ██╔═══╝ ██╔══██╗██║██║     ██╔══██║
  ██║     ██║  ██║██║╚██████╗██║  ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝
```
# prich

CLI tool for prompt-rich, shareable LLM templates with pre/post-processing and multi-step pipeline workflows — use it for your code review, git-diff summaries, CSV insights, logs and results analysis, and more!

- **Why prich?** Reusable Jinja2 templates, flexible steps (shell/Python/LLM), and isolated per-template venvs for dependable runs. Teams can share a `.prich/` folder or zip packages and install with one command.  
- **Supported providers:** Ollama API, OpenAI-compatible HTTP, MLX (local, mac), and a safe **echo**/STDIN mode for dry-runs or custom bridges.  

> **Status:** early, under active development.

## What you can do

- Chain steps: run `git diff`, parse files, then ask the LLM to summarize or review.
- Share and install templates from a remote repo or local zips/folders.

## 90-second Quickstart

```bash
# Install (recommended)
pipx install git+https://github.com/oleks-dev/prich

# Initialize config (global)
prich init --global

# Create & run your first template
prich create my-template
prich run my-template
```

By default, prich uses the echo provider (renders your prompt only). Switch providers by editing ~/.prich/config.yaml (see Reference → Config → [Providers](reference/config/providers.md)).

## Learn more
- Installation: [Install prich](how-to/install.md) · [Install templates](how-to/install-templates.md)
- Tutorials: [Quickstart](tutorials/quickstart.md)
- Reference: [Providers](reference/config/providers.md) · [Template](reference/template/content.md) · [CLI (auto)](reference/cli.md)
