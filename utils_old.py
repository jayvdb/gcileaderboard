#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Google Code-In unofficial leaderboard utils file
# Copyright (C) Ignacio Rodríguez <ignacio@sugarlabs.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from HTMLParser import HTMLParser
import sys
import urllib2
import json
from orgs import data_old as tmp

BASE_URL = "http://www.google-melange.com/gci"
TASKS_URL = BASE_URL + \
    "/org/google/gci{year}/{orgname}?fmt=json&limit=1000&idx=1"
ACCEPTED_ORGS_URL = BASE_URL + \
    "/org/list/public/google/gci{year}?fmt=json&limit=50&idx=1"
LEADERBOARD_URL = BASE_URL + \
    "/org_scores/google/gci{year}/{orgname}?fmt=json&limit=1000&idx=0"
TASK_URL = BASE_URL + "/task/view/google/gci{year}/{taskKey}"
CURRENT_CONTEST = 2014
ORG_TASKS = {2010: {}, 2011: {}, 2012: {}, 2013: {}, 2014: {}}
ORG_LEADERBOARD = {2010: {}, 2011: {}, 2012: {}, 2013: {}, 2014: {}}
CONTEST_LEADERBOARD = {2010: {}, 2011: {}, 2012: {}, 2013: {}, 2014: {}}
ORGS_DATA = {2010: {}, 2011: {}, 2012: {}, 2013: {}, 2014: {}}
ORG_TASKS = tmp.tasks
ORGS_DATA = tmp.data
PARSER = HTMLParser()


