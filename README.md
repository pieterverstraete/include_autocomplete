# Include Autocomplete

A Sublime Text plugin that enables autocompletion for `.h` files in `#include` directives.

## Synopsis

This plugin will try to autocomplete file names for `#include ""` directives in C files. By default it will (recursively) look in the same directory as the file for which we are trying to autocomplete the `#include`, but you can set custom search locations in the `.sublime-project` file (see [Settings](#settings)).

When an item from the autocomplete suggestions is selected, the path relative to the include location is added to the include directive, together with the filename. For example, given the following layout for your include location:
```
/include/loctaion/
├── dir1
│   └── include
│       └── x.h
└── dir2
    └── include
        └── y.h
```
Selecting `x.h` from the autocomplete suggestions, will be autocompleted as `dir1/include/x.h`.

Also, if you already have a path in your `#include` directive, that path will be taken into account when searching for `.h` files. Using the same include location directory layout as before, autocompletion for `#include "dir1/<...>"` will only look for files in the `dir1`, not `dir2`.

## Installation

The recommended way of installation is through Sublime Package Control.

## Settings

To add locations where the plugin should look for `.h` files, add the following to your `.sublime-project` file:

```
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
```

The "include locations" key is a list of dictionaries, each containing the following keys:
`path`: The directory where we should (recursively) look for `.h` files. This path can be either absolute or relative. In the latter case, we will look relative to the directory of the file in which we are trying to autocomplete an `#include` directive. This variable supports snippet-like variables, e.g. `${project_path}/include`.
`ignore`: A list of paths relative to `path`, that we should ignore when searching for `.h` files.

If the current file does not have an associated `.sublime-project` file, or the associated `.sublime-project` file does not contain the "include_locations" key, the following defaults will be used:

```
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
```
