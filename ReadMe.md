# Tornado Squash Ladder

- a squash ladder written in Python's Tornado, mongodb database, designed for deployment on heroku.
- pretty feature rich:
	- thorough match validation
	- challenge user feature
	- activity feed of matches and comments
	- public profile links, with recent match summaries
	- drag and drop ladder rearrangement in case of errors
	- all these features ajaxified and xsrf tokened in a pretty UI.
- tested in IE9, chrome, safari and firefox
	
- I did this in about 20hrs.

### Notes
- using python 3.3
- set if dev or prod in web.py
- set mongodb database information in config/
