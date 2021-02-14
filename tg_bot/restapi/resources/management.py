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


from time import sleep

from flask import request, abort
from flask_restplus import Namespace, Resource
from flask_restplus._http import HTTPStatus
from telegram import TelegramError

from tg_bot import OWNER_ID, CO_OWNER_ID, SUDO_USERS, dispatcher, LOGGER
import tg_bot.modules.sql.api_sql as sql
from tg_bot.restapi.models.management import *
from tg_bot.restapi.models.users import *
from tg_bot.modules.sql.users_sql import num_chats, get_all_chats, get_all_users, num_users, get_chats_by_member, get_chatname, update_user

api = Namespace("management", description="Administrative Access")

chatnumber = create_chatnumber_model(api)


@api.route("/countchats")
@api.response(200, "Number attached")
@api.response(403, "User is not bot admin.")
@api.response(401, "Unauthorized")
class NumChats(Resource):
    @api.marshal_with(chatnumber)
    def get(self):
        '''Count all chats from database'''
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
            return
        user_id = sql.verify_key(key)
        isowner = user_id is OWNER_ID
        iscowoner = user_id is CO_OWNER_ID
        isudo = user_id in SUDO_USERS
        isadmin = isowner or iscowoner or isudo
        if not isadmin:
            abort(HTTPStatus.FORBIDDEN, "User is not bot admin.")
        else:
            data = {'number': num_chats()}
            return data, HTTPStatus.OK


listchats = create_chatlist_model(api)


@api.route("/listchats")
@api.response(200, "List attached")
@api.response(403, "User is not bot admin.")
@api.response(401, "Unauthorized")
class ListChats(Resource):
    @api.marshal_with(listchats)
    def get(self):
        '''List all chats from database'''
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
            return
        user_id = sql.verify_key(key)
        if user_id is None:
            abort(HTTPStatus.UNAUTHORIZED, "Invalid Key")
        isowner = user_id is OWNER_ID
        iscowoner = user_id is CO_OWNER_ID
        isudo = user_id in SUDO_USERS
        isadmin = isowner or iscowoner or isudo
        if not isadmin:
            abort(HTTPStatus.FORBIDDEN, "User is not bot admin.")
        else:
            chats_sql = get_all_chats()
            chats = []
            for element in chats_sql:
                chats.append([{"id": element.chat_id, "name": element.chat_name}])
            return {"chats": chats}


broadcast = create_broadcast_model(api)


@api.route("/broadcast")
@api.response(200, "Broadcast completed")
@api.response(403, "User is not bot admin.")
@api.response(401, "Unauthorized")
@api.response(400, "Bad Request")
class Broadcast(Resource):
    @api.marshal_with(broadcast)
    def post(self):
        '''Send a message to all chats'''
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
            return
        user_id = sql.verify_key(key)
        if user_id is None:
            abort(HTTPStatus.UNAUTHORIZED, "Invalid Key")
        isowner = user_id is OWNER_ID
        iscowoner = user_id is CO_OWNER_ID
        isudo = user_id in SUDO_USERS
        isadmin = isowner or iscowoner or isudo
        if not isadmin:
            abort(HTTPStatus.FORBIDDEN, "User is not bot admin.")
        else:
            data = request.get_json()
            try:
                to_send = data["message"]
            except KeyError:
                abort(HTTPStatus.BAD_REQUEST, "Bad Request")
            bot = dispatcher.bot
            failed_chats = []
            if len(to_send) >= 2:
                chats = get_all_chats() or []
                failed = 0
                for chat in chats:
                    try:
                        bot.sendMessage(int(chat.chat_id), to_send)
                        sleep(0.1)
                    except TelegramError:
                        failed += 1
                        failed_chats.append([{"id": chat.chat_id, "name": chat.chat_name}])
                        LOGGER.warning("Couldn't send broadcast to %s, group name %s", str(chat.chat_id),
                                       str(chat.chat_name))
                if failed_chats == 0:
                    return {"message": to_send, "failed": failed}
                else:
                    return {"message": to_send, "failed": failed, "failed_chats": failed_chats}


