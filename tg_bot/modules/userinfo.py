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

from telegram import Message, Update, User
from telegram import ParseMode, MAX_MESSAGE_LENGTH
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.userinfo_sql as sql
from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user


def about_me(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(username + " hasn't set an info message about themselves  yet!")
    else:
        update.effective_message.reply_text("You haven't set an info message about yourself yet!")


def set_about_me(update: Update, context: CallbackContext):
    message = update.effective_message  # type: Optional[Message]
    user_id = message.from_user.id
    text = message.text
    info = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            message.reply_text("Updated your info!")
        else:
            message.reply_text(
                "Your info needs to be under {} characters! You have {}.".format(MAX_MESSAGE_LENGTH // 4, len(info[1])))


def about_bio(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text("{} hasn't had a message set about themselves yet!".format(username))
    else:
        update.effective_message.reply_text("You haven't had a bio set about yourself yet!")


def set_about_bio(update: Update, context: CallbackContext):
    args = context.args
    bot =context.bot
    message = update.effective_message  # type: Optional[Message]
    sender = update.effective_user  # type: Optional[User]
    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id
        if user_id == message.from_user.id:
            message.reply_text("Ha, you can't set your own bio! You're at the mercy of others here...")
            return
        if user_id == bot.id and sender.id not in SUDO_USERS:
            message.reply_text("Erm... yeah, I only trust sudo users to set my bio.")
            return

        text = message.text
        bio = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("Updated {}'s bio!".format(repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "A bio needs to be under {} characters! You tried to set {}.".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("Reply to someone's message to set their bio!")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return "<b>About user:</b>\n{me}\n<b>What others say:</b>\n{bio}".format(me=me, bio=bio)
    if bio:
        return "<b>What others say:</b>\n{bio}\n".format(me=me, bio=bio)
    if me:
        return "<b>About user:</b>\n{me}""".format(me=me, bio=bio)
    return ""


def __gdpr__(user_id):
    sql.clear_user_info(user_id)
    sql.clear_user_bio(user_id)


def __help__(update: Update) -> str:
    return "\n - /setbio <text>: while replying, will save another user's bio\n" \
           " - /bio: will get your or another user's bio. This cannot be set by yourself.\n" \
           " - /setme <text>: will set your info\n" \
           " - /me: will get your or another user's info"

__mod_name__ = "Bios and Abouts"

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio, run_async=True)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio, pass_args=True, run_async=True)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me, run_async=True)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me, pass_args=True, run_async=True)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)
