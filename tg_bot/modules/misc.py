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
import json
import os
import random
from datetime import datetime
from typing import Optional, List

import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters, CallbackContext
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, CO_OWNER_ID, LOGGER
from tg_bot.__main__ import GDPR
from tg_bot.__main__ import STATS, USER_INFO
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.strings.string_helper import get_string, get_random_string

import tg_bot.modules.sql.lang_sql as lang



GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"


@run_async
def runs(update: Update, context: CallbackContext):
    update.effective_message.reply_text(get_random_string("runs", lang.get_lang(update.effective_chat.id)))


@run_async
def nice(update: Update, context: CallbackContext):
    dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dir = f"{dir}/misc"
    if not os.path.isdir(dir):
        os.mkdir(dir)
    dir = f"{dir}/nice"
    if not os.path.isdir(dir):
            os.mkdir(dir)
    user = update.effective_user
    if not os.path.isfile(f"{dir}/{user.id}.json"):
        update.effective_message.reply_text(get_random_string("nice", lang.get_lang(update.effective_chat.id)))
    else:
        # This is gonna check for a file for the sender, and if it exists, it is gonna decide randomly whether it should
        # be used or not. If it is used, it is gonna send with a line from that file instead of the normal ones.
        use = bool(random.choice([True, False]))
        print(use)
        if use:
            path = f"{dir}/{user.id}.json"
            with open(path) as f:
                data = json.load(f)
            i = len(data)
            r = str(random.randint(1, i))
            update.effective_message.reply_text(data[r])
        else:
            update.effective_message.reply_text(get_random_string("nice", lang.get_lang(update.effective_chat.id)))


@run_async
def slap(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = get_random_string("slap", "en")
    item = get_random_string("items", "en")
    hit = get_random_string("hit", "en")
    throw = get_random_string("throws", "en")

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


@run_async
def get_bot_ip(update: Update, context: CallbackContext):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                get_string("misc", "MSG_ID_WITH_FORWARD", lang.get_lang(update.effective_chat.id)).format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id),
                parse_mode=ParseMode.MARKDOWN) # MSG_ID_WITH_FORWARD
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_text(get_string("misc", "MSG_ID_USER", lang.get_lang(update.effective_chat.id)).format(escape_markdown(user.first_name), user.id),
                                                parse_mode=ParseMode.MARKDOWN) # MSG_ID_USER
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text(get_string("misc", "MSG_YOUR_ID", lang.get_lang(update.effective_chat.id)).format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN) # MSG_YOUR_ID

        else:
            update.effective_message.reply_text(get_string("misc", "MSG_GROUP_ID", lang.get_lang(update.effective_chat.id)).format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN) # MSG_GROUP_ID


