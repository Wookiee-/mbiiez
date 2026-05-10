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
MAPLIST_MAX_SIZE = 750
SLEEP_INTERVAL = 0.075


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
        self.rtv_votes = {}  # Player RTV votes (before voting starts)
        self.rtm_votes = {}  # Player RTM votes (before voting starts)
        self.voting_active = False
        self.current_voting_type = None  # 'rtv' or 'rtm' or None
        self.voting_options = {}  # {option_number: {count, priority, value, display}}
        self.voting_start_time = 0
        self.voting_duration = 60  # 60 seconds
        self.players_voted = {}  # Track who voted in current voting
        self.current_map = None
        self.current_mode = None
        self.last_vote_time = 0
        self.vote_cooldown = 300  # 5 minutes
        
        # Configuration - use plugins.rtvrtm config with fallbacks
        self.rtv_rate = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtv_rate', 50)
        self.rtv_min_votes = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtv_min_votes', 10)
        self.rtm_rate = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtm_rate', 50)
        self.rtm_min_votes = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtm_min_votes', 20)
        
        # Map priority for nominations
        self.map_priority = instance.config.get('plugins', {}).get('rtvrtm', {}).get('map_priority', [0, 0, 0])
        self.nomination_type = instance.config.get('plugins', {}).get('rtvrtm', {}).get('nomination_type', 1)
        self.pick_secondary_maps = instance.config.get('plugins', {}).get('rtvrtm', {}).get('pick_secondary_maps', 1)
        self.enable_recently_played = instance.config.get('plugins', {}).get('rtvrtm', {}).get('enable_recently_played', 0)
        
        # RTM mode priority
        self.mode_priority = instance.config.get('plugins', {}).get('rtvrtm', {}).get('mode_priority', [0, 0, 0, 0, 0, 0])
        self.rtm_modes = [0, 1, 2, 3, 4]  # Default all modes
        
        # Player tracking - store as list [timer, rtv_vote, rtm_vote, nomination, vote_option]
        self.players = {}  # {player_id: [timer, rtv_vote, rtm_vote, nomination, vote_option]}
        self.recently_played = []  # List of recently played maps
        self.recently_played_dict = {}  # {map_name: timestamp} for recently played with expiry
        self.recently_played_max = 5
        self.nomination_order = []  # List of player_ids in nomination order
        
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
            
        # Un-RTV command
        if message.startswith('!unrtv'):
            self.handle_unrtv(player_id, player_name)
            return
            
        # Un-RTM command
        if message.startswith('!unrtm'):
            self.handle_unrtm(player_id, player_name)
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
            
        # Maplist command
        if message.startswith('!maplist'):
            parts = message.split(' ', 1)[1:] if len(message.split(' ', 1)) > 1 else []
            page = int(parts[0]) if parts and parts[0].isdigit() else 1
            self.handle_maplist(player_id, page)
            return
            
        # Search command
        if message.startswith('!search'):
            parts = message.split(' ', 1)
            expression = parts[1] if len(parts) > 1 else ''
            self.handle_search(player_id, expression)
            return
        
        # Unvote command (during active voting)
        if message == '!unvote':
            self.handle_unvote(player_id)
            return
        
        # Vote with digit (during active voting)
        if self.voting_active and message.startswith('!') and len(message) == 2 and message[1].isdigit():
            vote_num = int(message[1])
            self.handle_vote_digit(player_id, vote_num)
            return
        
    def on_player_connects(self, args):
        """Handle player connection"""
        player_id = args.get('player_id', '')
        player_name = args.get('player', 'Unknown')
        # Store as list: [timer, rtv_vote, rtm_vote, nomination, vote_option]
        self.players[player_id] = [0, False, False, None, None]
        
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
        # Add to recently played (list for simple nom_type compatibility)
        if self.current_map in self.recently_played:
            self.recently_played.remove(self.current_map)
        self.recently_played.insert(0, self.current_map)
        if len(self.recently_played) > self.recently_played_max:
            self.recently_played.pop()
        # Also track with timestamp for expiry-based checking
        if self.enable_recently_played:
            self.recently_played_dict[self.current_map] = time.time() + self.enable_recently_played
        # Clear votes on map change
        self.rtv_votes = {}
        self.rtm_votes = {}
        self.last_vote_time = 0
        self.voting_active = False
        
    def handle_rtv_vote(self, player_id, player_name):
        """Handle RTV vote"""
        if not self.rtv_enabled:
            self.instance.tell(player_id, '^1RTV is currently disabled')
            return
            
        current_time = time.time()
        if current_time - self.last_vote_time < self.vote_cooldown:
            remaining = int(self.vote_cooldown - (current_time - self.last_vote_time))
            self.instance.tell(player_id, '^3RTV vote is in cooldown. Try again in ^1%i^3 seconds' % remaining)
            return
            
        if self.voting_active:
            self.instance.tell(player_id, '^2[Voting] ^7A voting is already in progress.')
            return
            
        total_players = len(self.players)
        if total_players == 0:
            self.instance.tell(player_id, '^1No players on server')
            return
            
        # Add vote
        self.rtv_votes[player_id] = {'name': player_name}
        
        # Calculate required votes
        required = max(int(total_players * self.rtv_rate / 100), self.rtv_min_votes)
        current = len(self.rtv_votes)
        
        self.instance.tell(player_id, '^3Your RTV vote has been counted. ^1%i^3/^1%i^3 votes needed' % (current, required))
        self.instance.say('^3[RTV] ^1%i^3 RTV votes, ^1%i^3 needed to rock the vote' % (current, required))
        
        # Check if enough votes to start voting
        if current >= required:
            self.start_rtv_voting()
    
    def start_rtv_voting(self):
        """Start RTV voting process - pick nominated maps and start voting"""
        self.voting_active = True
        self.current_voting_type = 'rtv'
        
        # Get nominated maps - players stored as list [timer, rtv_vote, rtm_vote, nomination, vote_option]
        nominated_maps = []
        for player_data in self.players.values():
            if player_data[3]:  # index 3 is nomination
                nominated_maps.append(player_data[3])
        
        if not nominated_maps:
            # No nominations - pick random from available
            available_maps = [m for m in self.maps if m not in self.recently_played]
            if not available_maps:
                available_maps = self.maps
            self.voting_options = {
                1: {'count': 0, 'priority': 0, 'value': random.choice(available_maps), 'display': random.choice(available_maps)},
                2: {'count': 0, 'priority': 0, 'value': 'dontchange', 'display': "Don't change"}
            }
        else:
            # Use nominated maps - count nominations per map
            map_counts = {}
            for m in nominated_maps:
                map_counts[m] = map_counts.get(m, 0) + 1
            
            # Sort by count (priority) and pick top maps
            sorted_maps = sorted(map_counts.items(), key=lambda x: x[1], reverse=True)
            
            self.voting_options = {}
            for i, (map_name, count) in enumerate(sorted_maps[:4], 1):
                self.voting_options[i] = {'count': 0, 'priority': count, 'value': map_name, 'display': map_name}
            
            # Add "Don't change" option
            self.voting_options[len(self.voting_options) + 1] = {'count': 0, 'priority': 0, 'value': 'dontchange', 'display': "Don't change"}
        
        # Announce voting
        options_str = ', '.join(['^1%i^3: ^7%s' % (k, v['display']) for k, v in self.voting_options.items()])
        self.instance.say('^3[RTV] ^7Voting started! Cast your vote: ^1!1^7-^1!%i' % (len(self.voting_options)))
        self.instance.say('^2[Options] ^7%s' % options_str)
        
        self.voting_start_time = time.time()
        self.players_voted = {}
    
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
        
        # Check if enough votes - execute immediately like original
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
        if not self.maps:
            self.instance.tell(player_id, '^2[Voting] ^7Map voting is unavailable.')
            return
            
        # Check if nomination is allowed (only when >5 maps total)
        total_maps = len(self.maps) + len(self.secondary_maps if self.secondary_maps else [])
        if total_maps <= 5:
            self.instance.tell(player_id, '^2[Nominate] ^7Map nomination is unavailable because the number of maps is less than or equal 5.')
            return
            
        if not map_name:
            # Show available maps (first 10)
            available = [m for m in self.maps if m not in self.recently_played]
            if not available and self.secondary_maps:
                available = [m for m in self.secondary_maps if m not in self.recently_played]
            if available:
                available = sorted(available, key=lambda x: x.lower())[:10]
                self.instance.tell(player_id, '^2[Nominate] ^7%s' % ', '.join(available))
            else:
                self.instance.tell(player_id, '^2[Nominate] ^7No maps available for nomination.')
            return
            
        # Check if map exists
        all_maps = list(self.maps) + list(self.secondary_maps if self.secondary_maps else [])
        compare_map = None
        for m in all_maps:
            if m.lower() == map_name.lower():
                compare_map = m
                break
                
        if not compare_map:
            self.instance.tell(player_id, '^2[Nominate] ^7Invalid map. Please use <!>maplist or <!>search expression.')
            return
            
        if compare_map.lower() == self.current_map.lower():
            self.instance.tell(player_id, '^2[Nominate] ^7%s cannot be nominated (current map).' % compare_map)
            return
            
        # Check recently played
        current_time = time.time()
        if compare_map in self.recently_played_dict and self.recently_played_dict.get(compare_map, 0) > current_time:
            remaining = int(self.recently_played_dict[compare_map] - current_time)
            self.instance.tell(player_id, '^2[Nominate] ^7%s cannot be nominated (recently played) (%s left).' %
                (compare_map, self.format_time(remaining)))
            return
        
        # Nomination type determines behavior
        if self.nomination_type:  # Numbered nominations with priority
            # Check if already nominated - player_data is list [timer, rtv_vote, rtm_vote, nomination, vote_option]
            if player_id in self.players and self.players[player_id][3]:
                old_nomination = self.players[player_id][3]
                if old_nomination == compare_map:
                    nominations = sum(1 for p in self.players.values() if p[3] == compare_map)
                    self.instance.tell(player_id, '^2[Nominate] ^7%s ^7already nominated %s (%i nomination%s).' %
                        (player_name, compare_map, nominations, '' if nominations == 1 else 's'))
                    return
                else:
                    # Change nomination
                    self.players[player_id][3] = compare_map
                    if player_id not in self.nomination_order:
                        self.nomination_order.append(player_id)
                    nominations = sum(1 for p in self.players.values() if p[3] == compare_map)
                    self.instance.say('^2[Nominate] ^7%s ^7nomination changed to %s (%i nomination%s).' %
                        (player_name, compare_map, nominations, '' if nominations == 1 else 's'))
            else:
                # Add new nomination
                self.players[player_id][3] = compare_map
                self.nomination_order.append(player_id)
                nominations = sum(1 for p in self.players.values() if p[3] == compare_map)
                self.instance.say('^2[Nominate] ^7%s ^7nominated %s (%i nomination%s)!' %
                    (player_name, compare_map, nominations, '' if nominations == 1 else 's'))
        else:  # Simple nominations - max 5 total
            nominated_maps = [p[3] for p in self.players.values() if p[3]]
            if compare_map in nominated_maps:
                self.instance.tell(player_id, '^2[Nominate] ^7%s cannot be nominated (already nominated).' % compare_map)
                return
                
            if len(nominated_maps) >= 5:
                self.instance.tell(player_id, '^2[Nominate] ^7Maximum number of nominations (5) reached.')
                return
                
            if player_id in self.players and self.players[player_id][3]:
                self.instance.tell(player_id, '^2[Nominate] ^7%s ^7already nominated %s.' % (player_name, self.players[player_id][3]))
                return
                
            self.players[player_id][3] = compare_map
            self.nomination_order.append(player_id)
            self.instance.say('^2[Nominate] ^7%s ^7nominated %s!' % (player_name, compare_map))

    def format_time(self, seconds):
        """Format seconds into human readable time"""
        if seconds < 60:
            return '%i seconds' % seconds
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return '%i minutes' % minutes
        hours, minutes = divmod(minutes, 60)
        return '%i hours' % hours
            
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

    def handle_unrtv(self, player_id, player_name):
        """Handle unRTV - remove RTV vote"""
        if not self.rtv_enabled:
            self.instance.tell(player_id, '^1RTV is currently disabled')
            return
            
        if player_id not in self.rtv_votes:
            self.instance.tell(player_id, '^2[RTV] ^7%s ^7didn\'t want to rock the vote yet (%i/%i).' %
                (player_name, len(self.rtv_votes), max(int(len(self.players) * self.rtv_rate / 100), self.rtv_min_votes)))
            return
            
        del self.rtv_votes[player_id]
        self.instance.say('^2[RTV] ^7%s ^7no longer wants to rock the vote (%i/%i).' %
            (player_name, len(self.rtv_votes), max(int(len(self.players) * self.rtv_rate / 100), self.rtv_min_votes)))

    def handle_unrtm(self, player_id, player_name):
        """Handle unRTM - remove RTM vote"""
        if not self.rtm_enabled:
            self.instance.tell(player_id, '^1RTM is currently disabled')
            return
            
        if player_id not in self.rtm_votes:
            self.instance.tell(player_id, '^2[RTM] ^7%s ^7didn\'t want to rock the mode yet (%i/%i).' %
                (player_name, len(self.rtm_votes), max(int(len(self.players) * self.rtm_rate / 100), self.rtm_min_votes)))
            return
            
        del self.rtm_votes[player_id]
        self.instance.say('^2[RTM] ^7%s ^7no longer wants to rock the mode (%i/%i).' %
            (player_name, len(self.rtm_votes), max(int(len(self.players) * self.rtm_rate / 100), self.rtm_min_votes)))

    def handle_maplist(self, player_id, page):
        """Show map list with pagination"""
        if not self.maps:
            self.instance.tell(player_id, '^2[Voting] ^7Map voting is unavailable.')
            return
            
        # Combine maps and secondary maps
        all_maps = list(self.maps) + list(self.secondary_maps if self.secondary_maps else [])
        current_map = self.current_map
        
        # Filter out current map and recently played
        current_time = time.time()
        available_maps = [
            m for m in all_maps 
            if m.lower() != current_map.lower() and 
            (m not in self.recently_played or 
             self.recently_played_dict.get(m, 0) <= current_time)
        ]
        
        if not available_maps:
            self.instance.tell(player_id, '^2[Maplist] ^7No map is currently available for nomination.')
            return
            
        # Sort maps
        available_maps.sort(key=lambda x: x.lower())
        
        # Pagination - 10 maps per page
        maps_per_page = 10
        total_pages = (len(available_maps) + maps_per_page - 1) // maps_per_page
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * maps_per_page
        end_idx = start_idx + maps_per_page
        page_maps = available_maps[start_idx:end_idx]
        
        if total_pages > 1:
            self.instance.tell(player_id, '^2[Maplist %i] ^7%s' % (page, ', '.join(page_maps)))
            self.instance.tell(player_id, '^2[Maplist] ^7Page %i of %i' % (page, total_pages))
        else:
            self.instance.tell(player_id, '^2[Maplist] ^7%s' % ', '.join(page_maps))

    def handle_search(self, player_id, expression):
        """Search maps by expression"""
        if not self.maps:
            self.instance.tell(player_id, '^2[Voting] ^7Map voting is unavailable.')
            return
            
        if not expression:
            self.instance.tell(player_id, '^2[Search] ^7Usage: !search expression')
            return
            
        # Combine maps and search
        all_maps = list(self.maps) + list(self.secondary_maps if self.secondary_maps else [])
        current_map = self.current_map
        
        # Filter out current map
        available_maps = [m for m in all_maps if m.lower() != current_map.lower()]
        
        # Search by expression
        search_expr = expression.lower()
        results = [m for m in available_maps if search_expr in m.lower()]
        
        if not results:
            self.instance.tell(player_id, '^2[Search] ^7No matches found for expression \'%s\'.' % expression)
            return
            
        results.sort(key=lambda x: x.lower())
        result_str = ', '.join(results)
        
        # Check if result is too long (similar to MAPLIST_MAX_SIZE)
        if len(result_str) > 750:
            self.instance.tell(player_id, '^2[Search] ^7Result for expression \'%s\' is too long.' % expression)
        else:
            self.instance.tell(player_id, '^2[Search] ^7%s' % result_str)

    def handle_vote_digit(self, player_id, vote_number):
        """Handle voting with digits during active voting"""
        if not self.voting_active:
            return
        
        if vote_number not in self.voting_options:
            self.instance.tell(player_id, '^2[Voting] ^7Invalid vote option. Use ^1!1^7-^1!%i' % len(self.voting_options))
            return
        
        # Check if already voted
        if player_id in self.players_voted:
            old_vote = self.players_voted[player_id]
            self.voting_options[old_vote]['count'] -= 1
        
        # Record vote
        self.players_voted[player_id] = vote_number
        self.voting_options[vote_number]['count'] += 1
        
        # Announce vote
        self.instance.say('^3[Voting] ^7Player ^1%s ^7voted for ^1%s' % (player_id, self.voting_options[vote_number]['display']))
        
        # Check if voting should end (all players voted or time expired)
        self.check_voting_end()
    
    def handle_unvote(self, player_id):
        """Handle unvote - remove vote during active voting"""
        if not self.voting_active:
            self.instance.tell(player_id, '^2[Voting] ^7No voting is currently in progress.')
            return
        
        if player_id not in self.players_voted:
            self.instance.tell(player_id, '^2[Voting] ^7You haven\'t voted yet.')
            return
        
        old_vote = self.players_voted[player_id]
        self.voting_options[old_vote]['count'] -= 1
        del self.players_voted[player_id]
        
        self.instance.say('^2[Voting] ^7%s ^7removed their vote.' % (
            self.players.get(player_id, {}).get('name', 'Player')))
    
    def check_voting_end(self):
        """Check if voting should end and execute result"""
        if not self.voting_active:
            return
            
        total_players = len(self.players)
        voted_count = len(self.players_voted)
        
        # Check if all players have voted or time expired
        voting_time = time.time() - self.voting_start_time
        time_expired = voting_time >= self.voting_duration
        all_voted = voted_count >= total_players and total_players > 0
        
        if not (time_expired or all_voted):
            return
        
        # Find winning option
        winning_option = None
        max_votes = -1
        for opt_num, opt_data in sorted(self.voting_options.items()):
            if opt_data['count'] > max_votes:
                max_votes = opt_data['count']
                winning_option = opt_num
        
        winning_value = self.voting_options[winning_option]['value']
        
        # Execute result
        if self.current_voting_type == 'rtv':
            if winning_value == 'dontchange':
                self.instance.say('^3[RTV] ^7Voting failed - majority chose to stay.')
            else:
                self.execute_rtv_with_map(winning_value)
        elif self.current_voting_type == 'rtm':
            if winning_value == 'dontchange':
                self.instance.say('^3[RTM] ^7Voting failed - majority chose to stay.')
            else:
                self.execute_rtm(int(winning_value))
        
        # End voting
        self.voting_active = False
        self.voting_options = {}
        self.players_voted = {}
    
    def execute_rtv_with_map(self, map_name):
        """Execute RTV with specific map"""
        self.last_vote_time = time.time()
        
        self.instance.say('^3[RTV] ^1Rock the Vote ^3successful! Changing to ^2' + map_name)
        self.instance.log_handler.log('[RTV] Vote successful - Changing to ' + map_name)
        
        # Change map
        self.instance.map(map_name)
        
        # Add to recently played
        if map_name not in self.recently_played:
            self.recently_played.insert(0, map_name)
            if len(self.recently_played) > self.recently_played_max:
                self.recently_played.pop()

    def before_dedicated_server_launch(self):
        """Called before dedicated server starts"""
        self.instance.log_handler.log('[RTV/RTM] Server launch preparation complete')
        
    def on_dedicated_server_shutdown(self):
        """Called when dedicated server shuts down"""
        self.instance.log_handler.log('[RTV/RTM] Server shutdown')    