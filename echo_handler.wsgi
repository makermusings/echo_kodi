#!/usr/bin/env python

"""
The MIT License (MIT)

Copyright (c) 2015 Maker Musings

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# For a complete discussion, see http://www.makermusings.com

import datetime
import json
import os.path
import random
import re
import string
import sys

# Load the kodi.py file from the same directory where this wsgi file is located
sys.path += [os.path.dirname(__file__)]
import kodi


# These are words that we ignore when doing a non-exact match on show names
STOPWORDS = [
    "a",
    "about",
    "an",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "will",
    "with",
]


# Clean up show names to remove things like "(2005)" and "(US)" from their names

RE_SHOW_WITH_PARAM = re.compile(r"(.*) \([^)]+\)$")

def sanitize_show(show_name):
    m = RE_SHOW_WITH_PARAM.match(show_name)
    if m:
        return m.group(1)
    return show_name

def remove_the(name):
    # Very naive method to remove a leading "the" from the given string
    if name[:4].lower() == "the ":
        return name[4:]
    else:
        return name


# This utility function constructs the required JSON for a full Alexa Skills Kit response

def build_alexa_response(speech = None, session_attrs = None, card = None, reprompt = None, end_session = True):
    reply = {"version" : "1.0"}
    if session_attrs:
        reply['sessionAttributes'] = session_attrs
    response = {}
    if speech:
        response['outputSpeech'] = {'type':'PlainText', 'text':speech}
    if card:
        response['card'] = card
    if reprompt:
        response['reprompt'] = {'outputSpeech':{'type':'PlainText','text':reprompt}}
    response['shouldEndSession'] = end_session
    reply['response'] = response
    return json.dumps(reply)


# Handle the CheckNewShows intent

def alexa_check_new_episodes(slots):
    # Responds to the question, "Are there any new shows to watch?"

    # Get the list of unwatched EPISODES from Kodi
    new_episodes = kodi.GetUnwatchedEpisodes()

    # Find out how many EPISODES were recently added and get the names of the SHOWS
    really_new_episodes = [x for x in new_episodes if x['dateadded'] >= datetime.datetime.today() - datetime.timedelta(5)]
    really_new_show_names = list(set([sanitize_show(x['show']) for x in really_new_episodes]))

    if len(really_new_episodes) == 0:
        answer = "There isn't anything new to watch."
    elif len(really_new_show_names) == 1:
        # Only one new show, so provide the number of episodes also.
        count = len(really_new_episodes)
        if count == 1:
            answer = "There is one new episide of %(show)s to watch." % {"show":really_new_show_names[0]}
        else:
            answer = "You have %(count)d new episides of %(show)s." % {'count':count, 'show':really_new_show_names[0]}
    elif len(really_new_show_names) == 2:
        random.shuffle(really_new_show_names)
        answer = "There are new episodes of %(show1)s and %(show2)s." % {'show1':really_new_show_names[0], 'show2':really_new_show_names[1]}
    elif len(really_new_show_names) > 2:
        show_sample = random.sample(really_new_show_names, 2)
        answer = "You have %(show1)s, %(show2)s, and more waiting to be watched." % {'show1':show_sample[0], 'show2':show_sample[1]}
    return build_alexa_response(answer)


# Handle the NewShowInquiry intent.

def alexa_new_show_inquiry(slots):
    # Responds to the question, "Do we have any new episodes of <show>?"

    # Get the list of unwatched EPISODES from Kodi
    new_episodes = kodi.GetUnwatchedEpisodes()

    # Group the episodes by the show name in normalized format
    show_episodes = {}
    for one_episode in new_episodes:
        normalized = str(one_episode['show']).lower().translate(None, string.punctuation)
        if not normalized in show_episodes:
            show_episodes[normalized] = []
        show_episodes[normalized].append(one_episode)

    # See if we can match one of these to the show name the Echo heard
    
    heard_show =  str(slots['Show']['value']).lower().translate(None, string.punctuation)
    located = None
    fuzzy_match = False

    # Try an exact match first
    if heard_show in show_episodes:
        located = heard_show

    if not located:
        # Try an exact match after removing any leading "the"
        heard_minus_the = remove_the(heard_show)
        for one_show in show_episodes:
            if remove_the(one_show) == heard_minus_the:
                located = one_show
                break

    if not located:
        # See if the spoken show matches the beginning of our show names
        # removing leading "the" from both. E.g. "Daily Show" vs "Daily Show with Jon Stewart"
        for one_show in show_episodes:
            if heard_minus_the == remove_the(one_show)[:len(heard_minus_the)]:
                located = one_show
                break

    if not located:
        # Last resort -- take out some useless words and see if we have a show with
        # any of the remaining words in common
        heard_list = set([x for x in heard_show.split() if x not in STOPWORDS])
        for one_show in show_episodes:
            show_list = set(one_show.split())
            if heard_list & show_list:
                located = one_show
                fuzzy_match = True
                break

    if not located:
        answer = "There are no shows called %(show)s." % {'show': heard_show}
    else:
        if fuzzy_match:
            answer = "You asked about %(show)s. " % {'show': heard_show}
        else:
            answer = ""
        count = len(show_episodes[located])
        if count == 1:
            answer += "There is one unseen episode of %(real_show)s." % {'real_show': located}
        else:
            answer += "There are %(num)d episodes of  %(real_show)s." % {'real_show': located, 'num': count}
            

    return build_alexa_response(answer)





# Handle the WhatNewShows intent.

def alexa_what_new_episodes(slots):
    # Lists the shows that have had new episodes added to Kodi in the last 5 days

    # Get the list of unwatched EPISODES from Kodi
    new_episodes = kodi.GetUnwatchedEpisodes()

    # Find out how many EPISODES were recently added and get the names of the SHOWS
    really_new_episodes = [x for x in new_episodes if x['dateadded'] >= datetime.datetime.today() - datetime.timedelta(5)]
    really_new_show_names = list(set([sanitize_show(x['show']) for x in really_new_episodes]))
    num_shows = len(really_new_show_names)

    if num_shows == 0:
        # There's been nothing added to Kodi recently
        answers = [
            "You don't have any new shows to watch.",
            "There are no new shows to watch.",
        ]
        answer = random.choice(answers)
        if random.random() < 0.25:
            comments = [
                " Maybe you should go to the movies.",
                " Maybe you'd like to read a book.",
                " Time to go for a bike ride?",
                " You probably have chores to do anyway.",
            ]
            answer += random.choice(comments)
    elif len(really_new_show_names) == 1:
        # There's only one new show, so provide information about the number of episodes, too.
        count = len(really_new_episodes)
        if count == 1:
            answers = [
                "There is a single new episode of %(show)s." % {'show':really_new_show_names[0]},
                "There is one new episode of %(show)s." % {'show':really_new_show_names[0]},
            ]
        elif count == 2:
            answers = [
                "There are a couple new episodes of %(show)s" % {'show':really_new_show_names[0]},
                "There are two new episodes of %(show)s" % {'show':really_new_show_names[0]},
            ]
        elif count >= 5:
            answers = [
                "There are lots and lots of new episodes of %(show)s" % {'show':really_new_show_names[0]},
                "There are %(count)d new episodes of %(show)s" % {"count":count, "show":really_new_show_names[0]},
            ]
        else:
            answers = [
                "You have a few new episodes of %(show)s" % {'show':really_new_show_names[0]},
                "There are %(count)d new episodes of %(show)s" % {"count":count, "show":really_new_show_names[0]},
            ]
        answer = random.choice(answers)
    else:
        # More than one new show has new episodes ready
        random.shuffle(really_new_show_names)
        show_list = really_new_show_names[0]
        for one_show in really_new_show_names[1:-1]:
            show_list += ", " + one_show
        show_list += ", and " + really_new_show_names[-1]
        answer = "There are new episodes of %(show_list)s." % {"show_list":show_list}
    return build_alexa_response(answer)


# What should the Echo say when you just open your app instead of invoking an intent?

def prepare_help_message():
    help = "You can ask me whether there are any new shows, what new shows there are, or whether there are new episodes of a specific show."
    return build_alexa_response(help)


# This maps the Intent names to the functions that provide the corresponding Alexa response.

INTENTS = [
    ['CheckNewShows', alexa_check_new_episodes],
    ['NewShowInquiry', alexa_new_show_inquiry],
    ['WhatNewShows', alexa_what_new_episodes],
]


# Handle the requests that arrive from the Alexa Skills Kit when your app
# is invoked.

def do_alexa(environ, start_response):
    # Alexa requests come as POST messages with a request body
    try:
        length = int(environ.get('CONTENT_LENGTH', '0'))
    except ValueError:
        length = 0

    if length > 0:
        # Get the request body and parse out the Alexa JSON request
        body = environ['wsgi.input'].read(length)
        alexa_msg = json.loads(body)
        alexa_request = alexa_msg['request']

        if alexa_request['type'] == 'LaunchRequest':
            # This is the type when you just say "Open <app>"
            response = prepare_help_message()

        elif alexa_request['type'] == 'IntentRequest':
            # Get the intent being invoked and any slot values sent with it
            intent_name = alexa_request['intent']['name']
            intent_slots = alexa_request['intent'].get('slots', {})
            response = None

            # Run the function associated with the intent
            for one_intent in INTENTS:
                if intent_name == one_intent[0]:
                    response = one_intent[1](intent_slots)
                    break
            if not response:
                # This should not happen if your Intent Schema and your INTENTS list above are in sync.
                response = prepare_help_message()
        else:
            response = build_alexa_response("I received an unexpected request type.")
        start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(response)))])
        return [response]
    else:
        # This should never happen with a real Echo request but could happen
        # if your URL is accessed by a browser or otherwise.
        start_response('502 No content', [])
        return ['']


# Map the URL to the WSGI function that should handle it.

HANDLERS = [
    ['/', do_alexa],
    ['', do_alexa],
]


# The main entry point for WSGI scripts

def application(environ, start_response):
    # Execute the handler that matches the URL
    for h in HANDLERS:
        if environ['PATH_INFO'] == h[0]:
            output = h[1](environ, start_response)
            return output

    # If we don't have a handler for the URL, return a 404 error
    # page with diagnostic info. The details should be left blank
    # in a real production environment.

    details = ''
    if True:    # Change to False for productioN!
        for k in sorted(environ.keys()):
            details += '%s = %s<br/>\n' % (k, environ[k])
    output = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL %(url)s was not found on this server.</p>
<hr/>
%(details)s
<hr/>
<address>%(address)s</address>
</body></html>
""" % {'url':environ['PATH_INFO'], 'address':environ['SERVER_SIGNATURE'], 'details':details}
    start_response('404 Not Found', [('Content-type', 'text/html')])
    return [output]


 
