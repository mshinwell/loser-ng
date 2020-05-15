#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2018 Philip Withnall
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import argparse
import csv
import sys


class QmExtracter:
    """
    Class implementing the svx2qm command line tool.

    This provides a way to extract question marks (QMs) from Survex files.

    The code in this class is currently tightly tied to the command line tool.
    """
    def __init__(self, debug):
        self.debug = debug

    def extract_qms(self, svx_files):
        qms = []

        # Extract the QMs from the various Survex files.
        for svx_file in svx_files:
            survey_name_stack = []
            survey_date = None

            with open(svx_file) as fd:
                for line in fd:
                    try:
                        if line.lower().startswith('*begin'):
                            parts = line.split()
                            survey_name_stack.append(parts[1] if len(parts) > 1 else '')
                            continue
                        if line.lower().startswith('*end'):
                            survey_name_stack.pop()
                            continue
                        if not survey_date and line.lower().startswith('*date'):
                            parts = line.split()
                            if len(parts) > 1:
                                survey_date = parts[1]
                            continue

                        # Look for a line matching:
                        # ;[ QM1    A    surveyname.3    -    description of QM ]
                        # or
                        # ;QM1    A    surveyname.3    -    description of QM
                        is_placeholder = \
                            (line.startswith(';[') or line.startswith('; ['))
                        if not line.startswith(';'):
                            continue

                        fields = line[1:-1].split(None, 4)
                        if not fields or len(fields) != 5:
                            continue

                        [name, grade, nearest_station,
                         resolution_station, description] = fields
                        if not name.lower().startswith('qm') or len(name) <= 2:
                            continue

                        # Sanitise the grade.
                        grade = grade.upper()
                        if grade not in ['A', 'B', 'C', 'D', 'E', 'X']:
                            self.__print_error(svx_file, line,
                                               'Unknown QM grade ‘%s’' % grade)
                            continue

                        # Sanitise the resolution station.
                        if resolution_station == '-':
                            resolution_station = None

                        # Sanitise the description.
                        description = description.strip()

                        # Warn about (and ignore) lines which are just the
                        # example template.
                        if nearest_station.startswith('surveyname.'):
                            self.__print_error(svx_file, line,
                                               'QM line is an unmodified '
                                               'example line')
                            continue

                        # By this point we should have a survey name from a
                        # *begin line (or series of them). If not, the survex
                        # file is malformed.
                        if not survey_name_stack:
                            self.__print_error(svx_file, line,
                                               'No *begin with survey name')
                            continue

                        survey_name = '.'.join(survey_name_stack)

                        # Warn if the line was a placeholder
                        if is_placeholder:
                            self.__print_error(svx_file, line,
                                               'QM line contains placeholder '
                                               'square brackets')
                            continue

                        # Warn if the nearest-station’s name doesn’t match the
                        # survey name.
                        if not nearest_station.startswith(survey_name + '.'):
                            self.__print_error(svx_file, line,
                                               'QM nearest-station survey '
                                               'name (‘%s’) doesn’t match '
                                               '*begin statement in file '
                                               '(‘%s’)' %
                                               (nearest_station.split('.')[0],
                                                survey_name))
                            continue

                        # Warn if this QM number has been used before, then
                        # ignore it.
                        used_before = False
                        for qm in qms:
                            if qm[0] == survey_name and qm[2] == name:
                                self.__print_error(svx_file, line,
                                                   'QM number ‘%s’ already '
                                                   'used in this file' % name)
                                used_before = True
                                break
                        if used_before:
                            continue

                        qms.append((survey_name, survey_date, name, grade,
                                    nearest_station, resolution_station,
                                    description))
                    except (ValueError, IndexError) as e:
                        self.__print_error(svx_file, line, e)
                        continue

        # Order them by grade, then date, and then by survey name.
        qms.sort(key=lambda qm: (qm[3], qm[1], qm[0]))
        return qms

    def format_qms(self, qms, format, include_resolved=False):
        if format == 'csv':
            self.format_qms_csv(qms, include_resolved)
        elif format == 'human':
            self.format_qms_human(qms, include_resolved)
        else:
            # Should never be reached: input validation should check the format
            assert(False)

    def format_qms_csv(self, qms, include_resolved=False):
        writer = csv.writer(sys.stdout)

        writer.writerow(['Survey name', 'Survey date',
                         'QM name', 'Grade', 'Nearest station',
                         'Resolution station', 'Description'])
        for qm in qms:
            # Do we actually want this QM, if it’s been resolved?
            if not include_resolved and qm[5]:
                continue

            writer.writerow(qm)

    def format_qms_human(self, qms, include_resolved=False, colour=True):
        # Work out the maximum width of each field.
        field_names = ['Survey name', 'Survey date', 'QM name', 'Grade',
                       'Nearest station', 'Resolution station']
        lens = [len(field) for field in field_names]
        for qm in qms:
            # Do we actually want this QM, if it’s been resolved?
            if not include_resolved and qm[5]:
                continue

            for (idx, field) in enumerate(qm):
                if idx >= len(field_names):
                    break
                lens[idx] = max(lens[idx], len(field) if field else 0)

        # Print a header (bold if possible).
        if colour:
            print('\033[1m', end='')
        line_format = '  '.join(['{:<{}}'] * len(field_names))
        flattened = [x for t in zip(field_names, lens) for x in t]
        print(line_format.format(*flattened))
        if colour:
            print('\033[0m', end='')

        print('─' * (sum(lens) + 2 * (len(lens) - 1)))

        # Adjust the width of the grade, survey and QM name fields to account
        # for the color escapes.
        if colour:
            lens[0] += 8
            lens[2] += 8
            lens[3] += 9

        # Print out the rows.
        n_printed = 0
        for qm in qms:
            (survey_name, survey_date, name, grade, nearest_station, 
             resolution_station, description) = qm

            # Do we actually want this QM, if it’s been resolved?
            if not include_resolved and resolution_station:
                continue

            if not resolution_station:
                resolution_station = ''

            if colour:
                try:
                    # See https://stackoverflow.com/a/33206814/2931197.
                    grade_colour = {
                        'A': '32',
                        'B': '33',
                        'C': '31',
                        'D': '31',
                        'E': '31',
                        'X': '37',
                    }[grade]
                except KeyError:
                    grade_colour = '00'
                formatted_grade = '\033[{}m{}\033[0m'.format(grade_colour,
                                                             grade)
                formatted_survey_name = '\033[4m{}\033[0m'.format(survey_name)
                formatted_name = '\033[4m{}\033[0m'.format(name)
            else:
                formatted_grade = grade
                formatted_survey_name = survey_name
                formatted_name = name

            print(line_format.format(formatted_survey_name, lens[0],
                                     survey_date, lens[1],
                                     formatted_name, lens[2],
                                     formatted_grade, lens[3],
                                     nearest_station, lens[4],
                                     resolution_station, lens[5]))
            print('  ' + description)
            n_printed += 1

        # Have we finished all the QMs?
        if n_printed == 0 and not qms:
            print('No QMs found')
        elif n_printed == 0:
            print('No unresolved QMs found (but %u resolved ones were)' %
                  len(qms))

    def __print_error(self, svx_file, line, exc):
        sys.stderr.write('%s: %s\n  %s\n' % (svx_file, exc, line))


def main():
    """
    Main entry point to svx2qm. Handles arguments.
    
    Usage example:
       find -name '*.svx' | xargs ./svx2qm.py --format human
    """
    parser = argparse.ArgumentParser(
        description='Extract question marks (QMs) from one or more Survex '
                    'files. The QMs must be formatted appropriately, and '
                    'currently this script only supports commented-out QMs, '
                    'as the format has not been standardised yet. The QMs can '
                    'be returned as a human-readable list or as a CSV.')
    parser.add_argument('svx_files', metavar='SVX-FILE …', nargs='+',
                        help='SVX files to extract QMs from')
    parser.add_argument('--format', choices=['csv', 'human'], default='human',
                        help='output format (default: human)')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='output debug information')
    parser.add_argument('--include-resolved', action='store_true',
                        default=False,
                        help='include resolved QMs in the output')

    args = parser.parse_args()

    extracter = QmExtracter(args.debug)
    qms = extracter.extract_qms(args.svx_files)
    extracter.format_qms(qms, args.format, args.include_resolved)


if __name__ == '__main__':
    main()
