# Debug Templates

There is a way to execute your template pipeline in a debug mode that pauses after each step and allows you to debug your template steps.

To run template in a debug mode execute it with the `--debug` flag, like:
```commandline
prich run my-template --my-param test --debug
```

Or you can run it also in *verbose* mode, like:
```commandline
prich run my-template --my-param test --debug --verbose
```


## Debug Process

Happens after each step and shows you the input string with possible actions.

```text
[debug] Initial variables:
[debug] my_param = test
[debug] Stash variables before step 1
[debug] --- Step command My Step #1
• My Step
[debug] (c)ontinue, (r)epeat step, repeat (v)alidate, (t)erminate; show (s)tep, variab(l)es, variables stas(h):
```

On this stage you can select one of the available actions:  
- `continue` - execution to the next following step or end if no more steps present  
- `repeat step` - re-execute the current step again  
- `repeat validate` - re-do validation for the current step (available only when validation is present for the step)  
- `terminate` - exit execution  
- `step back` - move back to a previous step and re-execute it (available only when previous step is present)  
- `show step` - print current step yaml representation  
- `show variables` - show list of current variables with values  
- `show variables stash` - show all variables saved in stash before each executed step  

>NOTE: Between each of your actions the template would be reloaded if any changes happened in the template yaml file.
 
## Template reload during debug

The template would be reloaded if there were file changes between the debug steps during the execution. This allows you to open your template yaml file in another window/process/editor and modify it as required and test or tune it on-the-fly during the debug execution.  

In the following example we change the validation *match_exit_code* and *on_fail* for the command execution step and after reload we see that behaviour changes after the repeat step action:
```text
[debug] --- Step command My Step #1
• My Step
[debug] (c)ontinue, (r)epeat step, repeat (v)alidate, (t)erminate; show (s)tep, variab(l)es, variables stas(h): r
[debug] Template change detected - reloading
[debug] Updating stashed variables
[debug] Updating current variables
[debug] Updating template
[debug] Restoring variables from before step 1
[debug] --- Step command My Step #1
• My Step
No issues found – skipping next steps.
[debug] (c)ontinue, (r)epeat step, repeat (v)alidate, (t)erminate; show (s)tep, variab(l)es, variables stas(h): 
```

This allows you to tweak your template step with a simple repeat actions for the whole step, or it's validation only.

>NOTE: Keep in mind that template reloads completely and to not break the execution do not save the template with fewer steps than you are already on during the run.  
