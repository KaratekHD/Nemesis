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

import threading

from sqlalchemy import Column, UnicodeText, Boolean, Integer, String

from tg_bot.modules.sql import BASE, SESSION


class AFK(BASE):
    __tablename__ = "afk_users"

    user_id = Column(Integer, primary_key=True)
    is_afk = Column(Boolean)
    reason = Column(UnicodeText)
    chat_id = Column(String(14))

    def __init__(self, user_id, reason="", is_afk=True):
        self.user_id = user_id
        self.reason = reason
        self.is_afk = is_afk


    def __repr__(self):
        return "afk_status for {}".format(self.user_id)


AFK.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()

AFK_USERS = {}


def is_afk(user_id):
    return user_id in AFK_USERS


def check_afk_status(user_id):
    if user_id in AFK_USERS:
        return True, AFK_USERS[user_id]
    return False, ""


def set_afk(chat_id, user_id, reason=""):
    with INSERTION_LOCK:
        curr = SESSION.query(AFK).get(user_id)
        if not curr:
            curr = AFK(user_id, reason, True)
        else:
            curr.is_afk = True
            curr.reason = reason
            curr.chat_id = chat_id

        AFK_USERS[user_id] = reason

        SESSION.add(curr)
        SESSION.commit()


def rm_afk(user_id):
    with INSERTION_LOCK:
        curr = SESSION.query(AFK).get(user_id)
        if curr:
            if user_id in AFK_USERS:  # sanity check
                del AFK_USERS[user_id]

            SESSION.delete(curr)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def __load_afk_users():
    global AFK_USERS
    try:
        all_afk = SESSION.query(AFK).all()
        AFK_USERS = {user.user_id: user.reason for user in all_afk if user.is_afk}
    finally:
        SESSION.close()


__load_afk_users()
