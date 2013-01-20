
//=require "_jquery"
//=require "_spin"

//=require "_toolman_full"


$(function main() {

    Ladder.init();
    MatchesAndComments.init();
    Forms.init();
    ChallengeList.init();

});

var MatchesAndComments = (function() {
    var area, commentsCheckbox;

    function refreshComments() {
        if (commentsCheckbox.is(':checked')) {
            area.find('.item.comment').show();
        } else {
            area.find('.item.comment').hide();            
        }
    }

    function gameNodes(scores) {
        var i = 0, len = scores.length, out = "";

        for (;i < len;i++) {
            var oneWin = scores[i][0] > scores[i][1],
                twoWin = scores[i][1] > scores[i][0];

            out +=('<div class="game">' +
                '<div class="score ' + (oneWin ? 'winner' : '') + '">' +scores[i][0] + '</div>' +
                '<div class="score ' + (twoWin ? 'winner' : '') + '">' +scores[i][1] + '</div>' +
              '</div>');
        }

        return out;
    }

    function matchNodes(match) {
        if (!match.player_1_winner) {
            var temp = match.player_1_name,
                scores = [], i = 0, len = match.scores.length;

            match.player_1_name = match.player_2_name;
            match.player_2_name = temp;

            for (;i < len;i++) { scores.push([match.scores[i][1], match.scores[i][0]]); }
            
            match.scores = scores;
        }

        var nodes = $('<li item_date="' + match.date + '" class="item match flash-new">' +
          '<div class="top">' +
          '<div class="player1">' + match.player_1_name + '</div><i>beat</i>'+ 
          '<div class="player2">'+ match.player_2_name + '</div>' +
          '<div class="date">' + match.date_pretty + '</div>' +
          '</div>' +
          '<div class="bottom">' + gameNodes(match.scores) + '</div>' +
          '</li>');

        setTimeout(function() { nodes.removeClass('flash-new'); }, 250);

        return nodes[0];
    }

    function commentNodes(comment) {
        var nodes = $('<li class="item comment flash-new" style="">' +
                   '<div class="sender-name">' + comment.sender_name + '</div>' +
                   '<div class="text">' + comment.body + '</div>' + 
                   '<div class="date">' + comment.date_pretty + '</div>' +
                 '</li>').attr('item_date', comment.date);

        setTimeout(function() { nodes.removeClass('flash-new'); }, 250);

        return nodes[0];
    }

    function parseDate(d) {
        var split = d.split(' '),
            split2 = split[0].split('-'),
            split3 = (split.length > 1) ? split[1].split(':') : undefined,
            date = new Date(parseInt(split2[0]),
                            parseInt(split2[1]),
                            parseInt(split2[2]));

        if (split3) {
            date.setHours(parseInt(split3[0]));
            date.setMinutes(parseInt(split3[1]));
            date.setSeconds(parseInt(split3[2]));
        }

        return date;
    }

    function isMoreRecent(date1, date2) {
        return (parseDate(date1).getTime() - parseDate(date2).getTime()) > 0;
    }

    return {
        init: function() {
            area = $('.matches-comments-area');

            commentsCheckbox = $('#show-comments-label > input');
            commentsCheckbox.click(refreshComments);
            
        },
        addComment: function(comment) {
            var nodes = commentNodes(comment),
                dateFull = comment.date,
                given = false;

            $(area).children('.item').each(function() {
                if (given) return;
                if (isMoreRecent(dateFull, $(this).attr('item_date'))) {
                    $(this).before(nodes);
                    given = true;
                }
            });

            if (!given) {
                area.append(nodes);
            }
        },
        addMatch: function(match) {
            var nodes = matchNodes(match),
                dateFull = match.date,
                given = false;

            $(area).children('.item').each(function() {
                if (given) return;
                if (isMoreRecent(dateFull, $(this).attr('item_date'))) {
                    $(this).before(nodes);
                    given = true;
                }
            });

            if (!given) {
                area.append(nodes);
            }
        },
        refreshComments: refreshComments
    };


})();

/* toolman's globals */
var dragsort = ToolMan.dragsort();

