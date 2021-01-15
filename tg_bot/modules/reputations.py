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


from telegram import Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, CommandHandler

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleMessageHandler
import tg_bot.modules.sql.reputation_sql as sql
import tg_bot.modules.sql.reputation_settings_sql as settings



def increase(update: Update, context: CallbackContext):
    msg = update.effective_message
    user1 = update.effective_user
    chat = update.effective_chat
    if not settings.chat_should_reputate(chat.id):
        return
    if msg.reply_to_message:
        user2 = msg.reply_to_message.from_user
        if not settings.user_should_reputate(user1.id):
            msg.reply_text("You have opted out of reputations, so you are not able to change others reputation neither.")
            return
        if not settings.user_should_reputate(user2.id):
            msg.reply_text(f"{user2.full_name} opted out of reputations,"
                           f" so you are not able to change their reputation.")
            return
        if user1.id != user2.id:
            LOGGER.debug(f"{user2.id} : {sql.get_reputation(chat.id, user2.id)}")
            sql.increase_reputation(chat.id, user2.id)
            new_msg = msg.reply_text(f"<b>{user1.first_name}</b> ({sql.get_reputation(chat.id, user1.id)}) has increased reputation of <b>{user2.first_name}</b> ({sql.get_reputation(chat.id, user2.id)})", parse_mode=ParseMode.HTML).message_id
            try:
                context.bot.delete_message(chat.id, sql.get_latest_rep_message(chat.id))
            except BadRequest as err:
                LOGGER.debug("Could not delete that message.")
            sql.set_latest_rep_message(chat.id, new_msg)


def decrease(update: Update, context: CallbackContext):
    msg = update.effective_message
    user1 = update.effective_user
    chat = update.effective_chat
    if not settings.chat_should_reputate(chat.id):
        return
    if msg.reply_to_message:
        user2 = msg.reply_to_message.from_user
        if not settings.user_should_reputate(user1.id):
            msg.reply_text("You have opted out of reputations, so you are not able to change others reputation neither.")
            return
        if not settings.user_should_reputate(user2.id):
            msg.reply_text(f"{user2.full_name} opted out of reputations,"
                           f" so you are not able to change their reputation.")
            return
        if user1.id != user2.id:
            LOGGER.debug(f"{user2.id} : {sql.get_reputation(chat.id, user2.id)}")
            sql.decrease_reputation(chat.id, user2.id)
            new_msg = msg.reply_text(
                f"<b>{user1.first_name}</b> ({sql.get_reputation(chat.id, user1.id)}) has decreased reputation of <b>{user2.first_name}</b> ({sql.get_reputation(chat.id, user2.id)})",
                parse_mode=ParseMode.HTML).message_id
            try:
                context.bot.delete_message(chat.id, sql.get_latest_rep_message(chat.id))
            except BadRequest as err:
                LOGGER.debug("Could not delete that message.")
            sql.set_latest_rep_message(chat.id, new_msg)


def reputation(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                settings.set_user_setting(chat.id, True)
                msg.reply_text("Turned on reputation!")

            elif args[0] in ("no", "off"):
                settings.set_user_setting(chat.id, False)
                msg.reply_text("Turned off reputation!")
        else:
            msg.reply_text("Your current reputation preference is: `{}`".format(settings.user_should_reputate(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                settings.set_chat_setting(chat.id, True)
                msg.reply_text("Turned on reputation! Users will now be able to vote on each others messages, except "
                               "if they opted out.")

            elif args[0] in ("no", "off"):
                settings.set_chat_setting(chat.id, False)
                msg.reply_text("Turned off reputation!")
        else:
            msg.reply_text("This chat's current setting is: `{}`".format(settings.chat_should_reputate(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)


def __help__(update: Update) -> str:
    return "" \
           " - /reputation: manage this chats reputation settings, as well as yours.\n" \
           " - +: Increase someones reputation.\n" \
           " - -: Decrease someones reputation."


def __chat_settings__(chat_id, user_id):
    return "Reputations is enabled in this chat, change with /reputation: `{}`".format(
       settings.chat_should_reputate(chat_id))


def __user_settings__(user_id):
    return "Your current reputations setting is `{}`.\nChange this with /reputation in PM.".format(
        settings.user_should_reputate(user_id))


INCREASE_MESSAGE_HANDLER = DisableAbleMessageHandler(Filters.regex(r"^\+$"), increase, friendly="increase",
                                                     run_async=True)

dispatcher.add_handler(INCREASE_MESSAGE_HANDLER)
DECREASE_MESSAGE_HANDLER = DisableAbleMessageHandler(Filters.regex(r"^\-$"), decrease, friendly="decrease",
                                                     run_async=True)
dispatcher.add_handler(DECREASE_MESSAGE_HANDLER)
INCREASE_MESSAGE_HANDLER2 = DisableAbleMessageHandler(Filters.regex(r"^\👍$"), increase, friendly="increase",
                                                     run_async=True)

dispatcher.add_handler(INCREASE_MESSAGE_HANDLER2)
DECREASE_MESSAGE_HANDLER2 = DisableAbleMessageHandler(Filters.regex(r"^\👎$"), decrease, friendly="decrease",
                                                     run_async=True)
dispatcher.add_handler(DECREASE_MESSAGE_HANDLER2)
SETTINGS_HANDLER = CommandHandler("reputation", reputation, run_async=True)
dispatcher.add_handler(SETTINGS_HANDLER)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat_latest_messages(old_chat_id, new_chat_id)


__mod_name__ = "Reputations"
