from django.forms import BaseInlineFormSet
from django.contrib.admin import ModelAdmin, register, TabularInline

from .utils import reply
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


class MessageInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        print(form, form.instance)
        reply(form.instance, form.instance.thread.mails.order_by("-received_at").first())
        return super().save_new(form, commit)


class MailInlineAdmin(TabularInline):
    model = Mail
    extra = 1
    can_delete = False
    fields = [
        '_from',
        'to',
        'plain_text',
        'received_at'
    ]
    template = 'zenmailbox/messages_inline.html'
    readonly_fields = [
        '_from',
        'to',
        'received_at'
    ]
    formset = MessageInlineFormSet
    ordering = "received_at",


@register(Thread)
class ThreadAdmin(ModelAdmin):
    inlines = [MailInlineAdmin]