var Ladder = (function() {
    var area,
        editing,
        saveBut,
        alert,
        editLadderBut;

    function rungNodes(user, updated) {
        var nodes = $('<li class="rung" user_id="' + user._id + '">'+
                      '<div class="filler"></div>'+
                      '<div class="position">' + user.position + '</div>'+
                      '<a href="/profile/' + user.unique_username + '" class="name">' + user.name + '</a>'+
                      '<div class="count">'+ user.played_count + '<div class="count-text">played</div>'+
                      '</div>'+
                      '</li>');

        if (updated) {
            nodes.addClass('flash-new');
            setTimeout(function() { nodes.removeClass('flash-new'); }, 250);
        }

        return nodes[0];
    }

    function verticalOnly(item) {item.toolManDragGroup.verticalOnly(); }
    function setupDraggability(area) {
        dragsort.makeListSortable(area,
                                  verticalOnly,
                                  new Function());
    }

    function swapInDraggability() {
        var par = area.parent(),
            newArea = area.clone();
        
        newArea.find('.name').each(function() {
            $(this).attr('href_cache', $(this).attr('href')).attr('href', '#');
        });
        
        area.detach();
        par.append(newArea);
        area = newArea;
        setupDraggability(area[0]);
    }

    function swapOutDraggability() {
        var par = area.parent(),
            newArea = area.clone();
        
        newArea.find('.name').each(function() {
            $(this).attr('href', $(this).attr('href_cache'));
        });
        
        area.detach();
        par.append(newArea);
        area = newArea;
    }

    function update(newLadder, idsAffected) {
        area.empty();
            $.each(newLadder, function() {
            area.append(rungNodes(this, this._id in idsAffected));
        });
    }

    function toggleEditOff() {
        saveBut.hide();
        editLadderBut.html('edit');
        swapOutDraggability();
        editing = false;
    }

    function toggleEditOn() {
        saveBut.show();
        editLadderBut.html('cancel');
        swapInDraggability();
        editing = true;
    }

    return {
        init: function() {
            area = $('.ladder');
            saveBut = $('#save-edit-ladder');
            alert = area.parent().find('.alert');
            editLadderBut = $('#edit-ladder');

            editLadderBut.click(function() {
                if (editing) toggleEditOff();
                else toggleEditOn.call();
            });


            $('#save-edit-ladder').click(function() {
                var newOrder = [];
                area.children('.rung').each(function() { newOrder.push($(this).attr('user_id')); });
                Comms.manualUpateLadder({ order: JSON.stringify(newOrder) }, function(d) {
                    if (d && d.good && d.data) {
                        Forms.updateAlert(alert, true, 'ladder updated');
                        toggleEditOff();
                        update(d.data.users, {});
                        MatchesAndComments.addComment(d.data.comment);
                    } else {
                        Forms.updateAlert(alert, true, 'there was a problem');                        
                    }
                }, function() {
                    Forms.updateAlert(alert, true, 'there was a problem');
                });
            });
        },
        update: update
    };

})();

var ChallengeList = (function(){

    function prepareReceived() {
        var nodes = $(this),
            accept = $(this).find('button')[0],
            decline = $(this).find('button')[1],
            comment = $(this).find('input'),
            alert = $(this).parent().find('.alert'),
            challenge_id = $(this).attr('challenge_id'),
            sender_id = $(this).attr('sender_id');

        $(accept).click(function() {
            Comms.respondChallenge({
                    'challenge_id': challenge_id,
                    'sender_id': sender_id,
                    'comment': comment.val(),
                    'state': 'accept'
            },
            function(d) {
                if (d && d.good) {
                    nodes.remove();
                    Forms.updateAlert(alert, true, 'challenge accepted');
                } else {
                    Forms.updateAlert(alert, false, 'something went wrong');
                }
            },
            function() {
                Forms.updateAlert(alert, false, 'something went wrong');
            });
        });

        $(decline).click(function() {
            Comms.respondChallenge({
                'challenge_id': challenge_id,
                'state': 'decline'
            },
            function(d) {
                if (d && d.good) {
                    nodes.remove();                    
                }
            },
            function() {
                Forms.updateAlert(alert, false, 'something went wrong');
            });
        });
    }

    function prepareAccepted() {
        var nodes = $(this),
            close = $(this).find('button')[0],
            alert = $(this).parent().find('.alert'),
            challenge_id = $(this).attr('challenge_id');

        $(close).click(function() {
            Comms.respondChallenge({
                'challenge_id': challenge_id,
                'state': 'close'
            },
            function(d) {
                if (d && d.good) {
                    nodes.remove();                    
                } else {
                    Forms.updateAlert(alert, false, 'something went wrong');                    
                }
            },
            function() {
                Forms.updateAlert(alert, false, 'something went wrong');
            });
        });
    }
                         
    return {
        init: function() {
            $('#received-challenges').children('.item').each(prepareReceived);
            $('#accepted-challenges').children('.item').each(prepareAccepted);


        }
    };

})();

