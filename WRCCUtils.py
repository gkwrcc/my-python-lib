#!/usr/bin/python

'''
Module WRCCUtils
'''

import datetime
import time

############################################################################################
#Utils
############################################################################################
'''
JulDay; Function utilized to check for gap in data
This program is based on and algorithm presented in 'Sky And Telescope Magazine, March 1984.'
It will correctly calculate any date A.D. to the correct Julian date through at least 3500 A.D.
Note that Julain dates begin at noon GMT. For this reason, the number is incremented by one to
correspond to a day beginning at midnight.
'''
def JulDay(year, mon, day):
	jd = 367 * year - 7 * (year + (mon + 9) / 12) / 4\
	- 3 * ((year + (mon - 9) / 7) / 100 +1) / 4\
	+ 275 * mon / 9 + day + 1721029

	jd+=1
	return int(jd)

#Routine to compute day of year ignoring leap years
###################################################
def compute_doy(mon,day):
	mon_len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	nmon = int(mon.lstrip('0'))
	nday = int(day.lstrip('0'))
	if nmon == 1:
		ndoy = nday
	else:
		ndoy = sum(mon_len[0:nmon - 1]) + nday
	return ndoy

def is_leap_year(year):
	if year % 100 != 0 and year % 4 == 0:
		return True
	elif year % 100 == 0 and year % 400 == 0:
		return True
	else:
		return False

#This function is in place because Acis_WS does not return dates
#it takes as arguments a start date and an end date (format yyyymmdd)
#and returns the list of dates [s_date, ..., e_date] assuming that there are no gaps in the data
def get_dates(s_date, e_date):
	dates = [s_date]
	#convert to datetimes
	start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
	end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
	for n in range(int ((end_date - start_date).days +1)):
		next_date = start_date + datetime.timedelta(n)
		dates.append(str(time.strftime('%Y%m%d', next_date.timetuple())))
	return dates
