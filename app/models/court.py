
from bson import ObjectId

from app.models.column import Column

class CourtModel(Column):

    column_name = "court"

    default = {
		  "name": None,
			"lat": None,
			"long": None
    }