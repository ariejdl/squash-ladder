import os.path
import os
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata

import logging

from app.handlers import *

from settings import Settings

import app.models.mongo_conn
from app.models.user import UserModel
from app.models.court import CourtModel
from app.models.match import MatchModel
from app.models.challenge import ChallengeModel
from app.models.comment import CommentModel

from app import utils

from tornado.options import define, options

PROD = False
PORT = 5000
logger = logging.getLogger(__name__)
Settings.setup(PROD)

define("PORT", default=PORT, type=int)

class DBWrapper(object):
	def __init__(self, db):
		self.User = UserModel(db)
		self.Match = MatchModel(db)
		self.Challenge = ChallengeModel(db)
		self.Court = CourtModel(db)
		self.Comment = CommentModel(db)

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/", MainHandler),
			(r"/login", LoginHandler),
			(r"/admin_login", AdminLoginHandler),
			(r"/logout", LogoutHandler),

			(r"/record_match", RecordMatchHandler),
			(r"/send_challenge", SendChallengeHandler),
			(r"/respond_challenge", RespondChallengeHandler),
			(r"/make_comment", MakeCommentHandler),
			(r"/manual_update_ladder", ManualUpdateLadderHandler),

			(r"/profile/(.*)", ProfileHandler),
			(r"/profile_update", ProfileUpdateHandler),

			(r"/rules", RulesHandler),
			(r"/courts", CourtsHandler),
		]

		settings = dict(
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
			static_path=os.path.join(os.path.dirname(__file__), "static"),
			cookie_secret=Settings.secret,
			login_url="/login",
			xsrf_cookies=True,
			debug=True
		)

		db = app.models.mongo_conn.connect(Settings.config, PROD)
		self.db = DBWrapper(db)

		tornado.web.Application.__init__(self, handlers, **settings)


def main():
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())

	port = os.environ.get("PORT", PORT)
	http_server.listen(port)

	logger.info("starting up on %s" % port)

	tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
	main()
