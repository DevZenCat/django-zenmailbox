from datetime import timedelta

from django.utils.timezone import now

from .models import Folder, safe_delete


class FolderSet:
    UNWANTED_FLAGS = {"\\Junk", "\\Trash", "\\Drafts", "\\Noselect", "\\All"}

    def __init__(self, mb, mailbox):
        self.mb = mb
        self._imap_folders = None
        self.mailbox = mailbox

    @property
    def imap_folders(self):
        if self._imap_folders is None:
            self._imap_folders = [
                dict(**f, **self.mb.folder.status(f["name"]))
                for f in self.mb.folder.list()
                if not set(f["flags"]) & self.UNWANTED_FLAGS
            ]
        return self._imap_folders

    def create_folder(self, imap_folder):
        return Folder.objects.create(
            mailbox=self.mailbox,
            name=imap_folder["name"],
            last_uid=imap_folder["UIDNEXT"] - 1,
            uid_validity=imap_folder["UIDVALIDITY"],
            sent="\\Sent" in imap_folder["flags"]
        )

    @staticmethod
    def update_folder(imap_folder, db_folder):
        name = imap_folder.get("name")
        last_uid = imap_folder.get("UIDNEXT") - 1

        updated = False
        if db_folder.last_uid != last_uid:
            updated = True
            db_folder.last_uid = last_uid
        if db_folder.name != name:
            updated = True
            db_folder.name = name
        if db_folder.deleted_at is not None:
            updated = True
            db_folder.deleted_at = None
        if db_folder.is_deleted:
            updated = True
            db_folder.is_deleted = False
        if updated:
            db_folder.save()
        return db_folder

    def sync(self, fallback):
        synced_folders = []
        folders_names = []
        month_ago = now() - timedelta(days=30)
        last_updated_at = Folder.objects.filter(mailbox=self.mailbox).order_by("-updated_at").first()
        if not last_updated_at or last_updated_at.updated_at < month_ago:
            last_updated_at = month_ago
        else:
            last_updated_at = last_updated_at.updated_at
        for folder in self.imap_folders:
            name = folder.get("name")
            uid = folder.get("UIDVALIDITY")
            db_folder = Folder.objects.filter(mailbox=self.mailbox,
                                              name=name,
                                              uid_validity=uid,
                                              is_deleted=False).first()
            old_last_uid = None
            if db_folder:
                old_last_uid = db_folder.last_uid
                db_folder = self.update_folder(folder, db_folder)
            else:
                db_folder = Folder.objects.filter(mailbox=self.mailbox, uid_validity=uid).first()
                if db_folder and fallback:
                    old_last_uid = db_folder.last_uid
                    db_folder = self.update_folder(folder, db_folder)
                else:
                    db_folder = self.create_folder(folder)
            folders_names.append(name)
            if old_last_uid is None:
                mail_filters = {"since_date": last_updated_at}
            else:
                mail_filters = {"since_uid": old_last_uid}
            synced_folders.append(dict(**folder, mail_filters=mail_filters, obj=db_folder))
        safe_delete(Folder.objects.filter(mailbox=self.mailbox).exclude(name__in=folders_names))
        return synced_folders
