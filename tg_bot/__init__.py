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

import logging
import os
import sys

import telegram.ext as tg
from tg_bot.strings.string_helper import get_string

VERSION = 2.1

# Module name
module = "init"

# enable logging
LOGGER = logging.getLogger(__name__)

ENV = bool(os.environ.get('ENV', False))
if ENV:
    DEFAULT_LANG = os.environ.get('DEFAULT_LANG')
    DEBUG = os.environ.get('DEBUG', None)
else:
    from tg_bot.config import Development as Config
    DEFAULT_LANG = Config.DEFAULT_LANG
    DEBUG = Config.DEBUG

LOGFORMAT = "[%(asctime)s | %(levelname)s] %(message)s"
if DEBUG:
    logging.basicConfig(
        format=LOGFORMAT,
        level=logging.DEBUG)
else:
    logging.basicConfig(
        format=LOGFORMAT,
        level=logging.INFO)

LOGGER.info(f"Nemesis v{VERSION}\n"
            f"This program is free software: you can redistribute it and/or modify\n"
            f"it under the terms of the GNU General Public License as published by\n"
            f"the Free Software Foundation, either version 3 of the License, or\n"
            f"(at your option) any later version.")
# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(get_string(module, "ERR_INVALID_PYTHON_VERSION", DEFAULT_LANG)) # ERR_INVALID_PYTHON_VERSION
    quit(1)


if ENV:
    TOKEN = os.environ.get('TOKEN', None)
    try:
        OWNER_ID = int(os.environ.get('OWNER_ID', None))
    except ValueError:
        raise Exception(get_string(module, "ERR_INVALID_OWNER_ID", DEFAULT_LANG)) # ERR_INVALID_OWNER_ID

    try:
        CO_OWNER_ID = int(os.environ.get('CO_OWNER_ID', None))
    except ValueError:
        raise Exception(get_string(module, "ERR_INVALID_OWNER_ID", DEFAULT_LANG)) # ERR_INVALID_OWNER_ID # TODO CHange!

    MESSAGE_DUMP = os.environ.get('MESSAGE_DUMP', None)
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)

    try:
        SUDO_USERS = set(int(x) for x in os.environ.get("SUDO_USERS", "").split())
    except ValueError:
        raise Exception(get_string(module, "ERR_INVALID_SUDO_ID", DEFAULT_LANG)) # ERR_INVALID_SUDO_ID

    try:
        SUPPORT_USERS = set(int(x) for x in os.environ.get("SUPPORT_USERS", "").split())
    except ValueError:
        raise Exception(get_string(module, "ERR_INVALID_SUPPORT_ID", DEFAULT_LANG)) # ERR_INVALID_SUPPORT_ID

    try:
        WHITELIST_USERS = set(int(x) for x in os.environ.get("WHITELIST_USERS", "").split())
    except ValueError:
        raise Exception(get_string(module, "ERR_INVALID_WHITELIST_ID", DEFAULT_LANG)) # ERR_INVALID_WHITELIST_ID

    WEBHOOK = bool(os.environ.get('WEBHOOK', False))
    URL = os.environ.get('URL', "")  # Does not contain token
    PORT = int(os.environ.get('PORT', 5000))
    CERT_PATH = os.environ.get("CERT_PATH")

    DB_URI = os.environ.get('DATABASE_URL')
    DONATION_LINK = os.environ.get('DONATION_LINK')
    LOAD = os.environ.get("LOAD", "").split()
    NO_LOAD = os.environ.get("NO_LOAD", "translation").split()
    DEL_CMDS = bool(os.environ.get('DEL_CMDS', False))
    STRICT_GBAN = bool(os.environ.get('STRICT_GBAN', False))
    WORKERS = int(os.environ.get('WORKERS', 8))
    BAN_STICKER = os.environ.get('BAN_STICKER', 'CAADAgADOwADPPEcAXkko5EB3YGYAg')
    ALLOW_EXCL = os.environ.get('ALLOW_EXCL', False)


else:

    TOKEN = Config.API_KEY
    try:
        OWNER_ID = int(Config.OWNER_ID)
    except ValueError:
        raise Exception(get_string(module, "ERR_CONFIG_INVALID_OWNER_ID", DEFAULT_LANG)) # ERR_CONFIG_INVALID_OWNER_ID

    try:
        CO_OWNER_ID = int(Config.CO_OWNER_ID)
    except ValueError:
        raise Exception(get_string(module, "ERR_CONFIG_INVALID_OWNER_ID", DEFAULT_LANG)) # ERR_CONFIG_INVALID_OWNER_ID # TODO CHANGE!
    MESSAGE_DUMP = Config.MESSAGE_DUMP
    OWNER_USERNAME = Config.OWNER_USERNAME

    try:
        SUDO_USERS = set(int(x) for x in Config.SUDO_USERS or [])
    except ValueError:
        raise Exception(get_string(module, "ERR_CONFIG_INVALID_SUDO_ID", DEFAULT_LANG)) # ERR_CONFIG_INVALID_SUDO_ID

    try:
        SUPPORT_USERS = set(int(x) for x in Config.SUPPORT_USERS or [])
    except ValueError:
        raise Exception(get_string(module, "ERR_CONFIG_INVALID_SUPPORT_ID", DEFAULT_LANG)) # ERR_CONFIG_INVALID_SUPPORT_ID

    try:
        WHITELIST_USERS = set(int(x) for x in Config.WHITELIST_USERS or [])
    except ValueError:
        raise Exception(get_string(module, "ERR_CONFIG_INVALID_WHITELIST_ID", DEFAULT_LANG)) # ERR_CONFIG_INVALID_WHITELIST_ID

    WEBHOOK = Config.WEBHOOK
    URL = Config.URL
    PORT = Config.PORT
    CERT_PATH = Config.CERT_PATH

    DB_URI = Config.SQLALCHEMY_DATABASE_URI
    DONATION_LINK = Config.DONATION_LINK
    LOAD = Config.LOAD
    NO_LOAD = Config.NO_LOAD
    DEL_CMDS = Config.DEL_CMDS
    STRICT_GBAN = Config.STRICT_GBAN
    WORKERS = Config.WORKERS
    BAN_STICKER = Config.BAN_STICKER
    ALLOW_EXCL = Config.ALLOW_EXCL



SUDO_USERS.add(OWNER_ID)
SUDO_USERS.add(CO_OWNER_ID)
LOGGER.info("Owner: %s", OWNER_ID )

updater = tg.Updater(TOKEN, workers=WORKERS, use_context=True)

dispatcher = updater.dispatcher

SUDO_USERS = list(SUDO_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)

# Load at end to ensure all prev variables have been set
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler, CustomRegexHandler

# make sure the regex handler can take extra kwargs
tg.RegexHandler = CustomRegexHandler

if ALLOW_EXCL:
    tg.CommandHandler = CustomCommandHandler
