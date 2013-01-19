
import pymongo

from bson import ObjectId

import datetime

from app.models.utils import one_week
from app.models.column import Column

class CommentModel(Column):

    column_name = "comment"

    def get_default(self, date=None):
        if date is None: date = datetime.datetime.now()

        return {
		  "sender_id": None,
                  "date": date,
		  "body": None
        }

    def get_recent(self, date=one_week(), limit=20):
        out = []
        for match in self.col.find({'date': {"$gte": date}}).sort('date', pymongo.DESCENDING).limit(limit):
            out.append(match)
        return out
