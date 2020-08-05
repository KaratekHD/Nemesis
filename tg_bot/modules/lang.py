from telegram import Bot, Update
from telegram.ext import run_async, CommandHandler

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin


@run_async
@bot_admin
@user_admin
def setlang(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    message.reply_message("Test")

__mod_name__ = "Languages"

__help__ = "Test\n\nThis is a test."

LANG_HANDLER = CommandHandler("lang", setlang, pass_args=True)

dispatcher.add_handler(LANG_HANDLER)