from mbiiez.models import process
from mbiiez.db import db
from mbiiez.bcolors import bcolors

import multiprocessing
import os
import time
import subprocess
import shlex

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
                process = subprocess.Popen(shlex.split(func), shell=False, stdin=log, stdout=log, stderr=log) 
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
                        process = subprocess.Popen(shlex.split(func), shell=False, stdin=log, stdout=log, stderr=log) 
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
        """ 
        Is a process running by its name within this specific instance?
        """  
        # Special check for OpenJK/Screen sessions
        # This ensures that even if the DB is weird, we check the actual system
        if name == "OpenJK" or name == "Dedicated Server":
            screen_name = "mb2_{}".format(self.instance.name)
            # os.WEXITSTATUS returns 0 if the grep found the screen
            check = os.system(r"screen -ls | grep -q '\.{}$'".format(screen_name))
            if check == 0:
                return True

        # Standard check for Python forks (Log Watcher, etc)
        pr = db().select("processes", {"instance": self.instance.name, "name": name})
     
        if len(pr) == 0:
            return False
        
        # Check if the PIDs recorded in the DB actually exist on the system
        for p in pr:
            if self.process_status_pid(p['pid']):
                return True
        
        return False
       
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
        Stops all processes for this instance only
        """  
        # 1. Get all recorded processes for THIS instance from the DB
        pr = db().select("processes", {"instance": self.instance.name})

        # 2. Stop Python background forks (Managers, Log Watchers)
        # We kill the manager first so it doesn't restart the engine while we are stopping it
        for p in pr:          
            if self.process_status_pid(p['pid']):           
                self.stop_process_pid(p['pid'])
                print(bcolors.GREEN + "[Yes]" + bcolors.ENDC + " Stopped {}".format(str(p['name'])))
            else:
                db().delete("processes", p['id'])

        # 3. Port-Safe Screen Cleanup
        # This only kills the screen session named 'mb2_[instance]'
        screen_name = "mb2_{}".format(self.instance.name)
        
        # This sends a quit command to the specific screen session
        os.system("screen -S {} -X quit >/dev/null 2>&1".format(screen_name))
        
        # 4. Final Cleanup
        os.system("screen -wipe >/dev/null 2>&1")
        
        # Clear DB for this instance only
        db().execute("delete from processes where instance = '{}'".format(self.instance.name))
        
        print((bcolors.RED + "Instance {} has been safely stopped." + bcolors.ENDC).format(self.instance.name))


    def stop_process_name(self, name):
        """ 
        Stops all process by its name within this instance
        """         
        pr = db().select("processes", {"instance": self.instance.name, "name": name})
        
        if len(pr) == 0:
            # Fallback for the engine if it's not in the DB
            if name == "OpenJK":
                screen_name = "mb2_{}".format(self.instance.name)
                os.system("screen -S {} -X quit >/dev/null 2>&1".format(screen_name))
            return False
        
        for p in pr:
            self.stop_process_pid(p['pid'])
        
        db().execute("delete from processes where instance = \"{}\" and name = \"{}\"".format(self.instance.name, name))
        return True

            
    def stop_process_pid(self, pid):
        """ 
        Stops process by its pid
        """         
        try:
            if self.process_status_pid(pid):
                # Hard kill for this specific PID
                os.kill(pid, 9)
            
            db().execute("delete from processes where pid = {}".format(pid))
            return True
             
        except OSError:           
            return False  
