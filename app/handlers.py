import tornado.auth
import tornado.escape
import tornado.gen
import tornado.websocket
import tornado.httpserver
from tornado.ioloop import IOLoop

from voluptuous import *

from app.match_validations import record_match_validations

from app.models.challenge import ChallengeState

import datetime

import json
from app.utils import pretty_now, basic_validation

from settings import Settings

from bson import ObjectId

import logging
log = logging.getLogger()

def json_ser(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.time) or isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, '%Y-%m-%d')
    

def good_response(data = False):
    out = {'good': True, 'data': data} if data else {'good': True}
    return json.dumps(out, default=json_ser)

def bad_response(data = False):
    out = {'good': False, 'data': data} if data else {'good': False}
    return json.dumps(out, default=json_ser)

def cur_user(req):
    c = req.get_secure_cookie(Settings.auth)
    if c:
        u = req.db.User.find_one(str(c.decode('utf-8')))
        if u:
            return u
        else:
            req.clear_cookie(Settings.auth)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return cur_user(self)

    @property
    def db(self):
        return self.application.db

errors = {
    "1": "please fill in both fields",
    "2": "no spaces allowed in username",
    "3": "invalid username and password combination",
    "4": "username already taken"
}

def tidy_user(user):
    fst, lst = user.get('firstname'), user.get('lastname')
    if fst and lst:
        user['name'] = fst + ' ' + lst
    elif fst:
        user['name'] = fst
    elif 'name' not in user or not user['name']:
        user['name'] = user['username']

    if 'played_count' not in user or not user['played_count']:
        user['played_count'] = 0

    user['unique_username'] = user['username']

    del user['password']
    del user['username']

    return user
    

def tidy_users(users, me):
    for user in users:
        user = tidy_user(user)

        if me and user['_id'] == me['_id']:
            me = user

    return me, users

def get_user_lookup(user_list):
    return {u['_id']: u for u in user_list}

def tidy_match(match, user_lookup):
    p1, p2 = user_lookup.get(match['player_1']), user_lookup.get(match['player_2'])

    if p1 and p2:
        date_pretty = datetime.datetime.strftime(match['date'], '%a %d %b')
        match['date'] = datetime.datetime.strftime(match['date'], '%Y-%m-%d')

        return {
            'date': match['date'],
            'date_pretty': date_pretty,
            'player_1_winner': match['player_1_winner'],
            'scores': match['scores'],
            'player_1_id': p1['_id'],
            'player_1_name': p1['name'],
            'player_2_id': p2['_id'],
            'player_2_name': p2['name']
        }

def tidy_matches(matches, user_lookup):
    out = []

    for match in matches:
        match = tidy_match(match, user_lookup)
        if match:
            out.append(match)

    return out


def tidy_comment(comment, user_lookup):
    user = user_lookup.get(comment['sender_id'])
    if user:
        comment['sender_name'] = user['name']
        comment['date_pretty'] = datetime.datetime.strftime(comment['date'], '%a %d %b %H:%M')
        comment['date'] = datetime.datetime.strftime(comment['date'], '%Y-%m-%d %H:%M:%S')
        return comment

def tidy_comments(comments, user_lookup):
    out = []
    for comment in comments:
        comment = tidy_comment(comment, user_lookup[comment['sender_id']])
        if coment:
            out.append(comment)

    return out

def combine_matches_comments(matches, comments, user_lookup):
    combined = []

    for match in matches:
        when = match['date']
        match = tidy_match(match, user_lookup)
        if match:
            combined.append({
                    'when': when,
                    'is_match': True,
                    'content': match
             })

    for comment in comments:
        when = comment['date']
        comment = tidy_comment(comment, user_lookup)
        if comment:
            combined.append({
                    'when': when,
                    'is_match': False,
                    'content': comment
             })

    combined = sorted(combined, key=lambda c: c['when'], reverse=True)
    return combined

def tidy_challenge(c, user_lookup):
    p1, p2 = user_lookup.get(c['sender_id']), user_lookup.get(c['recipient_id'])
    if p1 and p2:
        c['date_pretty'] = datetime.datetime.strftime(c['date'], '%a %d %b at %H:%M')
        c['sender_name'] = p1['name']
        c['recipient_name'] = p2['name']
        return c

def process_challenges(challenges, my_id, user_lookup):
    challenges = sorted(challenges, key=lambda x: x['date'], reverse=True)
    received, responded = [], []

    for c in challenges:
        c = tidy_challenge(c, user_lookup)
        if c:
            if c['state'] == ChallengeState.Pending and c['recipient_id'] == my_id:
                received.append(c)
            if c['state'] == ChallengeState.Accepted and c['sender_id'] == my_id:
                responded.append(c)

    return received, responded

class MainHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self):
        u = self.current_user

        users = sorted(self.db.User.find_all(), key=lambda x: x['position'])
        u, users = tidy_users(users, u)
        others = [user for user in users if user['_id'] != u['_id']]

        user_lookup = get_user_lookup(users)

        matches = self.db.Match.get_recent()
        comments = self.db.Comment.get_recent()
        challenges = self.db.Challenge.get_user_challenges(u['_id'])

        c_received, c_responded = process_challenges(challenges, u['_id'], user_lookup)

        matches_and_comments = combine_matches_comments(matches, comments, user_lookup)

        self.render("index.html",
                    me=u,
                    others=others,
                    users=users,
                    challenges_received=c_received,
                    challenges_responded=c_responded,
                    matches_comments=matches_and_comments)

class LogoutHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        self.clear_cookie(auth)

class LoginHandler(BaseHandler):
    def get(self):
        err = self.get_argument("error", None)
        if err in errors:
            err = errors[err]

        self.render("login.html", error=err)

    def post(self):
        up = str(self.get_argument("username", "")), str(self.get_argument("password", ""))
        self.clear_cookie(Settings.auth)

        sign_up = bool(self.get_argument("sign_up", None))
        sign_in = bool(self.get_argument("sign_in", None))

        if sign_up:
            if ' ' in up[0]:
                self.redirect('/login?error=2')
                return
            elif up[0] and up[1]:
                u = self.db.User.find_by_username(up[0])
                if u:
                    self.redirect('/login?error=4')
                    return
                else:
                    u_id = self.db.User.create_new(*up)
                    self.set_secure_cookie(Settings.auth, str(u_id))
                    self.redirect('/')
                    return
            else:
                self.redirect('/login?error=1')
                return

        elif sign_in:
            u = self.db.User.find_by_username_password(*up)
            if u:
                self.set_secure_cookie(Settings.auth, str(u['_id']))
                self.redirect('/')
                return
            else:
                self.redirect('/login?error=3')
                return


# should be able to delete accounts (e.g. if outsider starts abusing it)
class AdminLoginHandler(BaseHandler):
    def get(self):
        self.render("admin_login.html", errors=[])

    def post(self):
        up = str(self.get_argument("username", "")), str(self.get_argument("password", ""))

        valid_combinations = [('widget', 'thecat')]

        if (up in valid_combinations):
            u_id = self.db.User.insert(self.db.User.get_default())
            self.set_secure_cookie(Settings.auth, str(u_id))
            self.redirect("/")
        else:
            self.clear_cookie(Settings.auth)
            self.redirect("/login")

def sanitised_params(args):
    return {arg: args[arg][0].decode('utf-8') for arg in args}

def sanitised_int_params(args):
    args = sanitised_params(args)
    for arg in args:
        try: args[arg] = int(args[arg])
        except: pass

    return args


def calc_winner(games):
    player_1, player_2 = 0, 0

    for v1, v2 in games:
        if v1 > v2: player_1 += 1
        else: player_2 += 1

    return player_1 > player_2

class RecordMatchHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        args = sanitised_int_params(self.request.arguments)
        bad, dt, player_2, valid_games = record_match_validations(self, args)

        if bad or (dt is None) or (player_2 is None) or (not valid_games):
            self.write(bad_response(bad))
            return
        else:
            player_1_id = ObjectId(self.current_user['_id'])
            player_2_id = ObjectId(args['other_player_id'])

            player_1_winner = calc_winner(valid_games)

            match = self.db.Match.get_default()
            match['player_1'] = player_1_id
            match['player_2'] = player_2_id
            match['date'] = dt
            match['scores'] = valid_games
            match['player_1_winner'] = player_1_winner

            self.db.Match.insert(match)

            player_1 = self.current_user

            lower_player_orig, higher_player_orig = None, None
            if player_1['position'] < player_2['position']:
                higher_player_orig = player_1
                lower_player_orig = player_2
            else:
                higher_player_orig = player_2
                lower_player_orig = player_1
                
            lower_player_new, higher_player_new = None, None
            if player_1_winner:
                higher_player_new = player_1
                lower_player_new = player_2
            else:
                higher_player_new = player_2
                lower_player_new = player_1

            self.db.User.inc_played_count(lower_player_new['_id'])
            self.db.User.inc_played_count(higher_player_new['_id'])

            if higher_player_new['_id'] != higher_player_orig['_id']:
                self.db.User.push_players_down(higher_player_orig['position'], lower_player_orig['position'])
                self.db.User.update_position(higher_player_new['_id'], higher_player_orig['position'])

            u, users = tidy_users(self.db.User.find_all(), self.current_user)
            user_lookup = get_user_lookup(users)
            matches = tidy_matches([match], user_lookup)

            users = sorted(users, key=lambda x: x['position'])

            self.write(good_response({
                        'positions': users,
                        'player_1_id': player_1_id,
                        'player_2_id': player_2_id,
                        'match': matches[0]
                        }))


send_challenge_args = [
    ('user_id', 'player')
]

class SendChallengeHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        args = sanitised_params(self.request.arguments)
        bad = basic_validation(args, send_challenge_args)

        if bad:
            self.write(bad_response(bad))
            return
        else:
            recipient_id = ObjectId(args['user_id'])
            recipient = self.db.User.find_one(recipient_id)
            if not recipient:
                self.write(bad_response('invalid recipient'))
                return

            comment = args.get('comment')
                
            c = self.db.Challenge.get_default()
            c['sender_id'] = self.current_user['_id']
            c['recipient_id'] = recipient_id
            if comment is not None: c['comments'].append(comment)

            c = self.db.Challenge.insert(c)            
            self.write(good_response())

respond_challenge_args = [
    ('challenge_id', 'challenge'),
    ('state', 'state'),
]

class RespondChallengeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        args = sanitised_params(self.request.arguments)
        bad = basic_validation(args, respond_challenge_args)

        if bad:
            self.write(bad_response(bad))
            return
        else:
            state = args['state']
            challenge_id = ObjectId(args['challenge_id'])
            challenge = self.db.Challenge.find_one(challenge_id)

            if not challenge:
                self.write(bad_response('invalid challenge'))
                return

            if state == 'accept':
                comment = args.get('comment')
                sender_id = ObjectId(args.get('sender_id'))
                valid = (challenge['recipient_id'] == self.current_user['_id']) and (challenge['sender_id'] == sender_id)
                if not valid:
                    self.write(bad_response('invalid challenge'))
                    return

                challenge['state'] = ChallengeState.Accepted
                if comment is not None: challenge['comments'].append(comment)

                self.db.Challenge.update(challenge['_id'], challenge)
                self.write(good_response())

            elif state == 'decline':
                valid = challenge['recipient_id'] == self.current_user['_id']

                if not valid:
                    self.write(bad_response('invalid challenge'))
                    return

                self.db.Challenge.delete(challenge_id)
                self.write(good_response())

            elif state == 'close':
                valid = challenge['sender_id'] == self.current_user['_id']

                if not valid:
                    self.write(bad_response('invalid challenge'))
                    return

                self.db.Challenge.delete(challenge_id)
                self.write(good_response())



make_comment_args = [
    ('comment', 'comment')
]

class MakeCommentHandler(BaseHandler):
    def get(self):
        args = sanitised_params(self.request.arguments)
        bad = basic_validation(args, make_comment_args)
        
        if bad:
            self.write(bad_response(bad))
        else:
            comment = self.db.Comment.get_default()
            comment['sender_id'] = self.current_user['_id']
            comment['body'] = args['comment']
            self.db.Comment.insert(comment)

            comment = tidy_comment(comment, { self.current_user['_id']: tidy_user(self.current_user) })
            
            self.write(good_response(comment))


class ManualUpdateLadderHandler(BaseHandler):
    def get(self):
        args = sanitised_params(self.request.arguments)
        order = json.loads(args.get('order', '[]'))
        if not order:
            self.write(bad_response())
            return

        order = [ObjectId(u_id) for u_id in order]
        users = self.db.User.find_all()
        # ensure have valid users
        user_ids = set([u['_id'] for u in users])
        if set(order) != set(user_ids):
            self.write(bad_response('invalid users'))
            return

        comment = self.db.Comment.get_default()
        comment['sender_id'] = self.current_user['_id']
        comment['body'] = 'automatic message: I updated the order manually'
        self.db.Comment.insert(comment)
        comment = tidy_comment(comment, { self.current_user['_id']: tidy_user(self.current_user) })

        for i, u_id in enumerate(order):
            self.db.User.update_position(u_id, i + 1)

        u, users = tidy_users(self.db.User.find_all(), self.current_user)
        users = sorted(users, key=lambda x: x['position'])

        self.write(good_response({ 'users':  users, 'comment': comment}))

class ProfileHandler(BaseHandler):

    def get(self, username):
        user = self.db.User.find_by_username(username)

        if user:
            user = tidy_user(user)

            me = self.current_user
            users = sorted(self.db.User.find_all(), key=lambda x: x['position'])
            me, users = tidy_users(users, me)

            last_matches = self.db.Match.get_last(user['_id'])

            user_lookup = get_user_lookup(users)
            last_matches = tidy_matches(last_matches, user_lookup)

            if me and me['_id'] == user['_id']:
                self.render("profile.html", profile=user, edit=True, matches=last_matches)
            else:
                self.render("profile.html", profile=user, edit=False, matches=last_matches)

        else:
            self.redirect('/')

class ProfileUpdateHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        args = sanitised_params(self.request.arguments)

        user_id = args.get('user_id', None)
        firstname = args.get('firstname', None)
        lastname = args.get('lastname', None)
        user = self.current_user


        if ObjectId(user_id) == user['_id']:
            if firstname: user['firstname'] = firstname
            if lastname: user['lastname'] = lastname
            
            if firstname or lastname:
                self.db.User.update(user['_id'], user)

            self.redirect('/profile/' + user['username'])
        else:
            self.redirect('/')



class RulesHandler(BaseHandler):
    def get(self):
        user = self.current_user
        user = tidy_user(user) if user else None
        
        self.render("rules.html", profile=user)

class CourtsHandler(BaseHandler):
    def get(self):
        user = self.current_user
        user = tidy_user(user) if user else None

        self.render("courts.html", profile=user)

