import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from random import choices

ALPHA = 'abcdef0123456789'


class SmtpClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def get_server(self):
        server = smtplib.SMTP_SSL(self.host, 465)
        server.login(self.username, self.password)
        return server

    @property
    def message_id(self):
        return "%s-%s-%s-%s" % (
            "".join(choices(ALPHA, k=8)),
            "".join(choices(ALPHA, k=8)),
            "".join(choices(ALPHA, k=8)),
            "".join(choices(ALPHA, k=8))
        )

    def send_mail(self, to, plain_text, subject, attachments=None, html=None, **headers):
        msg_id = self.message_id
        msg = MIMEMultipart('mixed')
        msg["Message-Id"] = msg_id
        msg["Subject"] = Header(subject, 'utf8')
        msg["From"] = self.username
        msg["To"] = to
        for name, val in headers.items():
            msg[name] = Header(val, 'utf8')
        text = MIMEMultipart('alternative')
        text.attach(MIMEText(plain_text, 'plain'))
        if html:
            text.attach(MIMEText(html, 'html'))
        msg.attach(text)
        if attachments:
            for mimetype, name, file in attachments:
                content_type = mimetype
                part = MIMEBase(*content_type.split('/'), name=name)
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(name))
                msg.attach(part)
        server = self.get_server()
        server.send_message(msg, self.username, to)
        server.quit()
        return msg_id
