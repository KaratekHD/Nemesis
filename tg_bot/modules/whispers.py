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


__mod_name__ = "Whisper Messages"

from datetime import datetime
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, ParseMode, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import CallbackContext, InlineQueryHandler, CallbackQueryHandler, \
    ChosenInlineResultHandler

from tg_bot import LOGGER, dispatcher
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


LIST = []


def chosen_inline_button(update: Update, context: CallbackContext):
    result = update.chosen_inline_result
    query = result.query
    q = query.split(" ")
    username = q[-1]
    receiver_id = get_user_id(username)
    sender_id = update.effective_user.id
    text = ""
    for element in q:
        if element is not username:
            text = text + " " + element
    sql.add_whisper(sender_id, receiver_id, text, sql.get_whispers(context.bot.id))
    sql.increase_whisper_ids(context.bot.id)


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    print(query)
    id = query.data.replace("whisper_", "")
    whisper_message = sql.get_message(int(id))
    sender = whisper_message.sender_id
    receiver = whisper_message.receiver_id
    message = whisper_message.message
    if update.effective_user.id not in (sender, receiver):
        context.bot.answer_callback_query(update.callback_query.id,
                                          "You are not permitted to read this message.",
                                          show_alert=False)
        return
    else:
        context.bot.answer_callback_query(update.callback_query.id, message, show_alert=True)


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
        for element in q:
            if element is not username:
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
                        input_message_content=InputTextMessageContent(f"🔒 A whisper message to @{receiver.username}, Only they can open it."),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                            text="show message",
                            callback_data="whisper_" + str(sql.get_whispers(context.bot.id)))
                        ]])
                    ))


                except BadRequest as excp:
                    if excp.message == 'Chat not found':
                        pass
                    else:
                        LOGGER.exception("Error extracting user ID")
    update.inline_query.answer(results)


QUERY_HANDLER = InlineQueryHandler(process_inline_query, run_async=True)
BUTTON_HANDLER = CallbackQueryHandler(button, pattern=r"whisper", run_async=True)
INLINE_RESULT_HANDLER = ChosenInlineResultHandler(chosen_inline_button, run_async=True)

dispatcher.add_handler(QUERY_HANDLER)
dispatcher.add_handler(BUTTON_HANDLER)
dispatcher.add_handler(INLINE_RESULT_HANDLER)
