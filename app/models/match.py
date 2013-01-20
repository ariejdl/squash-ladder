
import pymongo

from bson import ObjectId

from app.models.utils import one_week
from app.models.column import Column

class MatchModel(Column):

    column_name = "match"

    def get_default(self):
        return {
            "player_1": None,
            "player_2": None,
            "date": None,
            "scores": [(0,9),(9,0)],
            "player_1_winner": True
            }

    def get_recent(self, date=one_week(14), limit=20):
        out = []
        for match in self.col.find({'date': {"$gte": date}}).sort('date', pymongo.DESCENDING).limit(limit):
            out.append(match)
        return out
        
    def get_last(self, u_id, limit=10):
        out = []
        for match in self.col.find({ "$or": [{'player_1': u_id}, {'player_2': u_id}] }).sort('date', pymongo.DESCENDING).limit(limit):
            out.append(match)
        return out
