import json
import os
import random


# get string from json file
def get_string(module: str, name: str, lang: str):
    with open(os.path.dirname(os.path.abspath(__file__)) + "/" + lang + "/" + module + ".json") as f:
        data = json.load(f)

    return data[name]

# for /runs, /slap etc.
def get_random_string(module: str, lang: str):
    with open(os.path.dirname(os.path.abspath(__file__)) + "/" + lang + "/" + module + ".json") as f:
        data = json.load(f)
        i = len(data)
        r = random.randint(1, i)
        return data[r]
