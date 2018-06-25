import os
import json

def load_config():
    with open(os.path.dirname(__file__) + '/config.json', 'r') as f:
        return(json.load(f))
