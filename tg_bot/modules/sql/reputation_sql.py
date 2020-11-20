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

from sqlalchemy import Column, String, UnicodeText, Integer

from tg_bot.modules.sql import BASE, SESSION


class LatestRepMessage(BASE):
    __tablename__ = "rep_messages"
    chat_id = Column(String, primary_key=True)
    msg_id = Column(UnicodeText, default="")

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)


LatestRepMessage.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def migrate_chat_latest_messages(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(LatestRepMessage).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        SESSION.commit()


def set_latest_rep_message(chat_id, msg_id):
    with INSERTION_LOCK:
        l = SESSION.query(LatestRepMessage).get(str(chat_id))
        if not l:
            l = LatestRepMessage(str(chat_id))
        l.msg_id = msg_id
        SESSION.add(l)
        SESSION.commit()


def get_latest_rep_message(chat_id):
    l = SESSION.query(LatestRepMessage).get(str(chat_id))
    ret = 0
    if l:
        ret = l.msg_id

    SESSION.close()
    return ret


class Reputation(BASE):
    __tablename__ = "reputations"
    chat_id = Column(String, primary_key=True)
    user_id = Column(UnicodeText, primary_key=True)
    reputation = Column(Integer, default=0)

    def __init__(self, chat_id, user_id, reputation):
        self.chat_id = str(chat_id)
        self.user_id = str(user_id)
        self.reputation = reputation


Reputation.__table__.create(checkfirst=True)


def set_reputation(chat_id, user_id, reputation):
    s = SESSION.query(Reputation).get((str(chat_id), str(user_id)))
    if s:
        SESSION.delete(s)
    filt = Reputation(str(chat_id), str(user_id), int(reputation))
    SESSION.add(filt)
    SESSION.commit()


def get_reputation(chat_id, user_id):
    s = SESSION.query(Reputation).get((str(chat_id), str(user_id)))
    return s
    ret = 0
    if s:
        ret = s
    return ret
