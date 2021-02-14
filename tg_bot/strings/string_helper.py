#  OpenGM - Powerful  Telegram group managment bot
#  Copyright (C) 2017 - 2019 Paul Larsen
#  Copyright (C) 2019 - 2020 KaratekHD
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import random


# get string from json file
def get_string(module: str, name: str, lang: str):
    try:
        if not os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + "/" + lang + "/" + module + ".json"):
            lang = "en"
        with open(os.path.dirname(os.path.abspath(__file__)) + "/" + lang + "/" + module + ".json") as f:
            data = json.load(f)
        return data[name]
    except FileNotFoundError as excp:
        return excp.__cause__
    except KeyError as e:
        return e.__cause__




# for /runs, /slap etc.
def get_random_string(module: str, lang: str):
    if not os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + "/" + lang + "/" + module + ".json"):
        lang = "en"
    with open(os.path.dirname(os.path.abspath(__file__)) + "/" + lang + "/" + module + ".json") as f:
        data = json.load(f)
    i = len(data)
    r = str(random.randint(1, i))
    return data[r]
