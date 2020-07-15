# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger('ymsl')


def invalidate(rows):
    logger.debug('check all rows have the same number of columns')
    assert len(rows)
    num_cols = len(rows[0])
    assert num_cols
    assert all(map(lambda row: len(row) == num_cols, rows[1:]))

    assert all(invalidate_weeks(rows))
    return True


def invalidate_weeks(rows):
    num_weeks = 0
    while rows:
        num_weeks += 1
        current_row = rows.pop(0)
        logger.debug('check weeks: %d' % (num_weeks))
        week = current_row[0].split()[-1]
        assert week.index('賽') != -1
        week = week[:week.index('賽')]
        assert len(week)
        logger.debug('all columns except the first one should be empty')
        assert all(map(lambda field: len(field) == 0, current_row[1:]))
        assert invalidate_time_table(rows)
        assert invalidate_time_table(rows)
        yield True


def invalidate_time_table(rows):
    current_row = rows.pop(0)
    logger.debug('check time table heading')
    assert current_row[0] and current_row[1]
    assert len([col for col in current_row[2:] if col and '(' not in col]) == 2

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
