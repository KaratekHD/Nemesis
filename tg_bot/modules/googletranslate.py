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

from googletrans import Translator
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from tg_bot import dispatcher
from tg_bot.strings.string_helper import get_string
import tg_bot.modules.sql.lang_sql as lang


def translate(update: Update, context: CallbackContext):
    msg = update.effective_message
    args = context.args
    if not args:
        msg.reply_text(get_string("googletranslate", "ERR_NO_LANG", update.effective_chat.id)) # ERR_NO_LANG
        return
    text = update.effective_message.reply_to_message
    if not text:
        msg.reply_text(get_string("googletranslate", "ERR_NO_MSG", update.effective_chat.id)) # ERR_NO_MSG
        return
    try :
        translator = Translator()
        translated = translator.translate(text.text, dest=args[0]).text
    except ValueError as excp:
        msg.reply_text(str(excp))
        return
    msg.reply_text(translated)


TRANSLATION_HANDLER = CommandHandler("translate", translate, run_async=True)


dispatcher.add_handler(TRANSLATION_HANDLER)

__mod_name__ = "Translation"

def __help__(update: Update) -> str:
    return get_string("googletranslate", "HELP", update.effective_chat.id) # HELP


