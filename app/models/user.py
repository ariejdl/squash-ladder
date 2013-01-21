
import pymongo

from bson import ObjectId

from app.models.column import Column

class UserModel(Column):

    column_name = "user"

    def get_default(self):
        return {
            "firstname": None,
            "lastname": None,
            "username": None,
            "password": None,
            "position": 1,
            "played_count": 0,
            "new_user": True
        }

    def find_last_position(self):
        res = self.col.find().sort('position', pymongo.DESCENDING).limit(1)
        if not res: return
        for i in res:
            return i.get('position')

    def create_new(self, username, password):
        assert username and password

        position = self.find_last_position()
        if position is None: position = 0

        neu = self.get_default()
        neu['username'] = username
        neu['password'] = password
        neu.setdefault('position', 1)
        if position: neu['position'] = position + 1

        return self.insert(neu)

    def find_by_username(self, username):
        return self.col.find_one({ 'username': username })

    def find_by_username_password(self, username, password):
        return self.col.find_one({ 'username': username, 'password': password })

    def push_players_down(self, start, end):
        self.col.update({'position': {"$gte": start, "$lte": end }}, {"$inc" : { "position": 1 }}, multi=True)

    def inc_played_count(self, u_id):
        self.col.update({'_id': ObjectId(u_id)}, {"$inc": {'played_count': 1}})

    def update_position(self, u_id, pos):
        self.col.update({'_id': ObjectId(u_id)}, {"$set": {'position': pos}})

