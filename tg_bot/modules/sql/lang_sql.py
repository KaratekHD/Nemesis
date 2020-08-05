import threading

from sqlalchemy import Column, String, UnicodeText, func, distinct

from tg_bot.modules.sql import SESSION, BASE


class Lang(BASE):
    __tablename__ = "lang"
    chat_id = Column(String(14), primary_key=True)
    lang = Column(UnicodeText, default="")

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def __repr__(self):
        return "<Chat {} Language: {}>".format(self.chat_id, self.lang)


Lang.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def set_lang(chat_id, lang_text):
    with INSERTION_LOCK:
        l = SESSION.query(Lang).get(str(chat_id))
        if not l:
            l = Lang(str(chat_id))
        l.lang = lang_text

        SESSION.add(l)
        SESSION.commit()


def get_lang(chat_id):
    lang = SESSION.query(Lang).get(str(chat_id))
    ret = ""
    if lang:
        ret = lang.lang

    SESSION.close()
    return ret


def num_chats():
    try:
        return SESSION.query(func.count(distinct(Lang.chat_id))).scalar()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Lang).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        SESSION.commit()
