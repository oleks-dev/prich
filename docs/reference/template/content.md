# Template Content Details

Templates are stored in yaml files and folders with additional optional files like scrips and other resources.
Stored in `.prich/templates/<template_id>/<template_id>.yaml` folder and file.

Template YAML file consists of the following fields:
```yaml
# the lowercase id of the template using letters, numbers, hyphens, and underscores (without spaces), ex. `my-template`, `my_template`, `mytemplate`
id: "template_name"             # [str]

# name of the template, used just for the information
name: "Template Name"           # [str]

# version of the template, you can use it for template version maintenance
version: "1.0"                  # [str]

# author of the template
author: "John Doe"              # optional [str]

# description of the template, would be visible in the list of templates
description: "My template"      # [str]

# list of lowercase template tags, used to categorize templates and for search
tags: ["code", "review"]        # [list(str)]

# list of pipeline workflow steps that would be executed in order during the template execution
steps:                          # [list(dict)]
  - name: "..."
  # ...: "..."
  - name: "..."
  # ...: "..."
  # ...

variables:                      # optional [list(dict)]
  - name: "file"
  # ...: "..."
  # ...

# used to show examples of the template execution commands, used for information only
usage_examples:                 # optional [list(str)]
  - "template_name --file myfile.txt"
  # ...

# use only when `python` steps are used in the template to specify 
# if isolated venv should be created or to use one shared venv for all templates
# isolated venvs created in `.prich/templates/<template_id>/scripts/venv folder
# shared venv is created in `.prich/venv` folder
venv: "isolated"                # optional [str("isolated"/"shared")]

# version of the template schema to define support by the prich tool
schema_version: "1.0"           # [str]
```


### Simple Example  
Just one step to ask LLM to generate some text
```yaml
id: test-template
name: Test Template
version: '1.0'
description: Example template - Generate text about specified topic
tags:
- example
- writer
steps:
- name: Ask to generate text
  type: llm
  instructions: You are {{ role }}
  input: Generate text about {{ topic }}
variables:
- name: role
  type: str
  description: Role of the Assistant
  default: article writer
  required: false
  cli_option: --role
- name: topic
  type: str
  description: Generate text about Topic
  default: short brief about LLM usage
  required: false
  cli_option: --topic
schema_version: '1.0'
```

### Advanced Example  
Where we execute several commands including prich itself, curl, cat, and assemble LLM request to help fixing the prich template yaml file.
> Keep in mind: This example is not optimal from the tokens size as it includes all main documentation parts to the LLM request. 
> Links and functionality could be also changed with time, the following template is given for a syntax example.
```yaml
id: "prich-template-help"
name: "Prich Help"
schema_version: "1.0"
version: "1.0"
author: "prich"
description: Analyse template errors and provide fix suggestions
tags: ["prich", "help"]
steps:
  - name: "Run prich validate for analysis of invalid template"
    type: command
    call: prich
    args:
      - validate
      - --invalid
      - --id
      - "{{template_id}}"
      - "{% if only_local %}-l{% endif %}"  # when argument is "" it would be not be supplied
      - "{% if only_global %}-g{% endif %}"
    validate:
      # prich validate returns exit code 2 when template failures found
      match_exit_code: 2
      # skip all the following steps
      on_fail: skip
      message: "No template issues found"
    extract_variables:
      - regex: "[^|\\n]*- \\S+ \\(\\S+\\) (\\S+): is not valid"  # extract template files
        variable: "template_files"
        multiple: true
    filter:
      strip: true 
      regex_extract: "((?:.|\n)+)\\nAnalysed \\d+ templates, \\d+ invalid."  # cut out redundant information
    output_variable: "validation_results"

  - name: "Get template contents using cat command"
    # run only when template files extracted
    when: "(template_files | length) > 0"
    type: command
    call: cat
    args:
      - "{{template_files[0] | replace('~', '$HOME') | replace('./', '$PWD') }}"  # replace . and ~ with full path using env vars
    filter:
      strip: true
    output_variable: "template_content"

  - name: "Get 2nd template contents using cat command"
    # run only if more than one template found (could be global and local with same name)
    when: "(template_files | length) > 1"
    type: command
    call: cat
    args:
      - "{{template_files[1] | replace('~', '$HOME') | replace('./', '$PWD') }}"
    filter:
      strip: true
    output_variable: "template2_content"

  - name: "Get prich template content documentation from static github link"
    type: command
    call: curl
    args:
      - -sL
      - https://raw.githubusercontent.com/oleks-dev/prich/refs/heads/main/docs/reference/template/content.md
    filter:
      strip: true
    output_variable: "template_content_doc"

  - name: "Get prich template steps documentation from static github link"
    type: command
    call: curl
    args:
      - -sL
      - https://raw.githubusercontent.com/oleks-dev/prich/refs/heads/main/docs/reference/template/steps.md
    filter:
      strip: true
    output_variable: "template_steps_doc"

  - name: "Get prich template variables documentation"
    type: command
    call: curl
    args:
      - -sL
      - https://raw.githubusercontent.com/oleks-dev/prich/refs/heads/main/docs/reference/template/variables.md
    filter:
      strip: true
    output_variable: "template_variables_doc"

  - name: "Ask to suggest template fixes"
    type: llm
    instructions: |
      Assistant is a senior engineer who help to fix yaml template issues for prich cli tool (tool for building, running, and sharing llm prompt template pipelines).
    input: |
      Prich Documentation link for reference https://oleks-dev.github.io/prich
      
      --- start of https://oleks-dev.github.io/prich/reference/template/content/ ---
      {{ template_content_doc }}
      --- end ---
      
      --- start of https://oleks-dev.github.io/prich/reference/template/steps/ ---
      {{ template_steps_doc }}
      --- end ---
      
      --- start of https://oleks-dev.github.io/prich/reference/template/variables/ ---
      {{ template_variables_doc }}
      --- end ---

      {% if template_content or template_content2 %}Current failed prich yaml template contents:{% endif %}
      {% if template_content %}--- file: {{ template_files[0] }} ---
      ```yaml
      {{ template_content }}
      ```
      --- end ---{% endif %}
      {% if template_content2 %}--- file: {{ template_files[1] }} ---
      ```yaml
      {{ template_content2 }}
      ```
      --- end ---{% endif %}

      `prich validate` execution results:
      ```
      {{ validation_results }}
      ```

      Tool returns a list of available templates by template ids, location (local - .prich folder in cwd, global - .prich folder in home), and validation result "is valid" and "is not valid".
      Format is a list like
      ```
      - <template_id> (<location>) <path_to_template_yaml_file>: <is valid/is not valid>
        [optional_failure_details_list]
      ```
      For not valid templates tool adds details under the template list item about what exactly is wrong, it also could include the last child branch of the yaml structure where the problem is located. 
      Refer to the documentation while analysing templates validation output, for unrecognized fields suggest possible closest proper yaml fields usage from the documentation, for missing fields also describe yaml fields using documentation reference.
      Produce list of templates with suggested fixes for each template id, provide yaml fix suggestion - put attention on yaml parent child fields that are used. Ensure that you are listing proper template ids from the results.
      Ex.
      ```
      - <template_id> (<location>) <path_to_template_yaml_file>
        <suggested_fix_instructions>
      ```
variables:
  - name: template_id
    cli_option: --id
    required: true
    type: str
  - name: only_local
    cli_option: --only-local
    type: bool
  - name: only_global
    cli_option: --only-global
    type: bool
```
