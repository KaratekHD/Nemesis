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


from typing import List

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin
import tg_bot.modules.sql.lang_sql as sql
from tg_bot.strings.string_helper import get_string


@bot_admin
@user_admin
def setlang(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        SUPPORTED_LANGUAGES = ["de", "en"]
        if txt not in SUPPORTED_LANGUAGES:
            msg.reply_text(get_string("lang", "ERR_UNKNOWN_LANG", sql.get_lang(chat_id))) # ERR_UNKNOWN_LANG
        else:
            sql.set_lang(chat_id, txt)
            msg.reply_text(get_string("lang", "LANG_SET", sql.get_lang(chat_id))) # LANG_SET

    else:
        msg.reply_text(get_string("lang", "ERR_NO_LANG", sql.get_lang(chat_id))) # ERR_NO_LANG


__mod_name__ = "Languages"


def __chat_settings__(chat_id):
    return get_string("lang", "CHAT_SETTINGS", sql.get_lang(chat_id)).format(sql.get_lang(chat_id)) # CHAT_SETTINGS


def __user_settings__(user_id):
    return get_string("lang", "USER_SETTINGS", sql.get_lang(user_id)).format(
        sql.get_lang(user_id)) # USER_SETTINGS


def __help__(update: Update) -> str:
    return get_string("lang", "HELP", sql.get_lang(update.effective_chat.id)) # HELP


LANG_HANDLER = CommandHandler("lang", setlang, pass_args=True, run_async=True)

dispatcher.add_handler(LANG_HANDLER)
