"""Simple wrapper for BambooHR API calls"""
import json
import requests
from collections import namedtuple
from datetime import date, datetime

Employee = namedtuple("Employee", "display first last nick")
Leave = namedtuple("Leave", "start end")

class BambooHrClient(object):
    """Simple wrapper for getting employees directory and a list of who's out"""

    def __init__(self, api_key, company, host=None):
        self._api_key = api_key
        host = host or "https://api.bamboohr.com"
        self._base_url = "{}/api/gateway.php/{}/v1/".format(host, company)

    @staticmethod
    def _get_date_from_string(date_string):
        return datetime.strptime(date_string, '%Y-%m-%d').date()

    def get_timeoff_whosout(self):
        """Gets a dictionary of current leaves, indexed by employee id"""
        response = requests.get(
            self._base_url + "time_off/whos_out/?end=" + str(date.today()),
            auth=(self._api_key, 'pass'),
            headers={'Accept': 'application/json'})
        if response.status_code != 200:
            response.raise_for_status()
        leaves_json = json.loads(response.text)
        return {x['employeeId']: Leave(self._get_date_from_string(x['start']),
                                       self._get_date_from_string(x['end']))
                for x in leaves_json if 'employeeId' in x}

    def get_employees_directory(self):
        """Gets a dictionary of all Employees, indexed by employee id"""
        response = requests.get(self._base_url + "employees/directory",
                                auth=(self._api_key, "pass"),
                                headers={'Accept': 'application/json'})
        if response.status_code != 200:
            response.raise_for_status()
        emps_json = json.loads(response.text)['employees']
        return {int(e['id']): Employee(e['displayName'],
                                       e['firstName'],
                                       e['lastName'],
                                       e['nickname']) for e in emps_json}
