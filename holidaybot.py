import configparser
import imp
import json
import os
import re
import requests
import string

from collections import namedtuple
from errbot import BotPlugin, botcmd, re_botcmd
from os.path import join, realpath
bhr_client_source = join(realpath(os.path.dirname(__file__)), './bhr_client.py')
bhr_client = imp.load_source('bhr_client', bhr_client_source)

whosout_source = join(realpath(os.path.dirname(__file__)), './whosout.py')
whosout = imp.load_source('whosout', whosout_source)

WHERES_X_PATTERN = r"^where('?s| is) (@?[^?]+?)( today)?(\?|$)"
IS_X_IN_PATTERN = r"^is (@?.*) (in|out|here|away|at work|on holiday|on vacation|on leave)( today)?(\?)?$"

class HolidayBot(BotPlugin):
    """Plugin for querying who is on leave right now"""

    def __init__(self):
        super(HolidayBot, self).__init__()
        config = configparser.ConfigParser()
        if os.getenv('HOLIDAY_BOT_TEST_RUN') == 'True':
            config.read('./test_credentials.cfg')
        else:
            config.read('./credentials.cfg')
        bamboo_api_key = config.get('BambooHR', 'ApiKey')
        bamboo_host = config.get('BambooHR', 'Host')
        bamboo_company = config.get('BambooHR', 'Company')
        hipchat_host = config.get('HipChat', 'Host')
        hipchat_token = config.get('HipChat', 'Token')
        self.people = self.get_hipchat_users(hipchat_host, hipchat_token)
        self.checker = whosout.WhosOutChecker(bamboo_api_key,
                                              bamboo_company,
                                              bamboo_host)

    def get_hipchat_users(self, hipchat_host, hipchat_token):
        url = hipchat_host + "/v2/user?auth_token=" + hipchat_token
        response = requests.get(url)
        return json.loads(response.text)

    def get_name_from_mention(self, mention):
        for person in self.people['items']:
            if person['mention_name'].lower() == mention.lower():
                return person['name']

    @botcmd
    def hello(self, msg, args):
        """Say hello to HolidayBot"""
        return "Hello! Ask me \"who's out\" or \"is NAME in?\" to check up on your colleagues"

    @re_botcmd(pattern=WHERES_X_PATTERN, prefixed=False, flags=re.IGNORECASE)
    def wheres_x(self, msg, match):
        '''Reply to variants of "where is X?"'''
        name = match.group(2)
        for x in self.where_is(name):
            yield x

    @re_botcmd(pattern=IS_X_IN_PATTERN, prefixed=False, flags=re.IGNORECASE)
    def is_x_in(self, msg, match):
        """Reply to variants of 'is so-and-so in?'"""
        name = match.group(1)
        for x in self.where_is(name):
            yield x

    def where_is(self, name, debug=False):
        """Query if a specific person is here or on holiday"""
        if debug:
            yield "where_is called with args: " + name
        if name.startswith('@'):
            name = self.get_name_from_mention(name.lstrip('@'))
        where_is_results = self.checker.where_is(name)
        yield whosout.build_whereis_reply(name, where_is_results)

    @re_botcmd(pattern=r"^who('?s| is)[ ]?(out|away|around|on leave|on vaction|on holiday)( today)?(\?)?$", prefixed=False, flags=re.IGNORECASE)
    def whos_out(self, msg, match):
        """Say who is away today"""
        return whosout.build_whosout_reply(self.checker.get_whos_out())

    @re_botcmd(pattern=r"(?u)@([\w]+)([^\w]|$)",
               matchall=True,
               prefixed=False)
    def listen_for_at_mentions(self, msg, matches):
        "heard an @mention - i'll tell you if they're out"
        if re.match(IS_X_IN_PATTERN, msg.body) is not None \
           or re.match(WHERES_X_PATTERN, msg.body) is not None:
            return
        reply = ''
        for match in matches:
            mention_name = match.group(1)
            name = self.get_name_from_mention(mention_name)
            if name is None:
                continue
            all_results = self.checker.where_is(name)
            on_leave = [(emp, leave) for (emp, leave) in all_results
                        if leave is not None]
            if len(on_leave) == 0:
                continue
            reply += whosout.build_whereis_reply(mention_name, on_leave) + '\n'
        if reply == '':
            return
        else:
            return reply
