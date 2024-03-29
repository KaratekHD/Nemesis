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


import datetime
import importlib
import os
import re
import tg_bot.modules.sql.lang_sql as lang

from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.ext.dispatcher import run_async, DispatcherHandlerStop
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, updater, TOKEN, WEBHOOK, OWNER_ID, CERT_PATH, PORT, URL, LOGGER, \
    ALLOW_EXCL, DEFAULT_LANG, VERSION

from tg_bot.strings.string_helper import  get_string

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from tg_bot.modules import ALL_MODULES
from tg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.misc import paginate_modules
from tg_bot.modules.helper_funcs.misc import is_module_loaded
from multiprocessing import Process


IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("tg_bot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__
    LOGGER.debug("Loaded Module {}".format(imported_module.__mod_name__))
    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception(get_string("main", "NO_TWO_MODULES", DEFAULT_LANG)) # NO_TWO_MODULES

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module




@run_async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(chat_id=chat_id,
                                text=text,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=keyboard)


@run_async
def test(bot: Bot, update: Update):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text(get_string("main", "EDITED_MESSAGE", update.effective_chat.id)) # EDITED_MESSAGE
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    if update.effective_chat.type == "private":
        args = context.args
        if len(args) >= 1:
            if args[0].lower() == "help":
                HELP_STRINGS = get_string("main", "HELP_STRINGS", lang.get_lang(update.effective_chat.id))
                send_help(update.effective_chat.id, HELP_STRINGS)

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
                get_string("main", "PM_START_TEXT", lang.get_lang(update.effective_chat.id)).format(escape_markdown(first_name), escape_markdown(context.bot.first_name), OWNER_ID),
                parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text(get_string("main", "START_IN_GROUP", lang.get_lang(update.effective_chat.id))) # START_IN_GROUP


# for test purposes
def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        HELP_STRINGS = get_string("main", "HELP_STRINGS", lang.get_lang(update.effective_chat.id)).format(
            dispatcher.bot.first_name,
            "" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n")
        if mod_match:
            module = mod_match.group(1)

            text = HELP_STRINGS.format(HELPABLE[module].__mod_name__) \
                   + HELPABLE[module].__help__(update) # HELP_FOR_MODULE
            query.message.reply_text(text=text,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         [[InlineKeyboardButton(text="Back", callback_data="help_back")]]))

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.reply_text(HELP_STRINGS,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(curr_page - 1, HELPABLE, "help")))

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.reply_text(HELP_STRINGS,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(next_page + 1, HELPABLE, "help")))

        elif back_match:
            query.message.reply_text(text=HELP_STRINGS,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")))

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message == "Message is not modified": # ERR_MSG_NOT_MODIFIED
            pass
        elif excp.message == "Query_id_invalid": # ERR_QUERY_ID_INVALID
            pass
        elif excp.message == "Message can't be deleted": # ERR_MSG_CANT_DELETE
            pass
        else:
            LOGGER.exception(get_string("main", "ERR_EXCP_HELP_BUTTONS", DEFAULT_LANG), str(query.data)) # ERR_EXCP_HELP_BUTTONS


@run_async
def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_text(get_string("main", "PM_FOR_HELP", lang.get_lang(update.effective_chat.id)),
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text=get_string("main", "PM_FOR_HELP_BUTTON", lang.get_lang(chat.id)),
                                                                       url="t.me/{}?start=help".format(
                                                                           context.bot.username))]])) # PM_FOR_HELP and PM_FOR_HELP_BUTTON
        return

    if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = get_string("main", "HELP_FOR_MODULE_AVAILABLE", lang.get_lang(update.effective_chat.id)).format(HELPABLE[module].__mod_name__) \
                   + HELPABLE[module].__help__(update) # HELP_FOR_MODULE_AVAILABLE
        send_help(chat.id, text, InlineKeyboardMarkup([[InlineKeyboardButton(text="Back", callback_data="help_back")]]))

    else:
        send_help(chat.id, get_string("main", "HELP_STRINGS", lang.get_lang(update.effective_chat.id)).format(dispatcher.bot.first_name,
                       "" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n"))


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id)) for mod in USER_SETTINGS.values())
            dispatcher.bot.send_message(user_id, get_string("main", "CURRENT_SETTINGS", lang.get_lang(user_id)) + "\n\n" + settings,
                                        parse_mode=ParseMode.MARKDOWN) # CURRENT_SETTINGS

        else:
            dispatcher.bot.send_message(user_id, get_string("main", "ERR_NO_USER_SETTINGS", lang.get_lang(user_id)),
                                        parse_mode=ParseMode.MARKDOWN) # ERR_NO_USER_SETTINGS

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(user_id,
                                        text=get_string("main", "Q_SETTINGS_WHICH_MODULE", lang.get_lang(chat_id)).format(
                                            chat_name),
                                        reply_markup=InlineKeyboardMarkup(
                                            paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id))) # Q_SETTINGS_WHICH_MODULE
        else:
            dispatcher.bot.send_message(user_id, get_string("main", "Q_SETTINGS_TO_GROUP", lang.get_lang(user_id)),
                                        parse_mode=ParseMode.MARKDOWN)


