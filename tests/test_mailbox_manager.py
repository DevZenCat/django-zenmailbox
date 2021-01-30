from django.test import TestCase
from django.conf import settings

from zenmailbox.models import Mailbox, IMAPServer, IMAPAccount, SMTPServer, SMTPAccount, Mail, Thread
from zenmailbox.mailbox_manager import fetch_all_mail, fetch_new_mail
from tests.test_smtp import SmtpClient
from zenmailbox.mailbox import MailBox
from zenmailbox.utils import reply


class MailboxManagerTestCase(TestCase):
    def setUp(self):
        self.mailbox = Mailbox.objects.create(
            imap_account=IMAPAccount.objects.create(
                username=settings.USERNAME_RECEIVER,
                password=settings.PASSWORD_RECEIVER,
                server=IMAPServer.objects.create(host="imap.yandex.ru")
            ),
            smtp_account=SMTPAccount.objects.create(
                username=settings.USERNAME_RECEIVER,
                password=settings.PASSWORD_RECEIVER,
                server=SMTPServer.objects.create(host="smtp.yandex.ru"),
                from_email=settings.USERNAME_RECEIVER,
                from_name="panda lover"
            )
        )
        fetch_all_mail()
        self.inbox_folder = self.mailbox.folders.filter(name="INBOX").first()

    @property
    def imap_receiver(self):
        return MailBox("imap.yandex.ru").login(settings.USERNAME_RECEIVER, settings.PASSWORD_RECEIVER)

    @property
    def imap_sender(self):
        return MailBox("imap.yandex.ru").login(settings.USERNAME_SENDER, settings.PASSWORD_SENDER)

    def get_sender(self):
        return SmtpClient("smtp.yandex.ru", settings.USERNAME_SENDER, settings.PASSWORD_SENDER)

    def test_first_fetch(self):
        self.assertEqual(self.inbox_folder.mails.count(), 1)
        mail = self.inbox_folder.mails.first()
        self.assertEqual(mail._from.email, settings.USERNAME_SENDER)
        self.assertEqual(mail.to.first().email, settings.USERNAME_RECEIVER)
        self.assertEqual(mail.plain_text, "here is beautiful panda image!")
        self.assertEqual(mail.subject, "pandas is cute")

    def test_fetch_new_mail(self):
        sender = self.get_sender()
        sender.send_mail(
            settings.USERNAME_RECEIVER,
            "here is one more!",
            "pandas is cute",
            [
                ("images/jpeg", 'panda1.jpg', open('tests/attachments/panda1.jpg', 'br'))
            ]
        )
        try:
            fetch_new_mail()
            self.inbox_folder = self.mailbox.folders.filter(name="INBOX").first()
            self.assertEqual(self.inbox_folder.mails.count(), 2)
        finally:
            self.imap_receiver.delete(str(self.inbox_folder.last_uid))

    def test_threading(self):
        html = "thanks for images!<br>pandas are <b>so</b> cute!"
        plain_text = "thanks for images!\npandas are so cute!"
        mail = Mail(html=html, thread=Thread.objects.first())
        reply(mail)
        imap_mail = next(self.imap_sender.fetch(reverse=True))
        try:
            self.assertTrue(mail.folder.sent)
            self.assertEqual(mail.plain_text, plain_text)
            self.assertEqual(imap_mail.html, html)
            self.assertEqual(imap_mail.text.replace('\r\n', '\n'), plain_text)
            self.assertEqual(imap_mail.subject, mail.subject)
        finally:
            self.imap_sender.delete(str(imap_mail.uid))
