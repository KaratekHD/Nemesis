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

from typing import Optional

from telegram import Message, Update, User
from telegram import MessageEntity
from telegram.ext import Filters, MessageHandler, CallbackContext

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from tg_bot.modules.sql import afk_sql as sql
from tg_bot.modules.users import get_user_id
import tg_bot.modules.sql.lang_sql as lang
from tg_bot.strings.string_helper import get_string


AFK_GROUP = 7
AFK_REPLY_GROUP = 8


def afk(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    if len(args) >= 2:
        reason = args[1]
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    update.effective_message.reply_text(get_string("afk", "MSG_IS_AFK_NOW", lang.get_lang(update.effective_chat.id)).format(update.effective_user.first_name)) # MSG_IS_AFK_NOW


def no_longer_afk(update: Update, context: CallbackContext):
    user = update.effective_user  # type: Optional[User]

    if not user:  # ignore channels
        return

    res = sql.rm_afk(user.id)
    if res:
        update.effective_message.reply_text(get_string("afk", "MSG_IS_NOT_AFK", lang.get_lang(update.effective_chat.id)).format(update.effective_user.first_name)) # MSG_IS_NOT_AFK


def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message  # type: Optional[Message]
    entities = message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION])
    if message.entities and entities:
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

            elif ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset + ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return
                chat = bot.get_chat(user_id)
                fst_name = chat.first_name

            else:
                return

            if sql.is_afk(user_id):
                valid, reason = sql.check_afk_status(user_id)
                if valid:
                    if not reason:
                        res = get_string("afk", "MSG_IS_AFK", lang.get_lang(update.effective_chat.id)).format(fst_name) # MSG_IS_AFK
                    else:
                        res = get_string("afk", "MSG_IS_AFK_REASON", lang.get_lang(update.effective_chat.id)).format(fst_name, reason) # MSG_IS_AFK_REASON
                    message.reply_text(res)


def __gdpr__(user_id):
    sql.rm_afk(user_id)


def __help__(update: Update) -> str:
    return get_string("afk", "HELP", lang.get_lang(update.effective_chat.id))


__mod_name__ = "AFK" # MODULE_NAME


AFK_HANDLER = DisableAbleCommandHandler("afk", afk, run_async=True)
AFK_MESSAGE_HANDLER = DisableAbleMessageHandler(Filters.regex("(?i)brb"), afk, friendly="afk", run_async=True)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk, run_async=True)
AFK_REPLY_HANDLER = MessageHandler(Filters.entity(MessageEntity.MENTION) | Filters.entity(MessageEntity.TEXT_MENTION),
                                   reply_afk, run_async=True)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_MESSAGE_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)
