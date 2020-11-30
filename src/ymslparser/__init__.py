# -*- coding: utf-8 -*-

import csv
import datetime
import logging
import operator
import re
from .utils import *
from .validator import invalidate


logger = logging.getLogger('ymsl')


class League(object):
    def __init__(self):
        self.name = 'YMSL'
        self.teams = {}
        self.weeks = []

    def __del__(self):
        self.teams.clear()

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

    def clear(self):
        self.slots.clear()

    def add_slot(self, time_slot):
        self.slots.append(time_slot)


class Week(object):
    def __init__(self, name, date):
        self.name = name
        self.date = date
        self.slots = []

    def __str__(self):
        return 'Week %s: %s' % (self.name, self.date)

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
    def parse(filename, **kw):
        with open(filename, 'r', **kw) as f:
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
        date_pattern = re.compile('\d+')
        week_pattern = re.compile('第[一二三四五六七八九十]+週')
        while self.has_rows():
            num_weeks += 1
            row = self._pop_next_row()

            name, tournament, date = row[0].split()
            year_str = date_pattern.search(name)[0]
            month, day = map(int, date_pattern.findall(date))
            is_last_year = '春季熱身賽' == tournament and month > 10
            year = int(year_str) + (1910 if is_last_year else 1911)
            self.league.name = name[len(year_str):]
            self.league.year = year
            self.league.tournament = tournament

            week = Week(week_pattern.search(date)[
                        0], datetime.date(year, month, day))
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
                start_time = datetime.datetime.strptime(start_time, '%H:%M')
                start_time = datetime.datetime(
                    year, month, day, start_time.hour, start_time.minute)

                for i, team_pair in enumerate(teams):
                    team1, team2 = map(lambda name: self.league.get_team(
                        remove_spaces(name)), team_pair)
                    slot = TimeSlot(week, int(index), start_time,
                                    fields[i], team1, team2)
                    logger.info(slot)
                    team1.add_slot(slot)
                    team2.add_slot(slot)
                    week.add_slot(slot)

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
