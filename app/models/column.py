
from bson import ObjectId

class Column(object):

    def __init__(self, db):
        if not self.column_name:
            raise Exception('no column_name')

        self.col = db[self.column_name]


    def get_default(self):
        return {}

    def insert(self, doc):
        _id = str(self.col.insert(doc))
        return _id

    def find_one(self, _id):
        return self.col.find_one(ObjectId(_id));

    def update(self, _id, doc):
        return self.col.update({'_id': ObjectId(_id)}, doc);

    def find_all(self):
        """be careful"""
        out = []
        for doc in self.col.find():
            out.append(doc)
        return out

    def find_ids(self, ids):
        out = []
        docs = self.col.find({ '_id': { '$in': ids }})
        for doc in docs:
            out.append(doc)

        return out

    def delete(self, _id):
        return self.col.remove(_id);


