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


import secrets

from telegram.ext import run_async, CallbackContext, CommandHandler

from tg_bot import dispatcher
from tg_bot.restapi import api
from telegram import Update, ParseMode


@run_async
def get_api_key(update: Update, context: CallbackContext):
    if update.effective_chat.type == "private":
        generated_key = secrets.token_urlsafe(30)
        update.effective_message.reply_text(f"Your Api key is\n\n"
                                            f"<code>{generated_key}</code>\n"
                                            f"This key can be used to execute tasks as your user, so keep it secret!", parse_mode=ParseMode.MARKDOWN)

__mod_name__ = "REST Api"


def __help__(update: Update) -> str:
    return "Access the bots features using the brand new REST Api!"


KEY_HANDLER = CommandHandler("apikey", get_api_key)

dispatcher.add_handler(KEY_HANDLER)