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
import re
from typing import Optional, List

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, DispatcherHandlerStop, MessageHandler, Filters, \
    CallbackQueryHandler, CallbackContext
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, bot_admin, user_admin_no_reply, user_admin, \
    can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_text, extract_user_and_text, extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import split_message
from tg_bot.modules.helper_funcs.string_handling import split_quotes
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import warns_sql as sql

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Current warning filters in this chat:</b>\n"


# Not async
def warn(user: User, chat: Chat, reason: str, message: Message, warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        message.reply_text("Damn admins, can't even be warned!") # ERR_USER_IS_ADMIN
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter." # AUTOMATED_TAG

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = "{} warnings, {} has been kicked!".format(limit, mention_html(user.id, user.first_name)) # MSG_KICK

        else:  # ban
            chat.kick_member(user.id)
            reply = "{} warnings, {} has been banned!".format(limit, mention_html(user.id, user.first_name)) # MSG_BAN

        for warn_reason in reasons:
            reply += "\n - {}".format(html.escape(warn_reason))

        message.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        log_reason = "<b>{}:</b>" \
                     "\n#WARN_BAN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit) # MSG_WARNBAN_HTML

    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Remove warn", callback_data="rm_warn({})".format(user.id))]]) # BUTTON_REMOVE

        reply = "{} has {}/{} warnings... watch out!".format(mention_html(user.id, user.first_name), num_warns,
                                                             limit)  # MSG_WARN_SUCCESS
        if reason:
            reply += "\nReason for last warn:\n{}".format(html.escape(reason)) # MSG_WARN_SUCCESS_REASON

        log_reason = "<b>{}:</b>" \
                     "\n#WARN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit) # MSG_WARN_HTML

    try:
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False)
        else:
            raise
    return log_reason


@user_admin_no_reply
@bot_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    query = update.callback_query  # type: Optional[CallbackQuery]
    user = update.effective_user  # type: Optional[User]
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat  # type: Optional[Chat]
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "Warn removed by {}.".format(mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML) # MSG_WARN_DEL
            user_member = chat.get_member(user_id)
            return "<b>{}:</b>" \
                   "\n#UNWARN" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                mention_html(user.id, user.first_name),
                                                                mention_html(user_member.user.id, user_member.user.first_name),
                                                                user_member.user.id) # MSG_UNWARN_HTML
        else:
            update.effective_message.edit_text(
                "User has already has no warns.".format(mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML) # MSG_UNWARN_HAS_NO_WARNS

    return ""


@user_admin
@can_restrict
@loggable
def warn_user(update: Update, context: CallbackContext) -> str:
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    warner = update.effective_user  # type: Optional[User]

    user_id, reason = extract_user_and_text(message, args)

    if user_id:
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            return warn(message.reply_to_message.from_user, chat, reason, message.reply_to_message, warner)
        else:
            return warn(chat.get_member(user_id).user, chat, reason, message, warner)
    else:
        message.reply_text("No user was designated!") # ERR_NO_USER
    return ""


@user_admin
@bot_admin
@loggable
def reset_warns(update: Update, context: CallbackContext) -> str:
    args = context.args
    bot = context.bot
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Warnings have been reset!") # MSG_RESET
        warned = chat.get_member(user_id).user
        return "<b>{}:</b>" \
               "\n#RESETWARNS" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                            mention_html(user.id, user.first_name),
                                                            mention_html(warned.id, warned.first_name),
                                                            warned.id) # MSG_RESET_HTML
    else:
        message.reply_text("No user has been designated!") # ERR_NO_USER
    return ""


def warns(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = "This user has {}/{} warnings, for the following reasons:".format(num_warns, limit) # MSG_INFO
            for reason in reasons:
                text += "\n - {}".format(reason)

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                "User has {}/{} warnings, but no reasons for any of them.".format(num_warns, limit)) # MSG_INFO_NOREASON
    else:
        update.effective_message.reply_text("This user hasn't got any warnings!") # MSG_INFO_NO_WARNS


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(update: Update, context: CallbackContext):
    LOGGER.debug("WTH")
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text("Warn handler added for '{}'!".format(keyword)) # MSG_FILTER_ADDED
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("No warning filters are active here!") # ERR_NO_FILTERS
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Yep, I'll stop warning people for that.") # MSG_REMOVE_FILTER
            raise DispatcherHandlerStop

    msg.reply_text("That's not a current warning filter - run /warnlist for all active warning filters.") # ERR_NO_FILTER


