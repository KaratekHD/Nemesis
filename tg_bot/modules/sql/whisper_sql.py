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

from sqlalchemy import Column, String, Integer, BigInteger

from tg_bot.modules.sql import BASE, SESSION


class whisper_message():
    message = ""
    sender_id = 0
    receiver_id = 0

    def __init__(self, sender_id, receiver_id, message):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message = message


class Whispers(BASE):
    __tablename__ = "whispers"

    whisper_id = Column(String(14), primary_key=True)
    receiver_id = Column(BigInteger)
    sender_id = Column(BigInteger)
    message = Column(String, default="")

    def __init__(self, whisper_id, receiver_id, sender_id):
        self.whisper_id = whisper_id
        self.receiver_id = receiver_id
        self.sender_id = sender_id


Whispers.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def add_whisper(sender_id, receiver_id, message, id):
    with INSERTION_LOCK:
        w = Whispers(id, receiver_id, sender_id)
        w.message = message
        SESSION.add(w)
        SESSION.commit()


def get_message(whisper_id):
    try:
        w = SESSION.query(Whispers).filter(Whispers.whisper_id == whisper_id)
        if not w:
            return "null"
        result = whisper_message(w.sender_id, w.receiver_id, w.message)
        return result
    finally:
        SESSION.close()