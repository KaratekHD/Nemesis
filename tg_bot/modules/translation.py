#  Nemesis - Powerful  Telegram group managment bot
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

import json
from pprint import pprint

import requests
from telegram import Update, Bot
from telegram.ext import CommandHandler, CallbackContext

from tg_bot import dispatcher

# Open API key
from tg_bot.modules.disable import DisableAbleCommandHandler

API_KEY = "6ae0c3a0-afdc-4532-a810-82ded0054236"
URL = "http://services.gingersoftware.com/Ginger/correct/json/GingerTheText"


def translate(update: Update, context: CallbackContext):
    if update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message

        params = dict(
            lang="US",
            clientVersion="2.0",
            apiKey=API_KEY,
            text=msg.text
        )

        res = requests.get(URL, params=params)
        # print(res)
        # print(res.text)
        pprint(json.loads(res.text))
        changes = json.loads(res.text).get('LightGingerTheTextResult')
        curr_string = ""

        prev_end = 0

        for change in changes:
            start = change.get('From')
            end = change.get('To') + 1
            suggestions = change.get('Suggestions')
            if suggestions:
                sugg_str = suggestions[0].get('Text')  # should look at this list more
                curr_string += msg.text[prev_end:start] + sugg_str

                prev_end = end

        curr_string += msg.text[prev_end:]
        print(curr_string)
        update.effective_message.reply_text(curr_string)


def __help__(update: Update) -> str:
    return "\n - /t: while replying to a message, will reply with a grammar corrected version (English Only!)"

__mod_name__ = "Translator"


TRANSLATE_HANDLER = DisableAbleCommandHandler('t', translate)

dispatcher.add_handler(TRANSLATE_HANDLER)