def list_warn_filters(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("No warning filters are active here!") # ERR_NO_FILTERS
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = " - {}\n".format(html.escape(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)


@loggable
def reply_filter(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user = update.effective_user  # type: Optional[User]
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@user_admin
@loggable
def set_warn_limit(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("The minimum warn limit is 3!") # ERR_WRONG_NUMBER
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("Updated the warn limit to {}".format(args[0])) # MSG_UPDATE_SETTINGS
                return "<b>{}:</b>" \
                       "\n#SET_WARN_LIMIT" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet the warn limit to <code>{}</code>".format(html.escape(chat.title),
                                                                        mention_html(user.id, user.first_name), args[0]) # MSG_UPDATE_SETTINGS_HTML
        else:
            msg.reply_text("Give me a number as an arg!") # ERR_NO_ARG
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("The current warn limit is {}".format(limit))  # MSG_CURRENT_SETTINGS
    return ""


@user_admin
def set_warn_strength(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("Too many warns will now result in a ban!") # BAN_SETTING
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has enabled strong warns. Users will be banned.".format(html.escape(chat.title),
                                                                            mention_html(user.id, user.first_name)) # BAN_SETTING_HTML

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text("Too many warns will now result in a kick! Users will be able to join again after.")
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has disabled strong warns. Users will only be kicked.".format(html.escape(chat.title),
                                                                                  mention_html(user.id,
                                                                                               user.first_name)) # KICK_SETTING_HTML

        else:
            msg.reply_text("I only understand on/yes/no/off!") # ERR_SET_WRONG_ARG
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text("Warns are currently set to *kick* users when they exceed the limits.",
                           parse_mode=ParseMode.MARKDOWN) # INFO_KICK
        else:
            msg.reply_text("Warns are currently set to *ban* users when they exceed the limits.",
                           parse_mode=ParseMode.MARKDOWN) # INFO_BAN
    return ""


def __stats__():
    return "{} overall warns, across {} chats.\n" \
           "{} warn filters, across {} chats.".format(sql.num_warns(), sql.num_warn_chats(),
                                                      sql.num_warn_filters(), sql.num_warn_filter_chats()) # STATS


def __import_data__(chat_id, data):
    for user_id, count in data.get('warns', {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return "This chat has `{}` warn filters. It takes `{}` warns " \
           "before the user gets *{}*.".format(num_warn_filters, limit, "kicked" if soft_warn else "banned") # CHAT_SETTINGS, KICKED, BANNED


def __help__(update: Update) -> str:
    return "\n - /warns <userhandle>: get a user's number, and reason, of warnings.\n" \
           " - /warnlist: list of all current warning filters\n\n" \
           "*Admin only:*\n" \
           " - /warn <userhandle>: warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.\n" \
           " - /resetwarn <userhandle>: reset the warnings for a user. Can also be used as a reply.\n" \
           " - /addwarn <keyword> <reply message>: set a warning filter on a certain keyword. If you want your keyword to \
            be a sentence, encompass it with quotes, as such: `/addwarn \"very angry\" This is an angry user`. \n" \
            " - /nowarn <keyword>: stop a warning filter\n" \
            " - /warnlimit <num>: set the warning limit\n" \
            " - /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just kick."

__mod_name__ = "Warnings"

WARN_HANDLER = CommandHandler("warn", warn_user, pass_args=True, filters=Filters.group, run_async=True)

RESET_WARN_HANDLER = CommandHandler(["resetwarn", "resetwarns"], reset_warns, pass_args=True, filters=Filters.group,
                                    run_async=True)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn", run_async=True)
MYWARNS_HANDLER = DisableAbleCommandHandler("warns", warns, pass_args=True, filters=Filters.group, run_async=True)
ADD_WARN_HANDLER = CommandHandler("addwarn", add_warn_filter,
                                  filters=Filters.group)  # Dispatcher handler stop - do not async
RM_WARN_HANDLER = CommandHandler(["nowarn", "stopwarn"], remove_warn_filter,
                                 filters=Filters.group) # Dispatcher handler stop - do not async
LIST_WARN_HANDLER = DisableAbleCommandHandler(["warnlist", "warnfilters"], list_warn_filters,
                                              filters=Filters.group, admin_ok=True, run_async=True)
WARN_FILTER_HANDLER = MessageHandler(CustomFilters.has_text & Filters.group, reply_filter, run_async=True)
WARN_LIMIT_HANDLER = CommandHandler("warnlimit", set_warn_limit, pass_args=True, filters=Filters.group, run_async=True)
WARN_STRENGTH_HANDLER = CommandHandler("strongwarn", set_warn_strength, pass_args=True, filters=Filters.group,
                                       run_async=True)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)

