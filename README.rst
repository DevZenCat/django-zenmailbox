==========
ZenMailbox
==========

ZenMailbox provides functionality to sync inbox with Django admin, thread messages, and reply in threads.

Quick start
-----------

1. Add "zenmailbox" to your INSTALLED_APPS::

    INSTALLED_APPS = [
        ...
        'zenmailbox',
    ]

2. Run ``python manage.py migrate`` to create mail models.

3. Start the development server and visit http://127.0.0.1:8000/admin/
   to create mailbox.

4. Call ``zenmailbox.mailbox_manager.fetch_all_mail``. It can take a while.

5. Setup ``zenmailbox.mailbox_manager.fetch_new_mail`` calling periodically (celerybeat, cron etc)

Settings
--------
Django settings entries::

    ZENMAILBOX_ATTACHMENTS_FOLDER = os.path.join(BASE_DIR, 'attachments')
    ZENMAILBOX_ATTACHMENT_PATH_FORMAT = '{mailbox.id}/{folder.id}/{mail.id}/{attachment.filename}'

