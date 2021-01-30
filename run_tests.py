#!/usr/bin/env python
from tests.conf import USERNAME_RECEIVER, USERNAME_SENDER, PASSWORD_RECEIVER, PASSWORD_SENDER

HELPER_SETTINGS = {
    'USERNAME_RECEIVER': USERNAME_RECEIVER,
    'PASSWORD_RECEIVER': PASSWORD_RECEIVER,
    'USERNAME_SENDER': USERNAME_SENDER,
    'PASSWORD_SENDER': PASSWORD_SENDER
}


def run():
    from app_helper import runner
    runner.run('zenmailbox')


if __name__ == '__main__':
    run()
