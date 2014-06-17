#!/usr/bin/python
 
'''
Script to schedule iPQB journal club
'''
 
__author__ = "Kyle Barlow"
__email__ = "kb@kylebarlow.com"
__license__ = "GPL v3"
 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import argparse
import random
import difflib

class Student:
    def __init__(self, first_name, last_name, year):
        self.first_name = first_name
        self.last_name = last_name
        self.year = int(year)

        # Default parameters for gaussian distribution weighting
        self.mu = 0.0
        self.sigma = 1.0

    def __repr__(self):
        if self.year == 1:
            return '%s %s, 1st year' % (self.first_name, self.last_name)
        elif self.year == 2:
            return '%s %s, 2nd year' % (self.first_name, self.last_name)
        elif self.year == 3:
            return '%s %s, 3rd year' % (self.first_name, self.last_name)
        else:
            return '%s %s, %dth year' % (self.first_name, self.last_name, self.year)

class Week:
    def __init__(self, *students):
        assert( len(students) >= 1 )
        self.students = students
        
        mus = [float(student.mu) for student in students]
        sigmas = [float(student.sigma) for student in students]
    
        self.mu = sum(mus) / float(len(mus))
        self.sigma = sum(sigmas) / float(len(sigmas))

        self.last_random  = None

    def __repr__(self):
        student_str = '['
        for i, student in enumerate(self.students):
            if i+1 == len(self.students):
                student_str += '%s' % str(student)
            else:
                student_str += '%s; ' % str(student)
        student_str += ']'

        if self.last_random:
            return '(%.2f, %s)' % (self.last_random, student_str)
        else:
            return '(%.2f, %.2f, %s)' % (self.mu, self.sigma, student_str)

    def sort_number(self):
        self.last_random = random.gauss(self.mu, self.sigma)
        return self.last_random

def find_position(student, last_year_name_dict):
    best_match_score = 0.0
    best_match_position_number = 0
    best_matched_name = 'N/A'
    search_name = '%s %s' % (student.first_name.lower(), student.last_name.lower())
    for name in last_year_name_dict:
        score = difflib.SequenceMatcher(None, name, search_name).ratio()
        if score > best_match_score:
            best_match_score = score
            best_match_position_number = last_year_name_dict[name]
            best_matched_name = name

    print 'Matched "%s" to "%s" (position %d) with a score of %.1f' % (search_name, best_matched_name, best_match_position_number, best_match_score)
    return best_match_position_number

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('input_file', type=argparse.FileType('r'),
                        help='CSV file containing "first name,Last name,Year in program"')
    parser.add_argument('last_year_file', type=argparse.FileType('r'),
                        help='CSV file containing "Date,Name(s)"')
    args = parser.parse_args()

    # Parse last year's file
    # Expected format : two strings per line
    #  Date, Name/Name OR Date, Name
    last_year_file = args.last_year_file
    last_year_name_dict = {}
    for i, line in enumerate(last_year_file):
        line = line.strip()
        if line.lower().startswith('date'):
            continue

        data = line.split(',')
        if len(data) == 2:
            names = data[1].strip().lower().split('/')
            for name in names:
                last_year_name_dict[name.strip()] = i

    avg_last_year = sum(last_year_name_dict.values()) / float(len(last_year_name_dict))

    # Parse the input file
    # Expected format : three strings per line
    #  First name, last name, integer year in program
    input_file = args.input_file
    year_dict = {}
    total_students = 0
    for line in input_file:
        data = line.strip().split(',')

        if len(data) != 3:
            continue

        try:
            year = int(data[2])
        except ValueError:
            continue

        first_name = data[0].strip()
        last_name = data[1].strip()
        if len(first_name) == 0 or len(last_name) == 0:
            continue

        if year not in year_dict:
            year_dict[year] = []

        student = Student(first_name, last_name, year)
        if year >= 4:
            student.sigma = 3.0
            student.mu = avg_last_year
        elif year == 1:
            student.mu = 6.0
            student.sigma = 7.0
        else:
            student.mu = find_position(student, last_year_name_dict)
            student.sigma = 5.0

        # Special cases and students who missed last year
        if student.last_name == 'Himmelstein':
            # Special case as Daniel presented at retreat
            student.mu = avg_last_year
            student.sigma = 3.0
        elif student.last_name == 'Citron':
            student.mu = -20.0
            student.sigma = 0.1
        elif student.last_name == 'Loshbaugh':
            student.mu = -20.0
            student.sigma = 0.1
        elif student.last_name == 'Sharon':
            student.mu = 0.0
            student.sigma = 1.0

        year_dict[year].append( student )
        total_students += 1

    print 'Parsed input file and found %d total students in %d years' % (total_students, len(year_dict) )

    # Pair student speakers for specified years
    years_to_pair = [1,2]
    names_to_pair = []
    for year in years_to_pair:
        if year in year_dict:
            l = list(year_dict[year])
            random.shuffle(l)
            names_to_pair.extend(l)

    speakers_by_week = []
    paired_names = []
    for i, name in enumerate(names_to_pair):
        if name in paired_names:
            # Name already paired, so skip
            continue
        if i+2 <= len(names_to_pair):
            # Another element follows, so we can pair with that one
            speakers_by_week.append( Week(names_to_pair[i], names_to_pair[i+1]) )
            paired_names.append(names_to_pair[i])
            paired_names.append(names_to_pair[i+1])
        else:
            speakers_by_week.append( Week(name) )
            paired_names.append( name )

    # Add non-paired speakers
    for year in year_dict:
        if year in years_to_pair:
            continue
        
        for student in year_dict[year]:
            week = Week(student)
            speakers_by_week.append(week)


    # Generate random list
    speakers_by_week.sort(key=lambda x: x.sort_number())

    for i, week in enumerate(speakers_by_week):
        print 'Week %d: %s' % (i+1, str(week.students) )
            
if __name__=='__main__':
    main()
