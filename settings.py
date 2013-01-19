import base64
from uuid import UUID

import configparser
import logging

logger = logging.getLogger()

class Settings(object):

    @classmethod
    def setup(cls, PROD):
        Config = configparser.ConfigParser()

        logger.info('reading config settings: %s' 'PROD' if PROD else 'DEV')
        if PROD: Config.read('config/prod.conf')
        else: Config.read('config/dev.conf')

        cls.config = Config
        cls.PROD = PROD
        cls.secret = cls.getSecret()
        cls.auth = "auth_token"


    @classmethod
    def getSecret(cls):
        token1 = cls.config.get('secret', 'token-1')
        token2 = cls.config.get('secret', 'token-2')

        asB64 = base64.b64encode(UUID(token1).bytes + UUID(token2).bytes)

        return asB64
