## Latest News Update for Debian/Ubuntu 24.04/10

The installer has had an overhaul and redone.

If you are under root user please run:- 

- wget https://raw.githubusercontent.com/Wookiee-/mbiiez/refs/heads/main/runasroot.sh
- chmod +x runasroot.sh
- ./runasroot.sh

Then under mbiiez user account run:

- git clone https://github.com/Wookiee-/mbiiez.git
- cd mbiiez
- ./install.sh

## Changelog 

1. default.json.example and discord.json.example are there for examples
2. Launching with mbii command with discord.json not filled out will load RTVRTM service twice
3. RTVRTM have been been fixed and now working due to secondary maps in default.json.example not found on server
4. Pyenv is now used for python2 environment under the user so it doesn't break the system. 
5. Map rotation json example files are renamed in the mbiiez/configs and mbiiez/mbiiez folder ending with mr. defaultmr.json.example, discordmr.json.example, servermr.template and confmr.py.

