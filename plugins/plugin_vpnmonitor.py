#!/usr/bin/env python3
# Copyright (c) 2021, devon/spaghetti/2cwldys
# All rights reserved.

'''
MBIIEZ Plugin: VPN Monitor

This plugin monitors player connections and checks for VPN/proxy usage
using the iphub.info API. Detected VPN users can be warned and/or kicked/banned.

Ported from vpnmonitor.sh to Python 3 and integrated as a mbiiEZ plugin.
'''

import time
import os
import sqlite3
import json
import urllib.request

VERSION = '1.1_py3'


class plugin:
    '''VPN Monitor Plugin for mbiiEZ - Python 3 compatible'''
    
    plugin_name = 'VPN Monitor'
    plugin_author = 'Ported from vpnmonitor.sh (devon/spaghetti/2cwldys)'
    plugin_url = ''
    
    def __init__(self, instance):
        self.instance = instance
        
        # VPN config from instance config
        self.vpn_enabled = instance.config.get('plugins', {}).get('vpn_monitor', {}).get('enabled', False)
        self.uncertain_block = instance.config.get('plugins', {}).get('vpn_monitor', {}).get('uncertain_block', False)
        self.iphub_api_key = instance.config.get('plugins', {}).get('vpn_monitor', {}).get('iphub_api_key', '')
        
        # Database settings
        self.db_path = instance.config.get('plugins', {}).get('vpn_monitor', {}).get('database_path', 
            os.path.join(instance.mbiidir, 'vpn_monitor.db'))
        
        # Track recent connections to avoid duplicate checks
        self.recent_connections = {}
        self.recent_connections_max = 100
        self.connection_timeout = 60  # seconds
        
        # Initialize VPN database
        self.init_vpn_database()
    
    def register(self):
        '''Register event handlers'''
        self.instance.event_handler.register_event('player_connected', self.on_player_connects)
        self.instance.event_handler.register_event('new_log_line', self.on_new_log_line)
    
    def init_vpn_database(self):
        '''Initialize the VPN monitoring database'''
        try:
            # Ensure directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS iplist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT UNIQUE,
                    vpn INTEGER,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            self.instance.log_handler.log(f'[VPN Monitor] Database init error: {e}')
    
    def on_load(self):
        '''Called when plugin is loaded'''
        self.instance.log_handler.log('[VPN Monitor] Plugin loaded - Version ' + VERSION)
        if self.vpn_enabled:
            self.instance.log_handler.log('[VPN Monitor] VPN checking is enabled')
            if not self.iphub_api_key:
                self.instance.log_handler.log('[VPN Monitor] WARNING: No iphub.info API key configured!')
        else:
            self.instance.log_handler.log('[VPN Monitor] Plugin is disabled')
    
    def on_new_log_line(self, args):
        '''Handle new log lines - parse ClientConnect events'''
        log_line = args.get('log_line', '')
        
        # Check for ClientConnect pattern
        # Format: 123:45 ClientConnect: 1234 IP: 192.168.1.1
        if 'ClientConnect:' in log_line and 'IP:' in log_line:
            self.parse_connect_line(log_line)
    
    def parse_connect_line(self, log_line):
        '''Parse a ClientConnect log line and extract connection info'''
        try:
            # Parse: ClientConnect: playerId IP: ipAddress
            parts = log_line.split('ClientConnect:')
            if len(parts) < 2:
                return
            
            rest = parts[1].strip()
            
            # Extract player ID and IP
            player_id = None
            ip_address = None
            
            # Find player ID (before 'IP:')
            if 'IP:' in rest:
                id_part = rest.split('IP:')[0].strip()
                # Player ID is usually the last number before IP
                words = id_part.split()
                if words:
                    player_id = words[-1]
                
                # Extract IP
                ip_part = rest.split('IP:')[1].strip()
                # IP is the first word after IP:
                words = ip_part.split()
                if words:
                    ip_address = words[0]
            
            if player_id and ip_address:
                self.handle_connection(player_id, ip_address)
                
        except Exception as e:
            self.instance.log_handler.log(f'[VPN Monitor] Parse error: {e}')
    
    def on_player_connects(self, args):
        '''Handle player connection event'''
        player_id = args.get('player_id', '')
        player_name = args.get('player', 'Unknown')
        ip_address = args.get('ip', '')
        
        if ip_address:
            self.handle_connection(player_id, ip_address)
    
    def handle_connection(self, player_id, ip_address):
        '''Check a connection for VPN and take action'''
        if not self.vpn_enabled:
            return
        
        if not self.iphub_api_key:
            return
        
        # Check for duplicate/recent connection
        current_time = time.time()
        key = f'{player_id}:{ip_address}'
        
        if key in self.recent_connections:
            if current_time - self.recent_connections[key] < self.connection_timeout:
                return  # Already checked recently
        
        self.recent_connections[key] = current_time
        
        # Cleanup old entries
        if len(self.recent_connections) > self.recent_connections_max:
            self.cleanup_recent_connections()
        
        # Check database first
        vpn_status = self.check_database(ip_address)
        
        if vpn_status is None:
            # Not in database, check API
            self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: checking for VPN...')
            vpn_result = self.check_vpn_api(ip_address)
            
            if vpn_result is not None:
                vpn_status = vpn_result
                self.save_to_database(ip_address, vpn_status)
        
        if vpn_status is not None:
            self.handle_vpn_status(player_id, ip_address, vpn_status)
    
    def check_database(self, ip_address):
        '''Check if IP is already in our database'''
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT vpn FROM iplist WHERE ip = ?', (ip_address,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: found in database (vpn={result[0]})')
                return result[0]
            return None
            
        except Exception as e:
            self.instance.log_handler.log(f'[VPN Monitor] Database check error: {e}')
            return None
    
    def save_to_database(self, ip_address, vpn_status):
        '''Save VPN check result to database'''
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO iplist (ip, vpn, date) VALUES (?, ?, CURRENT_TIMESTAMP)', 
                         (ip_address, vpn_status))
            conn.commit()
            conn.close()
        except Exception as e:
            self.instance.log_handler.log(f'[VPN Monitor] Database save error: {e}')
    
    def check_vpn_api(self, ip_address):
        '''Check IP using iphub.info API'''
        try:
            url = f'http://v2.api.iphub.info/ip/{ip_address}'
            request = urllib.request.Request(url)
            request.add_header('X-Key', self.iphub_api_key)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                
                block = result.get('block', -1)
                self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: API response block={block}')
                
                return block
                
        except Exception as e:
            self.instance.log_handler.log(f'[VPN Monitor] API check error: {e}')
            return None
    
    def handle_vpn_status(self, player_id, ip_address, vpn_status):
        '''Handle VPN detection result'''
        # vpn_status values:
        # 0 = No VPN detected - allowed
        # 1 = VPN detected - block/warn/kick
        # 2 = Potential VPN - warn based on uncertain_block setting
        # -1 = Invalid response
        
        if vpn_status == 0:
            self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: no VPN detected - allowed')
            return
        
        if vpn_status == 1:
            self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: VPN detected, kicking!')
            self.kick_vpn_user(player_id, ip_address, confirmed=True)
            return
        
        if vpn_status == 2:
            if self.uncertain_block:
                self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: potential VPN detected')
                self.instance.rcon(f'svsay ^3[Bot] ^1Potential VPN detection for client {player_id}')
                self.kick_vpn_user(player_id, ip_address, confirmed=False)
            else:
                self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: potential VPN detected - warned only')
                self.instance.rcon(f'svsay ^3[Bot] ^1Potential VPN detection for client {player_id}')
    
    def kick_vpn_user(self, player_id, ip_address, confirmed=True):
        '''Kick a VPN user with warnings and ban'''
        if confirmed:
            # Send warning messages with countdown
            self.instance.rcon(f'svsay ^5[Bot] ^1VPN ^7use detected! ^3{player_id} ^7kicked in 15 seconds!')
            time.sleep(5)
            
            # Add to ban list
            self.instance.rcon(f'addip {ip_address}')
            self.instance.rcon(f'marktk {player_id}')
            self.instance.rcon(f'mute {player_id}')
            
            self.instance.rcon(f'svsay ^5[Bot] ^1VPN ^7use detected! ^3{player_id} ^7kicked in 10 seconds!')
            self.instance.rcon(f'marktk {player_id}')
            time.sleep(5)
            
            self.instance.rcon(f'svsay ^5[Bot] ^1VPN ^7use detected! ^3{player_id} ^7kicked in 5 seconds!')
            self.instance.rcon(f'marktk {player_id}')
            time.sleep(5)
            
            # Final kick
            self.instance.rcon(f'kick {player_id}')
            self.instance.rcon(f'svsay ^5[Bot] ^1Banned client ^3{player_id} ^1for VPN use!')
            
            self.instance.log_handler.log(f'[VPN Monitor] {ip_address}: banned & kicked')
        else:
            # Just warn for uncertain detections
            self.instance.rcon(f'svsay ^3[Bot] ^1Potential VPN ^7detected for {player_id} - allowed')
    
    def cleanup_recent_connections(self):
        '''Remove old entries from recent connections cache'''
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in self.recent_connections.items():
            if current_time - timestamp > self.connection_timeout * 2:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.recent_connections[key]