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


### **Initialize prich**:
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
     
