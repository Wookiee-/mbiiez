from mbiiez.models import process
from mbiiez.db import db
from mbiiez.bcolors import bcolors

import multiprocessing
import os
import time
import subprocess
import shlex
import socket

class process_handler:

    instance = None
    services = []
    
    def __init__(self, instance):
        self.instance = instance
               
    def register_service(self, name, func, priority = 99, awaiter = None, supervised = True):
        self.services.append({"name": name, "func": func, "priority": priority, "awaiter": awaiter, "supervised": supervised})

    def launch_services(self):
        """ 
            Launch all services 
        """       
        # Sort by Priority
        services = sorted(self.services, key=lambda k: k['priority'])
        
        for service in services:
        
            if(service['awaiter'] and callable(service['awaiter'])):
                service['awaiter']();
        
            self.instance.log_handler.log("Starting Service: " + service['name'])
            print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Launching " + service['name'])   
            self.start(service['func'], service['name'], self.instance.name, service['supervised'])
            time.sleep(1)
            
    def start(self, func, name, instance, supervised = True):
        """ 
            Start a given func (or shell command), with name for instance 
        """  

        # Is our service a Python Function?
        if(callable(func)):

            # Process is Forked
            pid = os.fork()
            
            # Child Process Continues
            if(pid == 0):
            
                # Capture the PID for this fork
                db().insert("processes", {"name": name, "pid": os.getpid(), "instance": instance})

                times_started = 0

                # Begin a Loop
                while(True):
                
                    if(times_started > 10):
                        self.instance.log_handler.log("{} Failed to start after 10 tries".format(name))
                        break;
                     
                    try:
                         func()
                    except Exception as e:     
                        self.instance.exception_handler.log(e)
                         
                    # Reached is func ends, should not end    
                    times_started = times_started + 1
                    time.sleep(1)
                          
        # It is a shell command so run inside a python container so we have the pid
        else:
            # Output from this process is sent to this log file, but is cleared on every restart. 
            std_out_file = "/home/mbiiez/openjk/MBII/{}-{}-output.log".format(instance.lower(),name.lower())

            # Used to clear the file, these output looks are not for persistant logging
            open(std_out_file, 'w').close()

            if not supervised:
                # Launch once and move on (Fire & Forget)
                log = open(std_out_file, 'a')
                env = os.environ.copy()
                _ld_path = "/usr/lib/i386-linux-gnu/libjemalloc.so.2"
                if 'LD_PRELOAD' in env:
                    if _ld_path not in env['LD_PRELOAD']:
                        env['LD_PRELOAD'] = _ld_path + ":" + env['LD_PRELOAD']
                else:
                    env['LD_PRELOAD'] = _ld_path
                process = subprocess.Popen(shlex.split(func), shell=False, stdin=log, stdout=log, stderr=log, env=env) 
                db().insert("processes", {"name": name, "pid": process.pid, "instance": instance})
                return

            pid = os.fork()
            if(pid == 0):
            
                func = "{} ".format(func)
                
                container_name = name + " Container"
            
                # When running a shell command, a fork is created which acts are the parent to the new process.
            
                db().insert("processes", {"name": container_name, "pid": os.getpid(), "instance": instance})
                
                process = None
                crashes = 0
                restart = False
                
                # Begin Loop
                while(True):
                
                    # Should stop this process if requested to stop
                    if(not self.process_status_name(container_name)):
                        break;
                        
                    if(crashes >= 10):
                        self.instance.log_handler.log("Service: {} was unable to start after {} retries...".format(name, crashes))
                        break;
                        
                    # Start the Process
                    if(process == None):  
                        if os.path.exists(std_out_file):
                            os.remove(std_out_file)
                        log = open(std_out_file, 'a')
                        env = os.environ.copy()
                        _ld_path = "/usr/lib/i386-linux-gnu/libjemalloc.so.2"
                        if 'LD_PRELOAD' in env:
                            if _ld_path not in env['LD_PRELOAD']:
                                env['LD_PRELOAD'] = _ld_path + ":" + env['LD_PRELOAD']
                        else:
                            env['LD_PRELOAD'] = _ld_path
                        process = subprocess.Popen(shlex.split(func), shell=False, stdin=log, stdout=log, stderr=log, env=env) 
                        db().insert("processes", {"name": name, "pid": process.pid, "instance": instance}) 
                        time.sleep(1)
                        if(crashes > 0):
                            time.sleep(5)
                        
                    # If either POLL returns some error or the PID is not running at all
                    if(not process == None):     
                        if(not process.poll() == None): # WHEN PROCESS CRASHES, POLL AND STATUS STILL SHOW ACTIVE
                            crashes = crashes + 1
                            db().execute("delete from processes where pid = {}".format(process.pid))
                            self.stop_process_name(name)
                            process = None
                            self.instance.log_handler.log("Restarting Service: {}, failed {} times".format(name, crashes))
                            
                    time.sleep(3)

    def process_pid_by_name(self, name):
        """ 
        Find a process pid by its name
        """            
        pr = db().select("processes", {"instance": self.instance.name, "name": name})
        # If there are multiple (which shouldn't happen for one instance), 
        # we return the most recent one.
        if pr:
            return pr[-1]['pid']
        return 0

    def process_status_name(self, name):
        screen_name = "mb2_{}".format(self.instance.name)
        
        # 1. Check if the screen/binary is physically there
        binary_check = os.system(r"pgrep -f 'screen.*{}' > /dev/null".format(screen_name))
        if binary_check != 0:
            return False

        # 2. Heartbeat Check: See if the UDP port is actually open
        # If the engine is a zombie, the port will usually be unreachable
        port = int(self.instance.config['server']['port'])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # We don't need to send data, just see if we can bind/connect
            sock.settimeout(1.0)
            # Note: UDP is connectionless, so we check if the OS reports the port as occupied
            # by trying to bind to it. If bind FAILS, the engine is still holding it.
            # If bind SUCCEEDS, the engine has dropped the port and is a zombie.
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.bind(('', port))
            test_sock.close()
            # If we got here, the port is FREE, meaning the engine is dead/zombie
            return False
        except:
            # Port is occupied, engine is likely alive
            return True
       
    def process_status_pid(self, pid):
        """ 
        Is a process running by its pid?
        """    
        if pid <= 0:
            return False
            
        try:
            # Signal 0 does not kill the process, but performs error checking.
            # It checks if the PID is valid and if we have permission to send signals.
            os.kill(pid, 0)
            return True
             
        except (OSError, ProcessLookupError):           
            return False
       
    def stop_all(self):
        """ 
        Stops all processes by targeting the specific port and screen.
        """  
        instance_name = self.instance.name
        screen_name = "mb2_{}".format(instance_name)
        port = self.instance.config['server']['port'] # Extract the unique port
        
        # 1. Kill Python forks from DB
        pr = db().select("processes", {"instance": instance_name})
        for p in pr:           
            self.stop_process_pid(p['pid'])

        # 2. TARGET THE PORT: Kill whatever is listening on this instance's port
        # This is the most reliable way to kill the specific mbiided engine
        os.system("fuser -k {}/udp >/dev/null 2>&1".format(port))
        
        # 3. Target the Screen Name as a backup
        os.system(r"pkill -9 -f '{}'".format(screen_name))
        
        # 4. Final Screen Cleanup
        os.system("screen -S {} -X quit >/dev/null 2>&1".format(screen_name))
        os.system("screen -wipe >/dev/null 2>&1")
        
        # 5. Clear DB
        db().execute("delete from processes where instance = '{}'".format(instance_name))
        print(bcolors.RED + f"Instance {instance_name} (Port {port}) fully terminated." + bcolors.ENDC)


    def stop_process_name(self, name):
        """ 
        Stops all processes by its name within this instance
        """         
        pr = db().select("processes", {"instance": self.instance.name, "name": name})
        
        # 1. Handle Engine/Screen fallback if no DB record exists
        # We check both "OpenJK" and "Dedicated Server" (the name used in launcher.py)
        if name in ["OpenJK", "mbiided", "Dedicated Server"]:
            screen_name = "mb2_{}".format(self.instance.name)
            port = self.instance.config['server']['port']

            # Force kill whatever is holding the port (Most reliable for engines)
            os.system("fuser -k {}/udp >/dev/null 2>&1".format(port))
            
            # Kill the screen session and its children using the anchored regex
            os.system(r"pkill -9 -f '\.{}$'".format(screen_name))
            
            # Clean up the screen socket
            os.system("screen -S {} -X quit >/dev/null 2>&1".format(screen_name))
            os.system("screen -wipe >/dev/null 2>&1")
        
        # 2. Stop Python processes (Log Watcher, RTVRTM, etc) from DB records
        for p in pr:
            self.stop_process_pid(p['pid'])
        
        # 3. Final cleanup of the DB for this specific name
        db().execute("delete from processes where instance = '{}' and name = '{}'".format(self.instance.name, name))
        return True

            
    def stop_process_pid(self, pid):
        """ 
        Stops process by its pid
        """         
        if pid <= 0:
            return False

        try:
            if self.process_status_pid(pid):
                # Hard kill for this specific PID
                os.kill(pid, 9)
            
            # Use a parameterized query or ensure string formatting is safe
            db().execute("delete from processes where pid = {}".format(pid))
            return True
             
        except (OSError, ProcessLookupError):           
            # Even if the process is already gone, ensure it's removed from DB
            db().execute("delete from processes where pid = {}".format(pid))
            return False 
