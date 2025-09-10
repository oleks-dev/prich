# Variables

`variables` is a list section that defines initial variables available for the template, can be supplied via CLI or by using default value (hardcoded or using env variable)

## Defining Variables

```yaml
variables:                          # optional [list]
    # name of the variable (should match specific formatting)
  - name: "test_variable"           # [str]

    # name of the cli option for setting this variable
    # if not added then the cli option would be taken from name like `--{name}`
    # useful when you like to use hyphen in the name for example or just a shorter form
    cli_option: "--test-var"        # optional [str]

    # description, shown in the with the --help option
    description: "Input file"       # optional [str]

    # type of the value, default is "str"
    # "str" (default)
    # "int"
    # "bool" (use for flags without values, ex `--report`, `--review`)
    # "path" (use for paths or files)
    # use list of type for multiple params supplied, ex. `--text "hello" --text "world" --text "!"`
    # loads into `text` list variable
    # "list[<type>]" (ex. "list[str]", "list[bool]")
    type: "str"                     # optional [str]

    # default value assigned to the variable
    # it would be overwritten if supplied as cli option
    default: "test"                 # optional [str]

    # is variable required, default is false
    # template will fail if variable is required but no default value is set or not supplied as a cli option
    required: true                  # optional [bool]

  # ...
```

> **NOTE:**  
> `name` of the variable should be lowercase and contain only letters, numbers, and underscores.


## Examples

```yaml
- name: count
  type: int
  description: Number of iterations
  required: true
  cli_option: --count
- name: role
  type: str
  description: Role of the Assistant
  default: article writer
  cli_option: --role
- name: topic
  description: Generate text about Topic
  default: short brief about LLM usage
  cli_option: --topic
```
