# prich: Craft Rich LLM Prompts for Any Workflow

```
  ██████╗ ██████╗ ██╗ ██████╗██╗  ██╗  Rich Templating CLI Engine
  ██╔══██╗██╔══██╗██║██╔════╝██║  ██║  For LLM Prompts and Shell Commands
  ██████╔╝██████╔╝██║██║     ███████║  with Multi-Step processing Pipelines
  ██╔═══╝ ██╔══██╗██║██║     ██╔══██║
  ██║     ██║  ██║██║╚██████╗██║  ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝
```

**prich** is a lightweight CLI tool for creating, managing, executing, and sharing reusable LLM prompt pipelines for *any* use case-development, data analysis, content generation, and more. With Jinja2 templating, flexible scripting (in any language), and shareable template packages, **prich** shines for teams collaborating on standardized LLM workflows. Share templates via files, git, or cloud storage, and streamline tasks like code review, git diff analysis, or CSV data insights.

### **NOTE**: Tool is still under development so there could be potential issues.

## Why prich?
- **Any Prompt, Any Domain**: Build prompts for coding (e.g., code review), data analysis (e.g., CSV summaries), content creation, or customer support, with preprocessing to prepare data (e.g., parse CSVs, clean text).
- **Team Collaboration**: Share template packages via git repos, file transfers, or cloud storage (e.g., Google Drive, Dropbox), ensuring consistent LLM outputs across teams.
- **Simple and Hackable**: Intuitive CLI and YAML configs make it easy to craft dynamic prompts, with support for Python, shell, or any scripting language.
- **Secure and Portable**: Isolated virtual environments (default and custom venvs) ensure dependency safety and portability.

## Key Features
- **Modular Prompts**: Define prompts with Jinja2 templates and per-template YAML configs.
- **Flexible Pipelines**: Chain preprocessing, postprocessing, and llm steps (e.g., parse CSVs, list files) using any language or shell command.
- **Team-Friendly Sharing**: Package templates with dependencies for easy sharing via files, git, or cloud storage.
- **Secure venv Management**: Default (`.prich/venv/`) and custom Python venvs (e.g., `.prich/templates/code_review/preprocess/venv`) isolate dependencies.
- **Simple CLI**: Commands like `prich run` and `prich install` streamline workflows.

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
**prich** uses nodejs-like home/local folder configurtions for flexible usage of the configs and templates per project.  

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

## Usage

- **Install a Template**:
    Download or clone a template package (e.g., csv_analysis_template/) and install it:

    ```bash
    prich install ./csv_analysis
    ```

    This copies files, sets up venvs, and installs dependencies.

- **List Templates**:
    ```bash
    prich list
    ```

    Output:
    ```
    - git_diff: Analyze and summarize git changes
    - code_review: Review Python files for code quality
    - csv_analysis: Analyze CSV data and generate business insights
    ```

- **Run a Template**:  
    See template help description and args
    ```bash
    prich run csv_analysis --help
    ```

    Run template
    ```bash
    prich run csv_analysis --file sales.csv
    ```

    Or:
    ```bash
    prich run code_review --dir src/
    ```

## Example Templates

### csv_analysis (non-development)
Analyzes CSV data (e.g., sales) and generates business insights.

- **Install**:
    ```bash
    prich template install ./csv_analysis
    ```
- **Run**:
    ```bash
    prich run csv_analysis --file sales.csv
    ```

- **Sample Output**:
    ```plaintext
    Sending prompt to LLM:
    You are a data analyst with expertise in business intelligence. Provide concise, actionable insights.

    CSV File: sales.csv

    Summary Statistics:
    Total Sales: $1,700.00
    Average Price: $599.99
    Top Product: Laptop

    Provide actionable business insights based on the summary statistics, including recommendations for improving sales performance.
    ```

### code_review (development)

Reviews Python files in a directory for code quality.

- **Install**:
    ```bash
    prich template install ./code_review
    ```

- **Run**:
    ```bash
    prich run code_review --dir src/
    ```

- **Sample Output**:
    ```plaintext
    Sending prompt to LLM:
    You are a senior developer with expertise in code review. Provide concise, actionable feedback.

    Directory: src/

    Files to review:
    src/main.py
    src/utils.py

    File contents:
    --- src/main.py ---
    def hello():
        print("Hello, world!")
    --- src/utils.py ---
    def add(a,b):
        return a+b

    Review the code for style issues, bugs, performance problems, and suggest improvements.
    ```

### git_diff (development)

Analyzes git changes with a raw diff and formatted summary.

- **Install**:
    ```bash
    prich template install ./git_diff_template
    ```

- **Run**:
    ```bash
    prich run git_diff --commit "HEAD^ HEAD"
    ```

- **Sample Output**:
    ```plaintext
    Sending prompt to LLM:
    You are a senior developer with expertise in code review. Provide concise, actionable feedback.

    Raw git diff:
    diff --git a/main.py b/main.py
    index 1234567..89abcde 100644
    --- a/main.py
    +++ b/main.py
    @@ -1,3 +1,5 @@
    def hello():
        print("Hello, world!")
    +def goodbye():
    +    print("Goodbye, world!")

    Summary of changes:
    def goodbye():
        print("Goodbye, world!")

    Provide suggestions for improving the code based on the diff and summary.
    ```

## Team Collaboration

**prich** is designed for teams to share and standardize LLM prompts across workflows:

- **Share Templates in repository**:
    Store `.prich/` folder with templates in your repository and work on them together.  
    For templates with python preprocess scripts you can add `venv` folders to `.gitignore` and ask team to install venvs personally:

    ```bash
    prich venv-install <template_name>
    ```

    or to re-install:

    ```bash
    prich venv-install <template_name> --force
    ```


- **Share Templates as files**:
    Package templates in a git repo, shared drive, or cloud storage (e.g., Google Drive, Dropbox):

    Team members install templates:

    ```bash
    git clone https://github.com/your-team/team-prich-templates.git
    prich template install team-prich-templates/csv_analysis
    ```

    Or download from cloud storage and run `prich template install`.

- **Standardize Workflows**:
Use shared templates to ensure consistent LLM outputs, whether for code reviews (“Add docstrings”) or business insights (“Focus marketing on Laptops”).

- **Cross-Functional Use**:
Developers, data analysts, marketers, or support teams can use prich for their prompts, with templates tailored to each domain.


## Advanced Features

- **Pipelines**: Use Python, shell, LLM, or any language for pipeline steps (e.g., parse CSVs with pandas, clean text with awk).

- **Conditional Expressions**: Use Jinja2 style conditional expressions to execute or skip pipeline steps

(((- **Python Injection**: Enable in ~/.prich/config.yaml for in-process Python preprocessing:
    ```yaml
    security:
      allow_python_injection: true
    ```)))

- **Custom Python Venvs**: Templates like code_review use dedicated venvs for dependency isolation.

(((- **Reusable Blocks**: Jinja2 blocks (e.g., prompt_header.j2) ensure consistent prompt structures.)))


## Contributing

Want to create templates for data analysis, content generation, or other domains? Fork the repo, add a template package, or submit a PR! See CONTRIBUTING.md for guidelines.


## License

MIT License. See LICENSE for details.



---
**prich**: Simplify any LLM prompt pipeline and collaborate effortlessly!