# Movie Battles II EZ (MBIIEZ)

MBIIEZ is a Python 3 wrapper for running and managing instances of Movie Battles II game servers. It provides both a CLI (Command Line Interface) and a Web GUI for managing game server instances.

## Features

- **Simple Web GUI** - Manage servers through an intuitive web interface
- **CLI Management** - Full command-line control for automation and scripting
- **Multi-Instance Support** - Run multiple game server instances simultaneously on different ports
- **Plugin System** - Extend functionality with custom Python plugins
- **RTV/RTM Support** - Built-in rock-the-vote and requested-to-vote management with map nominations
- **VPN Protection** - Detect and block VPN/proxy users (optional)
- **Auto Messages** - Rotating server messages to players
- **Discord Integration** - Control your server from Discord
- **Scheduled Restarts** - Automatic server restarts configurable per instance
- **Cross-Platform** - Runs on both Linux and Windows

---

## Quick Start

Get your MBII server running in under 5 minutes!

### 1. Install

**Linux:**
```bash
git clone https://github.com/Wookiee-/mbiiez.git && cd mbiiez
chmod +x install.sh && ./install.sh
# Select option 9 for Quick Install (recommended)
```

**Windows:**
```cmd
cd path\to\repository
install.bat
# Select option 9 for Quick Install
```

### 2. Create Your Server Config

**Linux:**
```bash
cp configs/default.json.example configs/myfirstserver.json
nano configs/myfirstserver.json
```

**Windows:**
```cmd
copy configs\/default.json.example configs\/myfirstserver.json
# Edit in your preferred text editor
```

**Required settings to change:**
- `host_name` - Your server's display name
- `port` - Unique port for this server (e.g., 29070)
- `rcon_password` - Set a secure RCON password

### 3. Start Your Server

```bash
mbii -i myfirstserver start
mbii -i myfirstserver status  # Verify it's running
```

Players connect at `your-ip:port` (e.g., `192.168.1.100:29070`).

---

## RTV/RTM Commands

The RTV/RTM plugin provides voting functionality for map and mode changes.

### Player Commands

| Command | Description |
|---------|-------------|
| `!rtv` | Initiate rock-the-vote (map change) |
| `!rtm <mode>` | Initiate requested-to-vote (mode change: 0=Open, 1=Semi, 2=Full, 3=Duel, 4=Legends) |
| `!nominate <map>` or `!nom <map>` | Nominate a map for RTV voting |
| `!maps` | Show all maps available for nomination |
| `!maplist` | Show maps available for voting (excludes current/recently played) |
| `!search <expression>` | Search for maps containing text |
| `!1`, `!2`, etc. | Vote for option during active voting |
| `!unvote` | Remove your vote during voting phase |

### How RTV Works

1. **Initiate RTV:** Player types `!rtv`
2. **Nominate Maps:** Players can nominate maps with `!nominate <mapname>` before or after initiating
3. **Voting Begins:** When `rtv_rate`% of players have voted (minimum `rtv_min_votes`), voting starts
4. **Vote:** Players use `!1`, `!2`, etc. to pick their preferred map
5. **Results:** Map with most votes wins after voting timer ends
6. **Execute:** If `rtv_queued` is true, map changes at round end; otherwise immediate

### RTV/RTM Settings

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

| Setting | Description | Default |
|---------|-------------|---------|
| `enable_rtv` | Enable rock-the-vote | `true` |
| `enable_rtm` | Enable requested-to-vote | `false` |
| `rtv_rate` | % of players needed to trigger RTV | `50` |
| `rtv_min_votes` | Minimum votes required | `10` |
| `rtm_rate` | % of players needed to trigger RTM | `50` |
| `rtm_min_votes` | Minimum votes required | `20` |
| `rtv_queued` | Change at round end (true) or immediate (false) | `true` |
| `rtm_queued` | Change at round end (true) or immediate (false) | `true` |

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

#### Using the Installer (Recommended)

```bash
git clone https://github.com/Wookiee-/mbiiez.git
cd mbiiez
chmod +x install.sh
./install.sh
```

The installer provides these options:
1. Install System Dependencies
2. Install Python Tools
3. Setup RTVRTM
4. Setup Links and MBII
5. Install .NET SDK
6. Install MBII Updater
7. Update MBII
8. Show Installation Status
9. **Quick Install (Run 1-4, 5)** - Recommended for new users

