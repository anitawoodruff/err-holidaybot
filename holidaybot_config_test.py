from gevent import monkey
monkey.patch_all()
import bottle
import errbot
import gevent
import holidaybot
import logging
import os
import pytest
import queue

from bottle import route
from errbot.backends.test import testbot

TEST_HOST = 'http://localhost:8080'
TEST_COMPANY = 'reynholm-industries'

@route("/api/gateway.php/" + TEST_COMPANY + "/v1/employees/directory")
def directory_request_handler():
    return """{
    "fields": [
    {"id":"displayName","type":"text","name":"Display name"},
    {"id":"firstName","type":"text","name":"First name"},
    {"id":"lastName","type":"text","name":"Last name"},
    {"id":"nickname","type":"text","name":"Nick name"}],
    "employees": []}"""

@route("/api/gateway.php/" + TEST_COMPANY + "/v1/time_off/whos_out/")
def whosout_request_handler():
    return '''[]'''

def run_fn():
    return bottle.run(host='localhost', port=8080, debug=True,
                      server='gevent')

class TestHolidayBot(object):
    """These tests should *not* be run with HOLIDAYBOT_TEST_RUN=True,
    but should be run from somewhere with no holidaybot_credentials.cfg file"""

    extra_plugin_dir = '.'
    loglevel = logging.ERROR

    @classmethod
    def setup_class(cls):
        cls.start_test_server(run_fn)

    @classmethod
    def teardown_class(cls):
        cls.stop_test_server()

    @classmethod
    def start_test_server(cls, f):
        cls.greenlet = gevent.spawn(f)

    @classmethod
    def stop_test_server(cls):
        cls.greenlet.kill()

    def where_is_x_no_credentials(self, testbot):
        testbot.push_message("Where's John?")
        check_reply(["Unable to check", "An admin needs to configure credentials"], testbot)

    def test_is_x_in_no_credentials(self, testbot):
        testbot.push_message("Is Mary in?")
        check_reply(["Unable to check", "An admin needs to configure credentials"], testbot)

    def test_whosout_no_credentials(self, testbot):
        testbot.push_message("Who's out?")
        check_reply(["Unable to check", "An admin needs to configure credentials"], testbot)

    def test_at_mentions_no_credentials(self, testbot):
        testbot.push_message("I'm talking to you @Julie")
        check_no_reply(testbot)

    def test_hello_no_credentials(self, testbot):
        # check that no errors are thrown
        testbot.push_message("!hello")
        check_reply("Hello!", testbot)

    def test_config_no_credentials(self, testbot):
        '''Should return the default config if none set from file'''
        testbot.push_message("!plugin config HolidayBot")
        check_reply(["'BAMBOOHR_APIKEY': 'changeme'",
                     "'BAMBOOHR_HOST': 'https://api.bamboohr.com'",
                     "'BAMBOOHR_COMPANY': 'changeme'"], testbot)

    def test_set_config(self, testbot):
        '''Should allow a new config to be set and read'''
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'IchangedYou',
        'BAMBOOHR_HOST': 'IchangedYou',
        'BAMBOOHR_COMPANY': 'IchangedYou'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("""!plugin config HolidayBot""")
        check_reply(["'BAMBOOHR_APIKEY': 'IchangedYou'",
                     "'BAMBOOHR_HOST': 'IchangedYou'",
                     "'BAMBOOHR_COMPANY': 'IchangedYou'"], testbot)

    def test_set_good_config_can_now_check_is_x_in(self, testbot):
        '''After setting config via chat, can ask whos out'''
        self.start_test_server(run_fn)
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'reynholm-industries'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("Is Julie in?")
        check_reply(["could not find", "Julie"], testbot)
        self.stop_test_server()


    def test_can_change_config_after_valid_config(self, testbot):
        '''After setting to a valid config, can change to another good one'''
        self.start_test_server(run_fn)

        # set to a valid (but non-working) config
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'unknown'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("Is Julie in?")
        check_reply("Unable to check", testbot)

        # set to a good config
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'reynholm-industries'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("Is Julie in?")
        check_reply(["could not find", "Julie"], testbot)
        self.stop_test_server()

    def test_set_valid_config_but_bad_company(self, testbot):
        '''After setting a config with valid format but not served,
         can ask whos out, but should fail'''
        self.start_test_server(run_fn)
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey2',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'not-a-real-company'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("Is Julie in?")
        check_reply(["Unable to check"], testbot)
        self.stop_test_server()

    def test_valid_config_after_good_one(self, testbot):
        '''Set valid but wrong config after setting a good one;
         check doesn't keep working'''
        self.start_test_server(run_fn)
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'reynholm-industries'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("Is Julie in?")
        check_reply(["could not find", "Julie"], testbot)
        
        # change to a valid but bad config
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'something',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'unknown'}""")
        check_reply("Plugin configuration done", testbot)

        testbot.push_message("Is Julie in?")
        check_reply(["Unable to check", "An admin needs to configure credentials"], testbot)
        self.stop_test_server()

    def test_invalid_config_after_good_one(self, testbot):
        '''Set bad config after setting a good one;
         check doesn't keep working'''
        self.start_test_server(run_fn)
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'reynholm-industries'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("Is Julie in?")
        check_reply(["could not find", "Julie"], testbot)
        # Set a bad config (bad format)
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'changeme',
        'BAMBOOHR_HOST': 'https://api.bamboohr.com',
        'BAMBOOHR_COMPANY_hh': 'changeme'}""")
        check_reply("Plugin configuration done", testbot)
        # Plugin should be deactivated
        testbot.push_message("!status plugins")
        check_reply(["D      │ HolidayBot"], testbot)
        testbot.push_message("Is Julie in?")
        check_no_reply(testbot)
        self.stop_test_server()

    def test_bad_config_can_be_overidden(self, testbot):
        '''So we can't stop err unloading the plugin, but
        this state should at least be recoverable from'''
        self.start_test_server(run_fn)
        # Set a bad config
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'IchangedYou',
        'BAMBOOHR_HOST': 'https://api.bamboohr.com',
        'BLAH_BLAH_BLAH': 'IchangedYou'}""")
        check_reply("Plugin configuration done", testbot)
        # Plugin should be deactivated
        testbot.push_message("!status plugins")
        check_reply(["D      │ HolidayBot"], testbot)

        # Set a good config
        testbot.push_message("""!plugin config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey',
        'BAMBOOHR_HOST': '""" + TEST_HOST + """',
        'BAMBOOHR_COMPANY': '""" + TEST_COMPANY + """'}""")
        check_reply("Plugin configuration done", testbot)
        testbot.push_message("""!plugin config HolidayBot""")
        check_reply([
            "'BAMBOOHR_APIKEY': 'testApikey'",
            "'BAMBOOHR_HOST': '" + TEST_HOST + "'",
            "'BAMBOOHR_COMPANY': '" + TEST_COMPANY + "'"], testbot)

        # Plugin should be active
        testbot.push_message("!status plugins")
        check_reply(["A      │ HolidayBot"], testbot)
        # and plugin should now function
        testbot.push_message("is x in?")
        check_reply(["could not find any employee named x"], testbot)
        self.stop_test_server()


def check_reply(expected, testbot):
    try:
        msg = testbot.pop_message(0.1)
    except queue.Empty:
        pytest.fail('No reply when expecting: ' + str(expected))
    assert len(msg) > 0
    if 'Computer says nooo' in msg:
        pytest.fail('Error message received when expecting: ' + str(expected))
    if type(expected) == str:
        expected = [expected]
    for e in expected:
        try:
            assert e in msg
        except AssertionError:
            pytest.fail("Expected reply: '" + e + "' not found in actual reply:\n" + msg)
    check_no_further_reply(msg, testbot)

def check_no_reply(testbot):
    with pytest.raises(queue.Empty):
        pytest.fail("Unexpected reply: " + testbot.pop_message(0.5))

def check_no_further_reply(previous_reply, testbot):
    with pytest.raises(queue.Empty):
        msg = testbot.pop_message(0.5)
        if (previous_reply == msg):
            pytest.fail("Duplicate reply: " + msg)
        pytest.fail("Unexpected extra reply: " + msg)
