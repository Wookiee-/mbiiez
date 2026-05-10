
import os, sys, inspect
import importlib
from plugins import *

import importlib
import pkgutil

from mbiiez import settings
from mbiiez.bcolors import bcolors

class plugin_handler:

    instance = None
    discovered_plugins = {}
    loaded_plugins = []

    def __init__(self, instance):
        self.instance = instance
        plugins = []
        
        # No Plugins are enabled for instance 
        if(not self.instance.plugins):
            return
            
        for plugin in self.instance.plugins.keys():
            plugins.append("plugin_" + plugin)
        
        sys.path.insert(0, settings.locations.plugins_path)

        # Debug: show plugins being looked for
        self.instance.log_handler.log("[PLUGIN_HANDLER] Looking for plugins: " + str(plugins))

        self.discovered_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in pkgutil.iter_modules()
            if name in plugins
        }
        
        # Debug: show what was discovered
        self.instance.log_handler.log("[PLUGIN_HANDLER] Discovered plugins: " + str(list(self.discovered_plugins.keys())))

        for p in self.discovered_plugins:
            plugin = self.discovered_plugins[p].plugin(self.instance)
            if(hasattr(plugin, 'register')):
                self.instance.plugins_registered.append(plugin.plugin_name)
                plugin.register()
            if(hasattr(plugin, 'on_load')):
                plugin.on_load()
            self.loaded_plugins.append(plugin)
    
    def launch_plugins(self):
        """Print [Yes] Launching messages for all loaded plugins - called during launch_services()"""
        for plugin in self.loaded_plugins:
            if hasattr(plugin, 'register'):
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Launching " + plugin.plugin_name)
        
    