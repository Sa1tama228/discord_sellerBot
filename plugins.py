import json

"""тут ставить плагины/аддоны"""

def load():
    with open('config.json', 'r') as f:
        return json.load(f)
