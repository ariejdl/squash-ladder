
import datetime

from bson import ObjectId

from app.models.column import Column

class ChallengeState:
    Pending = 1
    Accepted = 2

class ChallengeModel(Column):

    column_name = "challenge"

    def get_default(self, date=None):
        if date is None: date = datetime.datetime.now()

        return {
            "sender_id": None,
            "recipient_id": None,
            "date": date,
            "state": ChallengeState.Pending,
            "comments": [],
        }

    def get_user_challenges(self, u_id):
        out = []
        for doc in self.col.find({ "$or": [{'sender_id': u_id}, {'recipient_id': u_id}] }):
            out.append(doc)
        return out

        