@api.route("/listusers")
@api.response(403, "User is not bot admin.")
@api.response(401, "Unauthorized")
@api.response(400, "Bad Request")
class ListUsers(Resource):
    @api.marshal_with(create_userlist_model(api))
    def get(self):
        '''Get a list of all users known to the bot. Note that this does only include people who messaged the bot at least once.'''
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
            return
        user_id = sql.verify_key(key)
        if user_id is None:
            abort(HTTPStatus.UNAUTHORIZED, "Invalid Key")
        isowner = user_id is OWNER_ID
        iscowoner = user_id is CO_OWNER_ID
        isudo = user_id in SUDO_USERS
        isadmin = isowner or iscowoner or isudo
        if not isadmin:
            abort(HTTPStatus.FORBIDDEN, "User is not bot admin.")
        else:
            users = get_all_users()
            result = []
            list_groups_str = request.args.get('list_groups')
            if list_groups_str:
                if list_groups_str == "True" or list_groups_str == "true":
                    list_groups = True
                if list_groups_str == "False" or list_groups_str == "false":
                    list_groups = False
                if list_groups_str.lower() != "false" and list_groups_str.lower() != "true":
                    abort(HTTPStatus.BAD_REQUEST, "'list_groups' is invalid.")
            else:
                list_groups = False
            for user in users:
                data = {}
                try:
                    data.update({"id": user.user_id})
                    chat = dispatcher.bot.get_chat(user.user_id)
                    if chat.username:
                        data.update({"username": chat.username})
                        data.update({"link": chat.link})
                    data.update({"first_name": chat.first_name})
                    if chat.last_name:
                        data.update({"last_name": chat.last_name})

                    if list_groups:
                        groups = []
                        for group in get_chats_by_member(chat.id):
                            groups.append([{"id": group.chat, "name": get_chatname(group.chat)}])
                        data.update({"groups": groups})

                    result.append(data)
                except TelegramError as excp:
                    if excp.message == 'Chat not found':
                        pass


            return {"users": result}, HTTPStatus.OK


@api.route("/countusers")
@api.response(403, "User is not bot admin.")
@api.response(401, "Unauthorized")
@api.response(400, "Bad Request")
class CountUsers(Resource):
    @api.marshal_with(create_countusers_model(api))
    def get(self):
        '''Count all users from database'''
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
            return
        user_id = sql.verify_key(key)
        isowner = user_id is OWNER_ID
        iscowoner = user_id is CO_OWNER_ID
        isudo = user_id in SUDO_USERS
        isadmin = isowner or iscowoner or isudo
        if not isadmin:
            abort(HTTPStatus.FORBIDDEN, "User is not bot admin.")
        else:
            data = {'number': num_users()}
            return data, HTTPStatus.OK


@api.route("/updateuser")
@api.response(403, "User is not bot admin.")
@api.response(401, "Unauthorized")
@api.response(400, "Bad Request")
class UpdateUser(Resource):
    def post(self):
        '''Update a user inside the db. Use at your own risk!'''
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
            return
        user_id = sql.verify_key(key)
        if user_id is None:
            abort(HTTPStatus.UNAUTHORIZED, "Invalid Key")
        isowner = user_id is OWNER_ID
        iscowoner = user_id is CO_OWNER_ID
        isudo = user_id in SUDO_USERS
        isadmin = isowner or iscowoner or isudo
        if not isadmin:
            abort(HTTPStatus.FORBIDDEN, "User is not bot admin.")
        else:
            data = request.get_json()
            try:
                tochange = int(data["user_id"])
            except KeyError:
                abort(HTTPStatus.BAD_REQUEST, "Bad Request")
            try:
                chat_id = str(data["chat_id"])
            except KeyError:
                chat_id = None
                pass
            try:
                username = str(data["username"])
            except KeyError:
                username = None
                pass

            update_user(tochange, username, chat_id)

