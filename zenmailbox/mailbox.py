from imap_tools import MailBox as BaseMailBox
from imap_tools.message import MailMessage as BaseMailMessage
from functools import lru_cache

from imap_tools.utils import parse_email_date
from pytz import UTC


class MailMessage(BaseMailMessage):
    @property
    @lru_cache()
    def in_reply_to(self) -> (str,):
        return self.obj['In-Reply-To'] or ''

    @property
    @lru_cache()
    def message_id(self) -> (str,):
        return self.obj['Message-ID'] or self.obj['Message-Id'] or ''

    @property
    @lru_cache()
    def date(self):
        date = parse_email_date(self.date_str)
        if not date.tzinfo:
            date = UTC.localize(date)
        return date


class MailBox(BaseMailBox):
    email_message_class = MailMessage
