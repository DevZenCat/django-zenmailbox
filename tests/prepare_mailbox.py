from tests.test_smtp import SmtpClient
from tests.conf import PASSWORD_SENDER, USERNAME_RECEIVER, USERNAME_SENDER

client = SmtpClient('smtp.yandex.ru', USERNAME_SENDER, PASSWORD_SENDER)

client.send_mail(
    USERNAME_RECEIVER,
    "here is beautiful panda image!",
    "pandas is cute",
    [
        ("images/jpeg", 'panda0.jpg', open('tests/attachments/panda0.jpg', 'br'))
    ]
)
