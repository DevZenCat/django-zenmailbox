import os
from datetime import date

from django.db import IntegrityError
from django.core.files.base import ContentFile
from django.conf import settings

from .models import Mailbox, Mail, EMailEntity, Folder, Attachment, Thread
from .mailbox import MailBox
from .folder_set import FolderSet


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

SAVE_ATTACHMENTS = getattr(
    settings,
    "ZENMAILBOX_SAVE_ATTACHMENTS",
    True
)

ATTACHMENT_PATH = os.path.join(ATTACHMENTS_FOLDER, ATTACHMENT_PATH_FORMAT)


def get_imap_from_folder(folder):
    account = folder.mailbox.imap_account
    server = account.server
    mb = MailBox(server.host, server.port)
    mb.login(account.username, account.password)
    return mb


def build_criteria(since_date=None, since_uid=None):
    criteria = ['ALL']
    if since_uid:
        criteria.append('UID %d:*' % since_uid)
    if since_date:
        criteria.append('SINCE %s' % since_date.strftime("%d-%b-%Y"))
    return " ".join(criteria)


def fetch_folder(folder, filters, imap=None):
    imap = imap or get_imap_from_folder(folder)
    imap.folder.set(folder.name)
    criteria = build_criteria(**filters)
    mails = []
    for msg in imap.fetch(criteria):
        thread_is_created = False
        reply_to_msg = Mail.objects.filter(message_id=msg.in_reply_to).first()
        if reply_to_msg:
            thread = reply_to_msg.thread
            if not thread:
                thread_is_created = True
                thread = reply_to_msg.thread = Thread.objects.create()
        else:
            thread_is_created = True
            thread = Thread.objects.create()
        try:
            mail = Mail.objects.create(
                in_reply_to=reply_to_msg,
                plain_text=msg.text,
                html=msg.html,
                folder=folder,
                message_id=msg.message_id,
                received_at=msg.date,
                _from=EMailEntity.objects.get_or_create(email=msg.from_values["email"],
                                                        name=msg.from_values["name"])[0],
                subject=msg.subject,
                thread=thread
            )
        except IntegrityError as e:
            if str(e).startswith("UNIQUE constraint failed"):
                if thread_is_created:
                    thread.delete()
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
        if SAVE_ATTACHMENTS:
            for att in msg.attachments:
                if att.content_disposition != "attachment":
                    continue
                attachment = Attachment(mail=mail, filename=att.filename, content_type=att.content_type)
                attachment.file.save(
                    ATTACHMENT_PATH.format(mailbox=folder.mailbox, folder=folder, mail=mail, attachment=att),
                    ContentFile(att.payload)
                )
        mails.append(mail)
    return mails


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


def fetch_mailbox(mailbox, clean=False, criteria=None):
    criteria = criteria or {}
    account = mailbox.imap_account
    server = account.server
    token = account.token
    imap = MailBox(server.host, server.port)
    clean = clean or mailbox.initialized
    if token:
        imap.xoauth2(account.username, token)
    else:
        imap.login(account.username, account.password)
    if clean:
        Mail.objects.filter(folder__mailbox=mailbox).delete()
        mailbox.folders.all().delete()
        folders = FolderSet(imap, mailbox).sync(False)
    else:
        folders = FolderSet(imap, mailbox).sync(True)
    for folder in folders:
        filters = folder["mail_filters"]
        filters.update(criteria)
        folder = folder["obj"]
        if clean:
            folder.mails.all().delete()
        fetch_folder(folder, filters, imap)


def fetch_new_mail():
    mailboxes = Mailbox.objects.filter(is_deleted=False, is_active=True).all()
    for mailbox in mailboxes:
        fetch_mailbox(mailbox)


def fetch_all_mail(since_date=None):
    since_date = since_date or date(1970, 1, 1)
    mailboxes = Mailbox.objects.filter(is_deleted=False, is_active=True).all()
    for mailbox in mailboxes:
        fetch_mailbox(mailbox, True, {"since_date": since_date})
