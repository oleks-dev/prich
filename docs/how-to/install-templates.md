# Install Templates

There are several ways to install templates. You can install them from remote repository or from local zip archive or template folder.
For local option download or clone a template package (e.g., csv_analysis_template/) as a folder or a zip file and install it:

### Install template from remote GitHub Template Repository
Templates are stored in this [github prich-templates repository](https://www.github.com/oleks-dev/prich-templates)

- **List Available Remote Templates for Installation**

    ```bash
    # list all remote templates
    prich list --remote
    ```

    ```bash
    # filter remote templates using tags
    prich list --remote --tag code --tag review
    ```

- **Install Template from *prich-templates* Repository**

    ```bash
    # install in current prich folder
    prich install <template_id> --remote
    ```

    ```bash
    # install in home prich folder
    prich install <template_id> --remote --global
    ```


### Install from a local template zip file
```bash
prich install <template-zip-file>.zip
```

### Install from a local template folder
```bash
prich install <template-folder>
```

```bash
prich install ./code-review
```

This copies files, sets up venvs, and installs dependencies - if python is used there.

### Reinstall template
To reinstall template use `--force` flag together with the selected install template, this will reinstall the template and it's isolated venv (if any).

```bash
# from remote repo
prich install code-review --remote --force
# from local folder
prich install ./code-review --force
# from archive file
prich install code-review.zip --force
```
