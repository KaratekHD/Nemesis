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
from io import BytesIO
from typing import Optional

from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, DispatcherHandlerStop

from tg_bot import dispatcher, LOGGER
from tg_bot.__main__ import DATA_IMPORT
from tg_bot.modules.helper_funcs.chat_status import user_admin, bot_admin
import tg_bot.modules.sql.cust_filters_sql as custom_filters


@user_admin
@bot_admin
# NOTE: This file won't be translated (for now), since this feature is gonna get rewritten completely.
def import_data(bot: Bot, update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc
    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text("Try downloading and reuploading the file as yourself before importing - this one seems "
                           "to be iffy!")
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # from tg_bot.modules.sql.antiflood_sql import set_flood

        if (data["data"]["filters"]["filters"] is not None):
            chat_filters = custom_filters.get_chat_triggers(chat.id)
            filters = data["data"]["filters"]["filters"]
            for i in filters:
                if (i["type"] != "0"):
                    for keyword in chat_filters:
                        if keyword == i["name"]:
                            custom_filters.remove_filter(chat.id, i["name"])
                            raise DispatcherHandlerStop
                    HANDLER_GROUP = 10
                    # Add the filter
                    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
                    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
                        if handler.filters == (i["name"], chat.id):
                            dispatcher.remove_handler(handler, HANDLER_GROUP)

                    custom_filters.add_filter(chat.id, i["name"], i["text"])


        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        msg.reply_text("Backup fully imported. Welcome back! :D")


@run_async
@user_admin
def export_data(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    msg.reply_text("")


__mod_name__ = "Backups"

def __help__(update: Update) -> str:
    return "\n*Admin only:*\n" \
           " - /import: reply to a group butler backup file to import as much as possible, making the transfer super simple! Note \
           that files/photos can't be imported due to telegram restrictions.\n" \
           " - /export: !!! This isn't a command yet, but should be coming soon!"

IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data)

dispatcher.add_handler(IMPORT_HANDLER)
# dispatcher.add_handler(EXPORT_HANDLER)
