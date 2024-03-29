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


from functools import wraps
from typing import Optional

from tg_bot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Bot, Update, ParseMode, Message, Chat
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler, run_async, CallbackContext
    from telegram.utils.helpers import escape_markdown

    from tg_bot import dispatcher, LOGGER
    from tg_bot.modules.helper_funcs.chat_status import user_admin
    from tg_bot.modules.sql import log_channel_sql as sql


    def loggable(func):
        @wraps(func)
        def log_action(update: Update, context: CallbackContext, *args, **kwargs):
            bot = context.bot
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat  # type: Optional[Chat]
            message = update.effective_message  # type: Optional[Message]
            if result:
                if chat.type == chat.SUPERGROUP and chat.username:
                    result += "\n<b>Link:</b> " \
                              "<a href=\"http://telegram.me/{}/{}\">click here</a>".format(chat.username,
                                                                                           message.message_id) # LINK
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(bot, log_chat, chat.id, result)
            elif result == "":
                pass
            else:
                LOGGER.warning("%s was set as loggable, but had no return statement.", func) # ERR_MISSING_RETURN_STATE

            return result

        return log_action


    def send_log(bot: Bot, log_chat_id: str, orig_chat_id: str, result: str):
        try:
            bot.send_message(log_chat_id, result, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(orig_chat_id, "This log channel has been deleted - unsetting.") # ERR_LOG_CHANNEL_DELETED
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                bot.send_message(log_chat_id, result + "\n\nFormatting has been disabled due to an unexpected error.") # ERR_IN_FORMATING


    @user_admin
    def logging(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                "This group has all it's logs sent to: {} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                         log_channel),
                parse_mode=ParseMode.MARKDOWN) # CURRENT_LOG

        else:
            message.reply_text("No log channel has been set for this group!") # NO_LOG


    @user_admin
    def setlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == chat.CHANNEL:
            message.reply_text("Now, forward the /setlog to the group you want to tie this channel to!") # MSG_FORWARD

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("Error deleting message in log channel. Should work anyway though.") # ERR_CANT_DELETE

            try:
                bot.send_message(message.forward_from_chat.id,
                                 "This channel has been set as the log channel for {}.".format(
                                     chat.title or chat.first_name)) # LOG_SET
            except Unauthorized as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    bot.send_message(chat.id, "Successfully set log channel!") # SUCCESS_SET
                else:
                    LOGGER.exception("ERROR in setting the log channel.") # ERR_GENERAL

            bot.send_message(chat.id, "Successfully set log channel!") # SUCCESS_SET

        else:
            message.reply_text("The steps to set a log channel are:\n"
                               " - add bot to the desired channel\n"
                               " - send /setlog to the channel\n"
                               " - forward the /setlog to the group\n") # STEPS


    @user_admin
    def unsetlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(log_channel, "Channel has been unlinked from {}".format(chat.title)) # SUCCESS_UNSET_CHANNEL
            message.reply_text("Log channel has been un-set.") # SUCCESS_UNSET

        else:
            message.reply_text("No log channel has been set yet!") # ERR_NO_LOG


    def __stats__():
        return "{} log channels set.".format(sql.num_logchannels())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return "This group has all it's logs sent to: {} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                            log_channel) # SETTINGS
        return "No log channel is set for this group!" # SETTINGS_CLEAN


    def __help__(update: Update) -> str:
        return "\n*Admin only:*\n" \
               " - /logchannel: get log channel info\n" \
               " - /setlog: set the log channel.\n" \
               " - /unsetlog: unset the log channel.\n\n" \
               "Setting the log channel is done by:\n" \
               " - adding the bot to the desired channel (as an admin!)\n" \
               " - sending /setlog in the channel\n" \
               " - forwarding the /setlog to the group"
# HELP

    def not_supported(update: Update, context: CallbackContext):
        update.effective_message.reply_text("Log Channels are <b>not supported</b> anymore as of Nemesis v2.2. "
                                            "If you'd like to bring them back, see "
                                            "<a href=\"https://karatek.net/Projects_and_Services/Services/Nemesis/#get-involved\">the get involved section</a> "
                                            "in our wiki.", parse_mode=ParseMode.HTML)

    __mod_name__ = "Log Channels" # MODULE_NAME

    LOG_HANDLER = CommandHandler("logchannel", not_supported, run_async=True)
    SET_LOG_HANDLER = CommandHandler("setlog", not_supported, run_async=True)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", not_supported, run_async=True)

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func