@run_async
def settings_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = get_string("main", "MODULE_SETTINGS", lang.get_lang(chat_id)).format(escape_markdown(chat.title),
                                                                                     CHAT_SETTINGS[
                                                                                         module].__mod_name__) + \
                   CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id) # MODULE_SETTINGS
            query.message.reply_text(text=text,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         [[InlineKeyboardButton(text="Back",
                                                                callback_data="stngs_back({})".format(chat_id))]]))

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(get_string("main", "LOT_OF_SETTINGS", lang.get_lang(chat_id)).format(chat.title),
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(curr_page - 1, CHAT_SETTINGS, "stngs",
                                                          chat=chat_id))) # LOT_OF_SETTINGS

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(get_string("main", "LOT_OF_SETTINGS", lang.get_lang(chat_id)).format(chat.title),
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(next_page + 1, CHAT_SETTINGS, "stngs",
                                                          chat=chat_id))) # LOT_OF_SETTINGS

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(text=get_string("main", "LOT_OF_SETTINGS", lang.get_lang(chat_id)).format(escape_markdown(chat.title)),
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(paginate_modules(0, CHAT_SETTINGS, "stngs",
                                                                                        chat=chat_id))) # LOT_OF_SETTINGS

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message == "Message is not modified": # ERR_MSG_NOT_MODIFIED
            pass
        elif excp.message == "Query_id_invalid": # ERR_QUERY_ID_INVALID
            pass
        elif excp.message == "Message can't be deleted": # ERR_MSG_CANT_DELETE
            pass
        else:
            LOGGER.exception(get_string("main", "ERR_EXCP_SETTINGS_BUTTONS", DEFAULT_LANG), str(query.data)) # ERR_EXCP_SETTINGS_BUTTONS


@run_async
def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = msg.text.split(None, 1)

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = get_string("main", "CLICK_HERE_FOR_SETTINGS", lang.get_lang(chat.id)) # CLICK_HERE_FOR_SETTINGS
            msg.reply_text(text,
                           reply_markup=InlineKeyboardMarkup(
                               [[InlineKeyboardButton(text=get_string("main", "SETTINGS", lang.get_lang(chat.id)),
                                                      url="t.me/{}?start=stngs_{}".format(
                                                          bot.username, chat.id))]])) # SETTINGS
        else:
            text = get_string("main", "YOUR_SETTINGS", lang.get_lang(chat.id)) # YOUR_SETTINGS

    else:
        send_settings(chat.id, user.id, True)


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info(get_string("main", "MIGRATING", DEFAULT_LANG), str(old_chat), str(new_chat)) # MIGRATING
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info(get_string("main", "MIGRATING_SUCCESS", DEFAULT_LANG)) # MIGRATING_SUCCESS
    raise DispatcherHandlerStop


@run_async
def about(update: Update, context: CallbackContext):
    DEVELOPMENT = " - [KaratekHD](https://github.com/KaratekHD)\n" \
                                        " - [PaulSonOfLars](https://github.com/PaulSonOfLars)\n" \
                                        " - [Juliano Dorneles dos Santos](https://github.com/jvlianodorneles)\n" \
                                        " - [TermoZour](https://github.com/TermoZour)\n" \
                                        " - [Spherical Flying Kat](https://github.com/ATechnoHazard)\n" \
                                        " - [Rhyse Simpson](https://github.com/skittles9823)\n" \
                                        " - [Harsh Shandilya](https://github.com/msfjarvis)\n" \
                                        " - [Alif Fathur](https://github.com/herobuxx)\n" \
                                        " - [anirudhgupta109](https://github.com/anirudhgupta109)\n" \
                                        " - [Shrimadhav U K](https://github.com/SpEcHiDe)\n" \
                                        " - [Rohan](https://github.com/Rohk25)\n" \
                                        " - [Lenin AGC](https://github.com/IGUNUBLUE)\n" \
                                        " - [Maverick](https://github.com/1maverick1)\n\n"

    TRANSLATION = " - [Luna Loony](https://t.me/Luna_loony) - Quality Control\n" \
                                        " - [Nyx](https://t.me/HerrscherinNyx) - Translation\n" \
                                        " - [MeiFel10](https://crowdin.com/profile/MeiFel10) - Translation\n" \
                                        " - [KaratekHD](https://github.com/KaratekHD) - Manager\n\n"

    PRODUCTION = " - [KaratekHD](https://github.com/KaratekHD) - Owner\n" \
                                        " - [Severus Snape](https://t.me/GenosseSeverus) - Co-Owner\n" \
                                        " - [Luna Loony](https://t.me/Luna_loony) - Admin\n"

    update.effective_message.reply_text("*OpenGM v{} - Powerful open-source group manager*\n"
                                        "Copyright (C) 2017 - 2019 Paul Larsen\n"
                                        "Copyright (C) 2019 - 2023 KaratekHD\n\n"
                                        "This program is free software: you can redistribute it and/or modify "
                                        "it under the terms of the GNU General Public License as published by "
                                        "the Free Software Foundation, either version 3 of the License, or"
                                        "(at your option) any later version.\n\n"
                                        "*Contributors:*\n\n"
                                        "*Development:*\n"
                                        "{}"
                                        "*Translation*\n"
                                        "{}"
                                        "*Production*\n"
                                        "{}".format(VERSION, DEVELOPMENT, TRANSLATION, PRODUCTION), parse_mode=ParseMode.MARKDOWN)


