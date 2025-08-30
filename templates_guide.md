# prich Templates Guide

### Create a New Template

1. Create a new folder in the `.prich/templates/`, ex. `.prich/templates/mytemplate/`
2. Add a new yaml file in the `.prich/templates/mytemplate/` folder, ex. `.prich/templates/mytemplate/mytemplate.yaml`
> Note: Use same name for the template folder name and the yaml template file
3. Add the template contents into the yaml file

### Template Content Details

* `id` - the lowercase id of the template using letters, numbers, hyphens, and underscores (without spaces), ex. `my-template`, `my_template`, `mytemplate` 
* `name` - string name of the template, used just for the information
* `schema_version` - version of the template schema to define support by the prich tool
* `version` - version of the template, used for the information by user as needed
* `author` - author of the template, used for the information
* `description` - description of the template, used for describing the template purpose
* `tags` - list of lowercase tags used to mark template with some tags, could be used for searching later
* `steps` - list of pipeline workflow steps that would be executed in order during the template execution
* `usage_examples` - list of strings to show examples of the template execution commands, used for information only
* `variables` - list of variables available for the template
* `venv` - `isolated`/`shared` used only when `python` steps are used in the template to specify if isolated venv should be created or to use one shared venv for all templates

#### Steps Details  
Each step defines an action for the template pipeline workflow executed in order.

**Step can have next key parameters**:
* `name`: name of the step (should be unique for each step in the template)
* `output_variable`: save output of the execution into a variable for the following usage
* `output_file`: save output of the execution into a file
* `output_file_mode`: `write`/`append`
* `strip_output_prefix`: strip prefix string from the step output
* `slice_output_start`: slice step output from character number
* `slice_output_end`: slice step output to character number
* `when`: execute step only when true - simple jinja evaluation like `working_vs_last_commit or (not working_vs_last_commit and not working_vs_remote and not committed_vs_remote and not remote_vs_local)` or `not remote_vs_local`, etc.
* `validate`: validate step execution (see `step validate`)
* plus additional keys based on the step type

**Step `type`**:
* `llm` - send request to a llm provider and receive or print the response
    ```yaml
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
    ```

* `python` - execute python script from the templates folder using shared or isolated python venv
    ```yaml
      - name: "Preprocess step"
        type: "python"
        call: "parse_csv.py"
        args: ["{{csv_file}}"]
        output_variable: "csv_summary"
    ```

* `command` - execute shell command
    ```yaml
      - name: "Get current branch"
        type: "command"
        call: "git"
        args: ["rev-parse", "--abbrev-ref", "HEAD"]
        output_variable: "current_branch"
    ```

* `render` - render jinja template
    ```yaml
      - name: "Render text"
        type: "render"
        template: "Check the {{ file }} file"
        output_variable: "check_file_text"
    ```

**Step `validate`**:  
Could be a dict or list of validations
* `match`: regex to match output (jinja vars could be used)
* `not_match`: regex not match output (jinja vars could be used)
* `match_exit_code`: (for execution commands) match exit code number (jinja vars could be used when supplied as string)
* `not_match_exit_code`: (for execution commands) not match exit code number (jinja vars could be used when supplied as string)
* `on_fail`: `error`/`warn`/`skip`/`continue` default is `error`
* `message`: text message to show on failure


### Build a New Simple One-Step Template

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