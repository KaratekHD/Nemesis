import json
import os


def get_string(module: str, name: str, lang: str):
    with open(os.path.dirname(os.path.abspath(__file__)) + "/" + lang + "/" + module + ".json") as f:
        data = json.load(f)

    return data[name]
