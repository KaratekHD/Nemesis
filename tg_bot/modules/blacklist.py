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
import re
from typing import Optional, List

from telegram import Message, Chat, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext

import tg_bot.modules.sql.blacklist_sql as sql
import tg_bot.modules.sql.lang_sql as lang
from tg_bot import dispatcher, LOGGER, DEFAULT_LANG
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin, user_not_admin, user_not_approved
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.misc import split_message
from tg_bot.strings.string_helper import get_string

BLACKLIST_GROUP = 11

BASE_BLACKLIST_STRING = "Current <b>blacklisted</b> words:\n"


def blacklist(update: Update, context: CallbackContext):
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]

    all_blacklisted = sql.get_chat_blacklist(chat.id)

    filter_list = get_string("blacklist", "BASE_BLACKLIST_STRING", lang.get_lang(update.effective_chat.id))

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if text == BASE_BLACKLIST_STRING:
            msg.reply_text(get_string("blacklist", "MSG_NO_BLACKLIST", lang.get_lang(update.effective_chat.id))) # MSG_NO_BLACKLIST
            return
        msg.reply_text(text, parse_mode=ParseMode.HTML)


@user_admin
def add_blacklist(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    words = msg.text.split(None, 1)
    if len(words) > 1:
        text = words[1]
        to_blacklist = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat.id, trigger.lower())

        if len(to_blacklist) == 1:
            msg.reply_text(get_string("blacklist", "MSG_BLACKLIST_ADD_SUCCESS", lang.get_lang(update.effective_chat.id)).format(html.escape(to_blacklist[0])),
                           parse_mode=ParseMode.HTML) # MSG_BLACKLIST_ADD_SUCCESS

        else:
            msg.reply_text(
                get_string("blacklist", "MSG_BLACKLIST_ADD_SUCCESS_MULTIPLE", lang.get_lang(update.effective_chat.id)).format(len(to_blacklist)), parse_mode=ParseMode.HTML) # MSG_BLACKLIST_ADD_SUCCESS_MULTIPLE

    else:
        msg.reply_text(get_string("blacklist", "ERR_BAD_REQUEST", lang.get_lang(update.effective_chat.id))) # ERR_BAD_REQUEST


@user_admin
def unblacklist(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    words = msg.text.split(None, 1)
    if len(words) > 1:
        text = words[1]
        to_unblacklist = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat.id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                msg.reply_text(get_string("blacklist", "MSG_REMOVED_SUCCESS", lang.get_lang(update.effective_chat.id)).format(html.escape(to_unblacklist[0])),
                               parse_mode=ParseMode.HTML) # MSG_REMOVED_SUCCESS
            else:
                msg.reply_text(get_string("blacklist", "ERR_NOT_VALID_TRIGGER", lang.get_lang(update.effective_chat.id))) # ERR_NOT_VALID_TRIGGER

        elif successful == len(to_unblacklist):
            msg.reply_text(
                get_string("blacklist", "MSG_REMOVED_SUCCESS_MULTIPLE", lang.get_lang(update.effective_chat.id)).format(
                    successful), parse_mode=ParseMode.HTML) # MSG_REMOVED_SUCCESS_MULTIPLE

        elif not successful:
            msg.reply_text(
                get_string("blacklist", "ERR_NOT_VALID_TRIGGER_MULTIPLE", lang.get_lang(update.effective_chat.id)).format(
                    successful, len(to_unblacklist) - successful), parse_mode=ParseMode.HTML) # ERR_NOT_VALID_TRIGGER_MULTIPLE

        else:
            msg.reply_text(
                get_string("blacklist", "ERR_NOT_ALL_VALID_TRIGGER", lang.get_lang(update.effective_chat.id)).format(successful, len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML) # ERR_NOT_ALL_VALID_TRIGGER
    else:
        msg.reply_text(get_string("blacklist", "ERR_REMOVE_BAD_REQUEST", lang.get_lang(update.effective_chat.id))) # ERR_REMOVE_BAD_REQUEST


@user_not_approved
@user_not_admin
def del_blacklist(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception(get_string("blacklist", "ERR_CONSOLE_CANT_DELETE_MESSAGE", DEFAULT_LANG)) # ERR_CONSOLE_CANT_DELETE_MESSAGE
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return get_string("blacklist", "CHAT_SETTINGS", lang.get_lang(chat_id)).format(blacklisted) # CHAT_SETTINGS


def __stats__():
    return get_string("blacklist", "STATS", DEFAULT_LANG).format(sql.num_blacklist_filters(),
                                                            sql.num_blacklist_filter_chats()) # STATS


__mod_name__ = "Word Blacklists" # MODULE_NAME

def __help__(update: Update) -> str:
    return get_string("blacklist", "HELP", lang.get_lang(update.effective_chat.id))


BLACKLIST_HANDLER = DisableAbleCommandHandler("blacklist", blacklist, filters=Filters.group, pass_args=True,
                                              run_async=True)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist, filters=Filters.group, run_async=True)
UNBLACKLIST_HANDLER = CommandHandler(["unblacklist", "rmblacklist"], unblacklist, filters=Filters.group, run_async=True)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, del_blacklist, run_async=True)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)
