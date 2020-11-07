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
from http import HTTPStatus

from flask_httpauth import HTTPBasicAuth
from flask_restplus import Namespace, Resource
import tg_bot.modules.sql.api_sql as sql

auth = HTTPBasicAuth()


@auth.verify_password
def authenticate(username, password):
    if username and password:
        if username is "jens":
            return username
    else:
        return False


chats_api = Namespace("chats", description="Gather information about chats you have access to.")


@chats_api.route("")
class List(Resource):
    @auth.login_required
    def get(self):
        '''Get All chats you have access to.'''
        return "Nemesis Telegram Bot v2.0 Development Preview 1", HTTPStatus.OK
