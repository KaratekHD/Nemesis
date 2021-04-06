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


from http import HTTPStatus

from flask import request, abort
from flask_restplus import Namespace, Resource
from telegram import TelegramError

from tg_bot import dispatcher
from tg_bot.modules.sql import api_sql
import tg_bot.modules.sql.users_sql as user_sql
import tg_bot.modules.sql.mute as mute_sql
import tg_bot.restapi.models.modules.admin as admin_model

api = Namespace("admin", description="Functions designed to manage basic things inside a group.")


@api.route("/<id>")
@api.param('id', 'The group identifier')
@api.response(400, "Bad Request")
@api.response(404, 'Chat not found.')
@api.response(403, "User is not permitted to view this chat.")
@api.response(401, "Unauthorized")
@api.response(410, "Bot is not a member of the chat (anymore).")
class Admins(Resource):
    @api.marshal_with(admin_model.create_chat_model(api))
    @staticmethod
    def get(id):
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
        user_id = api_sql.verify_key(key)
        chats = []
        for element in user_sql.get_chats_by_member(user_id):
            chats.append(element.chat)
        if id not in chats:
            abort(HTTPStatus.NOT_FOUND, "Chat not found.")
        user_chats = []
        for element in user_sql.get_chats_by_member(user_id):
            user_chats.append(element.chat)
        if id not in user_chats:
            abort(HTTPStatus.FORBIDDEN, "User is not permitted to view this chat.")
        is_muted = mute_sql.get_muted(id)
        list_groups_str = request.args.get('list_groups')
        if list_groups_str:
            if list_groups_str in ("True", "true"):
                list_groups = True
            if list_groups_str in ("false", "False"):
                list_groups = False
            if list_groups_str.lower() not in ("false", "true"):
                abort(HTTPStatus.BAD_REQUEST, "'list_groups' is invalid.")
        else:
            list_groups = False
        try:
            groupchat = dispatcher.bot.get_chat(id)
        except TelegramError as excp:
            if excp.message == 'Chat not found':
                abort(HTTPStatus.GONE, "Bot is not a member of the chat (anymore).")
        admins = []
        for admin in groupchat.get_administrators():
            data = {}
            try:
                data.update({"id": admin.user.id})
                chat = admin.user
                if chat.username:
                    data.update({"username": chat.username})
                    data.update({"link": chat.link})
                data.update({"first_name": chat.first_name})
                if chat.last_name:
                    data.update({"last_name": chat.last_name})

                if list_groups:
                    groups = []
                    for group in user_sql.get_chats_by_member(chat.id):
                        groups.append([{"id": group.chat, "name": user_sql.get_chatname(group.chat)}])
                    data.update({"groups": groups})

                admins.append(data)
            except TelegramError as excp:
                if excp.message == 'Chat not found':
                    pass
        return {"id": id, "name" : groupchat.title, "is_muted" : is_muted, "admins" : admins}, HTTPStatus.OK
