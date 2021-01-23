from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.forms import BaseInlineFormSet, ModelForm
from django.contrib.admin import ModelAdmin, register, TabularInline
from django.http import HttpResponse
from django.urls import path

from .utils import reply
from .models import *
from .widgets import HtmlWidget
from .mailbox_manager import fetch_mailbox


def fetch_mail(modeladmin, request, queryset):
    for mb in queryset:
        fetch_mailbox(mb)


@register(Mailbox)
class MailboxAdmin(ModelAdmin):
    actions = fetch_mail,
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


class MailForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['html'].widget = HtmlWidget()


@register(Mail)
class MailAdmin(ModelAdmin):
    form = MailForm

    def get_urls(self):
        urls = super().get_urls()
        urls.insert(-1, path('<path:object_id>/view/', self.view_mail, name='zenmailbox_mail_view'))
        return urls

    def view_mail(self, request, object_id, extra_context=None):
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        return HttpResponse(obj.html.encode(), content_type="text/html")


@register(Folder)
class FolderAdmin(ModelAdmin):
    pass


@register(Attachment)
class AttachmentAdmin(ModelAdmin):
    pass


class MessageInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.fields['html'].widget = HtmlWidget()

    def save_new(self, form, commit=True):
        reply(form.instance)
        return super().save_new(form, commit)


class MailInlineAdmin(TabularInline):
    model = Mail
    extra = 1
    can_delete = False
    fields = [
        '_from',
        'to',
        'html',
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
