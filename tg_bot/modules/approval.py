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


from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher
from telegram.ext import CallbackContext, CommandHandler
from telegram import Update, ParseMode

import tg_bot.modules.sql.approval_sql as sql
from tg_bot.modules.helper_funcs.chat_action import typing_action
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user


def approved(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat

    all_approvals = sql.get_chat_approvals(chat.id)
    approval_list = ["List of approved users in  this chat:\n\n"]
    for user in all_approvals:
        if chat.get_member(user.user_id).user.username:
            u = "@" + escape_markdown(chat.get_member(user.user_id).user.username)
        else:
            u = "[{}](tg://user?id={})".format(chat.get_member(user.user_id).user.full_name, user.user_id)
        approval_list.append(" - {}\n".format(u))
    text = "".join(approval_list)
    if text is "List of approved users in  this chat:\n\n":
        text = "No approved users here!"
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@user_admin
@bot_admin
def approve(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(msg, args)
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            msg.reply_text("I can't seem to find this user")
            return ""
        raise
    if member.ADMINISTRATOR:
        msg.reply_text("This user is a chat admin, approving would not make any sense.")
        return
    if sql.check_approval(chat.id, member.user.id):
        msg.reply_text("This user is already approved, dumb ass.")
    else:
        sql.approve(chat.id, user_id)
        msg.reply_text("This user is now approved!")


@user_admin
@bot_admin
def unapprove(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(msg, args)
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            msg.reply_text("I can't seem to find this user")
            return ""
        raise
    if member.ADMINISTRATOR:
        msg.reply_text("This user is a chat admin, this does not make sense.")
    elif not sql.check_approval(chat.id, member.user.id):
        msg.reply_text("This user is not approved, how should I take away rights the user does not have?")
    else:
        sql.rm_approve(chat.id, user_id)
        msg.reply_text("This user is not approved anymore!")


def status(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(msg, args)
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message in ("User not found", "Invalid user_id specified"):
            if update.effective_user.username:
                u = "@" + escape_markdown(update.effective_user.username)
            else:
                u = "[{}](tg://user?id={})".format(update.effective_user.full_name, update.effective_user.id)
            if update.effective_message.chat.get_member(update.effective_user.id).ADMINISTRATOR:
                msg.reply_text(f"{u} is a chat admin.", parse_mode=ParseMode.MARKDOWN)
                return
            if sql.check_approval(chat.id, update.effective_user.id):
                msg.reply_text(f"The user {u} is approved.", parse_mode=ParseMode.MARKDOWN)
            else:
                msg.reply_text(f"The user {u} is not approved.", parse_mode=ParseMode.MARKDOWN)
            return
        raise

    if member.user.username:
        u = "@" + escape_markdown(member.user.username)
    else:
        u = "[{}](tg://user?id={})".format(member.user.full_name, member.user.id)
    if sql.check_approval(chat.id, member.user.id):
        msg.reply_text(f"The user {u} is approved.", parse_mode=ParseMode.MARKDOWN)
    else:
        msg.reply_text(f"The user {u} is not approved.", parse_mode=ParseMode.MARKDOWN)


@user_admin
@bot_admin
@typing_action
def unapproveall(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args
    sql.remove_all(chat.id)
    msg.reply_text("All approvals have been removed.")



APPROVE_HANDLER = CommandHandler("approve", approve, run_async=True)
APPROVED_HANDLER = CommandHandler("approved", approved, run_async=True)
UNAPPROVE_HANDLER = CommandHandler("unapprove", unapprove, run_async=True)
UNAPPROVEALL_HANDLER = CommandHandler("unapproveall", unapproveall, run_async=True)
STATUS_HANDLER = CommandHandler("approval", status, run_async=True)

dispatcher.add_handler(APPROVED_HANDLER)
dispatcher.add_handler(APPROVE_HANDLER)
dispatcher.add_handler(UNAPPROVE_HANDLER)
dispatcher.add_handler(STATUS_HANDLER)
dispatcher.add_handler(UNAPPROVEALL_HANDLER)


__mod_name__ = "Approval"


def __help__(update: Update) -> str:
    return "Sometimes, you might trust a user not to send unwanted content." \
        "Maybe not enough to make them admin, but you might be ok with locks, blacklists, and antiflood not applying to them." \
        "That's what approvals are for - approve of trustworthy users to allow them to send\n\n" \
        "Admin commands:\n" \
        "- /approval: Check a user's approval status in this chat.\n" \
        "- /approve: Approve of a user. Locks, blacklists, and antiflood won't apply to them anymore.\n" \
        "- /unapprove: Unapprove of a user. They will now be subject to locks, blacklists, and antiflood again.\n" \
        "- /approved: List all approved users.\n" \
        "- /unapproveall: Unapprove ALL users in a chat. This cannot be undone.\n"

