
import os
import shutil
import subprocess
import time
import signal
import datetime
import shlex
import resource

from mbiiez.bcolors import bcolors
from mbiiez.conf import conf
from mbiiez import settings
from mbiiez.log_handler import log_handler
from mbiiez.process_handler import process_handler
from mbiiez.platform import IS_WINDOWS, IS_LINUX, get_env_with_preload, get_log_path

class launcher: 

    # Names of various processes saved into database
    name_rtvrtm = "RTVRTM Service"
    name_dedicated = "Dedicated Server"
    name_auto_message = "Auto Message"
    name_log_watcher = "Log Watcher"

    event_handler = None
    log_handler = None
    config = None 
    instance_name = None 
    process_handler = None
    instance = None
    
    services = []

    def __init__(self, instance):
        self.config = instance.config      
        self.log_handler = instance.log_handler
        self.process_handler = instance.process_handler
        self.instance_name = self.config['server']['name']
        self.instance = instance

    # Register a service that needs launching
    def register_service(self, name, func, auto_restart = True):
        self.services.append({"name": name, "func": func})

    # Launch all services
    def launch_services(self):
        
        for service in self.services:
            self.log_handler.log("Starting Service: " + service['name'])
            self.process_handler.start(service['func'], service['name'], self.instance_name)
            
    # Dedicated Server Thread    def openjk_launch(self):   
        
        while True:
            print("Checking OpenJK Dedicated...")
            
            if self.process_handler.process_status_name("OpenJK"):
                print("running")
            else:
                print("not running")
            
            while not self.process_handler.process_status_name("OpenJK"): 
                print("Starting OpenJK Dedicated...")
                self.log_handler.log("Starting OpenJK Dedicated Server")
                
                # Build command - screen is Linux-only
                if IS_WINDOWS:
                    cmd = "{} --quiet +set dedicated 2 +set net_port {} +set fs_game {} +exec {}".format(
                        self.config['server']['engine'],
                        self.config['server']['port'],
                        "MBII",
                        self.config['server']['server_config_file']
                    )
                else:
                    screen_name = "mb2_{}".format(self.instance_name)
                    cmd = "screen -dmS {} {} --quiet +set dedicated 2 +set net_port {} +set fs_game {} +exec {}".format(
                        screen_name,
                        self.config['server']['engine'], 
                        self.config['server']['port'],
                        "MBII", 
                        self.config['server']['server_config_file']
                    )
                
                env = get_env_with_preload()
                if IS_LINUX:
                    # jemalloc memory optimization settings for Linux
                    env['MALLOC_CONF'] = "narenas:1,tcache:false,dirty_decay_ms:0,muzzy_decay_ms:0"
                
                process = subprocess.Popen(shlex.split(cmd), shell=False, env=env)
                pid = process.pid
                self.process_handler.add_pid("OpenJK", pid, self.instance_name)
                print(pid)
                time.sleep(3)
            time.sleep(3)
        return
        
    # KILL THIS - RTV/RTM is now handled by plugin_system
    def launch_rtv_thread(self):
        # This method is deprecated - RTV/RTM is now handled by the plugin system
        self.log_handler.log("RTV/RTM is now handled by the plugin system")
        return
       
    # Dedicated Server Thread
 
    # KILL THIS  
    def launch_dedicated_server(self):
    
        # Reason to Bail
        if(not os.path.isfile(self.config['server']['server_config_path'])):
            self.log_handler.log(bcolors.RED + "Failed to start. No config file found at {}".format(self.config['server']['server_config_path']) + bcolors.ENDC)        
            exit()
            
        # Reason to Bail  
        if(not os.path.isfile("{}/{}".format("/usr/bin", self.config['server']['engine']))):        
            self.log_handler.log(bcolors.RED + "Failed to start. No engine found at {}/{}".format("/usr/bin", self.config['server']['engine']) + bcolors.ENDC)   
            exit()
            
        # Make sure can be executed    
        # os.system("chmod +x {}/{}".format("/usr/bin", self.config['server']['engine']))  
          
        # Sym Links
        if(os.path.exists("/home/mbiiez/.local/share/openjk")):
            if(not os.path.islink("/home/mbiiez/.local/share/openjk")):
                shutil.rmtree("/home/mbiiez/.local/share/openjk")       
                os.symlink(settings.locations.game_path, "/home/mbiiez/.local/share/openjk")
        
        if(os.path.exists("/home/mbiiez/.ja")):
            if(not os.path.islink("/home/mbiiez/.ja")):
                shutil.rmtree("/home/mbiiez/.ja")       
                os.symlink(settings.locations.game_path, "/home/mbiiez/.ja")  
    
        self.process_handler.start(self.launch_dedicated_server_thread, self.name_dedicated, self.instance_name)

    # Backwards compatibility - RTV/RTM is now handled by plugin system
    def launch_rtv(self):
        # RTV/RTM is now handled by the plugin system - just log and return
        self.log_handler.log("RTV/RTM is now handled by the plugin system (plugins/plugin_rtvrtm.py)")
        
        # Check if RTV/RTM is enabled in plugins.rtvrtm config
        rtv_enabled = self.config.get('plugins', {}).get('rtvrtm', {}).get('enable_rtv', False)
        rtm_enabled = self.config.get('plugins', {}).get('rtvrtm', {}).get('enable_rtm', False)
        
        if rtv_enabled:
            self.log_handler.log("[RTV/RTM] RTV is enabled")
        if rtm_enabled:
            self.log_handler.log("[RTV/RTM] RTM is enabled")
        
        return

    def launch_rtvrtm(self):
        """Launch the RTVRTM plugin - now handled by plugin system"""
        self.log_handler.log("Starting RTV/RTM Plugin via plugin system")
        
        # Check plugins.rtvrtm config for enable flags
        rtv_enabled = self.config.get('plugins', {}).get('rtvrtm', {}).get('enable_rtv', False)
        rtm_enabled = self.config.get('plugins', {}).get('rtvrtm', {}).get('enable_rtm', False)
        
        # Check if plugin config exists
        plugin_configured = self.config.get('plugins', {}).get('rtvrtm') is not None
        
        if rtv_enabled or rtm_enabled:
            self.log_handler.log("[RTV/RTM] Plugin is enabled (RTV: {}, RTM: {})".format(rtv_enabled, rtm_enabled))
            if plugin_configured:
                self.log_handler.log("[RTV/RTM] Plugin config found, will be loaded by plugin_handler")
        else:
            self.log_handler.log("[RTV/RTM] RTV/RTM is disabled in plugins config")
        
        return