@run_async
def info(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        msg.reply_text(get_string("misc", "ERR_CANT_EXTRACT_USER", lang.get_lang(update.effective_chat.id))) # ERR_CANT_EXTRACT_USER
        return

    else:
        return

    text = get_string("misc", "MSG_USER_INFO_GENERAL", lang.get_lang(update.effective_chat.id)).format(user.id, html.escape(user.first_name)) # MSG_USER_INFO_GENERAL

    if user.last_name:
        text += get_string("misc", "MSG_USER_INFO_LAST_NAME", lang.get_lang(update.effective_chat.id)).format(html.escape(user.last_name)) # MSG_USER_INFO_LAST_NAME

    if user.username:
        text += get_string("misc", "MSG_USER_INFO_USERNAME", lang.get_lang(update.effective_chat.id)).format(html.escape(user.username)) # MSG_USER_INFO_USERNAME

    text += get_string("misc", "MSG_USER_INFO_LINK", lang.get_lang(update.effective_chat.id)).format(mention_html(user.id, "link")) # MSG_USER_INFO_LINK

    if user.id == OWNER_ID:
        text += get_string("misc", "MSG_USER_INFO_OWNER", lang.get_lang(update.effective_chat.id)) # MSG_USER_INFO_OWNER


    else:
        if user.id == CO_OWNER_ID:
            text += get_string("misc", "MSG_USER_INFO_CO_OWNER", lang.get_lang(update.effective_chat.id)) # MSG_USER_INFO_CO_OWNER
        elif user.id == 1048402045:
            text += "\n\nThis person is a good friend of my owner, so you can trust her without a doubt."
        else:
            if user.id in SUDO_USERS:
                text += get_string("misc", "MSG_USER_INFO_SUDO", lang.get_lang(update.effective_chat.id)) # MSG_USER_INFO_SUDO
            else:

                if user.id in SUPPORT_USERS:
                    text += get_string("misc", "MSG_USER_INFO_SUPPORT", lang.get_lang(update.effective_chat.id)) # MSG_USER_INFO_SUPPORT

                if user.id in WHITELIST_USERS:
                    text += get_string("misc", "MSG_USER_INFO_WHITELIST", lang.get_lang(update.effective_chat.id)) # MSG_USER_INFO_WHITELIST

    for mod in USER_INFO:
        mod_info = mod.__user_info__(user.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def get_time(update: Update, context: CallbackContext):
    # This does not work
    args = context.args
    bot = context.bot
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text(get_string("misc", "MSG_BANHAMMER_TIME", lang.get_lang(update.effective_chat.id))) # MSG_BANHAMMER_TIME
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location))

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get('status') == 'OK':
            lat = loc['results'][0]['geometry']['location']['lat']
            long = loc['results'][0]['geometry']['location']['lng']

            country = None
            city = None

            address_parts = loc['results'][0]['address_components']
            for part in address_parts:
                if 'country' in part['types']:
                    country = part.get('long_name')
                if 'administrative_area_level_1' in part['types'] and not city:
                    city = part.get('long_name')
                if 'locality' in part['types']:
                    city = part.get('long_name')

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().timestamp())
            res = requests.get(GMAPS_TIME, params=dict(location="{},{}".format(lat, long), timestamp=timenow))
            if res.status_code == 200:
                offset = json.loads(res.text)['dstOffset']
                timestamp = json.loads(res.text)['rawOffset']
                time_there = datetime.fromtimestamp(timenow + timestamp + offset).strftime("%H:%M:%S on %A %d %B")
                update.message.reply_text(get_string("misc", "MSG_TIME", lang.get_lang(update.effective_chat.id)).format(time_there, location)) # MSG_TIME


@run_async
def echo(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@run_async
def gdpr(update: Update, context: CallbackContext):
    update.effective_message.reply_text(get_string("misc", "MSG_DELETING_DATA", lang.get_lang(update.effective_chat.id))) # MSG_DELETING_DATA
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text(get_string("misc", "MSG_DELETING_SUCCESS", lang.get_lang(update.effective_chat.id)), parse_mode=ParseMode.MARKDOWN) # MSG_DELETING_SUCCESS


@run_async
def markdown_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(get_string("misc", "MARKDOWN_HELP", lang.get_lang(update.effective_chat.id)), parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(get_string("misc", "MARKDOWN_HELP_FORWARD", lang.get_lang(update.effective_chat.id))) # MARKDOWN_HELP_FORWARD
    update.effective_message.reply_text(get_string("misc", "MARKDOWN_HELP_FORWARD_MSG", lang.get_lang(update.effective_chat.id))) # MARKDOWN_HELP_FORWARD_MSG


@run_async
def stats(update: Update, context: CallbackContext):
    update.effective_message.reply_text(get_string("misc", "CURRENT_STATS", lang.get_lang(update.effective_chat.id)) + "\n".join([mod.__stats__() for mod in STATS]))


# /ip is for private use
def __help__(update: Update) -> str:
    return "\n - /id: get the current group id. If used by replying to a message, gets that user's id.\n" \
           " - /runs: reply a random string from an array of replies.\n" \
           " - /slap: slap a user, or get slapped if not a reply.\n" \
           " - /info: get information about a user.\n" \
           " - /gdpr: deletes your information from the bot's database. Private chats only.\n\n" \
           " - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats."

__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=CustomFilters.admin_filter)

TIME_HANDLER = CommandHandler("time", get_time)

RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap)
INFO_HANDLER = DisableAbleCommandHandler("info", info)
NICE_HANDLER = DisableAbleCommandHandler("nice", nice)

ECHO_HANDLER = CommandHandler("echo", echo, filters=CustomFilters.admin_filter)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=CustomFilters.sudo_filter)
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)

dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
# dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(NICE_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
