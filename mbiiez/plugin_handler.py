
import os, sys, inspect
import importlib
from plugins import *

import importlib
import pkgutil

from mbiiez import settings
from mbiiez.bcolors import bcolors

class plugin_handler:

    instance = None

    def __init__(self, instance):
        self.instance = instance
        plugins = []
        
        # No Plugins are enabled for instance 
        if(not self.instance.plugins):
            return
            
        for plugin in self.instance.plugins.keys():
            plugins.append("plugin_" + plugin)
        
        sys.path.insert(0, settings.locations.plugins_path)

        discovered_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in pkgutil.iter_modules()
            if name in plugins
        }
        
        for p in discovered_plugins:
            plugin = discovered_plugins[p].plugin(self.instance)
            if(hasattr(plugin, 'register')):
                self.instance.plugins_registered.append(plugin.plugin_name)
                plugin.register()
                # Print launch message for plugin
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Launching " + plugin.plugin_name)
            if(hasattr(plugin, 'on_load')):
                plugin.on_load()
        
    