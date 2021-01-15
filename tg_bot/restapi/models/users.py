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
from flask_restplus import fields

from tg_bot.restapi.models.chats import create_chat_model


def create_user_model(api):
    model = api.model("User", {
        "id": fields.Integer(description="Telegram ID of user", required=True),
        "first_name": fields.String(description="First name of user", required=True),
        "last_name": fields.String(description="Last name of user", required=False),
        "username": fields.String(description="Username", required=False),
        "link": fields.String(description="Convenience property. If username is available, returns a t.me link of the user.", required=False),
        "groups": fields.Nested(create_chat_model(api), description="All chats the user is part of.", required=False)
    })
    return model