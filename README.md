# Include Autocomplete

A Sublime Text plugin that enables autocompletion for `.h` files in `#include`
directives.

## Synopsis

This plugin will try to autocomplete file names for `#include ""` directives in
C files. By default it will (recursively) look in the same directory as the file
for which we are trying to autocomplete the `#include`, but you can set custom
search locations in the `.sublime-project` file (see [Settings](#settings)).

When an item from the autocomplete suggestions is selected, the path relative to
the include location is added to the include directive, together with the
filename. For example, given the following layout for your include location:

```
/include/loctaion/
├── dir1
│   └── include
│       └── x.h
└── dir2
    └── include
        └── y.h
```

Selecting `x.h` from the autocomplete suggestions, will be autocompleted as
`dir1/include/x.h`.

Also, if you already have a path in your `#include` directive, that path will be
taken into account when searching for `.h` files. Using the same include
location directory layout as before, autocompletion for `#include "dir1/<...>"`
will only look for files in the `dir1`, not `dir2`.

## Installation

The recommended way of installation is through Sublime Package Control.

## Settings

### Manual Setup

To add locations where the plugin should look for `.h` files, add the following
to your `.sublime-project` file:

```json
{
    "include_autocomplete_settings":
    {
        "include_locations":
        [
            {
                "path": ".",
                "ignore": []
            },
            {
                "path": "<path/to/include/directory>",
                "ignore": ["<exclude1>", "<exclude2>", ...]
            },
            ...
        ]
    }
}
```

The "include locations" key is a list of dictionaries, each containing the
following keys: `path`: The directory where we should (recursively) look for
`.h` files. This path can be either absolute or relative. In the latter case, we
will look relative to the directory of the file in which we are trying to
autocomplete an `#include` directive. This variable supports snippet-like
variables, e.g. `${project_path}/include`. `ignore`: A list of paths relative to
`path`, that we should ignore when searching for `.h` files.

### Compilation Database

The plugin can also take a compilation database into account. When you use
EasyClangComplete to specify your compilation database, you have to do nothing
at all. The plugin will use EasyClangComplete's settings in your
`.sublime-project`. To clarify, the plugin expects something of the form

```json
{
    "settings":
    {
        "ecc_flags_sources":
        [
            {
                "file": "compile_commands.json",
                "search_in": "$project_base_path/build"
            }
        ]
    }
}
```

If this key is not present in `"settings"`, the plugin also attempts to look for
a `"compile_commands"` key that specifies the directory where
`compile_commands.json` lives. Again, arbitrary snippet-like variables are
possible. To clarify, the plugin looks for something of the form

```json
{
    "settings":
    {
        "compile_commands": "${project_path}/build"
    }
}
```

If a compilation database is found, and we are inside a header file, the plugin
will collect all possible include locations from the compilation database. If
we're in an implementation file, the plugin will only add the include
directories for that specific implementation file. If the implementation file is
not present in the compilation database, a warning is printed to the console
informing you that the implementation file is not in the compilation database.

### No `.sublime-project` file

If the current file does not have an associated `.sublime-project` file, or the
associated `.sublime-project` file does not contain the "include_locations" key,
the following defaults will be used:

```json
{
    "include_autocomplete_settings":
    {
        "include_locations":
        [
            {
                "path": ".",
                "ignore": []
            }
        ]
    }
}
```
