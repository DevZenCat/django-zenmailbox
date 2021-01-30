from django.test import TestCase
from django.conf import settings

from zenmailbox.folder_set import FolderSet
from zenmailbox.mailbox import MailBox
from zenmailbox.models import Mailbox, IMAPServer, IMAPAccount, Folder
from .test_smtp import SmtpClient


class FolderSetTestCase(TestCase):
    def setUp(self):
        self.server = IMAPServer.objects.create(host="imap.yandex.ru")
        self.account = IMAPAccount.objects.create(
            username=settings.USERNAME_RECEIVER,
            password=settings.PASSWORD_RECEIVER,
            server=self.server
        )
        self.mailbox = Mailbox.objects.create(imap_account=self.account)
        self.initial_folders = self.folderset.imap_folders

    @property
    def imap_receiver(self):
        return MailBox(self.server.host, self.server.port).login(self.account.username, self.account.password)

    @property
    def folderset(self):
        return FolderSet(self.imap_receiver, self.mailbox)

    def get_sender(self):
        return SmtpClient("smtp.yandex.ru", settings.USERNAME_SENDER, settings.PASSWORD_SENDER)

    def test_folderset_clean(self):
        folders = self.folderset.sync(False)
        self.assertEqual(sorted([folder["obj"].name for folder in folders]), ['INBOX', 'Outbox', 'Sent'])

    def test_folderset_create_folder(self):
        self.folderset.sync(False)
        self.imap_receiver.folder.create("test")
        try:
            folders = self.folderset.sync(True)
            self.assertEqual(sorted([folder["obj"].name for folder in folders]), ['INBOX', 'Outbox', 'Sent', 'test'])
        finally:
            self.imap_receiver.folder.delete("test")

    def test_folderset_delete_folder(self):
        self.imap_receiver.folder.create("test")
        try:
            self.folderset.sync(False)
        finally:
            self.imap_receiver.folder.delete("test")
        folders = self.folderset.sync(True)
        self.assertEqual(sorted([folder["obj"].name for folder in folders]), ['INBOX', 'Outbox', 'Sent'])

    def test_folderset_new_message(self):
        self.folderset.sync(False)
        folder = Folder.objects.get(name="INBOX")
        last_uid = folder.last_uid
        sender = self.get_sender()
        sender.send_mail(settings.USERNAME_RECEIVER, 'this is a test', 'tasty test')
        try:
            self.folderset.sync(True)
            folder.refresh_from_db(fields=["last_uid"])
            self.assertGreater(folder.last_uid, last_uid)
        finally:
            self.imap_receiver.delete(str(folder.last_uid))
