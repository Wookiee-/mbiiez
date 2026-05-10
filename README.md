# Movie Battles II EZ (MBIIEZ)

MBIIEZ is a Python wrapper for running and managing instances of Movie Battles II game servers. It provides both a CLI (Command Line Interface) and a Web GUI for managing game server instances.

## Features

- **Simple Web GUI** - Manage servers through an intuitive web interface
- **CLI Management** - Full command-line control for automation and scripting
- **Multi-Instance Support** - Run multiple game server instances simultaneously on different ports
- **Plugin System** - Extend functionality with custom Python plugins
- **RTV/RTM Support** - Built-in rock-the-vote and requested-to-vote management
- **VPN Protection** - Detect and block VPN/proxy users (optional)
- **Auto Messages** - Rotating server messages to players
- **Discord Integration** - Control your server from Discord
- **Scheduled Restarts** - Automatic server restarts configurable per instance
- **Cross-Platform** - Runs on both Linux and Windows

---

## Quick Start (5 Minutes)

Get your MBII server running in under 5 minutes!

### 1. Install (Pick Your Platform)

**Linux:**
```bash
wget https://raw.githubusercontent.com/Wookiee-/mbiiez/refs/heads/main/runasroot.sh
chmod +x runasroot.sh && ./runasroot.sh
git clone https://github.com/Wookiee-/mbiiez.git && cd mbiiez && chmod +x install.sh && ./install.sh
```

**Windows:**
```cmd
# Run install.bat and select option 8 for Full Install
install.bat
```

### 2. Create Your Server Config

Copy the example config and edit it:

**Linux:**
```bash
cp configs/default.json.example configs/myfirstserver.json
nano configs/myfirstserver.json  # Edit host_name, port, rcon_password, and server_config_file
```

**Windows:**
```cmd
copy configs\default.json.example configs\myfirstserver.json
# Edit the file in your preferred text editor
```

### 3. Start Your Server

```bash
# Linux
mbii -i myfirstserver start

# Windows
mbii -i myfirstserver start
```

### 4. Verify It's Running

```bash
mbii -i myfirstserver status
```

You should see your server listed. Players can connect at `your-ip:port` (e.g., `192.168.1.100:29070`).

**That's it!** Your server is live. Continue to [Configuration](#configuration) to customize plugins, auto-restarts, and more.

---

## Included Plugins

| Plugin | Description |
|--------|-------------|
| `auto_message` | Rotating server messages on a timer |
| `rtvrtm` | Rock-the-vote and requested-to-vote functionality |
| `stats` | Player statistics tracking |
| `auto_map_rotation` | Automatic map rotation management |
| `vpn_monitor` | VPN/proxy detection and blocking via iphub.info API |

---

## Installation

### Linux (Debian/Ubuntu)

#### Quick Install (as root):

```bash
wget https://raw.githubusercontent.com/Wookiee-/mbiiez/refs/heads/main/runasroot.sh
chmod +x runasroot.sh
./runasroot.sh
```

Then as your mbiiez user:

```bash
git clone https://github.com/Wookiee-/mbiiez.git
cd mbiiez
chmod +x install.sh
./install.sh
```

#### Manual Installation:

1. Install system dependencies:
```bash
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y libc6:i386 lib32z1 libstdc++6:i386 libcurl4:i386 libjemalloc2:i386 sqlite3 net-tools fping python3 python3-pip unzip
```

2. Install Python packages:
```bash
pip3 install --user watchgod tailer six psutil prettytable urllib3 flask flask_httpauth flask-socketio discord.py
```

3. Download the game engine:
```bash
wget https://github.com/Wookiee-/OpenJK/releases/download/R20/mbiided.i386
chmod +x mbiided.i386
sudo cp mbiided.i386 /usr/bin/mbiided.i386
```

4. Create symlinks:
```bash
ln -s /path/to/openjk ~/.local/share/openjk
sudo ln -s /path/to/mbiiez/mbii.py /usr/bin/mbii
sudo chmod +x /usr/bin/mbii
```

### Windows

