# Settings `settings`

Global settings live under `settings`:

```yaml
settings:
  default_provider: "llama3.1-8b"   # default_provider: "<your-provider-name>"
  editor: "vim"                     # optional [str], default "vi"
  provider_assignments:             # optional [dict]
    "code-review": "llama3.1-8b"    # <template_id>: <provider_name>
    "summarize-git-diff": "qwen3-8b"
```

### Default Provider `default_provider`
Name of a provider defined in the same file.
Specify the default provider that would be used in all templates by default if no `provider_assignements` set and not overloaded with `--provider` argument option.

### Editor command `editor`
Used by commands that open an editor to edit config/template yaml files. 
`vi` by default, you can use your favorite like `vim`, `nano`, etc. that executes like `<cmd> <file>`

### Template to Provider assignments `provider_assignments`
Use this when you want to use different specific providers assigned to different templates.

