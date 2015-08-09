from gevent import monkey
monkey.patch_all()
import bottle
import gevent
import holidaybot
import logging
import pytest
import queue

from bottle import route
from datetime import date, timedelta
from errbot.backends.test import testbot, push_message, pop_message

TEST_HOST = 'http://localhost:8080'
TEST_TOKEN = 'testToken'
TEST_COMPANY = 'reynholm-industries'

TODAY = date.today().strftime('%Y-%m-%d')
TOMORROW = (date.today() + timedelta(1)).strftime('%Y-%m-%d')

@route('/hello')
def hello_handler():
    return "hello world"

@route("/v2/user")
def hipchat_request_handler():
    return '''{"items": [
    {"id": 5000101,
    "links": {"self": "https://api.hipchat.com/v2/user/5000101"},
    "mention_name": "Hugo", "name": "Hugo Boss"},
    {"id": 5000103,
    "links": {"self": "https://api.hipchat.com/v2/user/5000103"},
    "mention_name": "Zo\\u00e8", "name": "Zoe Ball"},
    {"id": 5000102,
    "links": {"self": "https://api.hipchat.com/v2/user/5000102"},
    "mention_name": "SarahSkiver", "name": "Sarah Skiver"},
    {"id": 7382739,
    "links": {"self": "https://api.hipchat.com/v2/user/7382739"},
    "mention_name": "WillSam", "name": "Willem Samuel"},
    {"id": 3334545,
    "links": {"self": "https://api.hipchat.com/v2/user/3334545"},
    "mention_name": "HolidayHarry", "name": "Holiday Harry"}]}'''

@route("/api/gateway.php/" + TEST_COMPANY + "/v1/employees/directory")
def directory_request_handler():
    return """{
    "fields": [
    {"id":"displayName","type":"text","name":"Display name"},
    {"id":"firstName","type":"text","name":"First name"},
    {"id":"lastName","type":"text","name":"Last name"},
    {"id":"nickname","type":"text","name":"Nick name"}],
    "employees": [
    {"id": "50446",
     "displayName": "Sarah Skiver",
     "firstName": "Sarah",
     "lastName": "Skiver",
     "nickname": null},
    {"id": "3001",
     "displayName": "Hugo Boss",
     "firstName": "Hugo",
     "lastName": "Boss",
     "nickname": "hugs"},
    {"id": "60401",
     "displayName": "Charlie Brown",
     "firstName": "Charlie",
     "lastName": "Brown",
     "nickname": null},
    {"id": "60402",
     "displayName": "Willem Samuel",
     "firstName": "Willem",
     "lastName": "Samuel",
     "nickname": "Will"},
    {"id": "1473",
     "displayName": "Holiday Harry",
     "firstName": "Holiday",
     "lastName": "Harry",
     "nickname": null},
    {"id": "39223",
     "displayName": "Zoe Ball",
     "firstName": "Zoe",
     "lastName": "Ball",
     "nickname": null}
    ]}"""

@route("/api/gateway.php/" + TEST_COMPANY + "/v1/time_off/whos_out/")
def whosout_request_handler():
    return '''[
    {"id":121, "type":"timeoff", "employeeId":50446, "name": "Sarah Skiver",
     "start": "''' + TODAY + '''", "end": "''' + TOMORROW + '''"},
    {"id":940, "type":"timeoff", "employeeId":60401, "name": "Charlie Brown",
     "start": "2015-05-21", "end": "2015-05-28"},
    {"id":131, "type":"timeoff", "employeeId":1473, "name": "Holiday Harry",
     "start": "''' + TODAY + '''", "end": "''' + TOMORROW + '''"},
    {"id":384, "type":"timeoff", "employeeId":39223, "name": "Zoe Ball",
     "start": "''' + TODAY + '''", "end": "''' + TOMORROW + '''"}]'''

def run_fn():
    return bottle.run(host='localhost', port=8080, debug=True,
                      server='gevent')

class TestHolidayBot(object):
    extra_plugin_dir = '.'
    loglevel = logging.ERROR

    @classmethod
    def setup_class(self):
        self.GREENLET = gevent.spawn(run_fn)

    @classmethod
    def teardown_class(self):
        self.GREENLET.kill()

    def test_whos_out(self, testbot):
        push_message("who's out?")
        msg = pop_message(0.2)
        assert len(msg) > 0
        assert 'Sarah Skiver:' in msg
        assert 'Charlie Brown:' in msg
        print(msg)

    def test_is_x_in_when_in(self, testbot):
        push_message("is Hugo out?")
        check_reply('Hugo Boss (hugs) is not on leave')

    def test_is_x_in_when_out(self, testbot):
        push_message("is Sarah in?")
        check_reply('Sarah Skiver is currently on leave')

    def test_is_x_in_using_hipchat_handle(self, testbot):
        push_message("is @SarahSkiver in?")
        check_reply('Sarah Skiver is currently on leave')
        push_message('where is @SarahSkiver?')
        check_reply('Sarah Skiver is currently on leave')
        push_message("is @Hugo in?")
        check_reply('Hugo Boss (hugs) is not on leave')
        push_message("is @WillSam in?")
        check_reply('Willem Samuel (Will) is not on leave')

    def test_at_mentions_when_out(self, testbot):
        push_message('@HolidayHarry')
        check_reply('Holiday Harry is currently on leave')
        push_message("hey there @SarahSkiver")
        check_reply('Sarah Skiver is currently on leave')

    def test_at_mentions_when_in(self, testbot):
        push_message("hey there @Hugo")
        check_no_reply()

    def test_multiple_at_mentions(self, testbot):
        push_message("can you hear me @Hugo and @SarahSkiver")
        check_reply('Sarah Skiver is currently on leave')
        push_message("@SarahSkiver @HolidayHarry")
        check_reply(['Sarah Skiver is currently on leave',
                     'Holiday Harry is currently on leave'])

    def test_at_mentions_with_punctuation(self, testbot):
        push_message("somethinig something (@HolidayHarry)")
        check_reply('Holiday Harry is currently on leave')
        push_message("Hello @SarahSkiver.")
        check_reply('Sarah Skiver is currently on leave')

    def test_at_mentions_not_case_sensitive(self, testbot):
        push_message("@SarahSkiver")
        check_reply('Sarah Skiver is currently on leave')
        push_message("@sarahskiver")
        check_reply('Sarah Skiver is currently on leave')

    def test_at_mentions_with_accents(self, testbot):
        push_message("@Zo\xe8")
        check_reply("Zoe Ball is currently on leave")

    def test_no_reply_to_gobbledigook(self, testbot):
        push_message('jklcjsklcs')
        check_no_reply()

def check_reply(expected):
    try:
        msg = pop_message(0.1)
    except queue.Empty:
        pytest.fail('No reply when expecting: ' + expected)
    assert len(msg) > 0
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
