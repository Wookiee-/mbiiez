#!/usr/bin/env python3
# Copyright (c) 2012-2013, klax / Cthulhu@GBITnet.com.br
# All rights reserved.

"""
MBIIEZ Plugin: RTV/RTM (Rock the Vote / Rock the Mode)

This plugin provides RTV and RTM functionality for Movie Battles II servers.
Ported from the original rtvrtm.py to Python 3 and integrated as a mbiiEZ plugin.
"""

import time
import random
from datetime import datetime

VERSION = '3.6c_py3'


class plugin:
    """RTV/RTM Plugin for mbiiEZ - Python 3 compatible"""
    
    plugin_name = 'RTV/RTM'
    plugin_author = 'Ported from klax/Cthulhu'
    plugin_url = ''
    
    def __init__(self, instance):
        self.instance = instance
        
        # RTV state from plugins config
        self.rtv_enabled = instance.config.get('plugins', {}).get('rtvrtm', {}).get('enable_rtv', False)
        self.rtm_enabled = instance.config.get('plugins', {}).get('rtvrtm', {}).get('enable_rtm', False)
        
        # Voting state
        self.rtv_votes = {}
        self.rtm_votes = {}
        self.current_map = None
        self.current_mode = None
        self.last_vote_time = 0
        self.vote_cooldown = 300  # 5 minutes
        
        # Configuration - use plugins.rtvrtm config with fallbacks
        self.rtv_rate = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtv_rate', 50)
        self.rtv_min_votes = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtv_min_votes', 10)
        self.rtm_rate = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtm_rate', 50)
        self.rtm_min_votes = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtm_min_votes', 20)
        
        # Player tracking
        self.players = {}
        self.recently_played = []
        self.recently_played_max = 5
        
        # Maps from instance config
        self.maps = instance.config.get('primary_maps', [])
        self.secondary_maps = instance.config.get('secondary_maps', [])
        
        # Mode definitions
        self.modes = {
            0: 'Open',
            1: 'Semi-Authentic', 
            2: 'Full-Authentic',
            3: 'Duel',
            4: 'Legends'
        }
    
    def register(self):
        """Register event handlers"""
        self.instance.event_handler.register_event('player_chat_command', self.on_player_chat_command)
        self.instance.event_handler.register_event('player_connects', self.on_player_connects)
        self.instance.event_handler.register_event('player_disconnects', self.on_player_disconnects)
        self.instance.event_handler.register_event('map_change', self.on_map_change)
        self.instance.event_handler.register_event('new_log_line', self.on_new_log_line)
        
    def on_load(self):
        """Called when plugin is loaded"""
        self.instance.log_handler.log('[RTV/RTM] Plugin loaded - Version ' + VERSION)
        if self.rtv_enabled:
            self.instance.log_handler.log('[RTV/RTM] RTV is enabled')
        if self.rtm_enabled:
            self.instance.log_handler.log('[RTV/RTM] RTM is enabled')
            
    def on_new_log_line(self, args):
        """Handle new log lines - for parsing RTV triggers from game log"""
        log_line = args.get('log_line', '')
        # Could parse RTV trigger messages from game log here
        # For now, chat commands handle the primary interaction
        
    def on_player_chat_command(self, args):
        """Handle player chat commands"""
        message = args.get('message', '')
        player_id = args.get('player_id', '')
        player_name = args.get('player', 'Unknown')
        
        # RTV command
        if message.startswith('!rtv') or message.startswith('!rockthevote'):
            self.handle_rtv_vote(player_id, player_name)
            return
            
        # RTM command  
        if message.startswith('!rtm') or message.startswith('!rockthemode'):
            self.handle_rtm_vote(player_id, player_name, message)
            return
            
        # Map nomination
        if message.startswith('!nominate') or message.startswith('!nom'):
            map_name = message.split(' ', 1)[-1] if ' ' in message else ''
            self.handle_nomination(player_id, player_name, map_name)
            return
            
        # Show votes
        if message == '!votes' or message == '!votestatus':
            self.show_vote_status(player_id)
            return
        
    def on_player_connects(self, args):
        """Handle player connection"""
        player_id = args.get('player_id', '')
        player_name = args.get('player', 'Unknown')
        self.players[player_id] = {'name': player_name, 'id': player_id}
        
    def on_player_disconnects(self, args):
        """Handle player disconnection"""
        player_id = args.get('player_id', '')
        if player_id in self.players:
            del self.players[player_id]
        if player_id in self.rtv_votes:
            del self.rtv_votes[player_id]
        if player_id in self.rtm_votes:
            del self.rtm_votes[player_id]
            
    def on_map_change(self, args):
        """Handle map change"""
        self.current_map = args.get('map_name', '')
        # Add to recently played
        if self.current_map in self.recently_played:
            self.recently_played.remove(self.current_map)
        self.recently_played.insert(0, self.current_map)
        if len(self.recently_played) > self.recently_played_max:
            self.recently_played.pop()
        # Clear votes on map change
        self.rtv_votes = {}
        self.rtm_votes = {}
        self.last_vote_time = 0
        
    def handle_rtv_vote(self, player_id, player_name):
        """Handle RTV vote"""
        if not self.rtv_enabled:
            self.instance.tell(player_id, '^1RTV is currently disabled')
            return
            
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_vote_time < self.vote_cooldown:
            remaining = int(self.vote_cooldown - (current_time - self.last_vote_time))
            self.instance.tell(player_id, '^3RTV vote is in cooldown. Try again in ^1' + str(remaining) + '^3 seconds')
            return
            
        total_players = len(self.players)
        if total_players == 0:
            self.instance.tell(player_id, '^1No players on server')
            return
            
        # Add vote
        self.rtv_votes[player_id] = {'name': player_name, 'time': current_time}
        
        # Calculate required votes
        required = max(int(total_players * self.rtv_rate / 100), self.rtv_min_votes)
        current = len(self.rtv_votes)
        
        self.instance.tell(player_id, '^3Your RTV vote has been counted. ^1' + str(current) + '^3/^1' + str(required) + '^3 votes needed')
        
        # Announce to all players
        self.instance.say('^3[RTV] ^1' + str(current) + '^3 RTV votes, ^1' + str(required) + '^3 needed to rock the vote')
        
        # Check if enough votes
        if current >= required:
            self.execute_rtv()
            
    def execute_rtv(self):
        """Execute RTV - change to random map"""
        self.last_vote_time = time.time()
        
        # Filter out recently played maps
        available_maps = [m for m in self.maps if m not in self.recently_played]
        if not available_maps:
            available_maps = self.maps
            
        # Pick random map
        new_map = random.choice(available_maps)
        
        self.instance.say('^3[RTV] ^1Rock the Vote ^3successful! Changing to ^2' + new_map)
        self.instance.log_handler.log('[RTV] Vote successful - Changing to ' + new_map)
        
        # Change map
        self.instance.map(new_map)
        
        # Clear votes
        self.rtv_votes = {}
        
    def handle_rtm_vote(self, player_id, player_name, message=''):
        """Handle RTM vote"""
        if not self.rtm_enabled:
            self.instance.tell(player_id, '^1RTM is currently disabled')
            return
            
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_vote_time < self.vote_cooldown:
            remaining = int(self.vote_cooldown - (current_time - self.last_vote_time))
            self.instance.tell(player_id, '^3RTM vote is in cooldown. Try again in ^1' + str(remaining) + '^3 seconds')
            return
            
        total_players = len(self.players)
        if total_players == 0:
            self.instance.tell(player_id, '^1No players on server')
            return
            
        # Parse mode from message if provided (e.g., !rtm 1 for Semi-Authentic)
        mode = 0  # Default to Open mode
        parts = message.split()
        if len(parts) > 1:
            try:
                mode = int(parts[1])
                if mode not in self.modes:
                    self.instance.tell(player_id, '^1Invalid mode. Valid modes: 0-Open, 1-Semi, 2-Full, 3-Duel, 4-Legends')
                    return
            except ValueError:
                self.instance.tell(player_id, '^1Usage: !rtm <mode 0-4> or !rtm for Open mode')
                return
        
        # Add vote
        self.rtm_votes[player_id] = {'name': player_name, 'mode': mode, 'time': current_time}
        
        # Calculate required votes
        required = max(int(total_players * self.rtm_rate / 100), self.rtm_min_votes)
        current = len(self.rtm_votes)
        
        mode_name = self.modes.get(mode, 'Unknown')
        self.instance.tell(player_id, '^3Your RTM vote for ^1' + mode_name + '^3 has been counted. ^1' + str(current) + '^3/^1' + str(required) + '^3 votes needed')
        
        # Announce to all players
        self.instance.say('^3[RTM] ^1' + str(current) + '^3 RTM votes for ^1' + mode_name + '^3, ^1' + str(required) + '^3 needed')
        
        # Check if enough votes
        if current >= required:
            self.execute_rtm(mode)
            
    def execute_rtm(self, mode):
        """Execute RTM - change mode"""
        self.last_vote_time = time.time()
        
        mode_name = self.modes.get(mode, 'Unknown')
        self.instance.say('^3[RTM] ^1Rock the Mode ^3successful! Changing to ^2' + mode_name)
        self.instance.log_handler.log('[RTM] Vote successful - Changing to mode ' + str(mode))
        
        # Change mode
        self.instance.mode(mode)
        
        # Clear votes
        self.rtm_votes = {}
        
    def handle_nomination(self, player_id, player_name, map_name):
        """Handle map nomination"""
        if not map_name:
            # Show available maps
            available = [m for m in self.maps if m not in self.recently_played]
            self.instance.tell(player_id, '^3Available maps: ^1' + ', '.join(available[:10]))
            return
            
        # Check if map exists
        if map_name in self.maps:
            self.instance.tell(player_id, '^3Map ^1' + map_name + '^3 has been nominated')
            self.instance.say('^3[NOMINATION] ^1' + player_name + '^3 nominated ^2' + map_name)
        else:
            self.instance.tell(player_id, '^1Map ^1' + map_name + '^1 not found in map list')
            
    def show_vote_status(self, player_id):
        """Show current vote status"""
        rtv_count = len(self.rtv_votes)
        rtm_count = len(self.rtm_votes)
        
        total_players = max(len(self.players), 1)
        rtv_required = max(int(total_players * self.rtv_rate / 100), self.rtv_min_votes)
        rtm_required = max(int(total_players * self.rtm_rate / 100), self.rtm_min_votes)
        
        status = '^3Current Votes:\n'
        status += '^1RTV: ^3' + str(rtv_count) + '/' + str(rtv_required) + ' needed\n'
        status += '^1RTM: ^3' + str(rtm_count) + '/' + str(rtm_required) + ' needed'
        
        self.instance.tell(player_id, status)
        
    def before_dedicated_server_launch(self):
        """Called before dedicated server starts"""
        self.instance.log_handler.log('[RTV/RTM] Server launch preparation complete')
        
    def on_dedicated_server_shutdown(self):
        """Called when dedicated server shuts down"""
        self.instance.log_handler.log('[RTV/RTM] Server shutdown')    