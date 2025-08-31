# Steps `steps`

Each template can have multiple steps for pre/postprocessing and llm requests.

```yaml
steps:
#  ...
```

### Generic base fields for each step  
```yaml
    # name of the step (should be unique)
  - name: "Step do work"

    # type of the step (see available steps)
    type: "llm"
```

> **Note:** Step name should be unique in each step.  


##### Output text transformations  
```yaml
    # strip spaces from beginning and end of the output
    strip_output: true                 # optional [bool]

    # strip prefix characters from the output
    strip_output_prefix: "> "          # optional [str]

    # slice output from N character
    slice_output_start: 3              # optional [int]

    # slice output till N character 
    # (use negative number for backwards count)
    slice_output_end: -1               # optional [int]

    # filter output using regex 
    # (take 1st group if groups are used otherwise take matching regex)
    output_regex: ".*"                 # optional [str]
```

> **Note:** Output text transformation params applied one by one in order as they mentioned in the example, each next one uses result of the previous.  


##### Store and show output  
```yaml
    # save output to a variable
    output_variable: "out_var"         # optional [str]

    # save output to file
    output_file: "out.txt"             # optional [str]

    # file mode overwrite or append
    output_file_mode: "write"          # optional ["write"|"append"]

    # print output to console during normal execution
    # (mostly for user reference when such information is needed)
    output_console: false              # optional [bool]
```


##### When to execute - conditional statement  
```yaml
    # when step should be executed 
    # (jinja2 template conditional template)
    when: "{{ in_var == 'hello' }}"    # optional [str]
```


##### Extract variables  
```yaml
    # create variables with extracted text from output
    extract_vars:                      # optional [list[dict]]

      # extract value using regex 
      # (same regex rules as in `output_regex`)
      - regex: "(\\d+)"                # [str]

        # variable name to create or update
        variable: "items_count"        # [str]

        # extract all occurrences into a list (false by default)
        multiple: false                # optional [bool]
```

> **Note:** When extracting variables with `extract_vars` the full initial output text is used (before transformations)  


##### Validate output  
```yaml
    # validate step output
    validate:                          # optional [dict|list[dict]]

      # matching regex pattern
      - match: ".*"                    # optional [str]

        # not matching regex pattern
        not_match: "^title"            # optional [str]

        # what to do on validation failure
        on_fail: "error"               # optional ["error"|"warn"|"skip"|"continue"]

        # custom message shown on failure
        message: "Failed to validate"  # optional [str]
```

### Step types  

#### Python step  
```yaml
    type: "python"                     # execute python script
    call: "file.py"                    # python file to execute
    args: ["arg1", "arg2"]             # optional [list[str]] - arguments for python file
    validate:
#      ...
       match_exit_code: 0              # optional [int|str] - check execution result exit code
       not_match_exit_code: 1          # optional [int|str] - check execution result exit code
```

> **Note**: Python step uses python based on template `venv` settings (see Template > [Content](content.md))  


#### Command step  
```yaml
    type: "command"                    # execute shell command
    call: "echo"                       # file to execute
    args: ["hello"]                    # optional [list[str]] - arguments for file execution
    validate:
#      ...
       match_exit_code: 0              # optional [int|str] - check execution result exit code
       not_match_exit_code: 1          # optional [int|str] - check execution result exit code
```


#### LLM step  
```yaml
    type: "llm"                                    # send llm prompt
    instructions: "You are {{ assistant_type }}."  # optional [str] - system instructions (jinja2 template string)
    input: "Summarize the following:\n{{ text }}"  # [str] - user prompt input (jinja2 template string)
```


#### Render step  
```yaml
    type: "render"                    # execute jinja2 render
    template: "Hello {{ user_var }}"  # jinja2 template string
```

