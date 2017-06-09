import os, re, time, collections
import sublime, sublime_plugin


# Include setting keys
STR_INCL_SETTINGS = 'include_autocomplete_settings'
STR_INCL_SETTING_INCL_LOC       = 'include_locations'
STR_INCL_SETTING_IL_PATH        = 'path'
STR_INCL_SETTING_IL_IGNORE      = 'ignore'

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


class IncludeAutoComplete(sublime_plugin.EventListener):
    def get_include_locations(self, view):
        # Returns a list of location tuples
        result = []
        filedir = os.path.dirname(view.file_name())
        # 1. Get include locations from project data
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

    def get_include_completions(self, basedir, subdir, ignore):
        completions = []
        root = os.path.join(basedir, subdir)
        root_len = len(root)
        print("Looking for completions in %s (ignoring %s)" % (root, ignore))
        for path, dirs, files in os.walk(root, topdown=True):
            reldir = path[root_len:]
            for f in files:
                if f.endswith(('.h', '.hh', '.hpp', '.hxx', '.inl', '.inc', '.ipp')):
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
        incl_locs = self.get_include_locations(view)

        # Get the subdir.
        scope = view.extract_scope(locations[0])
        firstline = view.split_by_newlines(scope)[0]
        subdir = view.substr(firstline)
        subdir = subdir.strip(' "<>')
        subdir = subdir[:-len(prefix)]

        # Present the completions.
        completions = []
        for location in incl_locs:
            completions += self.get_include_completions(location[0], subdir, location[1])
        if len(completions) > 0:
            return (completions,
                    sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        return None
