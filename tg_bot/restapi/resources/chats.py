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

import tg_bot.modules.sql.api_sql as sql
import tg_bot.modules.sql.users_sql as user_sql
from tg_bot import dispatcher
from tg_bot.restapi.models.chats import create_chat_model

chats_api = Namespace("chats", description="Gather information about chats you have access to.")

chat = create_chat_model(chats_api)


@chats_api.route("/<id>")
@chats_api.param('id', 'The group identifier')
@chats_api.response(404, 'Chat not found.')
@chats_api.response(401, "Unauthorized")
@chats_api.response(410, "Bot is not a member of the chat (anymore).")
class Chats(Resource):
    @chats_api.marshal_with(chat)
    @staticmethod
    def get(id):
        '''Gets a chat by id'''
        key = request.args.get('api_key')
        if not key:
            abort(HTTPStatus.UNAUTHORIZED, "Unauthorized")
        user_id = sql.verify_key(key)
        chats = []
        for element in user_sql.get_chats_by_member(user_id):
            chats.append(element.chat)
        if id not in chats:
            abort(HTTPStatus.NOT_FOUND, "Chat not found.")
        else:
            try:
                name = dispatcher.bot.get_chat(id).title
            except TelegramError as excp:
                if excp.message == 'Chat not found':
                    abort(HTTPStatus.GONE, "Bot is not a member of the chat (anymore).")
            return {"id": id, "name": name}
