# -*- coding: utf-8 -*-

import logging
from .utils import *

logger = logging.getLogger('ymsl')


def invalidate(rows):
    assert len(rows), "file is empty"
    logger.debug('check all rows have the same number of columns')
    num_cols = len(rows[0])
    assert num_cols, "no columns"
    assert all(map(lambda row: len(row) == num_cols, rows[1:]))

    assert all(invalidate_weeks(rows))
    return True


def invalidate_weeks(rows):
    num_weeks = 0
    while rows:
        num_weeks += 1
        logger.debug('check week #%d' % (num_weeks))

        current_row = rows.pop(0)
        assert all(map(lambda col: not col.strip(),
                       current_row[1:])), "columns should be empty except for the first one"

        title = current_row[0].split()
        assert len(title) == 3

        assert title[0][:3].isdigit(), 'reading: %s' % (title[0][:3])
        assert title[0][3:] == '陽明山慢速壘球聯盟', 'reading: %s' % (title[0][3:])

        tournament_name = title[1].strip()
        assert tournament_name, "this column should be the tournament name"

        week = title[2]
        week = week[:week.index('賽')].strip()
        assert week, 'reading: %s' % (week)

        assert invalidate_time_table(rows)
        assert invalidate_time_table(rows)
        yield True


def invalidate_time_table(rows):
    current_row = [col for col in rows.pop(0) if col.strip()]
    assert current_row[0] == "場次"
    assert current_row[1] == "時間"
    assert all([col.endswith('組)') for col in current_row[2:] if '(' in col])
    assert all([col.endswith('場地') or remove_spaces(col) ==
                "備註" for col in current_row[2:] if '(' not in col])

    counter = {}
    for i in range(9):
        current_row = rows.pop(0)
        logger.debug('check time table row %d' % (i+1))
        assert int(current_row[0]) == i + 1
        assert current_row[1] == '%02d:00' % (i + 8)

        for name in current_row[2:]:
            if not name or name == '雨備日':
                continue
            counter[name] = counter.get(name, 0) + 1
        assert sum(counter.values()) % 2 == 0
    assert not counter or len(set(counter.values())) == 1

    return True
