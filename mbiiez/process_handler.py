from mbiiez.models import process
from mbiiez.db import db
from mbiiez.bcolors import bcolors
from mbiiez.platform import *

import multiprocessing
import os
import time
import subprocess
import shlex
import socket
import sys

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
            
            if IS_WINDOWS:
                # Windows: use multiprocessing instead of fork
                from mbiiez.db import db
                times_started = 0
                
                def run_service():
                    db().insert("processes", {"name": name, "pid": os.getpid(), "instance": instance})
                    times_started = 0
                    while True:
                        if times_started > 10:
                            self.instance.log_handler.log("{} Failed to start after 10 tries".format(name))
                            break
                        try:
                            func()
                        except Exception as e:
                            self.instance.exception_handler.log(e)
                        times_started = times_started + 1
                        time.sleep(1)
                
                proc = multiprocessing.Process(target=run_service, name=name)
                proc.daemon = False
                proc.start()
                return
            else:
                # Linux: use fork
                pid = os.fork()
                
                # Child Process Continues
                if pid == 0:
                    db().insert("processes", {"name": name, "pid": os.getpid(), "instance": instance})
                    times_started = 0
                    while True:
                        if times_started > 10:
                            self.instance.log_handler.log("{} Failed to start after 10 tries".format(name))
                            break
                        try:
                            func()
                        except Exception as e:
                            self.instance.exception_handler.log(e)
                        times_started = times_started + 1
                        time.sleep(1)
                else:
                    return
        
        # It is a shell command so run inside a python container so we have the pid
        else:
            std_out_file = get_log_path(instance, name)

            # Used to clear the file, these output looks are not for persistant logging
            open(std_out_file, 'w').close()

            if not supervised:
                # Launch once and move on (Fire & Forget)
                log = open(std_out_file, 'a')
                env = get_env_with_preload()
                process = subprocess.Popen(shlex.split(func), shell=False, stdin=log, stdout=log, stderr=log, env=env)
                db().insert("processes", {"name": name, "pid": process.pid, "instance": instance})
                return

            if IS_WINDOWS:
                # Windows: use multiprocessing
                def run_supervised_service():
                    db().insert("processes", {"name": name + " Container", "pid": os.getpid(), "instance": instance})
                    process = None
                    crashes = 0
                    while True:
                        if not self.process_status_name(name):
                            break
                        if crashes >= 10:
                            self.instance.log_handler.log("Service: {} was unable to start after {} retries...".format(name, crashes))
                            break
                        if process is None:
                            if os.path.exists(std_out_file):
                                os.remove(std_out_file)
                            log = open(std_out_file, 'a')
                            env = get_env_with_preload()
                            process = subprocess.Popen(shlex.split(func), shell=False, stdin=log, stdout=log, stderr=log, env=env)
                            db().insert("processes", {"name": name, "pid": process.pid, "instance": instance})
                            time.sleep(1)
                            if crashes > 0:
                                time.sleep(5)
                        if process is not None:
                            if process.poll() is not None:
                                crashes = crashes + 1
                                db().execute("delete from processes where pid = {}".format(process.pid))
                                self.stop_process_name(name)
                                process = None
                                self.instance.log_handler.log("Restarting Service: {}, failed {} times".format(name, crashes))
                        time.sleep(3)
                
                proc = multiprocessing.Process(target=run_supervised_service, name=name)
                proc.daemon = False
                proc.start()
            else:
                # Linux: use fork
                pid = os.fork()
                if pid == 0:
                    func = "{} ".format(func)
                    container_name = name + " Container"
                    db().insert("processes", {"name": container_name, "pid": os.getpid(), "instance": instance})
                    process = None
                    crashes = 0
                    while True:
                        if not self.process_status_name(container_name):
                            break
                        if crashes >= 10:
                            self.instance.log_handler.log("Service: {} was unable to start after {} retries...".format(name, crashes))
                            break
                        if process is None:
                            if os.path.exists(std_out_file):
                                os.remove(std_out_file)
                            log = open(std_out_file, 'a')
                            env = get_env_with_preload()
                            process = subprocess.Popen(shlex.split(func), shell=False, stdin=log, stdout=log, stderr=log, env=env)
                            db().insert("processes", {"name": name, "pid": process.pid, "instance": instance})
                            time.sleep(1)
                            if crashes > 0:
                                time.sleep(5)
                        if process is not None:
                            if process.poll() is not None:
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
        """Check if a service/process is running by name"""
        
        # Use port check as the primary method (works on all platforms)
        port = int(self.instance.config['server']['port'])
        
        if IS_WINDOWS:
            # Windows: check if port is in use by our engine
            return check_port_in_use(port, 'udp')
        else:
            # Linux: check screen first, then port
            screen_name = "mb2_{}".format(self.instance.name)
            binary_check = os.system(r"pgrep -f 'screen.*{}' > /dev/null".format(screen_name))
            if binary_check != 0:
                return False
            return check_port_in_use(port, 'udp')
       
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
            return False    def stop_all(self):
        """
        Stops all processes by targeting the specific port and screen.
        """  
        instance_name = self.instance.name
        screen_name = "mb2_{}".format(instance_name)
        port = self.instance.config['server']['port']
        
        # 1. Kill Python processes from DB
        pr = db().select("processes", {"instance": instance_name})
        for p in pr:
            self.stop_process_pid(p['pid'])

        # 2. Kill process on port (works on all platforms)
        kill_process_on_port(port, 'udp')
        
        # 3. Linux-specific cleanup
        if not IS_WINDOWS:
            os.system(r"pkill -9 -f '{}'".format(screen_name))
            os.system("screen -S {} -X quit >/dev/null 2>&1".format(screen_name))
            os.system("screen -wipe >/dev/null 2>&1")
        
        # 4. Clear DB
        db().execute("delete from processes where instance = '{}'".format(instance_name))
        print(bcolors.RED + f"Instance {instance_name} (Port {port}) fully terminated." + bcolors.ENDC)    def stop_process_name(self, name):
        """
        Stops all processes by its name within this instance
        """         
        pr = db().select("processes", {"instance": self.instance.name, "name": name})
        
        # 1. Handle Engine/Screen fallback if no DB record exists
        if name in ["OpenJK", "mbiided", "Dedicated Server"]:
            port = self.instance.config['server']['port']

            # Kill whatever is holding the port (works on all platforms)
            kill_process_on_port(port, 'udp')
            
            # Linux-specific cleanup
            if not IS_WINDOWS:
                screen_name = "mb2_{}".format(self.instance.name)
                os.system(r"pkill -9 -f '\.{}$'".format(screen_name))
                os.system("screen -S {} -X quit >/dev/null 2>&1".format(screen_name))
                os.system("screen -wipe >/dev/null 2>&1")
        
        # 2. Stop Python processes from DB records
        for p in pr:
            self.stop_process_pid(p['pid'])
        
        # 3. Final cleanup of the DB for this specific name
        db().execute("delete from processes where instance = '{}' and name = '{}'".format(self.instance.name, name))
        return True    def add_pid(self, name, pid, instance):
        """
        Add a process PID to the database
        """
        db().insert("processes", {"name": name, "pid": pid, "instance": instance})

    def stop_process_pid(self, pid):
        """
        Stops process by its pid
        """         
        if pid <= 0:
            return False

        try:
            if process_exists(pid):
                kill_process(pid, force=True)
            
            db().execute("delete from processes where pid = {}".format(pid))
            return True
             
        except (OSError, ProcessLookupError):           
            db().execute("delete from processes where pid = {}".format(pid))
            return False 
