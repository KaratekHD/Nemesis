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


import threading

from sqlalchemy import Column, String, UnicodeText, func, distinct, Boolean

from tg_bot.modules.sql import SESSION, BASE
from tg_bot import DEFAULT_LANG


class Globalmute(BASE):
    __tablename__ = "mute"
    chat_id = Column(String(14), primary_key=True)
    muted = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def __repr__(self):
        return "<Chat {} is muted: {}>".format(self.chat_id, self.muted)


Globalmute.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def set_muted(chat_id, muted):
    with INSERTION_LOCK:
        l = SESSION.query(Globalmute).get(str(chat_id))
        if not l:
            l = Globalmute(str(chat_id))
        l.muted = muted

        SESSION.add(l)
        SESSION.commit()


def get_muted(chat_id):
    m = SESSION.query(Globalmute).get(str(chat_id))
    ret = False
    if m:
        ret = m.muted

    SESSION.close()
    return ret


def num_chats():
    try:
        return SESSION.query(func.count(distinct(Globalmute.chat_id))).scalar()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Globalmute).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        SESSION.commit()
