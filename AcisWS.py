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

def MultiStnData(params):
	return make_request(base_url+'MultiStnData',params)

def StnData(params):
	return make_request(base_url+'StnData',params)

def StnMeta(params):
	return make_request(base_url+'StnMeta',params)

#Utility functions
def find_start_end_dates(form_input):
	if 'start_date' not in form_input.keys():
		s_date = 'por'
	else:
		if form_input['start_date'] == '' or form_input['start_date'] == ' ':
			s_date = 'por'
		else:
			s_date = form_input['start_date']
	if 'end_date' not in form_input.keys():
		e_date = 'por'
	else:
		if form_input['end_date'] == '' or form_input['end_date'] == ' ':
			e_date = 'por'
		else:
			e_date = form_input['end_date']
	return s_date, e_date

def get_station_list(by_type, val):
	stn_list = []
	if by_type == 'county':
		params = dict(county=val)
	elif by_type == 'climdiv':
		params = dict(climdiv=val)
	elif by_type == 'cwa':
		params = dict(cwa=val)
	elif by_type == 'basin':
		params = dict(basin=val)
	elif by_type == 'state':
		params = dict(state=val)
	elif by_type == 'bounding_box':
		params = dict(bbox=val)
	else:
		pass
	request=StnMeta(params)
	try:
		request['meta']
		for i, stn in enumerate(request['meta']):
			sids = stn['sids']
			for sid in sids:
				sid_split = sid.split(' ')
				if sid_split[1] == '2':
					stn_list.append(str(sid_split[0]))
	except:
		pass

	return stn_list



def get_soddyrec_data(form_input):
	datadict = defaultdict(list)
	s_date, e_date = find_start_end_dates(form_input)
	if form_input['element'] == 'all':
		elements = ['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd']
	elif form_input['element'] == 'tmp':
		elements = ['maxt', 'mint', 'pcpn']
	elif form_input['element'] == 'wtr':
		elements = ['pcpn', 'snow', 'snwd']
	els = [dict(name='%s' % el) for el in elements]
	if 'coop_station_id' in form_input.keys():
		coop_station_ids =[form_input['coop_station_id']]
	elif 'coop_station_ids' in form_input.keys():
		coop_station_ids = form_input['coop_station_ids']
	elif 'county' in form_input.keys():
		coop_station_ids = get_station_list('county', form_input['county'])
	elif 'climdiv' in form_input.keys():
		coop_station_ids = get_station_list('climdiv', form_input['climdiv'])
	elif 'county_warning_area' in form_input.keys():
		coop_station_ids = get_station_list('cwa', form_input['county_warning_area'])
	elif 'basin' in form_input.keys():
		coop_station_ids = get_station_list('basin', form_input['basin'])
	elif 'state' in form_input.keys():
		coop_station_ids = get_station_list('state', form_input['state'])
	elif 'bounding_box' in form_input.keys():
		coop_station_ids = get_station_list('bounding_box', form_input['bounding_box'])
	else:
		coop_station_ids =[]
	station_names=[' ' for i in range(len(coop_station_ids))]
	#MULTISTATION
	params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=els)
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
				datadict[index] = stn_data['data']
			except:
				datadict[index] = []
		except:
			pass

	#STATION BY STATION
	#NOTE: VERY SLOW IN COMPARISON TO MULTI STATION CALL (~10fold or more)
	'''
	for i, stn in enumerate(coop_station_ids):
		params = dict(sid=stn, sdate=s_date, edate=e_date, elems=els)
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
	'''
	return datadict, elements, coop_station_ids, station_names

