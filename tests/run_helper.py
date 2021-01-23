#!/usr/bin/env python
HELPER_SETTINGS = {
    'INSTALLED_APPS': [],
    'ALLOWED_HOSTS': ['localhost", "127.0.0.1", "dev.thepeshka.ru']
}


def run():
    from app_helper import runner
    runner.run('zenmailbox')


if __name__ == '__main__':
    run()