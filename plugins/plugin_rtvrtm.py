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
        
        # Pending change for next round
        self.pending_change = None  # {'type': 'map' or 'mode', 'value': map_name or mode_num}
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
        
        # Queued changes (execute at round end) vs immediate
        self.rtv_queued = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtv_queued', True)
        self.rtm_queued = instance.config.get('plugins', {}).get('rtvrtm', {}).get('rtm_queued', True)
        
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
        
        # Maps from instance config - debug what's actually being loaded
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
        self.instance.event_handler.register_event('player_connected', self.on_player_connects)
        self.instance.event_handler.register_event('player_disconnected', self.on_player_disconnects)
        self.instance.event_handler.register_event('map_change', self.on_map_change)
        self.instance.event_handler.register_event('new_log_line', self.on_new_log_line)
        
    def on_load(self):
        """Called when plugin is loaded"""
        self.instance.log_handler.log('[RTV/RTM] Plugin loaded - Version ' + VERSION)
        if self.rtv_enabled:
            self.instance.log_handler.log('[RTV/RTM] RTV is enabled - primary_maps: ' + str(len(self.maps)) + ', secondary_maps: ' + str(len(self.secondary_maps)))
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
        
        # Debug command to check map loading
        if message == '!rtvdebug':
            self.instance.say('^2[RTV] ^7Maps: ^1' + str(len(self.maps)) + '^7 Secondary: ^1' + str(len(self.secondary_maps)) + '^7 Nominations: ^1' + str(len([p[3] for p in self.players.values() if p[3]])))
            return
        
        # Unvote command (during active voting)
        if message == '!unvote':
            self.handle_unvote(player_id, player_name)
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
        
        # Check for pending change to execute
        if self.pending_change:
            if self.pending_change['type'] == 'map':
                map_name = self.pending_change['value']
                self.instance.say('^2[RTV] ^1Rock the Vote ^3executing! Changing to ^2' + map_name)
                self.instance.log_handler.log('[RTV] Executing queued map change to ' + map_name)
                # Map change already in progress - don't call instance.map() again
                # Just update recently_played
                if map_name not in self.recently_played:
                    self.recently_played.insert(0, map_name)
                    if len(self.recently_played) > self.recently_played_max:
                        self.recently_played.pop()
            elif self.pending_change['type'] == 'mode':
                mode = self.pending_change['value']
                mode_name = self.modes.get(mode, 'Unknown')
                self.instance.say('^2[RTM] ^1Rock the Mode ^3executing! Changing to ^2' + mode_name)
                self.instance.log_handler.log('[RTM] Executing queued mode change to ' + mode_name)
                self.instance.mode(mode)  # Mode change still needed
            self.pending_change = None
        
        # Add current map to recently played
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
            self.instance.say('^1RTV is currently disabled')
            return
            
        current_time = time.time()
        if current_time - self.last_vote_time < self.vote_cooldown:
            remaining = int(self.vote_cooldown - (current_time - self.last_vote_time))
            self.instance.say('^2[RTV] ^7Rock the vote is temporarily disabled. Time remaining: %i seconds' % remaining)
            return
            
        if self.voting_active:
            self.instance.say('^2[RTV] ^7Rock the vote is temporarily disabled.')
            return
            
        total_players = len(self.players)
        if total_players == 0:
            return  # Silent reject - no players to vote
            
        # Add vote
        self.rtv_votes[player_id] = {'name': player_name}
        
        # Calculate required votes
        required = max(int(total_players * self.rtv_rate / 100), self.rtv_min_votes)
        current = len(self.rtv_votes)
        
        # Broadcast who wants to rock the vote (like original rtvrtm.py)
        self.instance.say('^2[RTV] ^7%s ^7wants to rock the vote (%i/%i).' % (player_name, current, required))

        # Check if enough votes to start voting
        if current >= required:

            self.start_rtv_voting()
    
    def start_rtv_voting(self):
        """Start RTV voting process - show map choices from nominations"""
        self.voting_active = True
        self.current_voting_type = 'rtv'
        
        total_players = len(self.players)
        
        # Get map choices from nominations (like original rtvrtm.py)
        nominated_maps = [p[3] for p in self.players.values() if p[3]]
        
        # Get all available maps (primary + secondary)
        all_maps = list(self.maps) + list(self.secondary_maps if self.secondary_maps else [])
        
        # Show map count in-game so user can see what's happening
        self.instance.say('^2[RTV] ^7Maps loaded: ^1' + str(len(all_maps)) + ' ^7(primary: ^1' + str(len(self.maps)) + '^7, secondary: ^1' + str(len(self.secondary_maps or [])) + '^7)')
        
        # If no nominations, get random maps from available
        if not nominated_maps:
            available = [m for m in all_maps if m not in self.recently_played] or all_maps
            map_choices = random.sample(available, min(5, len(available)))
        else:
            # Count nominations and get top maps
            from collections import Counter
            counts = Counter(nominated_maps)
            # Get maps sorted by nomination count (highest first), then priority
            map_choices = [m for m, c in counts.most_common(5)]
        
        # Create voting options from map choices (like original rtvrtm.py)
        self.voting_options = {}
        for i, map_name in enumerate(map_choices, 1):
            self.voting_options[i] = {'count': 0, 'priority': 0, 'value': map_name, 'display': map_name}
        
        # Add "Don't change" option
        self.voting_options[len(map_choices) + 1] = {'count': 0, 'priority': 0, 'value': None, 'display': "Don't change"}
        
        # Announce voting with map choices - match original rtvrtm.py format
        votes_display = ', '.join('%i(%i): %s' % (i, 0, m) for i, m in enumerate(map_choices, 1))
        votes_display += ', %i(0): Don\'t change' % (len(map_choices) + 1)
        
        # Broadcast voting messages using rcon directly (like original rtvrtm.py)
        self.instance.say('^2[RTV] ^7Type !number to vote. Voting will complete in ^21 ^7round (0/' + str(total_players) + ').')
        self.instance.say('^2[Votes] ^7' + votes_display)
        
        self.voting_start_time = time.time()
        self.players_voted = {}
        self.last_voting_broadcast = 0
    
    def handle_rtm_vote(self, player_id, player_name, message=''):
        """Handle RTM vote"""
        if not self.rtm_enabled:
            self.instance.say('^1RTM is currently disabled')
            return
            
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_vote_time < self.vote_cooldown:
            remaining = int(self.vote_cooldown - (current_time - self.last_vote_time))
            self.instance.say('^2[RTM] ^7Rock the mode is temporarily disabled. Time remaining: %i seconds' % remaining)
            return
            
        total_players = len(self.players)
        if total_players == 0:
            return  # Silent reject - no players to vote
            
        # Parse mode from message if provided (e.g., !rtm 1 for Semi-Authentic)
        mode = 0  # Default to Open mode
        parts = message.split()
        if len(parts) > 1:
            try:
                mode = int(parts[1])
                if mode not in self.modes:
                    self.instance.say('^1Invalid mode. Valid modes: 0-Open, 1-Semi, 2-Full, 3-Duel, 4-Legends')
                    return
            except ValueError:
                self.instance.say('^1Usage: !rtm <mode 0-4> or !rtm for Open mode')
                return
        
        # Add vote
        self.rtm_votes[player_id] = {'name': player_name, 'mode': mode, 'time': current_time}
        
        # Calculate required votes
        required = max(int(total_players * self.rtm_rate / 100), self.rtm_min_votes)
        current = len(self.rtm_votes)
        
        mode_name = self.modes.get(mode, 'Unknown')
        
        # Broadcast who wants to rock the mode (like original rtvrtm.py)
        self.instance.say('^2[RTM] ^7%s ^7wants to rock the mode (%i/%i).' % (player_name, current, required))

        # Check if enough votes - start RTM voting (like RTV)
        if current >= required:
            self.start_rtm_voting()

    def start_rtm_voting(self):
        """Start RTM voting process - show mode choices"""
        self.voting_active = True
        self.current_voting_type = 'rtm'
        
        total_players = len(self.players)
        
        # Get mode choices from RTM votes (like original rtvrtm.py)
        requested_modes = [v.get('mode', 0) for v in self.rtm_votes.values()]
        
        # Get unique modes requested, excluding current mode
        current_mode = getattr(self, 'current_mode', 0)
        mode_choices = [m for m in set(requested_modes) if m != current_mode][:5]  # Max 5 modes
        
        if not mode_choices:
            # Fallback to all available modes if no specific requests
            mode_choices = [m for m in self.modes.keys() if m != current_mode][:5]
        
        # Create voting options from mode choices (like original rtvrtm.py)
        self.voting_options = {}
        for i, mode in enumerate(mode_choices, 1):
            mode_name = self.modes.get(mode, 'Unknown')
            self.voting_options[i] = {'count': 0, 'priority': 0, 'value': mode, 'display': mode_name}
        
        # Add "Don't change" option
        self.voting_options[len(mode_choices) + 1] = {'count': 0, 'priority': 0, 'value': None, 'display': "Don't change"}
        
        # Announce voting with mode choices - match original rtvrtm.py format
        votes_display = ', '.join('%i(%i): %s' % (i, 0, self.modes.get(m, str(m))) for i, m in enumerate(mode_choices, 1))
        votes_display += ', %i(0): Don\'t change' % (len(mode_choices) + 1)
        # Broadcast voting messages using rcon directly (like original rtvrtm.py)
        self.instance.say('^2[RTM] ^7Type !number to vote. Voting will complete in ^21^7 rounds (0/' + str(total_players) + ').')
        self.instance.say('^2[Votes] ^7' + votes_display)
        
        self.voting_start_time = time.time()
        self.players_voted = {}
    
    def execute_rtm(self, mode):
        """Execute RTM - change mode"""
        self.last_vote_time = time.time()
        self.rtm_votes = {}  # Clear votes after execution
        
        mode_name = self.modes.get(mode, 'Unknown')
        self.instance.say('^2[RTM] ^1Rock the Mode ^3successful! Changing to ^2' + mode_name)
        self.instance.log_handler.log('[RTM] Vote successful - Changing to mode ' + str(mode))
        
        # Change mode
        self.instance.mode(mode)
        self.rtm_votes = {}
        
    def handle_nomination(self, player_id, player_name, map_name):
        """Handle map nomination"""
        if not self.maps:
            self.instance.say('^2[Voting] ^7Map voting is unavailable.')
            return
            
        # Check if nomination is allowed (only when >5 maps total)
        total_maps = len(self.maps) + len(self.secondary_maps if self.secondary_maps else [])
        if total_maps <= 5:
            self.instance.say('^2[Nominate] ^7Map nomination is unavailable because the number of maps is less than or equal 5.')
            return
            
        if not map_name:
            # Show available maps (first 10)
            available = [m for m in self.maps if m not in self.recently_played]
            if not available and self.secondary_maps:
                available = [m for m in self.secondary_maps if m not in self.recently_played]
            if available:
                available = sorted(available, key=lambda x: x.lower())[:10]
                self.instance.say('^2[Nominate] ^7%s' % ', '.join(available))
            else:
                self.instance.say('^2[Nominate] ^7No maps available for nomination.')
            return
            
        # Check if map exists
        all_maps = list(self.maps) + list(self.secondary_maps if self.secondary_maps else [])
        compare_map = None
        for m in all_maps:
            if m.lower() == map_name.lower():
                compare_map = m
                break
                
        if not compare_map:
            self.instance.say('^2[Nominate] ^7Invalid map. Please use <!>maplist or <!>search expression.')
            return
            
        if compare_map.lower() == self.current_map.lower():
            self.instance.say('^2[Nominate] ^7%s cannot be nominated (current map).' % compare_map)
            return
            
        # Check recently played
        current_time = time.time()
        if compare_map in self.recently_played_dict and self.recently_played_dict.get(compare_map, 0) > current_time:
            remaining = int(self.recently_played_dict[compare_map] - current_time)
            self.instance.say('^2[Nominate] ^7%s cannot be nominated (recently played) (%s left).' %
                (compare_map, self.format_time(remaining)))
            return
        
        # Nomination type determines behavior
        if self.nomination_type:  # Numbered nominations with priority
            # Check if already nominated - player_data is list [timer, rtv_vote, rtm_vote, nomination, vote_option]
            if player_id in self.players and self.players[player_id][3]:
                old_nomination = self.players[player_id][3]
                if old_nomination == compare_map:
                    nominations = sum(1 for p in self.players.values() if p[3] == compare_map)
                    self.instance.say('^2[Nominate] ^7%s ^7already nominated %s (%i nomination%s).' %
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
                self.instance.say('^2[Nominate] ^7%s cannot be nominated (already nominated).' % compare_map)
                return
                
            if len(nominated_maps) >= 5:
                self.instance.say('^2[Nominate] ^7Maximum number of nominations (5) reached.')
                return
                
            if player_id in self.players and self.players[player_id][3]:
                self.instance.say('^2[Nominate] ^7%s ^7already nominated %s.' % (player_name, self.players[player_id][3]))
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
        
        self.instance.say(status)

    def handle_unrtv(self, player_id, player_name):
        """Handle unRTV - remove RTV vote"""
        if not self.rtv_enabled:
            self.instance.say('^1RTV is currently disabled')
            return
            
        if player_id not in self.rtv_votes:
            self.instance.say('^2[RTV] ^7%s ^7didn\'t want to rock the vote yet (%i/%i).' %
                (player_name, len(self.rtv_votes), max(int(len(self.players) * self.rtv_rate / 100), self.rtv_min_votes)))
            return
            
        del self.rtv_votes[player_id]
        self.instance.say('^2[RTV] ^7%s ^7no longer wants to rock the vote (%i/%i).' %
            (player_name, len(self.rtv_votes), max(int(len(self.players) * self.rtv_rate / 100), self.rtv_min_votes)))

    def handle_unrtm(self, player_id, player_name):
        """Handle unRTM - remove RTM vote"""
        if not self.rtm_enabled:
            self.instance.say('^1RTM is currently disabled')
            return
            
        if player_id not in self.rtm_votes:
            self.instance.say('^2[RTM] ^7%s ^7didn\'t want to rock the mode yet (%i/%i).' %
                (player_name, len(self.rtm_votes), max(int(len(self.players) * self.rtm_rate / 100), self.rtm_min_votes)))
            return
            
        del self.rtm_votes[player_id]
        self.instance.say('^2[RTM] ^7%s ^7no longer wants to rock the mode (%i/%i).' %
            (player_name, len(self.rtm_votes), max(int(len(self.players) * self.rtm_rate / 100), self.rtm_min_votes)))

    def handle_maplist(self, player_id, page):
        """Show map list with pagination"""
        if not self.maps:
            self.instance.say('^2[Voting] ^7Map voting is unavailable.')
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
            self.instance.say('^2[Maplist] ^7No map is currently available for nomination.')
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
            self.instance.say('^2[Maplist %i] ^7%s' % (page, ', '.join(page_maps)))
            self.instance.say('^2[Maplist] ^7Page %i of %i' % (page, total_pages))
        else:
            self.instance.say('^2[Maplist] ^7%s' % ', '.join(page_maps))

    def handle_search(self, player_id, expression):
        """Search maps by expression"""
        if not self.maps:
            self.instance.say('^2[Voting] ^7Map voting is unavailable.')
            return
            
        if not expression:
            self.instance.say('^2[Search] ^7Usage: !search expression')
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
            self.instance.say('^2[Search] ^7No matches found for expression \'%s\'.' % expression)
            return
            
        results.sort(key=lambda x: x.lower())
        result_str = ', '.join(results)
        
        # Check if result is too long (similar to MAPLIST_MAX_SIZE)
        if len(result_str) > 750:
            self.instance.say('^2[Search] ^7Result for expression \'%s\' is too long.' % expression)
        else:
            self.instance.say('^2[Search] ^7%s' % result_str)

    def handle_vote_digit(self, player_id, vote_number):
        """Handle voting with digits during active voting"""
        if not self.voting_active:
            return
        
        if vote_number not in self.voting_options:
            self.instance.say('^2[Voting] ^7Invalid vote option. Use ^1!1^7-^1!%i' % len(self.voting_options))
            return
        
        # Check if already voted
        if player_id in self.players_voted:
            old_vote = self.players_voted[player_id]
            self.voting_options[old_vote]['count'] -= 1
        
        # Record vote
        self.players_voted[player_id] = vote_number
        self.voting_options[vote_number]['count'] += 1
        
        # Announce vote
        self.instance.say('^2[Voting] ^7Player ^1%s ^7voted for ^1%s' % (player_id, self.voting_options[vote_number]['display']))
        
        # Update voting message with current counts using rcon directly (like original rtvrtm.py)
        total_players = len(self.players)
        voted_count = len(self.players_voted)
        voting_name = self.current_voting_type.upper()
        votes_display = ', '.join('%i(%i): %s' % (opt_num, opt_data['count'], opt_data['display']) 
                                  for opt_num, opt_data in sorted(self.voting_options.items()))
        # Send voting countdown message
        if voted_count < total_players:
            rounds_left = total_players - voted_count
            self.instance.say('^2[%s] ^7Type !number to vote. Voting will complete in ^2%d ^7round%s (%i/%i).' % 
                                      (voting_name, rounds_left, 's' if rounds_left != 1 else '', voted_count, total_players))
        self.instance.say('^2[Votes] ^7' + votes_display)
        
        # Check if voting should end (all players voted or time expired)
        self.check_voting_end()
    
    def handle_unvote(self, player_id, player_name):
        """Handle unvote - remove vote during active voting"""
        if not self.voting_active:
            self.instance.say('^2[Voting] ^7No voting is currently in progress.')
            return
        
        if player_id not in self.players_voted:
            self.instance.say('^2[Voting] ^7You haven\'t voted yet.')
            return
        
        old_vote = self.players_voted[player_id]
        self.voting_options[old_vote]['count'] -= 1
        del self.players_voted[player_id]
        
        self.instance.say('^2[Voting] ^7%s ^7removed their vote.' % player_name)
    
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
            # Re-broadcast voting options periodically (like original rtvrtm.py does continuously)
            # Send every 30 seconds, not multiple times per second
            if voting_time - self.last_voting_broadcast >= 30:
                self.last_voting_broadcast = voting_time
                voting_name = self.current_voting_type.upper()
                votes_display = ', '.join('%i(%i): %s' % (opt_num, opt_data['count'], opt_data['display']) 
                                          for opt_num, opt_data in sorted(self.voting_options.items()))
                self.instance.say('^2[%s] ^7Type !number to vote. Voting will complete in ^21 ^7round (%i/%i).' % 
                                          (voting_name, voted_count, total_players))
                self.instance.say('^2[Votes] ^7' + votes_display)
            return
        
        # Find winning option (like original rtvrtm.py)
        winning_option = None
        max_votes = -1
        for opt_num, opt_data in sorted(self.voting_options.items()):
            if opt_data['count'] > max_votes:
                max_votes = opt_data['count']
                winning_option = opt_num
        
        winning_value = self.voting_options[winning_option]['value']
        winning_display = self.voting_options[winning_option]['display']
        
        if self.current_voting_type == 'rtv':
            if winning_value is None:
                # "Don't change" option won - stay on current map, clear nominations
                self.instance.say('^2[RTV] ^7Voting complete - majority chose to keep current map.')
                self.rtv_votes = {}
                self._clear_nominations()
            else:
                # Map change wins - use the voted-on map
                self.instance.say('^2[RTV] ^7%s ^7wins with ^1%i ^7votes!' % (winning_display, max_votes))
                if self.rtv_queued:
                    self.queue_rtv_change(winning_value)
                else:
                    self.execute_rtv_immediate(winning_value)
                self._clear_nominations()
        elif self.current_voting_type == 'rtm':
            if winning_value is None:
                # "Don't change" option won - stay on current mode, clear RTM votes
                self.instance.say('^2[RTM] ^7Voting complete - majority chose to keep current mode.')
                self.rtm_votes = {}
            else:
                # Mode change wins - use the voted-on mode
                self.instance.say('^2[RTM] ^7%s ^7wins with ^1%i ^7votes!' % (winning_display, max_votes))
                if self.rtm_queued:
                    self.queue_rtm_change(winning_value)
                else:
                    self.execute_rtm_immediate(winning_value)
        
        # End voting
        self.voting_active = False
        self.voting_options = {}
        self.players_voted = {}
        self.nomination_order = []
    
    def queue_rtv_change(self, map_name):
        """Queue RTV change for next round - uses the voted-on map"""
        self.pending_change = {'type': 'map', 'value': map_name}
        self.rtv_votes = {}  # Clear votes
        
        self.instance.say('^2[RTV] ^7Changing map to ^2%s ^7next round.' % map_name)
        self.instance.log_handler.log('[RTV] Vote successful - Queued map change to ' + map_name + ' for next round')
    
    def queue_rtm_change(self, mode):
        """Queue RTM change for next round - uses the voted-on mode"""
        mode_name = self.modes.get(mode, 'Unknown')
        self.pending_change = {'type': 'mode', 'value': mode}
        self.rtm_votes = {}  # Clear votes
        
        self.instance.say('^2[RTM] ^7Changing mode to ^2%s ^7next round.' % mode_name)
        self.instance.log_handler.log('[RTM] Vote successful - Queued mode change to ' + mode_name + ' for next round')
    
    def execute_rtv_immediate(self, map_name):
        """Execute RTV change immediately - uses the voted-on map"""
        self.rtv_votes = {}  # Clear votes
        self.instance.map(map_name)
        self.instance.say('^2[RTV] ^7Map changed to ^2%s.' % map_name)
        self.instance.log_handler.log('[RTV] Vote successful - Changed map to ' + map_name)
    
    def execute_rtm_immediate(self, mode):
        """Execute RTM change immediately - uses the voted-on mode"""
        mode_name = self.modes.get(mode, 'Unknown')
        self.rtm_votes = {}  # Clear votes
        self.instance.mode(mode)
        self.instance.say('^2[RTM] ^7Mode changed to ^2%s.' % mode_name)
        self.instance.log_handler.log('[RTM] Vote successful - Changed mode to ' + mode_name)
    
    def before_dedicated_server_launch(self):
        """Called before dedicated server starts"""
        self.instance.log_handler.log('[RTV/RTM] Server launch preparation complete')
        
    def on_dedicated_server_shutdown(self):
        """Called when dedicated server shuts down"""
        self.instance.log_handler.log('[RTV/RTM] Server shutdown')    