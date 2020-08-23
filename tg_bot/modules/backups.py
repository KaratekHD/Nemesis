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

import toml
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, DispatcherHandlerStop

from tg_bot import dispatcher, LOGGER
from tg_bot.__main__ import DATA_IMPORT
from tg_bot.modules.helper_funcs.chat_status import user_admin, bot_admin
import tg_bot.modules.helper_funcs.backups as helper



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

        if (data["data"]["filters"]["filters"] is not None):
            filters = data["data"]["filters"]["filters"]
            for i in filters:
                keyword = i["name"]
                text = i["text"]
                helper.import_filter(chat.id, keyword, text)
        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        data = data["data"]
        rules = data["rules"]
        helper.import_rules(chat.id, rules["content"])
        notes = data["notes"]
        if (notes["notes"] is not None):
            notes = notes["notes"]
            for i in notes:
                if i["type"] is 0:
                    helper.import_note(chat.id, i["name"], i["text"])

        msg.reply_text("Backup fully imported. Welcome back! :D")


@run_async
@user_admin
def export_data(bot: Bot, update: Update):
    with BytesIO(str.encode(helper.export_data(update.effective_chat, bot))) as output:
        output.name = str(update.effective_chat.id) + ".toml"
        update.effective_message.reply_document(document=output, filename=str(update.effective_chat.id) + ".toml",
                                                caption="Here you go.") # EXPORT_SUCCESS



__mod_name__ = "Backups"

def __help__(update: Update) -> str:
    return "\n*Admin only:*\n" \
           " - /import: reply to a group butler backup file to import as much as possible, making the transfer super simple! Note \
           that files/photos can't be imported due to telegram restrictions.\n" \
           " - /export: !!! This isn't a command yet, but should be coming soon!"

IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data)

dispatcher.add_handler(IMPORT_HANDLER)
dispatcher.add_handler(EXPORT_HANDLER)
