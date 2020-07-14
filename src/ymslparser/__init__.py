# -*- coding: utf-8 -*-

import csv
import datetime
import logging
import operator
from .utils import *
from .validator import invalidate


logger = logging.getLogger('ymsl')


class League(object):
    def __init__(self):
        self.teams = {}
        self.weeks = []

    def add_team(self, team):
        self.teams[team.name] = team

    def add_week(self, week):
        self.weeks.append(week)

    def get_team(self, team):
        return self.teams.setdefault(team, Team(team))


class Team(object):
    def __init__(self, name):
        self.name = name
        self.slots = []

    def __str__(self):
        return 'Team %s: %s' % (self.name, [str(slot) for slot in self.slots])

    def add_slot(self, time_slot):
        self.slots.append(time_slot)


class Week(object):
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.slots = []

    def __str__(self):
        return 'Week: %s' % (self.name)

    def add_slot(self, time_slot):
        self.slots.append(time_slot)


class TimeSlot(object):
    def __init__(self, week, idx, start_time, field, team1, team2):
        self.week = week
        self.idx = idx
        self.start_time = start_time
        self.field = field
        self.team1 = team1
        self.team2 = team2

    def __str__(self):
        return '%s @%s %s vs %s' % (self.start_time, self.field, self.team1.name, self.team2.name)


class Parser(object):
    @staticmethod
    def parse(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            parser = Parser(csv.reader(f))
        return parser.do_parse()

    def __init__(self, content):
        self._rows = [row for row in content]
        assert invalidate(self._rows[:])
        self.league = League()

    def do_parse(self):
        for week in self._parse_weeks():
            self.league.add_week(week)
        return self.league

    def has_rows(self):
        return not not self._rows

    def _pop_next_row(self):
        if not self.has_rows():
            return None
        return self._rows.pop(0)

    def _unpop_row(self, row):
        self._rows.insert(0, row)

    def _parse_weeks(self):
        num_weeks = 0
        while self.has_rows():
            num_weeks += 1
            row = self._pop_next_row()
            year_col = row[0].split()[0]
            week_col = row[0].split()[-1]

            date_string = '%s %s' % (
                int(year_col[year_col.index('1'):year_col.index('陽')].strip()) + 1911,
                week_col[:week_col.index('賽')]
            )
            date = datetime.datetime.strptime(date_string, '%Y %m月%d日')

            week = Week(num_weeks, week_col)
            logger.info(week)

            row = self._pop_next_row()
            if row is None:
                return
            upper_header = [remove_spaces(col) for col in row if col]

            upper_slots = list(self._parse_time_slot())
            if not upper_slots:
                return

            row = self._pop_next_row()
            if row is None:
                return
            lower_header = [remove_spaces(col) for col in row if col]

            lower_slots = list(self._parse_time_slot())
            assert len(lower_slots) == len(upper_slots)

            fields = list(filter(lambda col: not col.startswith(
                '(') and not col.endswith(')'), upper_header[2:] + lower_header[2:]))
            timeslots = [list(a) + list(b)[1:]
                         for a, b in zip(upper_slots, lower_slots)]

            for slot in timeslots:
                (index, start_time), teams = slot[0], slot[1:]
                start_time = datetime.datetime.strptime(date.strftime(
                    '%m/%d/%Y ') + start_time, '%m/%d/%Y %H:%M')

                for i, team_pair in enumerate(teams):
                    team1, team2 = map(lambda name: self.league.get_team(
                        remove_spaces(name)), team_pair)
                    slot = TimeSlot(week, int(index), start_time,
                                    fields[i], team1, team2)
                    logger.info(slot)
                    team1.add_slot(slot)
                    team2.add_slot(slot)
                    week.add_slot(slot)
                    # logger.info(
                    #     (index, start_time, fields[i], team1.name, team2.name))

            yield week

    def _parse_time_slot(self):
        while self.has_rows():
            row = self._pop_next_row()
            if not row[0].isdigit():
                self._unpop_row(row)
                return
            teams = [remove_spaces(col) for col in row if col]

            odd, even = teams[0:][::2], teams[1:][::2]
            yield zip(odd, even)
