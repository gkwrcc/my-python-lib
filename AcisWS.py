#!/usr/bin/python
'''
module AcisWS.py

This module handles all Acis-WS calls for data needed to run WRCC data apps.
WRCC programs included so far:
sodlist, sodsum
'''


#############################################################################
#python modules
import datetime
import sys
from collections import defaultdict
#############################################################################
#WRCC specific modules
import WRCCUtils
##############################################################################
# import modules required by Acis
import urllib2
import json
##############################################################################
# set Acis data server
base_url = 'http://data.rcc-acis.org/'
##############################################################################

#Acis WebServices functions
###########################
def make_request(url,params) :
	req = urllib2.Request(url,
	json.dumps(params),
	{'Content-Type':'application/json'})
	response = urllib2.urlopen(req)
	return json.loads(response.read())

def MultiStnData(params) :
	return make_request(base_url+'MultiStnData',params)

def StnData(params) :
	return make_request(base_url+'StnData',params)

#Routine to filter out data according to window specification
#############################################################
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


def find_start_end_dates(cmd):
	if 'start_date' not in cmd.keys():
		s_date = 'por'
	else:
		if cmd['start_date'] == '' or cmd['start_date'] == ' ':
			s_date = 'por'
		else:
			s_date = cmd['start_date']
	if 'end_date' not in cmd.keys():
		e_date = 'por'
	else:
		if cmd['end_date'] == '' or cmd['end_date'] == ' ':
			e_date = 'por'
		else:
			e_date = cmd['end_date']
	return s_date, e_date


def get_sodsum_data(cmd):
	if 'element' not in cmd.keys() or 'coop_station_ids' not in cmd.keys():
		print 'element and coop_station_id options required!'
		sys.exit(0)
	if not cmd['element'] or not cmd['coop_station_ids']:
		print 'element and coop_station_id options required!'
		sys.exit(0)
	s_date, e_date = find_start_end_dates(cmd)
	#Get list of station ids.
	#if 'county' in cmd.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_county(cmd['county'])
	#elif 'climdiv' in cmd.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_climdiv(cmd['climdiv'])
	#elif 'cwa' in cmd.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_cwa(cmd['cwa'])
	#elif 'basin' in cmd.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_basin(cmd['basin'])
	#elif 'state' in cmd.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_cwa(cmd['state'])
	#elif 'bounding_box' in cmd.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_cwa([cmd['bounding_box'].split(,)])
	coop_station_ids = cmd['coop_station_ids'] #list of stn ids (converted to list in form)
	#sort coop ids in ascending order, strip left zeros first, sort and reattach zeros
	c_ids_strip_list = [int(stn.lstrip('0')) for stn in coop_station_ids]
	coop_station_ids = sorted(c_ids_strip_list)
	for i, stn in enumerate(coop_station_ids):
		if len(str(stn)) == 5:
			coop_station_ids[i] = '0'+ str(stn)
		else:
			coop_station_ids[i] = str(stn)
	print coop_station_ids
	datadict = defaultdict(list)
	station_names=[' ' for i in range(len(coop_station_ids))]
	if cmd['element']!= 'multi':
		elements = [cmd['element']]
		#evap, wdmv, wesf not fully implemented into Acis_WS yet
		if cmd['element'] in ['evap', 'wdmv', 'wesf']:
			print 'Evaporation, wind and water equivalent not implemented yet. Please chose another element!'
			sys.exit(0)
	else:
		elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst']
	#request data on a station by station basis
	for i, stn_id in enumerate(coop_station_ids):
		if cmd['element']!= 'multi':
			params = dict(sid=stn_id, sdate=s_date, edate=e_date, elems=[dict(name='%s' % cmd['element'])])
		else:
			params = dict(sid=stn_id, sdate=s_date, edate=e_date, elems=[dict(name='pcpn'), \
			dict(name='snow'), dict(name='snwd'), dict(name='maxt'), dict(name='mint'), dict(name='obst')])

		request = StnData(params)
		try:
			request['meta']
			station_names[i] = request['meta']['name']
		except:
			station_names[i] = ' '

		try:
			request['data']
			datadict[i] = request['data']
		except:
			datadict[i]=[]

	return datadict, elements, coop_station_ids, station_names

