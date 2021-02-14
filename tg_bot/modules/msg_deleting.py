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


import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, CallbackContext
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, can_delete
from tg_bot.modules.log_channel import loggable


@user_admin
@loggable
def purge(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    if msg.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            message_id = msg.reply_to_message.message_id
            delete_to = msg.message_id - 1
            if args and args[0].isdigit():
                new_del = message_id + int(args[0])
                # No point deleting messages which haven't been written yet.
                if new_del < delete_to:
                    delete_to = new_del

            for m_id in range(delete_to, message_id - 1, -1):  # Reverse iteration over message ids
                try:
                    bot.deleteMessage(chat.id, m_id)
                except BadRequest as err:
                    if err.message == "Message can't be deleted":
                        bot.send_message(chat.id, "Cannot delete all messages. The messages may be too old, I might "
                                                  "not have delete rights, or this might not be a supergroup.")

                    elif err.message != "Message to delete not found":
                        LOGGER.exception("Error while purging chat messages.")

            try:
                msg.delete()
            except BadRequest as err:
                if err.message == "Message can't be deleted":
                    bot.send_message(chat.id, "Cannot delete all messages. The messages may be too old, I might "
                                              "not have delete rights, or this might not be a supergroup.")

                elif err.message != "Message to delete not found":
                    LOGGER.exception("Error while purging chat messages.")

            bot.send_message(chat.id, "Purge complete.")
            return "<b>{}:</b>" \
                   "\n#PURGE" \
                   "\n<b>Admin:</b> {}" \
                   "\nPurged <code>{}</code> messages.".format(html.escape(chat.title),
                                                               mention_html(user.id, user.first_name),
                                                               delete_to - message_id)

    else:
        msg.reply_text("Reply to a message to select where to start purging from.")

    return ""


@user_admin
@loggable
def spurge(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    if msg.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            message_id = msg.reply_to_message.message_id
            delete_to = msg.message_id - 1
            if args and args[0].isdigit():
                new_del = message_id + int(args[0])
                # No point deleting messages which haven't been written yet.
                if new_del < delete_to:
                    delete_to = new_del

            for m_id in range(delete_to, message_id - 1, -1):  # Reverse iteration over message ids
                try:
                    bot.deleteMessage(chat.id, m_id)
                except BadRequest as err:
                    if err.message == "Message can't be deleted":
                        bot.send_message(chat.id, "Cannot delete all messages. The messages may be too old, I might "
                                                  "not have delete rights, or this might not be a supergroup.")

                    elif err.message != "Message to delete not found":
                        LOGGER.exception("Error while purging chat messages.")

            try:
                msg.delete()
            except BadRequest as err:
                if err.message == "Message can't be deleted":
                    bot.send_message(chat.id, "Cannot delete all messages. The messages may be too old, I might "
                                              "not have delete rights, or this might not be a supergroup.")

                elif err.message != "Message to delete not found":
                    LOGGER.exception("Error while purging chat messages.")

            return "<b>{}:</b>" \
                   "\n#PURGE" \
                   "\n<b>Admin:</b> {}" \
                   "\nPurged <code>{}</code> messages.".format(html.escape(chat.title),
                                                               mention_html(user.id, user.first_name),
                                                               delete_to - message_id)

    else:
        msg.reply_text("Reply to a message to select where to start purging from.")

    return ""


@user_admin
@loggable
def del_message(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    if update.effective_message.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            update.effective_message.reply_to_message.delete()
            update.effective_message.delete()
            return "<b>{}:</b>" \
                   "\n#DEL" \
                   "\n<b>Admin:</b> {}" \
                   "\nMessage deleted.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))
    else:
        update.effective_message.reply_text("Whadya want to delete?")

    return ""


def __help__(update: Update) -> str:
    return "\n*Admin only:*\n" \
           "- /del: deletes the message you replied to\n" \
           " - /purge: deletes all messages between this and the replied to message.\n" \
           " - /purge <integer X>: deletes the replied message, and X messages following it.\n" \
            " - /spurge: same as /purge, but without sending a message after completing."


__mod_name__ = "Message Deletion"

DELETE_HANDLER = CommandHandler("del", del_message, filters=Filters.group, run_async=True)
PURGE_HANDLER = CommandHandler("purge", purge, filters=Filters.group, pass_args=True, run_async=True)
SPURGE_HANDLER = CommandHandler("spurge", spurge, filters=Filters.group, pass_args=True, run_async=True)
PURGE2_HANDLER = CommandHandler("p", purge, filters=Filters.group, pass_args=True, run_async=True)
SPURGE2_HANDLER = CommandHandler("sp", spurge, filters=Filters.group, pass_args=True, run_async=True)

dispatcher.add_handler(SPURGE_HANDLER)
dispatcher.add_handler(SPURGE2_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(PURGE_HANDLER)
dispatcher.add_handler(PURGE2_HANDLER)
