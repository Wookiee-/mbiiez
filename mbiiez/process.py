import os
import psutil

from mbiiez.platform import IS_WINDOWS, process_exists, kill_process

class process:

    # Return a PID contained in a given file
    def get_pid_from_file(self, pid_file):
        if(os.path.isfile(pid_file)):
            with open(pid_file, 'r') as file:
                pid = file.read()
                
            return int(pid)
        else:
            return 0
            
    # Kill PID contained in a given file
    def kill_pid_file(self, pid_file):
        if(self.pid_file_running(pid_file)):
            pid = self.get_pid_from_file(pid_file)
            try:             
                 os.kill(pid, 15)
                 return True
                 
            except OSError:
                return False
                
    # Is PID in a given file running 
    def pid_file_running(self, pid_file):
        pid = self.get_pid_from_file(pid_file)
        
        if(pid == 0):
            return False
        
        if(self.pid_is_running(pid)):
            return True
        else:
            os.remove(pid_file)     
            return False    # Is a PID  running
    def pid_is_running(self, pid):
        return process_exists(pid)
                  
    # Return PID of process by name      
    def find_process_by_name(self, search):
        for p in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                if p.info["cmdline"] and search in ' '.join(p.info["cmdline"]):
                    return p.pid

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return 0
     
    # Kill process by name
    def kill_process_by_name(self, search):
        if IS_WINDOWS:
            # Windows: use taskkill
            os.system(f'taskkill /F /IM {search}.exe >nul 2>&1')
        else:
            # Linux: use pkill
            os.system(f'pkill -15 -f "{search}"')   
        
        