from django.contrib.admin import ModelAdmin, register

from .models import *


@register(Mailbox)
class MailboxAdmin(ModelAdmin):
    pass


@register(IMAPAccount)
class IMAPAccountAdmin(ModelAdmin):
    pass


@register(SMTPAccount)
class SMTPAccountAdmin(ModelAdmin):
    pass


@register(IMAPServer)
class IMAPServerAdmin(ModelAdmin):
    pass


@register(SMTPServer)
class SMTPServerAdmin(ModelAdmin):
    pass


@register(Mail)
class MailAdmin(ModelAdmin):
    pass


@register(Folder)
class FolderAdmin(ModelAdmin):
    pass


@register(Attachment)
class AttachmentAdmin(ModelAdmin):
    pass
