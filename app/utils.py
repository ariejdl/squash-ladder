
import datetime

def pretty_now():
	return datetime.datetime.strftime(datetime.datetime.now(), "%YY/%m/%d %H:%M")

def basic_validation(args, required):
    for field, nice_name in required:
	    if field not in args:
		    return "%s invalid" % nice_name
	    elif args[field] is None:
		    return "%s not given" % nice_name

    return None