def load_api():
        if is_module_loaded("rest"):
            import tg_bot.restapi as restapi
            LOGGER.debug("Loading API...")
            LOGGER.warning("BE CAREFULLY!")
            LOGGER.warning("Rest API is still in early development and considered unstable. Only enable it if you "
                           "really know what you're doing. You have been warned.")
            p = Process(target=restapi.app.run())
            p.start()
            p.join()
        else:
            LOGGER.debug("Not loading API")


def main():
    LOGGER.debug(os.getcwd())
    # test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_")

    settings_handler = CommandHandler("settings", get_settings)
    about_handler = CommandHandler("about", about, pass_args=True)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(about_handler)

    # dispatcher.add_error_handler(error_callback)


    if WEBHOOK:
        LOGGER.info(get_string("main", "WEBHOOKS", DEFAULT_LANG)) # WEBHOOKS
        updater.start_webhook(listen="127.0.0.1",
                              port=PORT,
                              url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN,
                                    certificate=open(CERT_PATH, 'rb'))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info(get_string("main", "LONG_POLLING", DEFAULT_LANG)) # LONG_POLLING
        updater.start_polling(timeout=15, read_latency=4)
    load_api()
    updater.idle()


CHATS_CNT = {}
CHATS_TIME = {}


def process_update(self, update):
    # An error happened while polling
    if isinstance(update, TelegramError):
        try:
            self.dispatch_error(None, update)
        except Exception:
            self.logger.exception(get_string("main", "ERR_UNKNOWN", DEFAULT_LANG)) # ERR_UNKNOWN
        return

    now = datetime.datetime.utcnow()

    cnt = CHATS_CNT.get(update.effective_chat.id, 0)

    t = CHATS_TIME.get(update.effective_chat.id, datetime.datetime(1970, 1, 1))
    if t and now > t + datetime.timedelta(0, 1):
        CHATS_TIME[update.effective_chat.id] = now
        cnt = 0
    else:
        cnt += 1

    if cnt > 10:
        return

    CHATS_CNT[update.effective_chat.id] = cnt


    for group in self.groups:
        try:
            for handler in (x for x in self.handlers[group] if x.check_update(update)):
                handler.handle_update(update, self, handler.check_update(update))
                break

        # Stop processing with any other handler.
        except DispatcherHandlerStop:
            self.logger.debug(get_string("main", "ERR_DISPATCHERHANDLERSTOP", DEFAULT_LANG)) # ERR_DISPATCHERHANDLERSTOP
            break

        # Dispatch any error.
        except TelegramError as te:
            self.logger.warning(get_string("main", "ERR_TELEGRAM", DEFAULT_LANG)) # ERR_TELEGRAM

            try:
                self.dispatch_error(update, te)
            except DispatcherHandlerStop:
                self.logger.debug(get_string("main", "ERR_ERRHANDLER", DEFAULT_LANG)) # ERR_ERRHANDLER
                break
            except Exception:
                self.logger.exception(get_string("main", "ERR_UNKNOWN", DEFAULT_LANG)) # ERR_UNKNOWN

        # Errors should not stop the thread.
        except Exception:
            self.logger.exception(get_string("main", "ERR_UPDATE_UNKNOWN", DEFAULT_LANG)) # ERR_UPDATE_UNKNOWN




if __name__ == '__main__':
    LOGGER.info(get_string("main", "MODULES_LOADED", DEFAULT_LANG) + str(ALL_MODULES)) # MODULES_LOADED
    main()
