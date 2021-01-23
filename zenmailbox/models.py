from django.db.models import *
from django.utils.timezone import now


def safe_delete(qs):
    qs.update(deleted_at=now(), is_deleted=True)


class BaseModel(Model):
    class Meta:
        abstract = True

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    deleted_at = DateTimeField(blank=True, null=True)
    is_deleted = BooleanField(default=False)

    def safe_delete(self):
        if not self.is_deleted:
            self.deleted_at = now()
            self.is_deleted = False
            self.save()


class Server(BaseModel):
    class Meta:
        abstract = True

    host = CharField(max_length=255)
    port = IntegerField()

    def __str__(self):
        return self.host


class SMTPServer(Server):
    port = IntegerField(default=465)


class IMAPServer(Server):
    port = IntegerField(default=993)


class MailAccount(BaseModel):
    class Meta:
        abstract = True

    username = CharField(max_length=255)
    password = CharField(max_length=255, default=None, blank=True, null=True)
    token = CharField(max_length=255, default=None, blank=True, null=True)

    def __str__(self):
        return "%s:%s" % (self.server, self.username)


class IMAPAccount(MailAccount):
    server = ForeignKey(IMAPServer, on_delete=CASCADE, related_name="accounts")


class SMTPAccount(MailAccount):
    server = ForeignKey(SMTPServer, on_delete=CASCADE, related_name="accounts")
    from_name = CharField(max_length=255, null=True, blank=True)
    from_email = CharField(max_length=255, null=True, blank=True)


class Mailbox(BaseModel):
    is_active = BooleanField(default=True)
    imap_account = OneToOneField(IMAPAccount, on_delete=CASCADE, related_name="mailbox")
    smtp_account = OneToOneField(SMTPAccount, on_delete=SET_NULL, null=True, blank=True, related_name="mailbox")
    initialized = BooleanField(default=False)

    def __str__(self):
        return str(self.imap_account)


class Folder(BaseModel):
    is_active = BooleanField(default=True)
    mailbox = ForeignKey(Mailbox, on_delete=CASCADE, related_name="folders")
    name = CharField(max_length=255)
    last_uid = IntegerField()
    uid_validity = IntegerField()
    sent = BooleanField()

    def __str__(self):
        return self.name


class EMailEntity(Model):
    email = EmailField()
    name = CharField(max_length=255)

    def __str__(self):
        return "%s <%s>" % (self.email, self.name)


class Thread(Model):
    def __str__(self):
        return str(self.id)


class Mail(Model):
    message_id = CharField(max_length=255, unique=True)
    _from = ForeignKey(EMailEntity, on_delete=SET_NULL, null=True, related_name="mails_from")
    to = ManyToManyField(EMailEntity, related_name="mails_to")
    cc = ManyToManyField(EMailEntity, related_name="mails_cc", blank=True, null=True)
    bcc = ManyToManyField(EMailEntity, related_name="mails_bcc", blank=True, null=True)
    in_reply_to = ForeignKey("Mail", on_delete=SET_NULL, blank=True, null=True, related_name="replies")
    plain_text = TextField(blank=True)
    html = TextField(blank=True)
    received_at = DateTimeField()
    folder = ForeignKey(Folder, on_delete=SET_NULL, null=True, related_name="mails")
    subject = CharField(max_length=255, blank=True)
    thread = ForeignKey(Thread, on_delete=SET_NULL, null=True, related_name="mails")

    def __str__(self):
        return self.subject

    @property
    def sent(self):
        return self.folder.sent


class Attachment(Model):
    file = FileField()
    mail = ForeignKey(Mail, on_delete=CASCADE, related_name="attachments")
    filename = CharField(max_length=255)
    content_type = CharField(max_length=100)
