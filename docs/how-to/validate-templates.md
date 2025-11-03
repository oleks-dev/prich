# Validate Template YAML files

When template yaml file has syntax issues it would be ignored in the `list` and `run` commands as it's not possible to properly parse and load the template.

For such cases `prich` tool has a built-in validation doctor feature that helps to detect and highlight template issues in the corresponding YAML partial snippet.  

It could help to detect issues like:    
- not correct fields  
- missing fields  
- not correct value types  
- syntax errors  
- missing venvs  
- missing scripts or command files  

## Usage

#### All Templates

```commandline
# for all templates
prich validate

# for only global templates
prich validate --global

# for only local templates
prich validate --local
```

#### Specific Template by ID
```commandline
# for specific template (will return both local and global if present)
# prich validate <template_id>
prich validate my_template

# for specific template (only local)
# prich validate <template_id> --local
prich validate my_template --local

# for specific template (only global)
# prich validate <template_id> --global
prich validate my_template --global
```

#### Selected template YAML file
```commandline
prich validate --file .prich/templates/my-template/my-template.yaml
```

## Validation Exit Codes
Command `prich validate` will exit with next exit codes:  
- Exit code 0 - when templates are valid  
- Exit code 2 - when some template(s) issues were found  

## Examples of template validations

#### Validation successful
```commandline
➜ prich validate
- test-template (global) ~/.prich/templates/test-template/test-template.yaml: is valid
- test-template (local) ~/projects/myproject/.prich/templates/test-template/test-template.yaml: is valid
- test-example (local) ~/projects/myproject/.prich/templates/test-example/test-example.yaml: is valid

Analyzed 3 templates, 0 invalid.
```
Exit code is `0`


#### Missing required field
When required field `call` is missing in the template python step
```commandline
prich validate --id test-template -l
- test-template (local) ~/projects/myproject/.prich/templates/test-template/test-template.yaml: is not valid (1 issue)
  Failed to load template test-template (Test Template):
  1. Missing required field at 'steps[1].call':
  ---
  name: Run cmd
  type: python
  args:
  - test hello string
  +call: ...
  ...
  See Steps documentation:
  https://oleks-dev.github.io/prich/reference/template/steps/


Analyzed 1 templates, 1 invalid.
```

In this case the snippet shows where the field is missing and need to be added `+call: ...`

#### Unrecognized field  
In this case in yaml file in the step there is used `regex_replace` used not under `filter` key)  
```commandline
➜ prich validate --id test-template -l
- test-template (local) ~/projects/myproject/.prich/templates/test-template/test-template.yaml: is not valid (1 issue)
  Failed to load template test-template (Test Template):
  1. Unrecognized field at 'steps[1].regex_replace':
  ---
  name: Run command
  type: command
  call: echo
  args:
    - test hello string
  regex_replace:
  - - (?i)(hello)
    - \1****\2
  ...
  See Steps documentation:
  Output Text Transformations: https://oleks-dev.github.io/prich/reference/template/steps/#output-text-transformations
  command step: https://oleks-dev.github.io/prich/reference/template/steps/#command-step
  https://oleks-dev.github.io/prich/reference/template/steps/


  Analyzed 1 templates, 1 invalid.
```
Exit code is `2`

> Note also that there would be also a link to the documentation of the related section when possible.  

#### Failed to find call command file  
```commandline
➜ prich validate --id test-template -l
- test-template (local) ~/projects/myproject/.prich/templates/test-template/test-template.yaml: is not valid (1 issue)
  1. Failed to find call command file ~/projects/myproject/.prich/templates/test-template/scripts/echo1 for step #1 Run command


Analyzed 1 templates, 1 invalid.
```
Exit code is `2`


#### Failed to find venv  
When isolated venv is not found
```commandline
➜ prich validate --id test-template -l
- test-template (local) ~/projects/myproject/.prich/templates/test-template/test-template.yaml: is not valid (1 issue)
  1. Failed to find isolated venv at ~/projects/myproject/.prich/templates/test-template/scripts. Install it by running 'prich venv-install test-template'.


Analyzed 1 templates, 1 invalid.
```
Exit code is `2`
