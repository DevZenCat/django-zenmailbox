from django.test import TestCase
from zenmailbox.folder_set import FolderSet
from zenmailbox.mailbox import MailBox
from zenmailbox.models import Mailbox, IMAPServer, Folder, IMAPAccount
from os import environ

USERNAME = environ.get("MB_USERNAME")
PASSWORD = environ.get("MB_PASSWORD")


class FolderSetTestCase(TestCase):
    def setUp(self):
        server = IMAPServer.objects.create(host="imap.yandex.ru")
        account = IMAPAccount.objects.create(
            username=USERNAME,
            password=PASSWORD,
            server=server
        )
        self.mailbox = Mailbox.objects.create(imap_account=account)
        self.imap = MailBox(server.host, server.port)
        self.imap.login(account.username, account.password)
        self.folderset = FolderSet(self.imap, self.mailbox)

    def test_folderset_clean(self):
        folders_names = ["INBOX", "Outbox", "Sent"]
        folders = self.folderset.sync(False)
        self.assertEqual(len(folders), len(folders_names))
        for folder in folders:
            self.assertIn(folder["obj"].name, folders_names)

    def test_folderset_sync(self):
        pass
