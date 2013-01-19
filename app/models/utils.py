
import datetime

def one_week(days=7):
    delta = datetime.timedelta(days=days)
    today = datetime.datetime.now()
    return today - delta
