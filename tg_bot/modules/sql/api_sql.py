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



from sqlalchemy import Column, UnicodeText, Integer, BigInteger
from tg_bot.modules.sql import SESSION, BASE


class Api(BASE):
    __tablename__ = "api"
    user_id = Column(BigInteger, primary_key=True)
    key = Column(UnicodeText)

    def __init__(self, user_id, key=None):
        self.user_id = user_id
        self.key = key

    def __repr__(self):
        return "<User {} ({})>".format(self.username, self.user_id)


Api.__table__.create(checkfirst=True)


def set_key(user_id, key):
    user = SESSION.query(Api).get(user_id)
    if not user:
        user = Api(user_id, key)
        SESSION.add(user)
        SESSION.flush()
    else:
        user.key = key
    SESSION.commit()


def verify_key(key):
    result = SESSION.query(Api).filter(Api.key == str(key)).scalar()
    ret = None
    if result:
        ret = result.user_id
    SESSION.close()
    return ret


def get_key(user_id):
    key = SESSION.query(Api).get(str(user_id))
    ret = "null"
    if key:
        ret = key.key

    SESSION.close()
    return ret