def get_sodsum_data_multi(cmd):
	if 'element' not in cmd.keys() or 'coop_station_ids' not in cmd.keys():
		print 'Error in AcisWs.get_sodsum_data! element and coop_station_id options required!'
		sys.exit(0)
	s_date, e_date = find_start_end_dates(cmd)
	#FIX ME: Acis_WS MultiStnData call does not support 'por' yet!
	if s_date == 'por' or e_date == 'por':
		print "Error! Acis_WS multi station call does not support calls for period of record yet. Please chose a data!"
		sys.exit(1)
	coop_station_ids = cmd['coop_station_ids']
	stn_name = ' '
	#make list of dates in date range [s_date, e_date]
	#NOTE: this assumes no gaps in data which may not be true
	#Currently no dates come out of Acis_WS MultiStnData calls
	dates = WRCCUtils.get_dates(s_date, e_date)
	#make params list for data call
	if cmd['element']!= 'multi':
		element = cmd['element']
		elements = [cmd['element']]
		if element == 'evap': #need to work with var major (vX) and var minor (vN)
			vXvN = 7
		elif element == 'wdmv':
			vXvN = 12
		elif  element == 'wesf':
			vXvN = 13
		if element in ['evap', 'wdmv', 'wesf']:
			params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=[dict(vX=vXvN)])
		else:
			params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=[dict(name='%s' % element)])

		params_e = None
		params_w = None
		params_ws = None
	else:
		#elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst', 'evap', 'wdmv', 'wesf']
		elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst']
		params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
		elems=[dict(name='pcpn'), dict(name='snow'), dict(name='snwd'), dict(name='maxt'), dict(name='mint'), dict(name='obst')])
		#FIX ME: leaving out evap,wdmv, wesf data for now until MultiStnData is implemented fully
        #(date issue)

		'''
		FIX ME: leaving out evap,wdmv, wesf data for now until MultiStnData is implemented fully
		()
		params_e = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=[dict(vX=7)])
		params_w = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=[dict(vX=12)])
		params_ws = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=[dict(vX=13)])
		'''

	#Request data
	data_dict = defaultdict(list)
	station_names=[' ' for i in range(len(coop_station_ids))]
	request = MultiStnData(params)
	try:
		request['data']#list of data for the stations
	except:
		if request['error']:
			print '%s' % str(request['error'])
			sys.exit(1)
		else:
			'Unknown error ocurred when getting data'
			sys.exit(1)
	for j, stn_data in enumerate(request['data']):
		try:
			stn_data['meta']
			station_id = str(stn_data['meta']['sids'][1].split()[0])
			try:
				index = coop_station_ids.index(station_id)
			except ValueError:
				continue
			station_names[index] = stn_data['meta']['name']
			try:
				stn_data['data']
				data_dict[index] = stn_data['data']
			except:
				data_dict[index] = []
		except:
			pass
	'''
	#ADD rest of data
	params_list = [params_e, params_w, params_ws]
	for i, prms in enumerate(params_list):
		if prms:
			request = MultiStnData(prms)
			try:
				request['data']#list of data for the stations
			except:
				if request['error']:
					print '%s' % str(request['error'])
					print 'For element %s (1: evap, 2: wind movement, 3: water equivalent)' % i
				else:
					print 'Unknown error ocurred when getting data'

			for j, stn_data in enumerate(request['data']):
				try:
					stn_data['meta']
					station_id = stn_data['meta']['sids'][0].split()[0]
					index = coop_station_ids.find(station_id)
					try:
						stn_data['data']
						for k in stn_data['data']:
							data_dict[index][k]+= stn_data['data'][k]
					except:
						pass
				except:
					pass
	'''
	return data_dict, dates, elements, coop_station_ids, station_names

