==========
ZenMailbox
==========

ZenMailbox provides functionality to sync inbox with Django admin, thread messages, and reply in threads.

Installation
------------
1. Install package using pip::

    pip install django-zenmailbox

In order to use ckeditor in html text fields add use this command instead::

    pip install django-zenmailbox[ckeditor]

Quick start
-----------

1. Add "zenmailbox" to your INSTALLED_APPS::

    INSTALLED_APPS = [
        ...
        'zenmailbox',
        'ckeditor' # if you installed package with ckeditor extra requirement
    ]

2. Run ``python manage.py migrate`` to create mail models.

3. Start the development server and visit http://127.0.0.1:8000/admin/zenmailbox/mailbox/
   to create mailbox.

4. Choose created mailbox then use action Fetch mail. It can take a while.

5. Setup ``zenmailbox.mailbox_manager.fetch_new_mail`` calling periodically (celerybeat, cron etc)

Settings
--------
To change reply template place it under ``zenmailbox/reply.html``

Django settings entries::

    ZENMAILBOX_ATTACHMENTS_FOLDER = os.path.join(BASE_DIR, 'attachments')
    ZENMAILBOX_ATTACHMENT_PATH_FORMAT = '{mailbox.id}/{folder.id}/{mail.id}/{attachment.filename}'
    ZENMAILBOX_CKEDITOR_SETTINGS = "default"
