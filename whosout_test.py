from gevent import monkey
monkey.patch_all()
import bottle
import gevent
import unittest
import whosout

from bhr_client import Employee, Leave
from bottle import route
from datetime import date
from whosout import WhosOutChecker

TEST_API_KEY = 'testapikey'
TEST_COMPANY = 'reynholm-industries'
TEST_HOST = 'http://localhost:8080'

class TestWhosout(unittest.TestCase):

    def setUp(self):
        self.checker = WhosOutChecker(TEST_API_KEY, TEST_COMPANY, TEST_HOST)

    def test_get_whos_out(self):
        timeoffs = self.checker.get_whos_out()
        print('number of timeoffs returned:', len(timeoffs))
        expected = [
            (Employee('Sarah Surely', 'Sarah', 'Surely', None),
             Leave(date(2015, 5, 4), date(2015, 5, 4))),
            (Employee('Charlie Brown', 'Charlie', 'Brown', None),
             Leave(date(2015, 5, 21), date(2015, 5, 28)))]
        self.assertEqual(frozenset(expected), frozenset(timeoffs))

    def test_where_is(self):
        ### TODO : Add test case for multiple employees with the same name
        whereabouts = self.checker.where_is('Sarah')
        expected = [(Employee('Sarah Surely', 'Sarah', 'Surely', None),
                     Leave(date(2015, 5, 4), date(2015, 5, 4)))]
        self.assertEqual(frozenset(expected), frozenset(whereabouts))

    def test_where_is_unknown(self):
        result = self.checker.where_is("Polly")
        self.assertEqual(frozenset(), frozenset(result))

    def test_where_is_empty_string(self):
        result = self.checker.where_is("")
        self.assertEqual(frozenset(), frozenset(result))

    def test_build_whosout_reply(self):
        timeoffs = [
            (Employee('Sarah Surely', 'Sarah', 'Surely', None),
             Leave(date(2015, 5, 4), date(2015, 5, 4))),
            (Employee('Charlie Brown', 'Charles', 'Brown', None),
             Leave(date(2015, 5, 6), date(2015, 5, 8)))]
        reply = whosout.build_whosout_reply(timeoffs)
        self.assertIn('Sarah Surely: 4/5-4/5', reply)
        self.assertIn('Charlie Brown: 6/5-8/5', reply)

    def test_build_whereis_reply(self):
        whereabouts = [(Employee('Sarah Surely', 'Sarah', 'Surely', None),
                        Leave(date(2015, 5, 4), date(2015, 5, 4)))]

        reply = whosout.build_whereis_reply('sarah', whereabouts)
        self.assertIn("Sarah Surely is currently on leave", reply)
        self.assertIn('from 4/5 to 4/5', reply)

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
     "displayName": "Sarah Surely",
     "firstName": "Sarah",
     "lastName": "Surely",
     "nickname": null},
    {"id": "001",
     "displayName": "Firstname Surname",
     "firstName": "First",
     "lastName": "Last",
     "nickname": "firstlast"},
    {"id": "60401",
     "displayName": "Charlie Brown",
     "firstName": "Charlie",
     "lastName": "Brown",
     "nickname": null},
    {"id": "002",
     "displayName": "Barry Smith",
     "firstName": "Barry",
     "lastName": "Smith",
     "nickname": null}
    ]}"""

@route("/api/gateway.php/" + TEST_COMPANY + "/v1/time_off/whos_out/")
def whosout_request_handler():
    return """[
    {"id":121, "type":"timeoff", "employeeId":50446, "name": "Sarah Surely",
     "start": "2015-05-4", "end": "2015-05-4"},
    {"id":940, "type":"timeoff", "employeeId":60401, "name": "Charlie Brown",
     "start": "2015-05-21", "end": "2015-05-28"}]"""

def run_fn():
    return bottle.run(host='localhost', port=8080, debug=True,
                      server='gevent')

if __name__ == '__main__':
    GREENLET = gevent.spawn(run_fn)
    unittest.main()
    GREENLET.kill()