class GCIUtils():

    def __init__(self):
        self.updating = False

        # Start data. Take a few minutes
        for year in ORGS_DATA.keys():
            """
            DISABLED FOR TEST
            data = self.get_orglist(year)
            ORGS_DATA[year]['orglist'] = data[0]
            ORGS_DATA[year]['chart_data'] = data[1]
            self.update_orgs_tasks(year)
            """
            self.update_leaderboard(int(year))
        self.change_process_name()

    def change_process_name(self, name='gci-leaderboard'):
        if sys.platform == 'linux2':
            import ctypes
            libc = ctypes.cdll.LoadLibrary('libc.so.6')
            libc.prctl(15, name, 0, 0, 0)
            libc.prctl(15, name, 0, 0, 0)

    def get_orglist(self, year):
        url = ACCEPTED_ORGS_URL.format(year=str(year))
        request = urllib2.Request(url)
        data = json.loads(urllib2.urlopen(request).read())['data']['']
        orglist = ['all']
        # Data for the chart
        orglist_data = {}
        for item in data:
            org_id = item['columns']['org_id']
            org_name = item['columns']['name']
            orglist.append(org_id)
            orglist_data[org_id] = [org_name, 0]

        return (orglist, orglist_data)

    def update_orgs_tasks(self, year):
        """
        Update org tasks, used in a Thread.
        When GCI is running, this function is called every 5 minutes.
        """
        self.updating = True
        orglist = ORGS_DATA[year]['orglist']

        for org in orglist:
            if org == 'all':
                continue
            url = TASKS_URL.format(orgname=org, year=str(year))
            print url
            request = urllib2.Request(url)
            data = json.loads(urllib2.urlopen(request).read())['data']['']
            ORG_TASKS[year][org] = data

        print "Updated orgs %s for year %d." % (str(orglist), year)
        self.updating = False

    def _update_leaderboard(self, year):
        """
        Update org leaderboards, used in a Thread.
        When GCI is running, this function is called every 5 minutes.
        Currently unused.. Only works with 2014.. GCI lost data?
        """

        orglist = ORGS[year]['orglist']
        for org in orglist:
            url = LEADERBOARD_URL.format(orgname=org, year=str(year))
            request = urllib2.Request(url)
            data = json.loads(urllib2.urlopen(request).read())
            ORG_LEADERBOARD[year][org] = data

    def update_leaderboard(self, year):
        """
        Update org leaderboards, used in a Thread.
        When GCI is running, this function is called every 5 minutes.
        """
        orglist = ORGS_DATA[year]['orglist']
        CONTEST_LEADERBOARD[year]['all'] = {}
        for org in orglist:
            if org == 'all':
                continue
            data = ORG_TASKS[year][org]
            CONTEST_LEADERBOARD[year][org] = {}
            for row in data:
                student_name = row['columns']['student']
                if student_name not in CONTEST_LEADERBOARD[year][org]:
                    CONTEST_LEADERBOARD[year][org][student_name] = {
                        'name': PARSER.unescape(student_name),
                        'tasks': 1}
                else:
                    CONTEST_LEADERBOARD[year][org][student_name]['tasks'] += 1

                if student_name not in CONTEST_LEADERBOARD[year]['all']:
                    CONTEST_LEADERBOARD[year]['all'][student_name] = {
                        'name': PARSER.unescape(student_name),
                        'tasks': 1}
                else:
                    CONTEST_LEADERBOARD[year]['all'][
                        student_name]['tasks'] += 1

    def get_student_tasks(self, username, year, org):
        """
        Return the tasks of the student,
        requires username (str), year (int), org (str)
        """
        tasks_data = {
            'total_tags': {
                'User Interface': 0,
                'Code': 0,
                'Documentation/Training': 0,
                'Outreach/Research': 0,
                'Quality Assurance': 0},
            'tasks': {}}
        orgs = [org]
        if org == 'all':
            orgs = ORGS_DATA[year]['orglist']

        for org in orgs:
            if org == 'all':
                continue
            try:
                data = ORG_TASKS[year][org]
            except KeyError:
                return tasks_data

            for row in data:
                realdata = row['columns']
                if realdata['student'] != username:
                    continue
                title = PARSER.unescape(realdata['title']).capitalize()
                link = TASK_URL.format(
                    year=str(year),
                    taskKey=str(
                        realdata['key']))
                tags = realdata['types'].split(', ')

                for tag in tags:
                    if tag in ["Training", "Documentation"]:
                        tag = "Documentation/Training"
                    elif tag in ["Outreach", "Research"]:
                        tag = "Outreach/Research"
                    elif tag == "Testing":
                        tag = "Quality Assurance"
                    elif tag == "Translation":
                        tag = "User Interface"
                    try:
                        tasks_data['total_tags'][tag] += 1
                    except KeyError:
                        continue

                tasks_data['tasks'][
                    realdata['key']] = {
                    'title': title.capitalize(),
                    'link': link,
                    'tags': tags,
                    'org': self.get_org_name(year, org),
                    'key': realdata['key']}
        return tasks_data

    def get_org_name(self, year, org_id):
        if org_id == 'all':
            return 'All organizations'
        return ORGS_DATA[year]['chart_data'][org_id][0]

    def get_tasks_count(self, year, org_id):
        tags = {
            'User Interface': 0,
            'Code': 0,
            'Documentation/Training': 0,
            'Outreach/Research': 0,
            'Quality Assurance': 0}
        orgs = [org_id]
        if org_id == 'all':
            orgs = ORGS_DATA[year]['orglist']

        for org in orgs:
            if org == 'all':
                continue
            data = ORG_TASKS[year][org]
            for row in data:
                realdata = row['columns']
                tag_s = realdata['types'].split(', ')
                for tag in tag_s:
                    try:
                        if tag in ["Training", "Documentation"]:
                            tag = "Documentation/Training"
                        elif tag in ["Outreach", "Research"]:
                            tag = "Outreach/Research"
                        elif tag == "Testing":
                            tag = "Quality Assurance"
                        elif tag == "Translation":
                            tag = "User Interface"
                        tags[tag] += 1
                    except KeyError:
                        continue
        return tags

    def get_tasks(self, year, orgname):
        orgs = list(ORGS_DATA[int(year)]['orglist'])
        if orgname not in orgs:
            return page_not_found(404)

        pageOrgs = []
        for org in orgs:
            pageOrgs.append(
                {'id': org, 'name': self.get_org_name(year, org)})

        if orgname != 'all':
            totalTasks = len(ORG_TASKS[year][orgname])
        else:
            totalTasks = 0
            for org in ORGS_DATA[year]['orglist']:
                if org == 'all':
                    continue
                totalTasks += len(ORG_TASKS[year][org])

        userTasks = sorted(
            CONTEST_LEADERBOARD[year][orgname].iteritems(),
            key=lambda x: x[1]['tasks'],
            reverse=True)
        return {
            "userTasks": userTasks,
            "totalTasks": totalTasks,
            "pageOrgs": pageOrgs}
