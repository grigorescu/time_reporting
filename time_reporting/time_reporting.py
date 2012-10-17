#!/usr/bin/env python2

import requests
import getpass
import sys
import datetime

URL         = "https://hrnet.uihr.uillinois.edu/PTRApplication/index.cfm"
LOGIN_URL   = "https://eas.admin.uillinois.edu/eas/servlet/login.do"
OVERDUE_URL = URL + "?fuseaction=TimesheetEntryForm&Overdue=true&"
SUBMIT_URL  = URL + "?fuseaction=SubmitTimesheet" 

USERNAME = getpass.getuser()
session = requests.session()

def usage():
    print """time_reporting.py
             University of Illinois SOEEA Time Reporting Tool

             Usage:
               time_reporting.py [date] [hours]
               
               hours - 7 values, for Sunday - Saturday, of hours worked.
                       Default: 0 8 8 8 8 8 0 (40 hour work week M-F)
               date  - date for overdue time reporting
                       Example: 01/21/1999"""


def isLoggedIn():
    result = session.get(URL).content
    if "easFormId" in result:
        return False
    else:
        return True

def login():
    print "Logging in as %s..." % USERNAME
    pwd = getpass.getpass()
    result = session.post(LOGIN_URL, data={'inputEnterpriseId': USERNAME, 'password': pwd, 'queryString': 'null', 'BTN_LOGIN': 'Login'}, allow_redirects=True)
    return result.content

def submit(date_string=None, hours=[0,8,8,8,8,8,0]):

    # Go to the requested date.
    if date_string is not None:
        url = get_url_for_date(date_string)
        print url
        result = session.get(url).content

    if len(hours) != 7:
        raise ValueError("Expected 7 values for Sunday-Saturday")
    d = {}
    days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    total = 0
    for i in range(len(days)):
        d[days[i] + "TimesheetHourValue"] = int(hours[i])
        total += int(hours[i]) * 60
        minutes = hours[i] % 1
        if minutes not in [0.0, 0.25, 0.5, 0.75]:
            raise ValueError("Please only use hours rounded to the nearest quarter-hour.")
        d[days[i] + "TimesheetMinuteValue"] = minutes
        total += minutes
    d['weekTotalHours'] = int(total/60)
    d['weekTotalMinutes'] = total % 60
    result = session.post(SUBMIT_URL, data=d, allow_redirects=True)
    return "You have successfully submitted" in result.content

def get_url_for_date(date_string):
    month, day, year = [int(x) for x in date_string.split('/')]
    date = datetime.date(year, month, day)
    url = OVERDUE_URL + "month=" + str(date.month) + "&selectedWeek=" + date_string
    return url
    
def main():
    # Current date.
    date_string = None
    # Typical work week.
    hours = [0, 8, 8, 8, 8, 8, 0]

    result = ''

    if not isLoggedIn():
        result = login()
    
    if "Edit" not in result:
        if len(sys.argv) == 1 or len(sys.argv) == 2:
            date_string = sys.argv[1]
        elif len(sys.argv) == 8 or len(sys.argv) == 9:
            try:
                hours = [float(x) for x in sys.argv[-7:]]
            except ValueError:
                usage()
                raise
                sys.exit(1)
        if submit(date_string, hours):
            print "Successfully submitted."
            result = session.get(url).content
        else:
            print "Error: Only", len(sys.argv), "arguments found."
            usage()
            sys.exit(1)
    else:
        print "Time reporting for this week is up to date."

    if "Submission of time for the following week(s) is overdue." in result:
        overdue = [x.strip() for x in result[result.find('id="pastDueWeek">'):result.find('</select>&nbsp;<input type="submit" id="getPastDueTimeEntryForm"')].split('\n') if x.strip()][1:]
        overdue = [x[x.find('month='):x.find('">')] for x in overdue]
        overdue = [x[x.find('Week=')+5:] for x in overdue]

        print "Warning: Overdue time reports (" + str(len(overdue)) + ")."
        if len(overdue) < 10:
            print '\n'.join(overdue)

if __name__ == "__main__":
    main()
