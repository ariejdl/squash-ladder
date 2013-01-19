
from app.utils import basic_validation

import datetime

# mandatory arguments
record_match_games = [
    ('game1-me', 'game 1'), ('game1-other', 'game 1'),
    ('game2-me', 'game 2'), ('game2-other', 'game 2'),
    ('game3-me', 'game 3'), ('game3-other', 'game 3'),
]

record_match_games_full = record_match_games + [
    ('game4-me', 'game 4'), ('game4-other', 'game 4'),
    ('game5-me', 'game 5'), ('game5-other', 'game 5'),
]

record_match_pairs = [
    ('game1-me', 'game1-other', 'game 1'),
    ('game2-me', 'game2-other', 'game 2'),
    ('game3-me', 'game3-other', 'game 3'),
    ('game4-me', 'game4-other', 'game 4'),
    ('game5-me', 'game5-other', 'game 5'),
]

record_match_all_games = [
    'game1-me', 'game1-other',
    'game2-me', 'game2-other',
    'game3-me', 'game3-other',
    'game4-me', 'game4-other',
    'game5-me', 'game5-other',
]


record_match_args = [
    ('other_player_id', 'other player'),
    ('date', 'date'),
    ('month', 'month'),
    ('year', 'year'),
] + record_match_games

def datetime_valid(date, month, year):
    try:
        return datetime.datetime.strptime('%s-%s-%s' %
                                          (year, month, date),
                                          '%Y-%b-%d')
    except ValueError:
        pass

def must_be_int(args, required):
    for arg, nice_name in required:
        if arg in args:
            if args[arg] is None:
                continue
            elif not isinstance(args[arg], int):
                return "%s not an integer" % nice_name

def paired_games(args, pairs):
    for key1, key2, nice_name in pairs:
        v1 = args.get(key1)
        v2 = args.get(key2)

        if type(v1) != type(v2):
            return "%s is incomplete" % nice_name
        elif isinstance(v1, int):
            if v1 == v2:
                return "%s is a draw" % nice_name
            elif not ((v1 >= 9) or (v2 >= 9)):
                return "%s isn't finished" % nice_name

def record_match_validations(req, args):
    bad = None
    dt = None
    player_2 = None
    valid_games = None

    try:
        bad = basic_validation(args, record_match_args)
        if bad: raise Exception()

        dt = datetime_valid(args['date'], args['month'], args['year'])
        bad = "invalid date"
        if not dt: raise Exception()

        bad = must_be_int(args, record_match_games_full)
        if bad: raise Exception()

        bad = paired_games(args, record_match_pairs)
        if bad: raise Exception()

        bad = "invalid player"
        player_2 = req.db.User.find_one(args['other_player_id'])
        if player_2 is None: raise Exception()

        valid_games = []
        for i, game in enumerate(record_match_all_games):
            if i % 2 == 0:
                score1 = args.get(record_match_all_games[i])
                score2 = args.get(record_match_all_games[i+1])
                if (score1 is not None) and (score2 is not None):
                    valid_games.append((score1, score2))


        games_1_won = sum([1 if (game[0] > game[1]) else 0 for game in valid_games])
        games_2_won = sum([1 if (game[1] > game[0]) else 0 for game in valid_games])
        win_count = games_1_won if (games_1_won > games_2_won) else games_2_won

        bad = 'no outright winner'
        if games_1_won == games_2_won: raise Exception()
        
        bad = 'even number of won games'
        if win_count % 2 == 0: raise Exception()

        bad = None

    except Exception as e:
        #raise e
        pass

    return bad, dt, player_2, valid_games
