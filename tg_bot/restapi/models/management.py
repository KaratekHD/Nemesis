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

from flask_restplus import fields

from tg_bot.restapi.models.users import create_user_model


def create_chatnumber_model(api):
    model = api.model('Total Chats', {
        'number': fields.Integer(description="Number of group the bot has registered.", required=True)
    })
    return model


def create_countusers_model(api):
    model = api.model('Total Users', {
        'number': fields.Integer(description="Number of users the bot has registered.", required=True)
    })
    return model


def create_chat_model(api):
    model = api.model('Chat', {
        'id': fields.Integer(description="Telegram ID of chat", required=True),
        'name': fields.String(description="Name of the group", required=True)
    })
    return model


def create_chatlist_model(api):
    model = api.model('Chats', {
        'chats': fields.Nested(create_chat_model(api), description="list of chats", required=True)
    })
    return model


def create_broadcast_model(api):
    model = api.model("Broadcast", {
        'message': fields.String(description="The message that was broadcasted.", required=True),
        "failed": fields.Integer(description="Number of chats that failed receiving the broadcast.", required=True),
        "failed_chats": fields.Nested(create_chat_model(api), description="Chats that failed receiving the broadcast.", required=False)
    })
    return model


def create_userlist_model(api):
    model = api.model('Users', {
        'users': fields.Nested(create_user_model(api), description="list of users", required=True)
    })
    return model