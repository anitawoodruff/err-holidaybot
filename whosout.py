#!/usr/bin/python
import argparse
import configparser
import re

from bhr_client import BambooHrClient
from collections import defaultdict
from unidecode import unidecode

def _normalise_name(name):
    if isinstance(name, str):
        name = unidecode(name)
    return name.lower()

class WhosOutChecker(object):

    def __init__(self, api_key, company, host=None):
        self.bamboohr_client = BambooHrClient(api_key, company, host)
        self.emps = self.bamboohr_client.get_employees_directory()
        self.namesets = self._build_namesets(self.emps)

    @staticmethod
    def _build_namesets(employees):
        '''Maps all derived employee names to lists of employee ids
        they may refer to, for speedy querying'''
        namesets = defaultdict(set) # default dict of names - empIds
        for emp_id, emp in employees.items():
            names = sum((re.split('[ -]', _normalise_name(name))
                         for name in emp if name is not None), [])
            for name in names:
                namesets[name].add(emp_id)
        return namesets

    @staticmethod
    def _get_employee_ids_from_name(typed_name, namesets):
        '''Get a list of employee ids that a typed name can refer to'''
        typed_name = _normalise_name(typed_name)
        typed_names = re.split('[ -]', typed_name)
        match_sets = [namesets[tn] for tn in typed_names if tn in namesets]
        if len(match_sets) == 0:
            return []
        intersection = set(match_sets[0])
        for i in range(1, len(match_sets)):
            intersection.intersection_update(match_sets[i])
        return list(intersection)

    def get_whos_out(self):
        '''Get a list of who's out, each element as (Employee, Leave)'''
        leaves = self.bamboohr_client.get_timeoff_whosout()
        return [(self.emps[emp_id], leave) for emp_id, leave in leaves.items()]

    def where_is(self, name):
        '''Returns a list of (Employee, Leave) pairs for employees matching
        NAME; Leave will be None if the employee is not currently on leave'''
        matching_emps = sorted(
            self._get_employee_ids_from_name(name, self.namesets))
        if len(matching_emps) == 0:
            return []
        current_leaves = self.bamboohr_client.get_timeoff_whosout()
        return [(self.emps[x], current_leaves.get(x)) for x in matching_emps]

def build_whosout_reply(timeoffs):
    return "\n".join(
        sorted("{}{}: {}/{}-{}/{}".format(
            emp.display,
            ' (' + emp.nick + ')' if emp.nick is not None else '',
            leave.start.day,
            leave.start.month,
            leave.end.day,
            leave.end.month) for (emp, leave) in timeoffs))

def build_whereis_reply(name, timeoffs):
    if len(timeoffs) == 0:
        return "I could not find any employee named " + name
    return '\n'.join(
        sorted( ### TODO : just if-else on the pre-format string & use named {}s
            "{}{} is currently on leave, from {}/{} to {}/{}".format(
                emp.display,
                ' (' + emp.nick + ')' if emp.nick is not None else '',
                leave.start.day,
                leave.start.month,
                leave.end.day,
                leave.end.month) if leave is not None else
            "{}{} is not on leave at the moment".format(
                emp.display,
                ' (' + emp.nick + ')' if emp.nick is not None else '')
            for (emp, leave) in timeoffs))


### Functions just called from __main__ ###

def _parse_bamboo_credentials(path):
    config = configparser.ConfigParser()
    config.read(path)
    return config.get('BambooHR', 'ApiKey')

def _parse_command_line_args():
    parser = argparse.ArgumentParser(
        description="Tool for finding out who is on leave / whether a specific \
        person is on leave atm.")
    parser.add_argument(
        '-c', '--credentials',
        default='../../holidaybot_credentials.cfg',
        metavar='FILE',
        type=str,
        nargs="?",
        help="""Path to file containing BambooHR credentials. \
        If not specified, uses ../../holidaybot_credentials.cfg""")
    parser.add_argument(
        'person_to_check',
        metavar='NAME',
        type=str,
        nargs="?",
        help="Name of an employee. \
        If not provided, prints everyone currently on leave.")
    return parser.parse_args()

if __name__ == '__main__':
    ARGS = _parse_command_line_args()
    API_KEY = _parse_bamboo_credentials(ARGS.credentials)
    CHECKER = WhosOutChecker(API_KEY, 'swiftkey')
    if ARGS.person_to_check is None:
        print(build_whosout_reply(CHECKER.get_whos_out()))
    else:
        WHEREABOUTS = CHECKER.where_is(ARGS.person_to_check)
        print(build_whereis_reply(ARGS.person_to_check, WHEREABOUTS))
