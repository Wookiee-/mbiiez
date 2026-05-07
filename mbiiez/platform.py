#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Platform abstraction layer for cross-platform compatibility.
Handles differences between Windows and Linux/macOS.
'''

import sys
import os
import time
import subprocess
import platform as platform_module

# Check for psutil and provide clear error message on Windows
try:
    import psutil
except ImportError:
    if sys.platform.startswith('win'):
        raise ImportError("psutil is required for Windows support. Install with: pip install psutil")
    psutil = None

# Detect platform
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')


def get_platform():
    '''Get the current platform name'''
    return sys.platform


def get_os_name():
    '''Get the OS name for display purposes'''
    return platform_module.system()


def process_exists(pid):
    '''Check if a process exists by PID'''
    if pid <= 0:
        return False
    try:
        if IS_WINDOWS:
            import psutil
            return psutil.pid_exists(pid)
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError):
        return False


def kill_process(pid, force=False):
    '''Kill a process by PID'''
    if pid <= 0:
        return False
    try:
        if IS_WINDOWS:
            import psutil
            p = psutil.Process(pid)
            if force:
                p.kill()
            else:
                p.terminate()
        else:
            signal = 9 if force else 15
            os.kill(pid, signal)
        return True
    except (OSError, ProcessLookupError, psutil.NoSuchProcess):
        return False


def get_process_list():
    '''Get list of running processes - cross-platform'''
    if IS_WINDOWS:
        import psutil
        return [(p.pid, p.name()) for p in psutil.process_iter()]
    else:
        result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes = []
        lines = result.stdout.decode('utf-8', errors='ignore').split('\n')
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 2:
                try:
                    pid = int(parts[0])
                    name = ' '.join(parts[10:]) if len(parts) > 10 else parts[10] if len(parts) > 10 else ''
                    processes.append((pid, name))
                except (ValueError, IndexError):
                    continue
        return processes


def find_process_by_name(name):
    '''Find process PIDs by name - cross-platform'''
    pids = []
    for pid, proc_name in get_process_list():
        if name.lower() in proc_name.lower():
            pids.append(pid)
    return pids


def kill_process_by_name(name, force=False):
    '''Kill all processes matching name - cross-platform'''
    pids = find_process_by_name(name)
    for pid in pids:
        kill_process(pid, force)
    return len(pids)


def check_port_in_use(port, protocol='udp'):
    '''Check if a port is in use - cross-platform'''
    if IS_WINDOWS:
        import psutil
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                if protocol.upper() == 'UDP':
                    return conn.type == 2  # SOCK_DGRAM
                elif protocol.upper() == 'TCP':
                    return conn.type == 1  # SOCK_STREAM
                return True
        return False
    else:
        result = subprocess.run(
            ['netstat', '-uln'] if protocol.upper() == 'UDP' else ['netstat', '-tln'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return str(port) in result.stdout.decode()


def kill_process_on_port(port, protocol='udp'):
    '''Kill process using specified port - cross-platform'''
    if IS_WINDOWS:
        import psutil
        killed = 0
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                try:
                    proc = psutil.Process(conn.pid)
                    proc.kill()
                    killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        return killed
    else:
        # Linux: use fuser
        result = subprocess.run(
            ['fuser', '-k', f'{port}/{protocol}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.returncode == 0


def get_screen_commands():
    '''Return platform-specific screen/session commands'''
    if IS_WINDOWS:
        # Windows doesn't have screen - use alternative session management
        return {
            'has_screen': False,
            'create_session': None,  # Not applicable
            'send_to_session': None,
            'quit_session': None,
            'wipe_dead': None
        }
    else:
        return {
            'has_screen': True,
            'create_session': 'screen -dmS {} {}',  # screen_name, command
            'send_to_session': 'screen -S {} -X stuff {}',  # screen_name, command
            'quit_session': 'screen -S {} -X quit',  # screen_name
            'wipe_dead': 'screen -wipe'
        }


def find_jemalloc_path():
    '''Find jemalloc library path across different Linux distributions'''
    # Default paths for common distributions
    default_paths = [
        '/usr/lib/i386-linux-gnu/libjemalloc.so.2',  # Debian/Ubuntu i386
        '/usr/lib/i386-linux-gnu/libjemalloc.so.1',  # Debian/Ubuntu i386 (older)
        '/usr/lib/libjemalloc.so.2',                  # Fedora/RHEL
        '/usr/lib/libjemalloc.so.1',                  # Fedora/RHEL (older)
        '/usr/lib32/libjemalloc.so.2',                # Arch Linux
        '/usr/lib/libjemalloc.so',                    # Generic
    ]
    
    # Try to find via ldconfig first
    try:
        result = subprocess.run(['ldconfig', '-p'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'libjemalloc' in line and '.so' in line:
                # Format: libjemalloc.so.2 (libc6,...) => /path/to/libjemalloc.so.2
                if '=>' in line:
                    path = line.split('=>')[1].strip().split()[0]
                    if os.path.exists(path):
                        return path
    except:
        pass
    
    # Fallback to checking default paths
    for path in default_paths:
        if os.path.exists(path):
            return path
    
    # Return the most common path as last resort
    return '/usr/lib/i386-linux-gnu/libjemalloc.so.2'


def get_env_with_preload(env=None):
    '''Get environment with LD_PRELOAD for jemalloc if on Linux'''
    if env is None:
        env = os.environ.copy()
    
    if IS_LINUX:
        _ld_path = find_jemalloc_path()
        if 'LD_PRELOAD' in env:
            if _ld_path not in env['LD_PRELOAD']:
                env['LD_PRELOAD'] = _ld_path + ':' + env['LD_PRELOAD']
        else:
            env['LD_PRELOAD'] = _ld_path
    
    return env


def get_log_path(instance, name):
    '''Get platform-appropriate log file path'''
    if IS_WINDOWS:
        base_path = os.path.expanduser('~\\mbiiez')
    else:
        base_path = '/home/mbiiez/openjk'
    
    os.makedirs(base_path, exist_ok=True)
    return os.path.join(base_path, f'{instance.lower()}-{name.lower()}-output.log')


def get_default_engine_path():
    '''Get platform-appropriate default engine path'''
    if IS_WINDOWS:
        return 'C:\\Program Files\\OpenJK\\mbiided.exe'
    else:
        return '/usr/bin/mbiided.i386'


def supports_multiprocessing_fork():
    '''Check if we can use os.fork (not available on Windows)'''
    return not IS_WINDOWS and hasattr(os, 'fork')


def create_background_process(func, args=(), name='Service'):
    '''Create a background process - cross-platform'''
    if IS_WINDOWS:
        import multiprocessing
        proc = multiprocessing.Process(target=func, args=args, name=name)
        proc.daemon = False
        proc.start()
        return proc.pid
    else:
        pid = os.fork()
        if pid == 0:
            # Child process
            from mbiiez.db import db
            db().insert('processes', {'name': name, 'pid': os.getpid(), 'instance': args[0] if args else 'unknown'})
            while True:
                try:
                    func(*args)
                except Exception as e:
                    print(f'Error in {name}: {e}')
                time.sleep(1)
        else:
            return pid