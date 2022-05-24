import os

from dotenv import load_dotenv
try:
    load_dotenv()
except IOError:
    pass

ACCOUNTS = [i.split(":") for i in os.environ.get("ACCOUNTS").split(" ")]
START_URL = os.environ.get("START_URL")

__all__ = ['ACCOUNTS', 'START_URL', ]
