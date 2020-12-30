from django.test import TestCase
from zenmailbox.folder_set import FolderSet
from zenmailbox.mailbox import MailBox
from zenmailbox.models import Mailbox, IMAPServer, Folder, IMAPAccount


class FolderSetTestCase(TestCase):
    def setUp(self):
        server = IMAPServer.objects.create(host="imap.gmail.com")
        account = IMAPAccount.objects.create(
            username="peshka.acc1@gmail.com",
            password="bghgaanhdqaucojh",
            server=server
        )
        self.mailbox = Mailbox.objects.create(imap_account=account)
        self.imap = MailBox(server.host, server.port)
        self.imap.login(account.username, account.password)
        self.folderset = FolderSet(self.imap, self.mailbox)

    def test_folderset_clean(self):
        folders = self.folderset.sync(False)
        print(folders)