import os, re, time, collections
import sublime, sublime_plugin


# Include setting keys
STR_INCL_SETTINGS = 'include_autocomplete_settings'
STR_INCL_SETTING_INCL_LOC       = 'include_locations'
STR_INCL_SETTING_IL_PATH        = 'path'
STR_INCL_SETTING_IL_PREFIX      = 'prefix'
STR_INCL_SETTING_IL_IGNORE      = 'ignore'

# Default include setting values
DEF_INCL_SETTING_IL_PATH = '.'
DEF_INCL_SETTING_IL_PREFIX = ''
DEF_INCL_SETTING_IL_IGNORE = []
DEF_INCL_SETTING_INCL_LOC = [
    {
        STR_INCL_SETTING_IL_PATH:   DEF_INCL_SETTING_IL_PATH,
        STR_INCL_SETTING_IL_PREFIX: DEF_INCL_SETTING_IL_PREFIX,
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
        print(filedir)
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
                prefix = loc.get(STR_INCL_SETTING_IL_PREFIX, DEF_INCL_SETTING_IL_PREFIX)
                if path:
                    if os.path.isabs(path):
                        result.append((path, prefix))
                    else:
                        result.append((os.path.join(filedir,path), prefix))
        return result

    def get_subdir(self, view, location, prefix_length):
        # Checks whether the location is valid for our purposes
        # and gets the subdir and prefix
        posx, posy = view.rowcol(location)
        line = view.substr(view.line(location))[:posy]
        line_match = re.match(r'\s*(#include)\s+\"(.*)', line)
        if line_match:
            include_prefix = line_match.group(2)
            subdir = include_prefix[:-prefix_length]
            return (True, subdir)
        # Returns a boolean that signifies whether we are at a
        # completable location and the subdir if present
        return (False, "")

    def get_include_completions(self, basedir, subdir):
        completions = []
        print(os.path.join(basedir, subdir))
        for path, dirs, files in os.walk(os.path.join(basedir, subdir)):
            for f in files:
                if f[-2:] == ".h":
                    reldir = path[len(basedir)+len(subdir)+1:]
                    if len(reldir) > 0:
                        completion = "%s/%s"%(reldir,f)
                    else:
                        completion = f
                    completions.append(["%s\t%s"%(f,reldir), completion])
        # Returns include completions in sublime text format for
        # the given location
        return completions 

    def on_query_completions(self, view, prefix, locations):
        incl_locs = self.get_include_locations(view)
        ok,subdir = self.get_subdir(view, locations[0], len(prefix))
        completions = []
        if ok:
            for location in incl_locs:
                completions += self.get_include_completions(location[0], subdir)
        if len(completions) > 0:
            return (completions,
                    sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        return None
