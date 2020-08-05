from typing import List

from telegram import Bot, Update
from telegram.ext import run_async, CommandHandler

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin
import tg_bot.modules.sql.lang_sql as sql


@run_async
@bot_admin
@user_admin
def setlang(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        if txt == "de":
            sql.set_lang(chat_id, "de")
            msg.reply_text("Die Sprache wurde auf 'Deutsch' gesetzt.")
        else:
            sql.set_lang(chat_id, "en")
            msg.reply_text("Set language to English.")
    else:
        msg.reply_text("Bad syntax.")


__mod_name__ = "Languages"

__help__ = "Test\n\nThis is a test."

LANG_HANDLER = CommandHandler("lang", setlang, pass_args=True)

dispatcher.add_handler(LANG_HANDLER)