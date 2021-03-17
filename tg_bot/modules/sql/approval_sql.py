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

from sqlalchemy import Column, String

from tg_bot.modules.sql import BASE, SESSION


class Approval(BASE):
    __tablename__ = "approval"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = user_id


Approval.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()

APPROVALS = {}


def approve(chat_id, user_id):
    with INSERTION_LOCK:
        approval = Approval(str(chat_id), str(user_id))
        APPROVALS[str(chat_id)] = APPROVALS[str(chat_id)].append(str(user_id))
        SESSION.merge(approval)
        SESSION.commit()


def rm_approve(chat_id, user_id):
    with INSERTION_LOCK:
        approval = SESSION.query(Approval).get((str(chat_id), str(user_id)))
        if approval:
            SESSION.delete(approval)
            SESSION.commit()


def check_approval(chat_id, user_id):
    approval = SESSION.query(Approval).get((str(chat_id), str(user_id)))
    if approval:
        return True
    else:
        return False


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat_filters = SESSION.query(Approval).filter(Approval.chat_id == str(old_chat_id)).all()
        for approval in chat_filters:
            approval.chat_id = str(new_chat_id)
        SESSION.commit()


def remove_all(chat_id):
    with INSERTION_LOCK:
        m = SESSION.query(Approval).filter(Approval.chat_id == str(chat_id)).all()
        for element in m:
            approval = SESSION.query(Approval).get((str(chat_id), str(element.user_id)))
            SESSION.delete(approval)
        SESSION.commit()


def get_chat_approvals(chat_id):
    m = SESSION.query(Approval).filter(Approval.chat_id == str(chat_id)).all()
    return m