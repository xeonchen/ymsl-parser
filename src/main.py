#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import datetime
import sys
from ymslparser import Parser


def main(files):
    for file in files:
        print("Processing file: %s" % (file))
        league = Parser.parse(file, encoding='utf-8-sig')

        for week in league.weeks:
            print(week.date, week.name)
            for slot in week.slots:
                print(slot)

        for team in league.teams.values():
            with open('output/%s_%s_%s.csv' % (league.year, league.tournament, team.name), 'w', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Subject',
                    'Start Date',
                    'End Date',
                    'Start Time',
                    'End Time',
                    'Location',
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for slot in team.slots:
                    s = slot.start_time
                    e = slot.start_time + datetime.timedelta(hours=1)
                    writer.writerow({
                        'Subject': '%s vs %s' % (slot.team1.name, slot.team2.name),
                        'Start Date': s.strftime('%m/%d/%Y'),
                        'End Date': e.strftime('%m/%d/%Y'),
                        'Start Time': s.strftime('%I:%M %p'),
                        'End Time': e.strftime('%I:%M %p'),
                        'Location': slot.field
                    })


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
