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
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN, CO_OWNER_ID, DEFAULT_LANG
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

from tg_bot.strings.string_helper import get_string
import tg_bot.modules.sql.lang_sql as lang

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
}


def gban(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(get_string("gbans", "ERR_NO_TARGET", lang.get_lang(update.effective_chat.id))) # ERR_NO_TARGET
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text(get_string("gbans", "ERR_SUDO_USER", lang.get_lang(update.effective_chat.id))) # ERR_SUDO_USER
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text(get_string("gbas", "ERR_SUPPORT_USER", lang.get_lang(update.effective_chat.id))) # ERR_SUPPORT_USER
        return

    if user_id == bot.id:
        message.reply_text(get_string("gbans", "ERR_IS_ITSELF", lang.get_lang(update.effective_chat.id))) # ERR_IS_ITSELF
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text(get_string("gbans", "ERR_NO_USER", lang.get_lang(update.effective_chat.id))) # ERR_NO_USER
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text(get_string("gbans", "ERR_GBANNED_NO_REASON", lang.get_lang(update.effective_chat.id))) # ERR_GBANNED_NO_REASON
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text(get_string("gbans", "ALREADY_BANNED", lang.get_lang(update.effective_chat.id)).format(html.escape(old_reason)),
                               parse_mode=ParseMode.HTML) # ALREADY_BANNED
        else:
            message.reply_text(get_string("gbans", "ALREADY_BANNED_WITHOUT_REASON", lang.get_lang(update.effective_chat.id))) # ALREADY_BANNED_WITHOUT_REASON

        return

    message.reply_text(get_string("gbans", "BANNED", lang.get_lang(update.effective_chat.id))) # BANNED

    banner = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 get_string("gbans", "BROADCAST", DEFAULT_LANG).format(mention_html(banner.id, banner.first_name),
                                       mention_html(user_chat.id, user_chat.first_name), reason or get_string("gbans", "BROADCAST_NO_REASON", DEFAULT_LANG)),
                 html=True) # BROADCAST and BROADCAST_NO_REASON

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(get_string("gbans", "GENERAL_ERROR", lang.get_lang(update.effective_chat.id)).format(excp.message)) # GENERAL_ERROR
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, get_string("gbans", "GENERAL_ERROR", DEFAULT_LANG).format(excp.message)) # GENERAL_ERROR
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, get_string("gbans", "SUCCESS", lang.get_lang(update.effective_chat.id))) # SUCCESS
    message.reply_text(get_string("gbans", "SUCCESS_REPLY", lang.get_lang(update.effective_chat.id))) # SUCCESS_REPLY


def ungban(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(get_string("gbans", "ERR_NO_TARGET", lang.get_lang(update.effective_chat.id))) # ERR_NO_TARGET
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text(get_string("gbans", "ERR_NO_USER", lang.get_lang(update.effective_chat.id))) # ERR_NO_USER
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text(get_string("gbans", "ERR_NOT_BANNED", lang.get_lang(update.effective_chat.id))) # ERR_NOT_BANNED
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text(get_string("gbans", "UNBANNED", lang.get_lang(update.effective_chat)).format(user_chat.first_name)) # UNBANNED

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 get_string("gbans", "UNBANNED_BC", DEFAULT_LANG).format(mention_html(banner.id, banner.first_name),
                                                   mention_html(user_chat.id, user_chat.first_name)),
                 html=True) # UNBANNED_BC

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(get_string("gbans", "ERR_UNBANN_GENERAL", lang.get_lang(update.effective_chat.id)).format(excp.message))
                bot.send_message(OWNER_ID, get_string("gbans", "ERR_UNBANN_GENERAL", lang.get_lang(OWNER_ID)).format(excp.message))
                bot.send_message(CO_OWNER_ID, get_string("gbans", "ERR_UNBANN_GENERAL", lang.get_lang(CO_OWNER_ID)).format(excp.message))
                # ERR_UNBANN_GENERAL
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, get_string("gbans", "UNBANN_SCS", DEFAULT_LANG)) # UNBANN_SCS

    message.reply_text(get_string("gbans", "UNBANN_SCS_REPLY", lang.get_lang(update.effective_chat.id))) # UNBANN_SCS_REPLY


def gbanlist(update: Update, context: CallbackContext):

    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(get_string("gbans", "NO_GBANS", lang.get_lang(update.effective_chat.id)))
        return

    banfile = get_string("gbans", "EXPORT_HEAD", lang.get_lang(update.effective_chat.id)) # EXPORT_HEAD
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"]) # REASON

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption=get_string("gbans", "EXPORT_SUCCESS", lang.get_lang(update.effective_chat.id))) # EXPORT_SUCCESS


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(get_string("gbans", "THIS_IS_A_BAD_PERSON", lang.get_lang(update.effective_chat.id))) # THIS_IS_A_BAD_PERSON


def enforce_gban(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(get_string("gbans", "GBANS_ON", lang.get_lang(update.effective_chat.id))) # GBANS_ON
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(get_string("gbans", "GBANS_OFF", lang.get_lang(update.effective_chat.id))) # GBANS_OFF
    else:
        update.effective_message.reply_text(get_string("gbans", "GBAN_NO_ARGS", lang.get_lang(update.effective_chat.id)).format(sql.does_chat_gban(update.effective_chat.id))) # GBAN_NO_ARGS


def __stats__():
    return get_string("gbans", "STATS", DEFAULT_LANG).format(sql.num_gbanned_users()) # STATS


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = get_string("gbans", "USER_INFO", DEFAULT_LANG) # USER_INFO # TODO update this to update
    if is_gbanned:
        text = text.format("Yes") # USER_INFO_YES
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += get_string("gbans", "USER_INFO_REASON", DEFAULT_LANG).format(html.escape(user.reason)) # USER_INFO_REASON
    else:
        text = text.format(get_string("gbans", "USER_INFO_NO", DEFAULT_LANG)) # USER_INFO_NO
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return get_string("gbans", "CHAT_SETTINGS", lang.get_lang(chat_id)).format(sql.does_chat_gban(chat_id)) # CHAT_SETTINGS


def __help__(update: Update) -> str:
    return get_string("gbans", "HELP", lang.get_lang(update.effective_chat.id))

__mod_name__ = "Global Bans" # MODULE_NAME

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter, run_async=True)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter, run_async=True)
GBAN_LIST = CommandHandler("gbanlist", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter, run_async=True)

GBAN_STATUS = CommandHandler("gbanstat", gbanstat, pass_args=True, filters=Filters.group, run_async=True)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban, run_async=True)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
