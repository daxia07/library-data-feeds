import os


def get_name():
    return os.environ.get('APP_NAME')


def main():
    print(get_name())
