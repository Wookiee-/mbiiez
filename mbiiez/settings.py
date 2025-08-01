import configparser
import os

class globals:
    script_path = os.path.dirname(os.path.realpath(__file__ + "/.."))   
    config = configparser.ConfigParser()
    config.read(script_path + "/mbiiez.conf")
    verbose = False

class locations:

    script_path = globals.script_path
    game_path = globals.config.get('locations', 'game_path')
    mbii_path = globals.config.get('locations', 'mbii_path')
    base_path = globals.config.get('locations', 'base_path')
    config_path = globals.config.get('locations', 'config_path')
    plugins_path = os.path.join(script_path, "plugins")
    
class dedicated:    
    
    game = globals.config.get('dedicated', 'game')
    engine = globals.config.get('dedicated', 'engine')

class database:

    database = globals.config.get('database', 'database')
    
