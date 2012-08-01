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

#This function is in place because Acis_WS's MultiStnCall does not return dates
#it takes as arguments a start date and an end date (format yyyymmdd)
#and returns the list of dates [s_date, ..., e_date] assuming that there are no gaps in the data
def get_dates(s_date, e_date):
	if s_date and e_date:
		dates = [s_date]
		#convert to datetimes
		start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
		end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
		for n in range(int ((end_date - start_date).days +1)):
			next_date = start_date + datetime.timedelta(n)
			dates.append(str(time.strftime('%Y%m%d', next_date.timetuple())))
	else:
		dates = []
	return dates

def strip_n_sort(station_list):
	c_ids_strip_list = [int(stn.lstrip('0')) for stn in station_list]
	stn_list = sorted(c_ids_strip_list)
	for i, stn in enumerate(stn_list):
		if len(str(stn)) == 5:
			stn_list[i] = '0' + str(stn)
		else:
			stn_list[i] = str(stn)
	return stn_list

#Utility functions
def find_start_end_dates(form_input):
	if 'start_date' not in form_input.keys():
		s_date = 'por'
	else:
		if form_input['start_date'] == '' or form_input['start_date'] == ' ':
			s_date = 'por'
		else:
			if len(form_input['start_date']) == 4:
				s_date = form_input['start_date'] + '0101'
			elif len(form_input['start_date']) == 8:
				s_date = form_input['start_date']
			else:
				print 'Invalid start date format, should be yyyy or yyyymmdd!'
				s_date = None
	if 'end_date' not in form_input.keys():
		e_date = 'por'
	else:
 		if form_input['end_date'] == '' or form_input['end_date'] == ' ':
 			e_date = 'por'
 		else:
			if len(form_input['end_date']) == 4:
				e_date = form_input['end_date'] + '1231'
			elif len(form_input['end_date']) == 8:
				e_date = form_input['end_date']
			else:
				print 'Invalid end date format, should be yyyy or yyyymmdd!'
				e_date = None
	return s_date, e_date

def get_element_list(form_input, program):
	if program == 'soddyrec':
		if form_input['element'] == 'all':
			elements = ['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd']
		elif form_input['element'] == 'tmp':
			elements = ['maxt', 'mint', 'pcpn']
		elif form_input['element'] == 'wtr':
			elements = ['pcpn', 'snow', 'snwd']
	elif program == 'soddynorm':
		elements = ['maxt', 'mint', 'pcpn']
	else:
		elements = []
	return elements
#Routine to filter out data according to window specification(sodlist)
#######################################################################
def get_windowed_data(data, start_date, end_date, start_window, end_window):
	if start_window == '0101' and end_window == '1231':
		windowed_data = data
	else:
		windowed_data = []
		start_indices=[]
		end_indices=[]
		if start_date == 'por':
			start_d = ''.join(data[0][0].split('-'))
		else:
			start_d = start_date
		if end_date == 'por':
			end_d = ''.join(data[-1][0].split('-'))
		else:
			end_d = end_date
		st_yr = int(start_d[0:4])
		st_mon = int(start_d[4:6])
		st_day = int(start_d[6:8])
		end_yr = int(end_d[0:4])
		end_mon = int(end_d[4:6])
		end_day = int(end_d[6:8])
		#Date formatting needed to deal with end of data and window size
		#doy = day of year
		if WRCCUtils.is_leap_year(st_yr) and st_mon > 2:
			doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday -1
		else:
			doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday
		if WRCCUtils.is_leap_year(end_yr) and end_mon > 2:
			doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday - 1
		else:
			doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday
		doy_window_st = WRCCUtils.compute_doy(start_window[0:2], start_window[2:4])
		doy_window_end = WRCCUtils.compute_doy(end_window[0:2], end_window[2:4])
		dates = [data[i][0] for i  in range(len(data))]
		start_w = '%s-%s' % (start_window[0:2], start_window[2:4])
		end_w = '%s-%s' % (end_window[0:2], end_window[2:4])
		#silly python doesn't have list.indices() method
		#Look for windows in data
		for i, date in enumerate(dates):
			if date[5:] == start_w:
				start_indices.append(i)
			if date[5:] == end_w:
				end_indices.append(i)
		#Check end conditions at endpoints:
		if doy_window_st == doy_window_end:
			pass
		elif doy_window_st < doy_window_end:
			if doy_first <= doy_window_end and doy_window_st < doy_first:
				start_indices.insert(0, 0)
			if doy_last < doy_window_end and doy_window_st <= doy_last:
				end_indices.insert(len(dates),len(dates)-1)
		else: #doy_window_st > doy_window_end
			if (doy_window_st > doy_first and doy_first <= doy_window_end) or (doy_window_st < doy_first and doy_first >= doy_window_end):
				start_indices.insert(0, 0)
			if (doy_last <= doy_window_st and doy_last < doy_window_end) or (doy_window_st <= doy_last and doy_last > doy_window_end):
				end_indices.insert(len(dates),len(dates)-1)
		#Sanity check
		if len(start_indices)!= len(end_indices):
			print 'Index error when finidng window. Maybe your window is not chronologically defined?'
			sys.exit(1)

		for j in range(len(start_indices)):
			add_data = data[start_indices[j]:end_indices[j]+1]
			windowed_data = windowed_data + add_data
	return windowed_data































