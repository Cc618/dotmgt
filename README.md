# Dot Manager
Dot Manager is a set of tools used to manage dot files.
It targets portability across multiple devices and
user customization (ability to change themes / tweaks).

## Instructions
### Install
```sh
./install.sh
```

## Tools
- txtpp : Text PreProcessor, used to preprocess text files
  like cpp.
- dotmgt : Dot file manager, uses txtpp to update files.

## Example
### Dot files
First, go to a directory where your dot files will be located.
```sh
mkdir dotfiles
cd dotfiles
```

Second, initalize the dot files directory
```sh
dotmgt i # Or init
```

Here are all created files :
```
.
├── config.yml  # dotmgt config file
└── deffile.py  # txtpp config file
```

You can add a new config file like a .vimrc by creating it without
the dot at the start of the name.
```sh
echo '" My vimrc' > vimrc
```

The config.yml file contains files with custom paths or ignored files :
```sh
files:
  i3: .config/i3/config

ignored:
  - README.md
```

Finally, the deffile.py is used to add programmatically preprocessor
definitions using python :
```py
import os

definitions = [
    'LAPTOP' if 'laptop' in os.uname().nodename else 'DESKTOP',
]
```

Here are some useful commands :
- `dotmgt u # Or update` Update user config with dot files
- `dotmgt d # Or diff` Compare between user config and dot files
- `dotmgt l # Or list` List every config file path

### Text preprocessor syntax
The preprocessor is inspired by the c preprocessor, it uses the @ symbol
to declare a directive.
Directives can be controls (if / ifnot / elif / elifnot / else),
instructions (define / undef / error / warning) or comments.

```sh
# Background
@@ Preprocessor comment
@if THEME_DARK
exec_always --no-startup-id feh --bg-scale "dark.png"
@elif THEME_LIGHT
exec_always --no-startup-id feh --bg-scale "light.png"
@else
@   error No theme found
@end
```

More details [here](txtpp/README.md).
