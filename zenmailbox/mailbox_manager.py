import os
from datetime import date

from django.db import IntegrityError
from django.core.files.base import ContentFile
from django.conf import settings

from .models import Mailbox, Mail, EMailEntity, Folder, Attachment
from .mailbox import MailBox


UNWANTED_FLAGS = {"\\Junk", "\\Trash", "\\Drafts", "\\Noselect", "\\All"}

ATTACHMENTS_FOLDER = getattr(
    settings,
    "ZENMAILBOX_ATTACHMENTS_FOLDER",
    os.path.join(getattr(settings, 'BASE_DIR', './'), 'attachments')
)

ATTACHMENT_PATH_FORMAT = getattr(
    settings,
    "ZENMAILBOX_ATTACHMENT_PATH_FORMAT",
    '{mailbox.id}/{folder.id}/{mail.id}/{attachment.filename}'
)

ATTACHMENT_PATH = os.path.join(ATTACHMENTS_FOLDER, ATTACHMENT_PATH_FORMAT)


def get_imap_from_folder(folder):
    account = folder.mailbox.imap_account
    server = account.server
    mb = MailBox(server.host, server.port)
    mb.login(account.username, account.password)
    return mb


def fetch_folder(folder, imap=None, criteria=None):
    imap = imap or get_imap_from_folder(folder)
    imap.folder.set(folder.name)
    criteria = criteria or "UID %d:*" % folder.last_uid
    for msg in imap.fetch(criteria):
        try:
            mail = Mail.objects.create(
                in_reply_to=Mail.objects.filter(message_id=msg.in_reply_to).first(),
                plain_text=msg.text,
                html=msg.html,
                folder=folder,
                message_id=msg.message_id,
                received_at=msg.date,
                _from=EMailEntity.objects.get_or_create(email=msg.from_values["email"], name=msg.from_values["name"])[0]
            )
        except IntegrityError as e:
            if str(e).startswith("UNIQUE constraint failed"):
                continue
        mail.to.set([
            EMailEntity.objects.get_or_create(email=email["email"], name=email["name"])[0]
            for email in msg.to_values
        ])
        mail.cc.set([
            EMailEntity.objects.get_or_create(email=email["email"], name=email["name"])[0]
            for email in msg.cc_values
        ])
        mail.bcc.set([
            EMailEntity.objects.get_or_create(email=email["email"], name=email["name"])[0]
            for email in msg.bcc_values
        ])
        for att in msg.attachments:
            if att.content_disposition != "attachment":
                continue
            attachment = Attachment(mail=mail, filename=att.filename, content_type=att.content_type)
            attachment.file.save(
                ATTACHMENT_PATH.format(mailbox=folder.mailbox, folder=folder, mail=mail, attachment=att),
                ContentFile(att.payload)
            )


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


def create_folder(mailbox, imap_folder):
    return Folder.objects.create(
        mailbox=mailbox,
        name=imap_folder["name"],
        last_uid=imap_folder["UIDNEXT"] - 1,
        uid_validity=imap_folder["UIDVALIDITY"],
        sent="\\Sent" in imap_folder["flags"]
    )


def create_folders(mailbox, imap):
    imap_folders = [
        dict(**f, **imap.folder.status(f["name"]))
        for f in imap.folder.list()
        if not set(f["flags"]) & UNWANTED_FLAGS
    ]
    return [create_folder(mailbox, folder) for folder in imap_folders]


def sync_folders(mailbox, imap):
    imap_folders = [
        {**f, **imap.folder.status(f["name"])}
        for f in imap.folder.list()
        if not set(f["flags"]) & UNWANTED_FLAGS
    ]
    synced_folders = []
    for folder in imap_folders:
        db_folder = mailbox.folders\
            .filter(name=folder["name"], uid_validity=folder["UIDVALIDITY"], is_deleted=False).first()
        old_last_uid = 0
        if db_folder:
            old_last_uid = db_folder.last_uid
            db_folder = update_folder(folder, db_folder)
        else:
            db_folder = mailbox.folders.filter(uid_validity=folder["UIDVALIDITY"]).first()
            if db_folder:
                old_last_uid = db_folder.last_uid
                db_folder = update_folder(folder, db_folder)
            else:
                db_folder = create_folder(folder, db_folder)
        db_folder.last_uid = old_last_uid
        if db_folder.is_active:
            synced_folders.append(db_folder)
    mailbox.folders.filter(mailbox=mailbox).exclude(name__in=[f["name"] for f in imap_folders]).safe_delete()
    return synced_folders


def fetch_mailbox(mailbox, clean=False, criteria=None):
    account = mailbox.imap_account
    server = account.server
    imap = MailBox(server.host, server.port)
    imap.login(account.username, account.password)
    if clean:
        mailbox.folders.all().delete()
        folders = create_folders(mailbox, imap)
    else:
        folders = sync_folders(mailbox, imap)
    for folder in folders:
        if clean:
            folder.mails.all().delete()
            fetch_folder(folder, imap, criteria)
        else:
            fetch_folder(folder, imap)


def fetch_new_mail():
    mailboxes = Mailbox.objects.filter(is_deleted=False, is_active=True).all()
    for mailbox in mailboxes:
        fetch_mailbox(mailbox)


def fetch_all_mail(since_date=None):
    since_date = since_date or date(1970, 1, 1)
    mailboxes = Mailbox.objects.filter(is_deleted=False, is_active=True).all()
    for mailbox in mailboxes:
        fetch_mailbox(mailbox, True, "SINCE %s" % since_date.strftime("%d-%b-%Y"))