1. Ensure you have Python 3.8+ installed from [python.org](https://python.org)

2. Download and extract this repository to your desired location

3. Run the installer:
```cmd
cd path\to\repository
install.bat
```

4. Select option **8** for a Full Install, or run individual steps:
   - **1** - Install Python Dependencies
   - **2** - Check System Dependencies  
   - **3** - Setup Directory Structure
   - **5** - Create MBII Launcher (mbii.bat)

---

## Configuration

### Create an Instance

Create a JSON config file in the `configs/` directory. Use `configs/default.json.example` as a template.

**Minimal Configuration Example:**

```json
{
  "server": {
    "host_name": "My MBII Server",
    "port": 29070,
    "engine": "mbiided.i386",
    "game": "MBII",
    "restart_instance_every_hours": 24
  },
  "plugins": {
    "auto_message": {
      "messages": ["Welcome to the server!", "Check our Discord!"],
      "repeat_minutes": 5
    },
    "stats": {},
    "rtvrtm": {
      "enable_rtv": true,
      "enable_rtm": false
    }
  },
  "security": {
    "rcon_password": "your_secure_password"
  }
}
```

**With VPN Protection** (see [VPN Monitor Plugin](#vpn-monitor-plugin) for setup):

```json
{
  "server": {
    "host_name": "My MBII Server",
    "port": 29070,
    "engine": "mbiided.i386",
    "game": "MBII",
    "restart_instance_every_hours": 24
  },
  "plugins": {
    "auto_message": {
      "messages": ["Welcome to the server!"],
      "repeat_minutes": 5
    },
    "stats": {},
    "rtvrtm": {
      "enable_rtv": true,
      "enable_rtm": false
    },
    "vpn_monitor": {
      "enabled": true,
      "iphub_api_key": "YOUR_IPHUB_API_KEY",
      "uncertain_block": false
    }
  },
  "security": {
    "rcon_password": "your_secure_password"
  }
}
```

### Configuration Reference

#### Server Section

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `host_name` | string | Your server's display name | (required) |
| `port` | integer | Server port (unique per instance) | (required) |
| `engine` | string | Path to game engine | `mbiided.i386` |
| `game` | string | Game mod folder | `MBII` |
| `restart_instance_every_hours` | integer | Auto-restart interval (0=disabled) | `24` |
| `enable_rtv` | boolean | Enable rock-the-vote (in plugins.rtvrtm) | `true` |
| `enable_rtm` | boolean | Enable requested-to-vote (in plugins.rtvrtm) | `false` |

#### Security Section

| Setting | Description |
|---------|-------------|
| `rcon_password` | RCON access password (required) |
| `server_password` | Server password (leave blank for open) |

#### Game Section

| Setting | Description | Valid Values |
|---------|-------------|--------------|
| `mode` | Game mode | `open`, `semi-authentic`, `full-authentic`, `duel`, `legends` |
| `map` | Starting map | Any valid map name |

### Plugin Configuration

#### RTV/RTM Plugin
```json
"plugins": {
  "rtvrtm": {
    "enable_rtv": true,
    "enable_rtm": false,
    "rtv_rate": 50,
    "rtv_min_votes": 10,
    "rtm_rate": 50,
    "rtm_min_votes": 20,
    "rtv_queued": true,
    "rtm_queued": true
  }
}
```

| RTV/RTM Setting | Description | Default |
|-----------------|-------------|---------|
| `enable_rtv` | Enable rock-the-vote functionality | `true` |
| `enable_rtm` | Enable requested-to-vote functionality | `false` |
| `rtv_rate` | Percentage of players needed to trigger RTV | `50` |
| `rtv_min_votes` | Minimum votes required for RTV | `10` |
| `rtm_rate` | Percentage of players needed to trigger RTM | `50` |
| `rtm_min_votes` | Minimum votes required for RTM | `20` |
| `rtv_queued` | RTV changes at round end (true) or immediately (false) | `true` |
| `rtm_queued` | RTM changes at round end (true) or immediately (false) | `true` |

**How RTV/RTM Works:**
- **Initiate:** Players use `!rtv` or `!rtm` to initiate. RTV requires `rtv_rate`% of players (minimum `rtv_min_votes`).
- **Nominations (RTV):** Before or after initiating, players can nominate maps with `!nominate <map>` or `!nom <map>`. Use `!maplist` or `!search <expression>` to see available maps.
- **Mode Requests (RTM):** When using `!rtm <mode>`, the mode is recorded. Modes: 0=Open, 1=Semi, 2=Full, 3=Duel, 4=Legends
- **Voting Phase:** When threshold is reached, voting starts with map/mode choices:
  - RTV shows map choices from nominations (falls back to random maps if none nominated)
  - RTM shows mode choices from RTM votes
  - Players vote with `!1`, `!2`, etc. to pick their preferred option
  - "Don't change" option is always available
- **Results:** Option with most votes wins after 1 round. Use `!unvote` to change your vote during voting.
- **Execution:** If `rtv_queued`/`rtm_queued` is `true`: change happens at round end; if `false`: immediate change
- **Cooldown:** After a vote completes (success or failure), a cooldown period applies before new votes can be initiated

#### Auto Message Plugin
```json
"plugins": {
  "auto_message": {
    "messages": [
      "Welcome to the server!",
      "Join our Discord!"
    ],
    "repeat_minutes": 5
  }
}
```

#### VPN Monitor Plugin

**Requires:** Free API key from [iphub.info/api](https://iphub.info/api)

```json
"plugins": {
  "vpn_monitor": {
    "enabled": true,
    "iphub_api_key": "YOUR_API_KEY_HERE",
    "uncertain_block": false
  }
}
```

| VPN Setting | Description |
|-------------|-------------|
| `enabled` | Enable/disable the plugin |
| `iphub_api_key` | Your API key from iphub.info |
| `uncertain_block` | Also block uncertain detections (block=2) |

---

## Usage

### CLI Commands

Start, stop, and manage your server instances:

```bash
# Start an instance
mbii -i myinstance start

# Stop an instance
mbii -i myinstance stop

# Restart an instance
mbii -i myinstance restart

# Check server status
mbii -i myinstance status

# Send a message to players
mbii -i myinstance say Hello everyone!

# Send RCON commands
mbii -i myinstance rcon g_gametype 0

# Get/Set CVAR values
mbii -i myinstance cvar g_gametype
mbii -i myinstance cvar g_gametype 2
```

### Web Interface

Start the web server:
```bash
mbii web
```

Then access `http://your-server-ip:5000` in your browser.

---

## Plugin Development

Create your own plugins in the `plugins/` directory:

```python
from mbiiez.bcolors import bcolors

class my_plugin:
    def __init__(self, instance):
        self.instance = instance
        
    def on_load(self):
        self.register_events()
        self.instance.log_handler.log(bcolors.OK + f'{__name__} loaded!' + bcolors.ENDC)
        
    def register_events(self):
        self.instance.event_handler.register_event('player_connects', self.on_player_connect)
        
    def on_player_connect(self, data):
        player = data['player']
        self.instance.rcon(f'svsay Welcome {player} to the server!')
```

### Available Events

| Event | Arguments | Description |
|-------|-----------|-------------|
| `before_dedicated_server_launch` | None | Before server starts |
| `after_dedicated_server_launch` | None | After server starts |
| `new_log_line` | `log_line` | Every new log entry |
| `player_chat_command` | `message, player, player_id` | Chat starting with `!` |
| `player_chat` | `type, message, player, player_id` | All chat (TEAM/PUBLIC) |
| `player_connects` | `player, player_id` | Player connects |
| `player_disconnects` | `player, player_id` | Player disconnects |
| `player_killed` | `fragger_id, fragger, fragged_id, fragged, weapon` | Player killed |
| `player_begin` | `player, player_id` | Player enters map |
| `map_change` | `current_map, new_map` | Map changes |

---

## Troubleshooting

### Common Issues

**Server won't start?**
- Check port isn't already in use: `netstat -tulpn | grep PORT`
- Verify paths in your config file
- Check the log file for errors

**RTV/RTM not working?**
- Ensure RTV plugin is enabled in your config
- Check that your firewall allows the RTV port

**VPN monitor issues?**
- Verify your iphub.info API key is correct
- Check database path exists and is writable

### Getting Help

- Check the logs in your instance directory
- Review your config JSON for syntax errors
- Ensure all dependencies are installed

---

## Updating

### Linux
```bash
cd ~/mbiiez
git pull
./install.sh
```

### Windows
```cmd
cd path\to\repository
git pull
install.bat
```

---

## Memory Optimization (Linux)

MBIIEZ uses jemalloc for memory optimization on Linux servers. This is automatically configured:

- **Package:** `libjemalloc2:i386` (installed via install.sh)
- **Purpose:** Reduces memory fragmentation, improves long-running server performance
- **Applied:** Automatically via LD_PRELOAD when starting game server processes

This is Linux-only and provides better memory management for sustained gameplay sessions.

---

## License

This project is open source and available for contribution. If you encounter issues or have feature requests, please submit them to the GitHub repository.
