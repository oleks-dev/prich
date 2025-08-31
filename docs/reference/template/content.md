# Template Content Details

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

Example:  
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