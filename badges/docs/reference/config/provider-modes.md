# Provider Modes `provider_modes`  

Use to specify how the prompt would be constructed for the LLM, you can modify or add your own as needed in the `config.yaml` - `provider_modes`.

`mode` controls how custom instructions/input (system/user) are arranged for the provider, ex:  
- `plain` → instructions and input without extras  
- `flat` → simple “System/User/Assistant” text blocks with headers  
- `chatml` → `[{role, content}, …]`  
- `mistral-instruct`, `llama2-chat`, `anthropic` → provider-specific wrappers  

> For Ollama use `raw: true` to bypass standard provider prompt formatting and use your custom prompt mode.  

## More detailed examples

There are two fields available that are used in the template prompts. It could be `instructions` for system instructions and `input` as a user query.

### `plain`
```text
{% if instructions %}{{ instructions }}\n{% endif %}{{ input }}
```
Example
```text
You are an assistant.
Write a small tech article.
```

### `flat`  
```text
{% if instructions %}### System:
{{ instructions }}

{% endif %}### User:
{{ input }}

### Assistant:
```

```text
### System:
You are an assistant.

### User:
Write a small tech article.

### Assistant:
```

### `chatml`
```text
[
  {% if instructions %}{"role": "system", "content": "{{ instructions }}" },
  {% endif %}{"role": "user", "content": "{{ input }}" }
]
```

```json
[
  {"role": "system", "content": "You are an assistant."},
  {"role": "user", "content": "Write a small tech article."}
]
```

### `anthropic`
```text
Human: {% if instructions %}{instructions}

{% endif %}{{ input }}

Assistant:
```

```text
Human: You are an assistant.

Write a small tech article.

Assistant:
```



