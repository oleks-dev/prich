# Variables `variables`

Section defines initial variables available for the template, can be supplied via CLI or by using default value (hardcoded or using env variable)

### Variable fields

##### Name
Name of the variable, should be lowercase and contain only letters, numbers, and underscores.

```yaml
    name: "test_variable"
```

##### CLI option `cli_option`
CLI option name that would be used for the variable (if different from the `name`). 
By default `cli_option` would be `--{name}`.

##### Description
```yaml
    description: "Input file"
```
Description for the variable

##### Type
```yaml
    type: "str"
```

- `str` (default)
- `int`
- `bool`
- `path`
- `list[str]`  # multiple params supplied, ex. `--text "hello" --text "world" --text "!"` > loads into `text` list variable
- `list[int]`
- `list[bool]`
- `list[path]`  

##### Default value
```yaml
    default: "test"
```

##### Required
Is variable required or not (false by default)
```yaml
    required: true
```

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
  required: false
  cli_option: --role
- name: topic
  type: str
  description: Generate text about Topic
  default: short brief about LLM usage
  required: false
  cli_option: --topic
```
