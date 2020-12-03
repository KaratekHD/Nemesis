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
from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, CallbackContext, MessageHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_action import typing_action
from tg_bot.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, user_not_admin
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.log_channel import loggable
from tg_bot.strings.string_helper import get_string
import tg_bot.modules.sql.lang_sql as lang
import tg_bot.modules.sql.mute as mute_sql


@bot_admin
@user_admin
@loggable
def toggle_mute(update: Update, context: CallbackContext) -> str:
    msg = update.effective_message
    chat = update.effective_chat
    is_muted = mute_sql.get_muted(chat.id)
    if is_muted:
        mute_sql.set_muted(chat.id, False)
        msg.reply_text("This chat is now unmuted, everyone may write now!")
        return f"{update.effective_user.first_name} unmuted the chat!"
    if not is_muted:
        mute_sql.set_muted(chat.id, True)
        msg.reply_text("This chat is now muted, only administrators may write now!")
        return f"{update.effective_user.first_name} muted the chat!"


@user_not_admin
def on_message(update: Update, context: CallbackContext):
    LOGGER.debug("Yeet!")
    if mute_sql.get_muted(update.effective_chat.id):
        update.effective_message.delete()


@typing_action
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    chat_id = update.effective_chat.id
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(get_string("admin", "ERR_NO_USER", lang.get_lang(update.effective_chat.id)))  # ERR_NO_USER
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text(get_string("admin", "ERR_CANT_PROMOTE_ADMIN",
                                      lang.get_lang(update.effective_chat.id)))  # ERR_CANT_PROMOTE_ADMIN
        return ""

    if user_id == bot.id:
        message.reply_text(get_string("admin", "ERR_CANT_PROMOTE_MYSELF",
                                      lang.get_lang(update.effective_chat.id)))  # ERR_CANT_PROMOTE_MYSELF
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    bot.promoteChatMember(chat_id, user_id,
                          can_change_info=bot_member.can_change_info,
                          can_post_messages=bot_member.can_post_messages,
                          can_edit_messages=bot_member.can_edit_messages,
                          can_delete_messages=bot_member.can_delete_messages,
                          # can_invite_users=bot_member.can_invite_users,
                          can_restrict_members=bot_member.can_restrict_members,
                          can_pin_messages=bot_member.can_pin_messages,
                          can_promote_members=bot_member.can_promote_members)

    message.reply_text(
        get_string("admin", "PROMOTE_SUCCESS", lang.get_lang(update.effective_chat.id)))  # PROMOTE_SUCCESS
    return get_string("admin", "PROMOTE_SUCCESS_HTML", lang.get_lang(update.effective_chat.id)).format(
        html.escape(chat.title),
        mention_html(user.id, user.first_name),
        mention_html(user_member.user.id, user_member.user.first_name))  # PROMOTE_SUCCESS_HTML


@bot_admin
@can_promote
@user_admin
@typing_action
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(get_string("admin", "ERR_NO_USER", lang.get_lang(update.effective_chat.id)))  # ERR_NO_USER
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text(
            get_string("admin", "ERR_DEMOTE_CREATOR", lang.get_lang(update.effective_chat.id)))  # ERR_DEMOTE_CREATOR
        return ""

    if not user_member.status == 'administrator':
        message.reply_text(get_string("admin", "ERR_DEMOTE_NON_ADMIN",
                                      lang.get_lang(update.effective_chat.id)))  # ERR_DEMOTE_NON_ADMIN
        return ""

    if user_id == bot.id:
        message.reply_text(get_string("admin", "ERR_CANT_DEMOTE_MYSELF",
                                      lang.get_lang(update.effective_chat.id)))  # ERR_CANT_DEMOTE_MYSELF
        return ""

    try:
        bot.promoteChatMember(int(chat.id), int(user_id),
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)
        message.reply_text(
            get_string("admin", "DEMOTE_SUCCESS", lang.get_lang(update.effective_chat.id)))  # DEMOTE_SUCCESS
        return get_string("admin", "DEMOTE_SUCCESS_HTML", lang.get_lang(update.effective_chat.id)).format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(user_member.user.id, user_member.user.first_name))  # DEMOTE_SUCCESS_HTML

    except BadRequest:
        message.reply_text(get_string("admin", "ERR_GENERAL", lang.get_lang(update.effective_chat.id)))  # ERR_GENERAL
        return ""


@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return get_string("admin", "PINNED_HTML", lang.get_lang(update.effective_chat.id)).format(
            html.escape(chat.title), mention_html(user.id, user.first_name))  # PINNED_HTML

    return ""


@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return get_string("admin", "UNPINNED_HTML", lang.get_lang(update.effective_chat.id)).format(html.escape(chat.title),
                                                                                                mention_html(user.id,
                                                                                                             user.first_name))  # UNPINNED_HTML


@bot_admin
@user_admin
@typing_action
def invite(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.username:
        update.effective_message.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(get_string("admin", "ERR_NO_PERMS_INVITELINK", lang.get_lang(
                update.effective_chat.id)))  # ERR_NO_PERMS_INVITELINK
    else:
        update.effective_message.reply_text(get_string("admin", "ERR_NO_PERMS_INVITELINK",
                                                       lang.get_lang(update.effective_chat.id)))  # ERR_NO_SUPERGROUP


@typing_action
def adminlist(update: Update, context: CallbackContext):
    administrators = update.effective_chat.get_administrators()
    text = get_string("admin", "ADMINS_IN", lang.get_lang(update.effective_chat.id)).format(
        update.effective_chat.title or get_string("admin", "THIS_CHAT",
                                                  lang.get_lang(update.effective_chat.id)))  # ADMINS_IN and THIS_CHAT
    for admin in administrators:
        user = admin.user
        name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
        if user.username:
            name = escape_markdown("@" + user.username)
        text += "\n - {}".format(name)
    # TODO Maybe add some logic for titles and different roles?
    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def __chat_settings__(chat_id, user_id):
    return get_string("admin", "YOU_ADMIN", lang.get_lang(chat_id)).format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator"))  # YOU_ADMIN


def __help__(update: Update) -> str:
    return get_string("admin", "HELP", lang.get_lang(update.effective_chat.id))


# HELP

__mod_name__ = "Admin"  # MODULE_NAME

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True, filters=Filters.group, run_async=True)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group, run_async=True)

INVITE_HANDLER = CommandHandler("invitelink", invite, filters=Filters.group, run_async=True)

PROMOTE_HANDLER = CommandHandler("promote", promote, pass_args=True, filters=Filters.group, run_async=True)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True, filters=Filters.group, run_async=True)

ADMINLIST_HANDLER = CommandHandler("adminlist", adminlist, filters=Filters.group, run_async=True)

MUTE_HANDLER = CommandHandler("globalmute", toggle_mute, run_async=True)
DELETE_HANDLER = MessageHandler(Filters.all & Filters.group, on_message, run_async=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(DELETE_HANDLER, 70)  # I have no idea why this number is necessary, but without it it breaks...
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