#### Manual Installation

1. System dependencies:
```bash
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y libc6:i386 lib32z1 libstdc++6:i386 libcurl4t64:i386 libjemalloc2:i386 sqlite3 net-tools fping python3 python3-pip unzip
```

2. Python packages:
```bash
pip3 install --user watchgod tailer six psutil prettytable urllib3 flask flask_httpauth flask-socketio discord.py --break-system-packages
```

3. Create symlinks:
```bash
sudo ln -s /path/to/mbiiez/mbii.py /usr/bin/mbii
sudo chmod +x /usr/bin/mbii
ln -s /path/to/openjk ~/.local/share/openjk
```

### Windows

1. Ensure Python 3.8+ is installed from [python.org](https://python.org)

2. Download and extract this repository

3. Run the installer:
```cmd
cd path\to\repository
install.bat
```

4. Select **option 9 for Quick Install** (recommended)

The installer checks your system and creates the necessary directories and launcher.

---

## Configuration

### Create an Instance

Create a JSON config file in the `configs/` directory using `configs/default.json.example` as a template.

### Minimal Configuration

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

### With VPN Protection

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

| Setting | Type | Description |
|---------|------|-------------|
| `host_name` | string | Server display name |
| `port` | integer | Server port (unique per instance) |
| `engine` | string | Path to game engine |
| `game` | string | Game mod folder |
| `restart_instance_every_hours` | integer | Auto-restart interval (0=disabled) |

#### Security Section

| Setting | Description |
|---------|-------------|
| `rcon_password` | RCON access password (required) |
| `server_password` | Server password (blank=open) |

#### Game Section

| Setting | Description | Valid Values |
|---------|-------------|--------------|
| `mode` | Game mode | `open`, `semi-authentic`, `full-authentic`, `duel`, `legends` |
| `map` | Starting map | Any valid map name |

### Plugin Configuration

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

---

## Usage

### CLI Commands

```bash
# Start/stop/restart an instance
mbii -i myinstance start
mbii -i myinstance stop
mbii -i myinstance restart

# Check status
mbii -i myinstance status

# Send messages and RCON commands
mbii -i myinstance say Hello everyone!
mbii -i myinstance rcon g_gametype 0

# Get/Set CVARs
mbii -i myinstance cvar g_gametype
mbii -i myinstance cvar g_gametype 2
```

### Web Interface

```bash
mbii web
```

Access `http://your-server-ip:5000` in your browser.

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
        self.instance.log_handler.log(f'{__name__} loaded!')
        
    def register_events(self):
        self.instance.event_handler.register_event('player_connects', self.on_player_connect)
        
    def on_player_connect(self, data):
        player = data['player']
        self.instance.rcon(f'svsay Welcome {player}!')
```

### Available Events

| Event | Arguments | Description |
|-------|-----------|-------------|
| `before_dedicated_server_launch` | - | Before server starts |
| `after_dedicated_server_launch` | - | After server starts |
| `new_log_line` | `log_line` | Every new log entry |
| `player_chat_command` | `message, player, player_id` | Chat starting with `!` |
| `player_chat` | `type, message, player, player_id` | All chat (TEAM/PUBLIC) |
| `player_connected` | `player, player_id` | Player connects |
| `player_disconnected` | `player, player_id` | Player disconnects |
| `player_killed` | `fragger_id, fragger, fragged_id, fragged, weapon` | Player killed |
| `player_begin` | `player, player_id` | Player enters map |
| `map_change` | `current_map, new_map` | Map changes |

---

## Troubleshooting

### Server Won't Start

- Check port isn't in use: `netstat -tulpn | grep PORT`
- Verify paths in your config
- Check the log file in your instance directory

### RTV/RTM Not Working

- Ensure `enable_rtv` or `enable_rtm` is `true` in your config
- Verify firewall allows the server port
- Check that maps are configured in `primary_maps` in your config

### VPN Monitor Issues

- Verify your iphub.info API key is correct
- Check database path exists and is writable

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

MBIIEZ uses jemalloc for memory optimization on Linux servers:
- **Package:** `libjemalloc2:i386` (installed via install.sh)
- **Purpose:** Reduces memory fragmentation, improves long-running server performance
- **Applied:** Automatically via LD_PRELOAD when starting game server processes

---

## License

This project is open source. Submit issues and feature requests to the GitHub repository.