#Routine to return data for programs sodlist, sodmonline(my), sodcnv
def get_sod_data(cmd, program):
	s_date, e_date = find_start_end_dates(cmd)
	coop_station_id = cmd['coop_station_id']
	if program in ['sodlist', 'sodcnv']:
		if 'include_tobs_evap' in cmd.keys():
			params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, \
			elems=[dict(name='pcpn', add='f,t'), dict(name='snow', add='f,t'), dict(name='snwd', add='f,t'),
			dict(name='maxt', add='f,t'), dict(name='mint', add='f,t'), dict(name='obst', add='f,t')])

			params_e = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(vX=7,add='f,t', prec=2)])
		else:
			if not program == 'sodcnv':
				params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, \
				elems=[dict(name='pcpn', add='f,t'), dict(name='snow', add='f,t'), dict(name='snwd', add='f,t'),
				dict(name='maxt', add='f,t'), dict(name='mint', add='f,t')])
			else:
				params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, \
				elems=[dict(name='pcpn', add='f,t'), dict(name='snow', add='f,t'), dict(name='snwd', add='f,t'),
				dict(name='maxt', add='f,t'), dict(name='mint', add='f,t'), dict(name='obst', add='f,t')])
	elif program in ['sodmonline', 'sodmonlinemy']:
		#sodmonline(my) only available for full years
		s_date = '%s%s' % (s_date[0:4], '0101')
		e_date = '%s%s' % (e_date[0:4], '1231')
		if cmd['element'] == 'evap':
			vXvN = 7
		elif cmd['element'] == 'wdmv':
			vXvN = 12
		elif cmd['element'] in ['wesf']:
			vXvN = 13

		if cmd['element'] in ['evap','wdmv', 'wesf' ]: #need to work with var major (vX) and var minor (vN)
			params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[vXvN])
		elif cmd['element'] in ['dtr', 'mmt']:
			params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(name='maxt'), dict(name='mint')])
		else:
			params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(name='%s' % cmd['element'])])
	else:
		print 'Program %s not supported in get_sod_data. Program should be one out of [sodlist, sodcnv, sodmonline, sodmonlinemy]!' % program
		sys.exit(0)

	#Request evap, wind and water equivalent data
	#NOTE: these data need to be obtained via var major:
	if program == 'sodlist' and 'include_tobs_evap' in cmd.keys():
		request_evap = StnData(params_e)
		try:
			request_evap['meta']
		except:
			if request_evap['error']:
				print '%s' % str(request_evap['error'])
			else:
				print 'Unknown error ocurred when getting evap data'
		try:
			request_evap['data']
			evap_data = request_evap['data']
		except:
			evap_data = None
	else:
		evap_data = None

	#retrieve data via Acis webservices
	request = StnData(params)

	#Test for successful data retrieval and get metadata information
	try:
		request['meta']
		stn_name = request['meta']['name']
	except:
		if request['error']:
			print '%s' % str(request['error'])
			stn_name = ' '
		else:
			print 'Unknown error ocurred. Check input values!'

	try:
		request['data']
		req_data = request['data']
	except:
		print 'No data found!'
		req_data = None

	#get windowed data is program is sodlist
	if program == 'sodlist':
		if 'start_window' not in cmd.keys():
			s_window = '0101'
		else:
			s_window = cmd['start_window']
		if 'end_window' not in cmd.keys():
			e_window = '1231'
		else:
			e_window = cmd['end_window']


        	if s_window!= '0101' or e_window != '1231':
			if req_data:
                		data = get_windowed_data(req_data, s_date, e_date, s_window, e_window)
			else:
				data = None
        	else:
			if req_data:
                		data = req_data
			else:
				data = None
	else:
		if req_data:
        		data = req_data
		else:
			data = None

	#Join evap_data if present
	if evap_data:
		for i, val in enumerate(evap_data):
			data[i].append(val[1])

	return data, stn_name
