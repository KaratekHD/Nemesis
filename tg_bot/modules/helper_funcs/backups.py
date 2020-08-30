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

import toml
from telegram import Bot, Chat

import tg_bot.modules.sql.cust_filters_sql as filters
import tg_bot.modules.sql.rules_sql as rules_sql
import tg_bot.modules.sql.notes_sql as notes_sql
from tg_bot import dispatcher
from tg_bot.modules.cust_filters import HANDLER_GROUP
from tg_bot.modules.helper_funcs.string_handling import markdown_parser
from tg_bot.modules.sql import welcome_sql, antiflood_sql, global_bans_sql, lang_sql


def import_filter(chatid, trigger, reply):

    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    buttons = []
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (trigger, chatid):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    filters.add_filter(chatid, trigger, reply, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                   buttons)

def import_rules(chatid, rules):
    markdown_rules = markdown_parser(rules)
    rules_sql.set_rules(chatid, markdown_rules)

def import_note(chatid, name, text):
    notes_sql.import_note_to_db(chatid, name, text)

def export_data(chat : Chat, bot: Bot) -> str:
    export = {"bot": {"id": bot.id, "name": bot.first_name, "username": bot.username},
              "chat": {"id": chat.id, "title": chat.title, "members": chat.get_members_count()},
              "welcomes": {"welcome": welcome_sql.get_custom_welcome(chat.id),
                           "goodbye": welcome_sql.get_custom_gdbye(chat.id)},
              "antiflood": {"limit": antiflood_sql.get_flood_limit(chat.id)},
              "gbans": {"enabled": global_bans_sql.does_chat_gban(chat.id)},
              "languages": {"lang": lang_sql.get_lang(chat.id)}, "rules": {"text": rules_sql.get_rules(chat.id)},
              "filters": {"null": "null"}
              }
    
    for i in filters.get_chat_triggers(chat.id):
        export["filters"][i] = filters.get_filter(chat.id, i).reply
    
    del export["filters"]["null"]
    return toml.dumps(export)
