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

from tg_bot.restapi.models import users


def create_chat_model(api):
    model = api.model("Chat", {
        "id": fields.Integer(description="Telegram ID of group", required=True),
        "name": fields.String(description="Name of group", required=True),
        "is_muted": fields.Boolean(description="Global mute status", required=True),
        # "link": fields.String(description="Convenience property. If username is available, returns a t.me link of the user.", required=False),
        "admins": fields.Nested(users.create_user_model(api), description="Administrators", required=False)
    })
    return model