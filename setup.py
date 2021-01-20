from setuptools import setup


def get_requirements():
    with open('requirements.txt') as f:
        return [l.strip() for l in f.readlines()]


setup(
    install_requires=get_requirements()
)