var Forms = (function() {
    var recordMatchForm,
        sendChallengeForm,
        makeCommentForm;

    function resetDates(form) {
        var today = new Date(),
            date = today.getDate(),
            month = {
                0: 'jan', 1: 'feb', 2: 'mar',
                3: 'apr', 4: 'may', 5: 'jun',
                6: 'jul', 7: 'aug', 8: 'sep',
                9: 'oct', 10: 'nov', 11: 'dec'
            }[today.getMonth()],
            year = today.getFullYear();

        form.find('[name="date"]').val(date);
        form.find('[name="month"]').val(month);
        form.find('[name="year"]').val(year);

    }

    function setupForm(el, commsMethod, sucFn, failFn) {
        el.find('button[type="submit"]').click(function() {
            var form = el.serialize();
            Comms[commsMethod](form, sucFn, failFn);

            return false;
        });
    }

    function updateAlert(el, good, text) {
        el.removeClass('amber green').hide();

        if (text) {
            el.slideDown(150).html(text);

            if (good) el.addClass('green');
            else el.addClass('amber');

            setTimeout(function() { el.slideUp(); }, 5 * 1000);
        }

    }

    function recordMatchGood(d) {
        var alert = recordMatchForm.find('.alert');
        if (d && d.good) {
            var info = d.data.match.player_1_winner ? 'well done, match added' : 'match added';
            updateAlert(alert, true, info);

            $(recordMatchForm).find('input, select').val('');
            resetDates(recordMatchForm);

            var affected = {};
            affected[d.data.player_1_id] = true;
            affected[d.data.player_2_id] = true;

            Ladder.update(d.data.positions, affected);
            MatchesAndComments.addMatch(d.data.match);            

            MatchesAndComments.refreshComments();

        } else if (d.data) {
            updateAlert(alert, false, d.data);
        } else {
            updateAlert(alert, false, 'there was a problem');
        }
        
    }

    function recordMatchBad() {
        var alert = recordMatchForm.find('.alert');
        updateAlert(alert, false, 'There was a problem with that');

    }

    function sendChallengeGood(d) {
        var alert = sendChallengeForm.find('.alert');

        if (d && d.good) {
            updateAlert(alert, true, 'Challenge Sent');
            $(sendChallengeForm).find('select, textarea').val('');
        } else if (d.data) {
            updateAlert(alert, false, d.data);
        } else {
            updateAlert(alert, false, 'there was a problem');            
        }
        
    }

    function sendChallengeBad() {
        var alert = sendChallengeForm.find('.alert');
        updateAlert(alert, false, 'There was a problem with that');
    }

    function makeCommentGood(d) {
        var alert = makeCommentForm.find('.alert');

        if (d && d.good) {
            updateAlert(alert, true, 'Comment made!');
            $(makeCommentForm).find('textarea').val('');

            MatchesAndComments.addComment(d.data);

        } else if (d.data) {
            updateAlert(alert, false, d.data);
        } else {
            updateAlert(alert, false, 'there was a problem');            
        }

        MatchesAndComments.refreshComments();
        
    }

    function makeCommentBad() {
        var alert = makeCommentForm.find('.alert');
        updateAlert(alert, false, 'There was a problem with that');
    }

    return {
        init: function() {
            recordMatchForm = $("#record-match-form");
            sendChallengeForm = $("#send-challenge-form");
            makeCommentForm = $("#make-comment-form");

            setupForm(recordMatchForm, 'recordMatch',
                      recordMatchGood, recordMatchBad);

            setupForm(sendChallengeForm, 'sendChallenge',
                      sendChallengeGood, sendChallengeBad);

            setupForm(makeCommentForm, 'makeComment',
                      makeCommentGood, makeCommentBad);

            resetDates(recordMatchForm);
        },
        updateAlert: updateAlert
    };

})();

var Comms = (function() {
    function getCookie(name) {
        var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
        return r ? r[1] : undefined;
    }

    function getLoader(cont) {
        var opts = {
            lines: 18, length: 23, width: 5,
            radius: 23, corners: 1, rotate: 0,
            color: '#6B6659', speed: 1.7, trail: 37,
            shadow: false, hwaccel: false, className: 'spinner',
            zIndex: 1000, top: 'auto', left: 'auto'
        },
        spinner = new Spinner(opts).spin(cont);

        return spinner;
    }

    function sendWrapped(url, data, sucFn, failFn) {
        var loader = getLoader(document.body);

        data._xsrf = getCookie("_xsrf");
        $.ajax(url, { data: data, type: 'GET' })
                .success(function(d) {
                    loader.stop();
                    if (d) d = JSON.parse(d);
                    sucFn.call(this, d);
                })
                .error(function(d) {
                    loader.stop();
                    if (d) d = JSON.parse(d);
                    failFn.call(this, d);
                });
    }

    return {
        getLoader: getLoader,
        recordMatch: function(data, suc, fail) {
            sendWrapped('/record_match', data, suc, fail);
        },
        sendChallenge: function(data, suc, fail) {
            sendWrapped('/send_challenge', data, suc, fail);
        },
        makeComment: function(data, suc, fail) {
            sendWrapped('/make_comment', data, suc, fail);
        },
        respondChallenge: function(data, suc, fail) {
            sendWrapped('/respond_challenge', data, suc, fail);            
        },
        manualUpateLadder: function(data, suc, fail) {
            sendWrapped('/manual_update_ladder', data, suc, fail);                        
        }
    };

})();