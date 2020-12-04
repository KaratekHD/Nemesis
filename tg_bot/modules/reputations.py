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


from telegram import Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, run_async, MessageHandler

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleMessageHandler, DisableAbleCommandHandler
import tg_bot.modules.sql.reputation_sql as sql


def increase(update: Update, context: CallbackContext):
    msg = update.effective_message
    user1 = update.effective_user
    chat = update.effective_chat
    if msg.reply_to_message:
        user2 = msg.reply_to_message.from_user
        if user1.id is not user2.id:
            LOGGER.debug(f"{user2.id} : {sql.get_reputation(chat.id, user2.id)}")
            sql.increase_reputation(chat.id, user2.id)
            new_msg = msg.reply_text(f"<b>{user1.first_name}</b> ({sql.get_reputation(chat.id, user1.id)}) has increased reputation of <b>{user2.first_name}</b> ({sql.get_reputation(chat.id, user2.id)})", parse_mode=ParseMode.HTML).message_id
            try:
                context.bot.delete_message(chat.id, sql.get_latest_rep_message(chat.id))
            except BadRequest as err:
                LOGGER.debug("Could not delete that message.")
            sql.set_latest_rep_message(chat.id, new_msg)


def decrease(update: Update, context: CallbackContext):
    msg = update.effective_message
    user1 = update.effective_user
    chat = update.effective_chat
    if msg.reply_to_message:
        user2 = msg.reply_to_message.from_user
        if user1.id is not user2.id:
            LOGGER.debug(f"{user2.id} : {sql.get_reputation(chat.id, user2.id)}")
            sql.decrease_reputation(chat.id, user2.id)
            new_msg = msg.reply_text(
                f"<b>{user1.first_name}</b> ({sql.get_reputation(chat.id, user1.id)}) has decreased reputation of <b>{user2.first_name}</b> ({sql.get_reputation(chat.id, user2.id)})",
                parse_mode=ParseMode.HTML).message_id
            try:
                context.bot.delete_message(chat.id, sql.get_latest_rep_message(chat.id))
            except BadRequest as err:
                LOGGER.debug("Could not delete that message.")
            sql.set_latest_rep_message(chat.id, new_msg)


def __help__(update: Update) -> str:
    return "\n*Admin only:*\n" \
           "- /del: deletes the message you replied to\n" \
           " - /purge: deletes all messages between this and the replied to message.\n" \
           " - /purge <integer X>: deletes the replied message, and X messages following it."


INCREASE_MESSAGE_HANDLER = DisableAbleMessageHandler(Filters.regex("(?i)\+"), increase, friendly="increase",
                                                     run_async=True)
dispatcher.add_handler(INCREASE_MESSAGE_HANDLER)

INCREASE_MESSAGE_HANDLER = DisableAbleMessageHandler(Filters.regex("(?i)\-"), decrease, friendly="decrease",
                                                     run_async=True)
dispatcher.add_handler(INCREASE_MESSAGE_HANDLER)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat_latest_messages(old_chat_id, new_chat_id)


__mod_name__ = "Reputations"
