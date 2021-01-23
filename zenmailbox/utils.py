import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from random import choices

from django.template.loader import get_template
from django.utils.timezone import now

from .models import Mail, EMailEntity


def format_email(email, name=None):
    h = Header()
    if name:
        h.append(name, "utf8")
    h.append("<%s>" % email, "ascii")
    return h


def format_email_list(email_list):
    return ", ".join(["<%s>" % email for email in email_list])


ALPHA = 'abcdef0123456789'


def reply(instance: Mail):
    thread = instance.thread
    folder = thread.mails.first().folder
    account = folder.mailbox.smtp_account
    server = account.server
    email = account.username
    token = account.token
    password = account.password
    smtp_host = server.host
    smtp_port = server.port

    in_reply_to = thread.mails.exclude(_from__email=account.from_email).order_by("-received_at").first()

    template = get_template('zenmailbox/reply.html')
    template_context = dict(text=instance.html, in_reply_to=in_reply_to)
    plain_text = template.render(template_context)
    html = template.render(dict(**template_context, html=True))

    instance._from = EMailEntity.objects.get_or_create(email=account.from_email, name=account.from_name)[0]
    instance.message_id = "%s-%s-%s-%s" % (
        "".join(choices(ALPHA, k=8)),
        "".join(choices(ALPHA, k=8)),
        "".join(choices(ALPHA, k=8)),
        "".join(choices(ALPHA, k=8))
    )
    instance.in_reply_to = in_reply_to
    instance.plain_text = plain_text
    instance.html = html
    instance.received_at = now()
    instance.folder = in_reply_to.folder.mailbox.folders.filter(sent=True).first()
    instance.subject = ("Re: " if in_reply_to.subject else "") + in_reply_to.subject
    instance.save()
    instance.to.set([in_reply_to._from])
    instance.cc.set(in_reply_to.cc.all())
    instance.bcc.set(in_reply_to.bcc.all())

    to = [in_reply_to._from.email]
    cc = [email.cc for email in in_reply_to.cc.all()]
    bcc = [email.bcc for email in in_reply_to.bcc.all()]
    in_reply_to_email = in_reply_to._from.email
    subject = ("" if in_reply_to.subject.startswith('Re:') else "Re:") + in_reply_to.subject
    from_name = account.from_name
    from_email = account.from_email

    msg = MIMEMultipart('mixed')
    msg["Message-Id"] = instance.message_id
    msg["Subject"] = Header(subject, 'utf8')
    msg["From"] = format_email(from_email, from_name)
    msg["To"] = format_email_list(to)
    msg["Reply-To"] = format_email(to)
    if cc:
        msg["Cc"] = format_email_list(cc)
    if bcc:
        msg["Bcc"] = format_email_list(bcc)
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to_email
    text = MIMEMultipart('alternative')
    if plain_text:
        text.attach(MIMEText(plain_text, 'plain'))
    if html:
        text.attach(MIMEText(html, 'html'))
    msg.attach(text)

    # if attachments:
    #     for file in attachments:
    #         content_type = guess_type(path)[0] or "application/octet-stream"
    #         part = MIMEBase(*content_type.split('/'), name=filename)
    #         part.set_payload(file.read())
    #         encoders.encode_base64(part)
    #         part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(filename))
    #         msg.attach(part)

    server = smtplib.SMTP_SSL(smtp_host, smtp_port)
    if token:
        server.ehlo()
        server.auth(
            "XOAUTH2",
            lambda challenge=None: None if challenge is None else 'user={}\1auth=Bearer {}\1\1'.format(email, token)
        )
    else:
        server.login(email, password)
    result = server.send_message(msg, from_email, [*to, *cc, *bcc])
    server.quit()
    return result
