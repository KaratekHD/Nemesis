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

import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters, CallbackContext
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
import tg_bot.modules.sql.lang_sql as lang
from tg_bot.strings.string_helper import get_string


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(get_string("bans", "ERR_NO_TARGET", lang.get_lang(update.effective_chat.id))) # ERR_NO_TARGET
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(get_string("bans", "ERR_USER_NOT_FOUND", lang.get_lang(update.effective_chat.id))) # ERR_USER_NOT_FOUND
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(get_string("bans", "ERR_TARGET_IS_ADMIN", lang.get_lang(update.effective_chat.id))) # ERR_TARGET_IS_ADMIN
        return ""

    if user_id == bot.id:
        message.reply_text(get_string("bans", "ERR_TARGET_ITSELF", lang.get_lang(update.effective_chat.id))) # ERR_TARGET_ITSELF
        return ""

    log = get_string("bans", "MSG_BAN_HTML", lang.get_lang(update.effective_chat.id)).format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id) # MSG_BAN_HTML
    if reason:
        log += get_string("bans", "MSG_BAN_HTML_REASON", lang.get_lang(update.effective_chat.id)).format(reason) # MSG_BAN_HTML_REASON

    try:
        chat.kick_member(user_id)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(get_string("bans", "MSG_BAN_SUCCESS", lang.get_lang(update.effective_chat.id))) # MSG_BAN_SUCCESS
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(get_string("bans", "MSG_BAN_SUCCESS", lang.get_lang(update.effective_chat.id)), quote=False) # MSG_BAN_SUCCESS
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(get_string("bans", "ERR_CONSOLE_CANT_BAN", lang.get_lang(update.effective_chat.id)), user_id, chat.title, chat.id,
                             excp.message) # ERR_CONSOLE_CANT_BAN
            message.reply_text(get_string("bans", "ERR_CANT_BAN", lang.get_lang(update.effective_chat.id))) # ERR_CANT_BAN

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(get_string("bans", "ERR_NO_TARGET", lang.get_lang(update.effective_chat.id))) # ERR_NO_TARGET
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(get_string("bans", "ERR_USER_NOT_FOUND", lang.get_lang(update.effective_chat.id))) # ERR_USER_NOT_FOUND
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(get_string("bans", "ERR_TARGET_IS_ADMIN", lang.get_lang(update.effective_chat.id))) # ERR_TARGET_IS_ADMIN
        return ""

    if user_id == bot.id:
        message.reply_text(get_string("bans", "ERR_TARGET_ITSELF", lang.get_lang(update.effective_chat.id))) # ERR_TARGET_ITSELF
        return ""

    if not reason:
        message.reply_text(get_string("bans", "ERR_TEMPBAN_NO_TIME", lang.get_lang(update.effective_chat.id))) # ERR_TEMPBAN_NO_TIME
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = get_string("bans", "MSG_TEMPBAN_HTML", lang.get_lang(update.effective_chat.id)).format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val) # MSG_TEMPBAN_HTML
    if reason:
        log += get_string("bans", "MSG_TEMPBAN_HTML_REASON", lang.get_lang(update.effective_chat.id)).format(reason) # MSG_TEMPBAN_HTML_REASON

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(get_string("bans", "MSG_TEMPBAN_SUCCES", lang.get_lang(update.effective_chat.id)).format(time_val)) # MSG_TEMPBAN_SUCCES
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(get_string("bans", "MSG_TEMPBAN_SUCCES", lang.get_lang(update.effective_chat.id)).format(time_val), quote=False) # MSG_TEMPBAN_SUCCES
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(get_string("bans", "ERR_CONSOLE_CANT_BAN", lang.get_lang(update.effective_chat.id)), user_id, chat.title, chat.id,
                             excp.message) # ERR_CONSOLE_CANT_BAN
            message.reply_text(get_string("bans", "ERR_CANT_BAN", lang.get_lang(update.effective_chat.id))) # ERR_CANT_BAN

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(get_string("bans", "ERR_USER_NOT_FOUND", lang.get_lang(update.effective_chat.id))) # ERR_USER_NOT_FOUND
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text(get_string("bans", "ERR_KICK_TARGET_ADMIN", lang.get_lang(update.effective_chat.id))) # ERR_KICK_TARGET_ADMIN
        return ""

    if user_id == bot.id:
        message.reply_text(get_string("bans", "ERR_KICK_TARGET_ITSELF", lang.get_lang(update.effective_chat.id))) # ERR_KICK_TARGET_ITSELF
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(get_string("bans", "MSG_KICK_SUCCESS", lang.get_lang(update.effective_chat.id)))
        log = get_string("bans", "MSG_KICK_HTML", lang.get_lang(update.effective_chat.id)).format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id) # MSG_KICK_HTML
        if reason:
            log += get_string("bans", "MSG_KICK_HTML_REASON", lang.get_lang(update.effective_chat.id)).format(reason) # MSG_KICK_HTML_REASON

        return log

    else:
        message.reply_text(get_string("bans", "ERR_CANT_KICK", lang.get_lang(update.effective_chat.id)))

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(get_string("bans", "ERR_KICKME_TARGET_IS_ADMIN", lang.get_lang(update.effective_chat.id))) # ERR_KICKME_TARGET_IS_ADMIN
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text(get_string("bans", "MSG_KICKME_SUCCESS"), lang.get_lang(update.effective_chat.id))
    else:
        update.effective_message.reply_text(get_string("bans", "ERR_KICKME_GENERAL", lang.get_lang(update.effective_chat.id)))


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(get_string("bans", "ERR_USER_NOT_FOUND", lang.get_lang(update.effective_chat.id))) # ERR_USER_NOT_FOUND
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text(get_string("bans", "ERR_UNBAN_ITSELF", lang.get_lang(update.effective_chat.id))) # ERR_UNBAN_ITSELF
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text(get_string("bans", "ERR_UNBAN_NOT_BANNED", lang.get_lang(update.effective_chat.id))) # ERR_UNBAN_NOT_BANNED
        return ""

    chat.unban_member(user_id)
    message.reply_text(get_string("bans", "MSG_UNBAN_SUCCESS", lang.get_lang(update.effective_chat.id))) # MSG_UNBAN_SUCCESS

    log = get_string("bans", "MSG_UNBAN_HTML", lang.get_lang(update.effective_chat.id)).format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id) # MSG_UNBAN_HTML
    if reason:
        log += get_string("bans", "MSG_UNBAN_HTML_REASON", lang.get_lang(update.effective_chat.id)).format(reason) # MSG_UNBAN_HTML_REASON

    return log


def __help__(update: Update) -> str:
    return get_string("bans", "HELP", lang.get_lang(update.effective_chat.id))
# HELP

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban,filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
