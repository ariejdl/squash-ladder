
import logging
log = logging.getLogger()

from pymongo import Connection
from pymongo.database import Database

import urllib

def connect(conf, prod):
    log.info('setting up mongo connection')

    url = conf.get('mongo', 'url')
    port = conf.getint('mongo', 'port')
    db = conf.get('mongo', 'db')

    conn = Connection(url, port)
    db = Database(conn, db)

    if (prod):
        log.info('authenticating mongo connection')
        username = conf.get('mongo', 'username')
        pwd = conf.get('mongo', 'password')

        db.authenticate(username, pwd)

    return db


