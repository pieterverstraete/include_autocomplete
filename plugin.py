"""Listens to completion queries in #include statements."""

import os
import collections
import json
import sublime
import sublime_plugin

import logging


def InitializeMainLogger(main_logger):
    """Apply required settings to the main logger.
    """
    if not main_logger.hasHandlers():
        # Must be set to lowest level to get total freedom in handlers
        main_logger.setLevel(logging.DEBUG)

        # Disable log duplications when reloading
        main_logger.propagate = False

        # Create / override console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Create formatter and add it to the handler
        formatter = logging.Formatter(
            '[Include Autocomplete / %(levelname)s] %(message)s')
        console_handler.setFormatter(formatter)

        # Add the handler to logger
        main_logger.addHandler(console_handler)


logger = logging.getLogger(__name__)
InitializeMainLogger(logger)


# Include setting keys
STR_INCL_SETTINGS = 'include_autocomplete_settings'
STR_INCL_SETTING_INCL_LOC = 'include_locations'
STR_INCL_SETTING_IL_PATH = 'path'
STR_INCL_SETTING_IL_IGNORE = 'ignore'

# Default include setting values
DEF_INCL_SETTING_IL_PATH = '.'
DEF_INCL_SETTING_IL_IGNORE = []
DEF_INCL_SETTING_INCL_LOC = [
    {
        STR_INCL_SETTING_IL_PATH:   DEF_INCL_SETTING_IL_PATH,
        STR_INCL_SETTING_IL_IGNORE: DEF_INCL_SETTING_IL_IGNORE
    }
]
DEF_INCL_SETTINGS = {
    STR_INCL_SETTING_INCL_LOC: DEF_INCL_SETTING_INCL_LOC
}

HEADER_EXT = (".h", ".hh", ".hpp", ".hxx", ".inl", ".inc", ".ipp")


class IncludeAutoComplete(sublime_plugin.EventListener):
    """Listens to completion queries in "#include" statements."""

    def _get_include_locations(self, view):
        result = self._get_include_locations_from_compile_commands(view)
        result.extend(self._get_include_locations_from_project_data(view))
        return result

    def _get_include_locations_from_compile_commands(self, view):

        # Look for various commonly used settings. This is a heuristic.
        sources = view.settings().get("ecc_flags_sources", [])
        if not sources:
            sources = view.settings().get("easy_clang_complete_flags_sources", [])
        if not sources:
            sources = sublime.load_settings("EasyClangComplete.sublime-settings").get("ecc_flags_sources", [])
        if not sources:
            sources = sublime.load_settings("EasyClangComplete.sublime-settings").get("easy_clang_complete_flags_sources", [])
        vars = view.window().extract_variables()

        # EasyClangComplete hack.
        vars.update({"project_base_path": vars.get("project_path",
                                                   vars.get("folder", ""))})

        # Parse EasyClangComplete's "flags_sources" dictionary (if we have it).
        for source in sources:
            if source["file"] == "compile_commands.json":
                compdb = source["search_in"]
                compdb = sublime.expand_variables(compdb, vars)
                compdb = os.path.join(compdb, "compile_commands.json")
                if os.path.exists(compdb):
                    # Success.
                    return self._read_compilation_database(view, compdb)

        # Try this one at this point.
        sources = view.settings().get("compile_commands", "")
        if sources:
            sources = sublime.expand_variables(sources, vars)
            sources = os.path.join(sources, "compile_commands.json")
            if os.path.exists(sources):
                # Success.
                return self._read_compilation_database(view, sources)

        # No success.
        return []

    def _read_compilation_database(self, view, path):
        logger.info("found compilation database: %s", path)
        result = set()

        def add_include(result, include, directory):
            if not os.path.isabs(include):
                include = os.path.join(directory, include)
                include = os.path.abspath(include)
            result.add(include)

        def parse_command(result, command, directory):
            command = command.split()
            take_next = False
            for c in command:
                if take_next:
                    add_include(result, c, directory)
                    take_next = False
                elif c in ("-isystem", "-I"):
                    take_next = True
                elif c.startswith("-I"):
                    add_include(result, c[2:], directory)

        found = None
        with open(path, "r") as f:
            compdb = json.load(f)
            if view.file_name().endswith(HEADER_EXT):
                # Just add all possible include dirs if we're in a header file.
                for item in compdb:
                    parse_command(result, item["command"], item["directory"])
            else:
                # Otherwise, find our file in the compilation database, and
                # parse the compiler invocation.
                found = False
                for item in compdb:
                    if item["file"] == view.file_name():
                        parse_command(result, item["command"], item["directory"])
                        found = True
                        break

        if found is not None and not found:
            # The file is not a header, there's a compilation database, but the
            # file is not in it.
            logger.warning(
                "%s does not have compile commands.", view.file_name())
        return [(include, []) for include in result]

    def _get_include_locations_from_project_data(self, view):
        result = []
        filedir = os.path.dirname(view.file_name())
        incl_settings = DEF_INCL_SETTINGS
        project_data = view.window().project_data()
        if project_data:
            incl_settings = project_data.get(STR_INCL_SETTINGS, DEF_INCL_SETTINGS)
        incl_locations = incl_settings.get(STR_INCL_SETTING_INCL_LOC, DEF_INCL_SETTING_INCL_LOC)
        if isinstance(incl_locations, collections.Sequence):
            # 2. Verify and format all found locations
            for loc in incl_locations:
                path = loc.get(STR_INCL_SETTING_IL_PATH, None)
                if not path:
                    continue
                path = sublime.expand_variables(path, view.window().extract_variables())
                path = os.path.join(filedir,path) if not os.path.isabs(path) else path
                ignore = loc.get(STR_INCL_SETTING_IL_IGNORE, DEF_INCL_SETTING_IL_IGNORE)
                if not isinstance(ignore, collections.Sequence):
                    ignore = DEF_INCL_SETTING_IL_IGNORE
                ignore = list(map(lambda x: sublime.expand_variables(x, view.window().extract_variables()), ignore))
                result.append((path, ignore))
        return result

    def _get_include_completions(self, basedir, subdir, ignore):
        completions = []
        root = os.path.join(basedir, subdir)
        root_len = len(root)
        logger.debug(
            "Looking for completions in %s (ignoring %s)", root, ignore)
        for path, dirs, files in os.walk(root, topdown=True):
            reldir = path[root_len:]
            for f in files:
                if f.endswith(HEADER_EXT):
                    completion = os.path.join(reldir,f) if len(reldir) > 0 else f
                    completions.append(["%s\t%s"%(f,reldir), completion])
            dirs[:] = [d for d in dirs if os.path.join(reldir,d) not in ignore]
        # Returns include completions in sublime text format for
        # the given location
        return completions

    def on_query_completions(self, view, prefix, locations):
        # If we have more than one location, forget about it.
        if len(locations) != 1:
            return None

        # If we're not in an include statement, forget about it.
        if not view.match_selector(locations[0],
                                   "meta.preprocessor.include & "
                                   "(string.quoted.other | "
                                   "string.quoted.double)"):
            return None

        # Get the include directories of the project.
        incl_locs = self._get_include_locations(view)

        # Get the subdir.
        scope = view.extract_scope(locations[0])
        firstline = view.split_by_newlines(scope)[0]
        subdir = view.substr(firstline)
        subdir = subdir.strip(' "<>')
        subdir = subdir[:-len(prefix)]

        # Present the completions.
        completions = []
        for location in incl_locs:
            completions += self._get_include_completions(location[0], subdir, location[1])
        if len(completions) > 0:
            return (completions,
                    sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        return None
