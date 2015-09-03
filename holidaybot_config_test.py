from gevent import monkey
monkey.patch_all()
import bottle
import errbot
import gevent
import holidaybot
import logging
import pytest
import queue

from bottle import route
from errbot.backends.test import testbot, push_message, pop_message

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
    """These tests should *not* to be run with HOLIDAYBOT_TEST_RUN=True,
    but should be run from somewhere with no credentials.cfg file"""

    extra_plugin_dir = '.'
    loglevel = logging.ERROR

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def where_is_x_no_credentials(self, testbot):
        push_message("Where's John?")
        check_reply(["Unable to check", "An admin needs to configure credentials"])

    def test_is_x_in_no_credentials(self, testbot):
        push_message("Is Mary in?")
        check_reply(["Unable to check", "An admin needs to configure credentials"])

    def test_whosout_no_credentials(self, testbot):
        push_message("Who's out?")
        check_reply(["Unable to check", "An admin needs to configure credentials"])

    def test_at_mentions_no_credentials(self, testbot):
        push_message("I'm talking to you @Julie")
        check_no_reply()

    def test_hello_no_credentials(self, testbot):
        # check that no errors are thrown
        push_message("!hello")
        check_reply("Hello!")

    def test_config_no_credentials(self, testbot):
        '''Should return the default config if none set from file'''
        push_message("!config HolidayBot")
        check_reply(["'BAMBOOHR_APIKEY': 'changeme'",
                     "'BAMBOOHR_HOST': 'https://api.bamboohr.com'",
                     "'BAMBOOHR_COMPANY': 'changeme'"])

    def test_set_config(self, testbot):
        '''Should allow a new config to be set and read'''
        push_message("""!config HolidayBot {
        'BAMBOOHR_APIKEY': 'IchangedYou',
        'BAMBOOHR_HOST': 'IchangedYou',
        'BAMBOOHR_COMPANY': 'IchangedYou'}""")
        check_reply("Plugin configuration done")
        push_message("""!config HolidayBot""")
        check_reply(["'BAMBOOHR_APIKEY': 'IchangedYou'",
                     "'BAMBOOHR_HOST': 'IchangedYou'",
                     "'BAMBOOHR_COMPANY': 'IchangedYou'"])

    def test_set_config_can_now_check_is_x_in(self, testbot):
        '''After setting config via chat, can ask whos out'''
        self.start_test_server(run_fn)
        push_message("""!config HolidayBot {
        'BAMBOOHR_APIKEY': 'testApikey',
        'BAMBOOHR_HOST': 'http://localhost:8080',
        'BAMBOOHR_COMPANY': 'reynholm-industries'}""")
        check_reply("Plugin configuration done")
        push_message("Is Julie in?")
        check_reply(["could not find", "Julie"])
        self.stop_test_server()

    def test_bad_config_can_be_overriden(self, testbot):
        '''So we can't stop err unloading the plugin, but
        this state should at least be recoverable from'''
        # Set a bad config
        push_message("""!config HolidayBot {
        'BAMBOOHR_APIKEY': 'IchangedYou',
        'BAMBOOHR_HOST': 'IchangedYou',
        'BLAH_BLAH_BLAH': 'IchangedYou'}""")
        check_reply("Plugin configuration done")
        # Plugin should be unloaded
        push_message("!status plugins")
        check_reply(["[U] HolidayBot"])

        # Set a good config
        push_message("""!config HolidayBot {
        'BAMBOOHR_APIKEY': 'IchangedYou',
        'BAMBOOHR_HOST': '""" + TEST_HOST + """',
        'BAMBOOHR_COMPANY': '""" + TEST_COMPANY + """'}""")
        check_reply("Plugin configuration done")
        # Plugin should be loaded
        push_message("!status plugins")
        check_reply(["[L] HolidayBot"])
        # and plugin should now function
        self.start_test_server(run_fn)
        push_message("is x in?")
        check_reply(["could not find any employee named x"])
        self.stop_test_server()

    def start_test_server(self, f):
        self.greenlet = gevent.spawn(f)

    def stop_test_server(self):
        self.greenlet.kill()

def check_reply(expected):
    try:
        msg = pop_message(0.1)
    except queue.Empty:
        pytest.fail('No reply when expecting: ' + str(expected))
    assert len(msg) > 0
    if 'Computer says nooo' in msg:
        pytest.fail('Error message received when expecting: ' + str(expected))
    if type(expected) == str:
        expected = [expected]
    for e in expected:
        assert e in msg
    check_no_further_reply(msg)

def check_no_reply():
    with pytest.raises(queue.Empty):
        pytest.fail("Unexpected reply: " + pop_message(0.5))

def check_no_further_reply(previous_reply):
    with pytest.raises(queue.Empty):
        msg = pop_message(0.5)
        if (previous_reply == msg):
            pytest.fail("Duplicate reply: " + msg)
        pytest.fail("Unexpected extra reply: " + msg)
