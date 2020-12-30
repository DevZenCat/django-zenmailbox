from .default_settings import *

INSTALLED_APPS = INSTALLED_APPS + ['zenmailbox']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ZENMAILBOX_ATTACHMENTS_FOLDER = os.path.join(BASE_DIR, 'attachments')
ZENMAILBOX_ATTACHMENT_PATH_FORMAT = '{mailbox.id}/{folder.id}/{mail.id}/{attachment.filename}'
