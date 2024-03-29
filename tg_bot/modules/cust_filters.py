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


import re
from typing import Optional

import telegram
from telegram import ParseMode, InlineKeyboardMarkup, Message, Chat
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, DispatcherHandlerStop, CallbackContext
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, LOGGER, DEFAULT_LANG
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import build_keyboard
from tg_bot.modules.helper_funcs.string_handling import split_quotes, button_markdown_parser
from tg_bot.modules.sql import cust_filters_sql as sql

import tg_bot.modules.sql.lang_sql as lang
from tg_bot.strings.string_helper import get_string

HANDLER_GROUP = 10
# BASIC_FILTER_STRING = "*Filters in this chat:*\n" # BASIC_FILTER_STRING


def list_handlers(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    all_handlers = sql.get_chat_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text(get_string("filters", "NO_FILTERS_ACTIVE", lang.get_lang(update.effective_chat.id))) # NO_FILTERS_ACTIVE
        return

    filter_list = get_string("filters", "BASIC_FILTER_STRING", lang.get_lang(update.effective_chat.id))
    for keyword in all_handlers:
        entry = " - `{}`\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=telegram.ParseMode.MARKDOWN)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == get_string("filters", "BASIC_FILTER_STRING", lang.get_lang(update.effective_chat.id)):
        update.effective_message.reply_text(filter_list, parse_mode=telegram.ParseMode.MARKDOWN)


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
def filters(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])
    if len(extracted) < 1:
        return
    # set trigger -> lower, so as to avoid adding duplicate filters with different cases
    keyword = extracted[0].lower()

    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    buttons = []

    # determine what the contents of the filter are - text, image, sticker, etc
    if len(extracted) >= 2:
        offset = len(extracted[1]) - len(msg.text)  # set correct offset relative to command + notename
        content, buttons = button_markdown_parser(extracted[1], entities=msg.parse_entities(), offset=offset)
        content = content.strip()
        if not content:
            msg.reply_text(get_string("filters", "ERR_NO_MESSAGE", lang.get_lang(update.effective_chat.id))) # ERR_NO_MESSAGE
            return

    elif msg.reply_to_message and msg.reply_to_message.sticker:
        content = msg.reply_to_message.sticker.file_id
        is_sticker = True

    elif msg.reply_to_message and msg.reply_to_message.document:
        content = msg.reply_to_message.document.file_id
        is_document = True

    elif msg.reply_to_message and msg.reply_to_message.photo:
        content = msg.reply_to_message.photo[-1].file_id  # last elem = best quality
        is_image = True

    elif msg.reply_to_message and msg.reply_to_message.audio:
        content = msg.reply_to_message.audio.file_id
        is_audio = True

    elif msg.reply_to_message and msg.reply_to_message.voice:
        content = msg.reply_to_message.voice.file_id
        is_voice = True

    elif msg.reply_to_message and msg.reply_to_message.video:
        content = msg.reply_to_message.video.file_id
        is_video = True

    else:
        msg.reply_text(get_string("filters", "ERR_NO_ANSWER", lang.get_lang(update.effective_chat.id))) # ERR_NO_ANSWER
        return

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    sql.add_filter(chat.id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                   buttons)

    msg.reply_text(get_string("filters", "HANDLER_ADDED", lang.get_lang(update.effective_chat.id)).format(keyword)) # HANDLER_ADDED
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
def stop_filter(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    if len(args) < 2:
        return

    chat_filters = sql.get_chat_triggers(chat.id)

    if not chat_filters:
        update.effective_message.reply_text(get_string("filters", "NO_FILTERS_ACTIVE", lang.get_lang(update.effective_chat.id))) # NO_FILTERS_ACTIVE
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat.id, args[1])
            update.effective_message.reply_text(get_string("filters", "HANDLER_REMOVED", lang.get_lang(update.effective_chat.id))) # HANDLER_REMOVED
            raise DispatcherHandlerStop

    update.effective_message.reply_text(get_string("filters", "ERR_NOT_A_FILTER", lang.get_lang(update.effective_chat.id))) # ERR_NOT_A_FILTER


def reply_filter(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            filt = sql.get_filter(chat.id, keyword)
            if filt.is_sticker:
                message.reply_sticker(filt.reply)
            elif filt.is_document:
                message.reply_document(filt.reply)
            elif filt.is_image:
                message.reply_photo(filt.reply)
            elif filt.is_audio:
                message.reply_audio(filt.reply)
            elif filt.is_voice:
                message.reply_voice(filt.reply)
            elif filt.is_video:
                message.reply_video(filt.reply)
            elif filt.has_markdown:
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                try:
                    message.reply_text(filt.reply, parse_mode=ParseMode.MARKDOWN,
                                       disable_web_page_preview=True,
                                       reply_markup=keyboard)
                except BadRequest as excp:
                    if excp.message == "Unsupported url protocol":
                        message.reply_text(get_string("filters", "ERR_BAD_URL", lang.get_lang(update.effective_chat.id))) # ERR_BAD_URL
                    elif excp.message == "Reply message not found":
                        bot.send_message(chat.id, filt.reply, parse_mode=ParseMode.MARKDOWN,
                                         disable_web_page_preview=True,
                                         reply_markup=keyboard)
                    else:
                        message.reply_text(get_string("filters", "ERR_NO_REPLY", lang.get_lang(update.effective_chat.id))) # ERR_NO_REPLY
                        LOGGER.warning(get_string("filters", "ERR_COULDNT_PARSE", DEFAULT_LANG), str(filt.reply)) # ERR_COULDNT_PARSE
                        LOGGER.exception(get_string("filters", "ERR_COULDNT_PARSE_FILTER", DEFAULT_LANG), str(filt.keyword), str(chat.id)) # ERR_COULDNT_PARSE_FILTER

            else:
                # LEGACY - all new filters will have has_markdown set to True.
                message.reply_text(filt.reply)
            break


def __stats__():
    return get_string("filters", "STATS", DEFAULT_LANG).format(sql.num_filters(), sql.num_chats()) # STATS


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return get_string("filters", "CHAT_SETTINGS", lang.get_lang(chat_id)).format(len(cust_filters)) # CHAT_SETTINGS


def __help__(update: Update) -> str:
    return get_string("filters", "HELP", lang.get_lang(update.effective_chat.id))


__mod_name__ = "Filters"


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
FILTER_HANDLER = CommandHandler("filter", filters, run_async=False)
# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
STOP_HANDLER = CommandHandler("stop", stop_filter, run_async=False)
LIST_HANDLER = DisableAbleCommandHandler("filters", list_handlers, run_async=True)
CUST_FILTER_HANDLER = MessageHandler(CustomFilters.has_text, reply_filter, run_async=True)


dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