def get_sodsum_data(form_input):
	if 'element' not in form_input.keys() or 'coop_station_ids' not in form_input.keys():
		print 'element and coop_station_id options required!'
		sys.exit(0)
	if not form_input['element'] or not form_input['coop_station_ids']:
		print 'element and coop_station_id options required!'
		sys.exit(0)
	s_date, e_date = find_start_end_dates(form_input)
	#Get list of station ids.
	#if 'county' in form_input.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_county(form_input['county'])
	#elif 'climdiv' in form_input.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_climdiv(form_input['climdiv'])
	#elif 'cwa' in form_input.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_cwa(form_input['cwa'])
	#elif 'basin' in form_input.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_basin(form_input['basin'])
	#elif 'state' in form_input.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_cwa(form_input['state'])
	#elif 'bounding_box' in form_input.keys():
		#coop_station_ids = AcisWS.get_station_ids_by_cwa([form_input['bounding_box'].split(,)])
	coop_station_ids = form_input['coop_station_ids'] #list of stn ids (converted to list in form)
	#sort coop ids in ascending order, strip left zeros first, sort and reattach zeros
	coop_station_ids = WRCCUtils.strip_n_sort(coop_station_ids)
	datadict = defaultdict(list)
	station_names=[' ' for i in range(len(coop_station_ids))]
	if form_input['element']!= 'multi':
		elements = [form_input['element']]
		#evap, wdmv, wesf not fully implemented into Acis_WS yet
		if form_input['element'] in ['evap', 'wdmv', 'wesf']:
			print 'Evaporation, wind and water equivalent not implemented yet. Please chose another element!'
			sys.exit(0)
	else:
		elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst']
	#request data on a station by station basis
	for i, stn_id in enumerate(coop_station_ids):
		if form_input['element']!= 'multi':
			params = dict(sid=stn_id, sdate=s_date, edate=e_date, elems=[dict(name='%s' % form_input['element'])])
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

def get_sodsum_data_multi(form_input):
	if 'element' not in form_input.keys() or 'coop_station_ids' not in form_input.keys():
		print 'Error in AcisWs.get_sodsum_data! element and coop_station_id options required!'
		sys.exit(0)
	s_date, e_date = find_start_end_dates(form_input)
	#FIX ME: Acis_WS MultiStnData call does not support 'por' yet!
	if s_date == 'por' or e_date == 'por':
		print "Error! Acis_WS multi station call does not support calls for period of record yet. Please chose a data!"
		sys.exit(1)
	coop_station_ids = form_input['coop_station_ids']
	stn_name = ' '
	#make list of dates in date range [s_date, e_date]
	#NOTE: this assumes no gaps in data which may not be true
	#Currently no dates come out of Acis_WS MultiStnData calls
	dates = WRCCUtils.get_dates(s_date, e_date)
	#make params list for data call
	if form_input['element']!= 'multi':
		element = form_input['element']
		elements = [form_input['element']]
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
def get_sod_data(form_input, program):
	s_date, e_date = find_start_end_dates(form_input)
	coop_station_id = form_input['coop_station_id']
	if program in ['sodlist', 'sodcnv']:
		if 'include_tobs_evap' in form_input.keys():
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
		if form_input['element'] == 'evap':
			vXvN = 7
		elif form_input['element'] == 'wdmv':
			vXvN = 12
		elif form_input['element'] in ['wesf']:
			vXvN = 13

		if form_input['element'] in ['evap','wdmv', 'wesf' ]: #need to work with var major (vX) and var minor (vN)
			params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[vXvN])
		elif form_input['element'] in ['dtr', 'mmt']:
			params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(name='maxt'), dict(name='mint')])
		else:
			params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(name='%s' % form_input['element'])])
	else:
		print 'Program %s not supported in get_sod_data. Program should be one out of [sodlist, sodcnv, sodmonline, sodmonlinemy]!' % program
		sys.exit(0)

	#Request evap, wind and water equivalent data
	#NOTE: these data need to be obtained via var major:
	if program == 'sodlist' and 'include_tobs_evap' in form_input.keys():
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
		if 'start_window' not in form_input.keys():
			s_window = '0101'
		else:
			s_window = form_input['start_window']
		if 'end_window' not in form_input.keys():
			e_window = '1231'
		else:
			e_window = form_input['end_window']


        	if s_window!= '0101' or e_window != '1231':
			if req_data:
                		data = WRCCUtils.get_windowed_data(req_data, s_date, e_date, s_window, e_window)
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
