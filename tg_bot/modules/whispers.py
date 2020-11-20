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

__mod_name__ = "Whisper Messages"

from datetime import datetime
from multiprocessing.context import Process
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, ParseMode, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import run_async, CallbackContext, InlineQueryHandler, MessageHandler, Filters, CallbackQueryHandler, \
    ChosenInlineResultHandler
from telegram.utils.helpers import escape_markdown

from tg_bot import LOGGER, dispatcher
from tg_bot.modules.sql.users_sql import get_chat_members
from tg_bot.modules.users import get_user_id
import tg_bot.modules.sql.whisper_sql as sql

class Whisper():
    receiver = 0
    message = 0

    def __init__(self, receiver, message):
        self.message = message,
        self.receiver = receiver

    def to_string(self):
        return str(self.receiver.id) + str(self.message)


@run_async
def chosen_inline_button(update: Update, context: CallbackContext):
    LOGGER.debug("HIIII!")
    LOGGER.debug(update.chosen_inline_result)
    #sql.add_whisper(update.effective_user.id,)


@run_async
def button(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(update.callback_query.id, "Test", show_alert=True)


@run_async
def process_inline_query(update: Update, context: CallbackContext):
    user = update.effective_user
    query = update.inline_query.query
    results = []
    q = query.split(" ")
    username = q[-1]
    if not username.startswith("@"):
        results.append(InlineQueryResultArticle(
            id=uuid4(),
            title="This does not work.",
            description="You need to specify the user you want to message. If this person does not have one, you can not whisper to them.",
            input_message_content=InputTextMessageContent("Write targets @username at the end of your message in order to send a message.", ParseMode.MARKDOWN)
        ))
    else:
        text = ""
        for element in q:
            if element is not username:
                text = text + element
                try:
                    current_time = datetime.now()
                    receiver = context.bot.get_chat(get_user_id(username))
                    name = receiver.first_name
                    title = "A whisper message to " + name
                    print("Title: " + title)
                    results.append(InlineQueryResultArticle(
                        id=uuid4(),
                        title=title,
                        description="Only they can open it.",
                        input_message_content=InputTextMessageContent(f"🔒 A whisper message to {name}, Only they can open it."),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                            text="show message",
                            callback_data=str(receiver.id + current_time.year + current_time.month + current_time.day + current_time.hour + current_time.minute + current_time.second + current_time.microsecond))
                        ]])
                    ))


                except BadRequest as excp:
                    if excp.message == 'Chat not found':
                        pass
                    else:
                        LOGGER.exception("Error extracting user ID")
    update.inline_query.answer(results)


QUERY_HANDLER = InlineQueryHandler(process_inline_query)
BUTTON_HANDLER = CallbackQueryHandler(button)
INLINE_RESULT_HANDLER = ChosenInlineResultHandler(chosen_inline_button)

dispatcher.add_handler(QUERY_HANDLER)
dispatcher.add_handler(BUTTON_HANDLER)
dispatcher.add_handler(INLINE_RESULT_HANDLER)
