# Install & Update
### **Install prich**
    
Until prich is published on PyPI, you can install it directly from GitHub.
 
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

### **Update prich**

Using `pipx` with `--force` to reinstall:
```bash
pipx install git+https://github.com/oleks-dev/prich --force
```


### **Initialize prich**
**prich** uses nodejs-like home/local folder configurations for flexible usage of the configs and templates per project.  

   - Local folder based
       ```bash
       prich init
       ```
       > Creates `.prich/` with a default preprocessing shared venv (`.prich/venv/`) and config file.  

   - Global user folder based
       ```bash
       prich init -g
       ```
     
       > Creates `~/.prich/` with a default preprocessing shared venv (`~/.prich/venv/`) and config file.


### Shell Completion  
`prich` supports autocompletion for **zsh**, **bash**, and **fish**.

#### Zsh  
```bash
# Option 1: One-liner (recommended)
prich completion zsh > ~/.zfunc/_prich
echo 'fpath=(~/.zfunc $fpath)' >> ~/.zshrc
autoload -Uz compinit && compinit

# Option 2: Source manually in ~/.zshrc
prich completion zsh > ~/.prich-completion.zsh
echo 'source ~/.prich-completion.zsh' >> ~/.zshrc
```

#### Bash  
> **NOTE!**: Requires bash ≥ 4.4 (the system bash on macOS is too old,
install `brew install bash` if needed).

```bash
# Option 1: One-liner
prich completion bash > ~/.prich-completion.bash
echo 'source ~/.prich-completion.bash' >> ~/.bashrc

# Option 2: Generate directly inside ~/.bashrc
echo 'eval "$(_PRICH_COMPLETE=bash_source prich)"' >> ~/.bashrc
```

#### Fish
```bash
# Option 1: Copy into fish completions dir
prich completion fish > ~/.config/fish/completions/prich.fish

# Option 2: Source manually from config.fish
prich completion fish > ~/.prich-completion.fish
echo 'source ~/.prich-completion.fish' >> ~/.config/fish/config.fish
```

After running one of the above, restart your shell and try:  
```bash
prich <TAB>
```
