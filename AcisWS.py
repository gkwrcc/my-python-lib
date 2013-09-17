#!/usr/bin/python
'''
module AcisWS.py

This module handles all Acis-WS calls for data needed to run WRCC data apps.
WRCC programs included so far:
sodlist, sodsum
'''

#############################################################################
#python modules
import numpy, bisect
import datetime
import sys
from collections import defaultdict
#############################################################################
#WRCC specific modules
import WRCCUtils, WRCCClasses, WRCCData
##############################################################################
# import modules required by Acis
import urllib2
import json
##############################################################################
# set Acis data server
#base_url = 'http://data.rcc-acis.org/'
base_url = 'http://data.wrcc.rcc-acis.org/'
## For Prism Data
test_url = 'http://data.test.rcc-acis.org/'
##############################################################################

#Acis WebServices functions
###########################
def make_request(url,params) :
    req = urllib2.Request(url,
    json.dumps(params),
    {'Content-Type':'application/json'})
    try:
        response = urllib2.urlopen(req)
        return json.loads(response.read())
    except urllib2.HTTPError as error:
        if error.code == 400 : print error.msg

def MultiStnData(params):
    return make_request(base_url+'MultiStnData',params)

def StnData(params):
    return make_request(base_url+'StnData',params)

def StnMeta(params):
    return make_request(base_url+'StnMeta',params)

def GridData(params):
    return make_request(base_url+'GridData',params)

def PrismData(params):
    return make_request(test_url+'GridData',params)

def GridCalc(params):
    return make_request(base_url+'GridCalc',params)

def General(request_type, params):
    '''
    request_type in [basin, climdiv,cwa,state, county]
    '''
    return make_request(base_url+'General' + '/' + request_type, params)


###################################
#Southwest CSC DATA PORTAL modules
###################################


####################################
#Functions
#####################################
def get_meta_data(search_area, val):
        '''
        Find meta data for  search_area = val
        '''
        meta_params = {
                        search_area: val,
                        'meta':'name,state,sids,ll,elev,uid,county,climdiv'
                      }
        request = StnMeta(meta_params)
        if 'error' in request.keys() or not 'meta' in request.keys() or not request:
            return {}
        return request

def station_meta_to_json(by_type, val, el_list=None, time_range=None, constraints=None):
    '''
    Requests station meta data from ACIS and writes results to a json file
    This json file is read by the javascript funcition initialize_station_map
    which generates the station finder map
    Keyword arguments:
    by_type    -- station selection argument.
                  station selection is one of: county, climate_division,
                  county_warning_area, basin, bounding_box, state or states
    val        -- Value of station selection argument, e.g, AL if by_type = state
    el_list    -- List of var_majors of climate elements (default None)
    time_range -- [start_date, end_date](default None)

    If el_list and time_range are given, only stations that have elements
    for the given time range are listed.
    '''
    stn_list = []
    stn_json={'network_codes': WRCCData.KELLY_NETWORK_CODES, 'network_icons': WRCCData.KELLY_NETWORK_ICONS}
    vX_list= ['1','2','43','3','4','10','11','7','45']
    vX_tuple = '1,2,43,3,4,10,11,7,45'
    '''
    if el_list is None:
        vX_list= ['1','2','43','3','4','10','11','7','45']
        vX_tuple = '1,2,43,3,4,10,11,7,45'
    else:
        vX_list = el_list
        vX_tuple = ','.join(el_list)
    '''
    params = {'meta':'name,state,sids,ll,elev,uid,county,climdiv,valid_daterange',"elems":vX_tuple}
    if by_type == 'county':
        params['county'] = val
    elif by_type == 'climate_division':
        params['climdiv'] = val
    elif by_type == 'county_warning_area':
        params['cwa'] = val
    elif by_type == 'basin':
        params['basin'] =val
    elif by_type == 'state':
        params['state'] =val
    elif by_type == 'bounding_box':
        params['bbox'] = val
    elif by_type == 'id' or by_type == 'station_id' or by_type == 'station_ids':
        params['sids'] =val
    elif by_type == 'states': #multiple states
        params['state'] = val
    elif by_type == 'sw_states':
        params['state'] = 'az,ca,co,nm,nv,ut'
    elif by_type == 'station':
        params['sids'] = val
    else:
        pass

    #Acis WS call
    request = StnMeta(params)
    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    stn_meta_list = []
    if 'meta' in request.keys():
        #For alphabetic ordering of station names
        sorted_list =[]
        for i, stn in enumerate(request['meta']):
            if not stn['valid_daterange']:
                continue
            #check if we are looking for stations with particular elements
            if el_list is not None and time_range is not None:

                #Check if ACIS produced correct output, i.e. one valid_daterange per element
                if len(stn['valid_daterange']) < len(el_list):
                    continue
                #Check if constraints are met for element list and date range
                if constraints in ['any_any', 'any_all']:
                    flag_invalid_station = True
                elif constraints in ['all_all', 'all_any']:
                    flag_invalid_station = False
                for el_idx, el_vX in enumerate(el_list):
                    #Find correct index in vX_list
                    try:
                        idx = vX_list.index(el_vX)
                    except:
                        if constraints in ['all_all', 'all_any']:
                            flag_invalid_station = True
                            break
                        elif constraints in ['any_any', 'any_all']:
                            continue
                    #Sanity Check
                    if not stn['valid_daterange'][idx] and (constraints == 'all_all'  or constraints == 'all_any' or constraints is None):
                        #data for this element does not exist at station
                        flag_invalid_station = True
                        break
                    elif not stn['valid_daterange'][idx] and (constraints == 'any_any' or constraints == 'any_all'):
                        continue

                    #Find period of record for this element and station
                    por_start = datetime.datetime(int(stn['valid_daterange'][idx][0][0:4]), int(stn['valid_daterange'][idx][0][5:7]),int(stn['valid_daterange'][idx][0][8:10]))
                    por_end = datetime.datetime(int(stn['valid_daterange'][idx][1][0:4]), int(stn['valid_daterange'][idx][1][5:7]),int(stn['valid_daterange'][idx][1][8:10]))
                    if time_range[0].lower() != 'por':
                        user_start = datetime.datetime(int(time_range[0][0:4]), int(time_range[0][4:6]),int(time_range[0][6:8]))
                    else:
                        user_start = por_start
                    if time_range[1].lower() != 'por':
                        user_end = datetime.datetime(int(time_range[1][0:4]), int(time_range[1][4:6]),int(time_range[1][6:8]))
                    else:
                        user_end = por_end
                    #Check constraints logic for this element and station
                    if constraints == 'all_all' or constraints is None:
                        #all  elements have data records for all dates within start and end date given by user
                        if user_start < por_start or user_end > por_end:
                            flag_invalid_station =  True
                            break
                    elif constraints == 'any_any':
                        #At least one element has one data record within user given time_range
                        if (user_end >= por_start and user_start <= por_end) or (user_start <= por_end and user_end >=por_start):
                            flag_invalid_station = False
                            break
                    elif constraints == 'all_any':
                        #All elements have at least one data record within user given time_range
                        if (user_end >= por_start and user_start <= por_end) or (user_start <= por_end and user_end >=por_start):
                            continue
                        else:
                            flag_invalid_station =  True
                            break
                    elif constraints == 'any_all':
                        #At least one elements has data records for all dates within given date_range
                        if user_start >= por_start and user_end <= por_end:
                            flag_invalid_station = False
                            break
                #Check if station is valid, if not, proceed to next station
                if flag_invalid_station:
                    continue


            stn_sids = []
            stn_networks = []
            stn_network_codes = []
            sids = stn['sids'] if 'sids' in stn.keys() else []
            marker_icons = []
            for sid in sids:
                sid_split = sid.split(' ')
                #put coop id up front (for csc application metagraph  and possibly others)
                if str(sid_split[1]) == '2':
                    stn_sids.insert(0,str(sid_split[0]).replace("\'"," "))
                    stn_network_codes.insert(0, str(sid_split[1]))
                    marker_icons.insert(0, WRCCData.NETWORK_ICONS[str(sid_split[1])])
                    stn_networks.insert(0,WRCCData.NETWORK_CODES[str(sid_split[1])])
                else:
                    stn_sids.append(str(sid_split[0]).replace("\'"," "))
                    stn_network_codes.append(str(sid_split[1]))
                    if int(sid_split[1]) <= 10:
                        stn_networks.append(WRCCData.NETWORK_CODES[str(sid_split[1])])
                        marker_icons.append(WRCCData.NETWORK_ICONS[str(sid_split[1])])
                    else:
                        stn_networks.append('Misc')
                        marker_icons.append(WRCCData.NETWORK_ICONS['11'])
            #Sanity check : Some Acis records are incomplete, leading to key error
            if 'll' in stn.keys():
                lat = str(stn['ll'][1])
                lon = str(stn['ll'][0])
            else:
                continue
            name = str(stn['name']).replace("\'"," ") if 'name' in stn.keys() else 'Name not listed'
            uid = str(stn['uid']) if 'uid' in stn.keys() else 'Uid not listed'
            elev = str(stn['elev']) if 'elev' in stn.keys() else 'Elevation not listed'
            state_key = str(stn['state']).lower() if 'state' in stn.keys() else 'State not listed'
            #Generate one entry per network that the station belongs to
            for j, sid in enumerate(stn_networks):
                stn_dict = {"name":name,"uid":uid,"sids":stn_sids,"elevation":elev,"lat":lat,"lon":lon,\
                "state":state_key, 'marker_icon': marker_icons[j], 'marker_category':stn_networks[j], \
                'stn_networks':stn_networks, 'stn_network_codes': stn_network_codes}
                #check which elements are available at the stations[valid_daterange is not empty]
                valid_date_range_list = stn['valid_daterange']
                available_elements = []
                for j,rnge in enumerate(valid_date_range_list):
                    if rnge:
                        available_elements.append([WRCCData.ACIS_ELEMENTS[vX_list[j]]['name_long'], [str(rnge[0]), str(rnge[1])]])

                if available_elements:
                    stn_dict['available_elements'] = available_elements
                #find index in alphabetically ordered list of station names
                sorted_list.append(name.split(' ')[0])
                try:
                    sorted_list.sort()
                    stn_idx = sorted_list.index(name.split(' ')[0])
                except ValueError:
                    stn_idx = -1
                #Insert stn into alphabeticlly ordered list
                if stn_idx == -1:
                    stn_meta_list.append(stn_dict)
                else:
                    stn_meta_list.insert(stn_idx, stn_dict)
    else:
        if 'error' in request.keys():
            stn_json['error'] = request['error']
        else:
            stn_json['error'] = ['No meta data found']

    stn_json["stations"] = stn_meta_list
    #double quotes needed for jquery json.load
    stn_json_str = str(stn_json).replace("\'", "\"")
    time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_')
    if by_type == 'sw_states':
        f_name = 'SW_stn.json'
        f = open('/www/apps/csc/media/tmp/' + f_name,'w+')
    else:
        f_name = time_stamp + 'stn.json'
        f = open('/tmp/' +  f_name,'w+')
    f.write(stn_json_str)
    f.close()
    return stn_json, f_name


def get_station_data(form_input, program):
    '''
    Retrieves Station Data from ACIS.
    Keyword arguments:
    form_input -- parameter file for data request obtained from user of CSC pages
    program -- specifies program that is making the request.

    Returned is a resultsdictionary with entries:
    'stn_data'   -- list of station data of form [date, val_element1, val_element2, ...val_elementn]
                    for each station
    'dates'      -- list of dates of request
    'stn_ids'    -- list of station ids
    'stn_names'  -- list of station names
    'stn_errors' -- list of errors that occurred during request
    'elements'   -- list of elements of request
    '''
    #Set up parameters for data request
    resultsdict = defaultdict(list)
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    #Sanity check for valid date input:
    if (s_date.lower() == 'por' or e_date.lower() == 'por') and ('station_id' not in form_input.keys()):
        resultsdict['error'] = 'Parameter error. Start/End date ="por" not supported for multi station call.'
        return resultsdict

    elements = WRCCUtils.get_element_list(form_input, program)
    elems_list = []
    for el in elements:
        el_strip = el[0:3]
        try:
            base_temp = int(el[3:])
        except:
            base_temp = None
        if el_strip in ['gdd', 'hdd', 'cdd'] and base_temp is not None:
            elems_list.append(dict(vX=WRCCData.ACIS_ELEMENTS_DICT[el_strip]['vX'], base=base_temp, add='f,t'))
        else:
            elems_list.append(dict(vX=WRCCData.ACIS_ELEMENTS_DICT[el]['vX'],add='f,t'))
    params = dict(sdate=s_date, edate=e_date, \
    meta='name,state,sids,ll,elev,uid,county,climdiv,valid_daterange', \
    elems=elems_list)
    '''
    params = dict(sdate=s_date, edate=e_date, \
        meta='name,state,sids,ll,elev,uid,county,climdiv,valid_daterange', \
        elems=[dict(name=el, add='f,t')for el in elements])
    '''
    #Check for por start end dates
    if 'station_id' in form_input.keys():
        if s_date.lower() =='por' or e_date.lower() == 'por':
            #meta_params = dict(sids=form_input['station_id'],elems=[dict(name=el)for el in elements], meta='valid_daterange')
            elems_list =[]
            for el in elements:
                el_strip = el[0:3]
                try:
                    base_temp = int(el[3:])
                except:
                    base_temp = None
                if el_strip in ['gdd', 'hdd', 'cdd'] and base_temp is not None:
                    elems_list.append(dict(vX=WRCCData.ACIS_ELEMENTS_DICT[el_strip]['vX'], base=base_temp))
                else:
                    elems_list.append(dict(vX=WRCCData.ACIS_ELEMENTS_DICT[el]['vX']))

            meta_params = dict(sids=form_input['station_id'],elems=elems_list, meta='valid_daterange')
            try:
                meta_request = StnMeta(meta_params)
                if not 'meta' in meta_request.keys() or not meta_request['meta']:
                    resultsdict['errors'] = 'Metadata request fail. Cant find start, end data for station. Pameters: %s.' %(str(meta_params))
                    return resultsdict
            except Exception, e:
                resultsdict['errors'] = 'Metadata request fail. Cant find start, end data for station. Pameters: %s. Error: %s' %(str(meta_params), str(e))
                return resultsdict
            #Find largest daterange
            try:
                start = datetime.datetime(int(meta_request['meta'][0]['valid_daterange'][0][0][0:4]), int(meta_request['meta'][0]['valid_daterange'][0][0][5:7]),int(meta_request['meta'][0]['valid_daterange'][0][0][8:10]))
                end = datetime.datetime(int(meta_request['meta'][0]['valid_daterange'][0][1][0:4]), int(meta_request['meta'][0]['valid_daterange'][0][1][5:7]),int(meta_request['meta'][0]['valid_daterange'][0][1][8:10]))
                idx_s = 0
                idx_e = 0
            except Exception, e:
                resultsdict['errors'] = 'Metadata request fail. Cant find start, end data for station. Pameters: %s. Error: %s' %(str(meta_params), str(e))
                return resultsdict
            for el_idx, dr in enumerate(meta_request['meta'][0]['valid_daterange']):
                new_start = datetime.datetime(int(meta_request['meta'][0]['valid_daterange'][el_idx][0][0:4]), int(meta_request['meta'][0]['valid_daterange'][el_idx][0][5:7]),int(meta_request['meta'][0]['valid_daterange'][el_idx][0][8:10]))
                new_end = datetime.datetime(int(meta_request['meta'][0]['valid_daterange'][el_idx][1][0:4]), int(meta_request['meta'][0]['valid_daterange'][el_idx][1][5:7]),int(meta_request['meta'][0]['valid_daterange'][el_idx][1][8:10]))
                if new_start < start:
                    start = new_start
                    idx_s = el_idx
                if new_end > end:
                    end = new_end
                    idx_e = el_idx
            if s_date.lower() == 'por':
                s_yr = meta_request['meta'][0]['valid_daterange'][idx_s][0][0:4]
                s_mon = meta_request['meta'][0]['valid_daterange'][idx_s][0][5:7]
                s_day = meta_request['meta'][0]['valid_daterange'][idx_s][0][8:10]
                s_date = '%s%s%s' %(s_yr,s_mon,s_day)
            if e_date.lower() == 'por':
                e_yr = meta_request['meta'][0]['valid_daterange'][idx_e][1][0:4]
                e_mon = meta_request['meta'][0]['valid_daterange'][idx_e][1][5:7]
                e_day = meta_request['meta'][0]['valid_daterange'][idx_e][1][8:10]
                e_date = '%s%s%s' %(e_yr,e_mon,e_day)
        params['sdate']= s_date
        params['edate'] = e_date
        params['sids'] = form_input['station_id']
    elif 'station_ids' in form_input.keys():
        params['sids'] = form_input['station_ids']
        #NOTE: ACIS quirk when data request are multiple stations
                #If a station in the list has no data, nothing is returned instead of an empty list
                # We need to registed an aempty stn data return for this list:
                #check
                #if id is in input_stn_list, if so, delete from that list
                #any stn that is left over in input_stn_list after we run through all request data
                #had no data returned
        #input_stn_list = form_input['station_ids']
        stn_list_in = form_input['station_ids']
    elif 'county' in form_input.keys():
        params['county'] = form_input['county']
    elif 'climate_division' in form_input.keys():
        params['climdiv'] = form_input['climate_division']
    elif 'county_warning_area' in form_input.keys():
        params['cwa'] = form_input['county_warning_area']
    elif 'basin' in form_input.keys():
        params['basin'] = form_input['basin']
    elif 'state' in form_input.keys():
        params['state'] = form_input['state']
    elif 'bounding_box' in form_input.keys():
        params['bbox'] = form_input['bounding_box']
    else:
        params['sids'] =''

    #Data request
    try:
        request = MultiStnData(params)
    except Exception, e:
        resultsdict['error'] = 'StnData request failed. Error: %s. Pameters: %s.' %(str(e), params)
        for key in ['stn_data', 'dates', 'stn_ids', 'stn_names', 'stn_errors', 'elements']:
            resultsdict[key] = []
        return resultsdict
    try:
        request['data']
        if not request['data']:
            resultsdict['error'] = 'No data Found! Pameters: %s.' %(params)
            for key in ['stn_data', 'dates', 'stn_ids', 'stn_names', 'stn_errors', 'elements']:
                resultsdict[key] = []
            return resultsdict
    except Exception, e:
        resultsdict['error'] = 'No data found! Error: %s. Pameters: %s.' %(str(e), params)
        for key in ['stn_data', 'dates', 'stn_ids', 'stn_names', 'stn_errors', 'elements']:
            resultsdict[key] = []
        return resultsdict
    #Initialize outpout lists
    if s_date is not None and e_date is not None:
        dates = WRCCUtils.get_dates(s_date, e_date, program)
    else:
        dates = []
    resultsdict['dates'] = dates
    resultsdict['elements'] = elements
    resultsdict['stn_errors'] = ['' for stn in request['data']]
    resultsdict['stn_names'] = ['' for stn in request['data']]
    resultsdict['stn_ids'] = [[] for stn in request['data']]
    resultsdict['stn_data'] = [[] for stn in request['data']]
    idx_empty_list = []
    for stn, data in enumerate(request['data']):
        if not 'data' in data.keys():
            data['data'] = []
        if 'error' in data.keys():
            resultsdict['stn_errors'][stn] = str(data['error'])
        try:
            resultsdict['stn_ids'][stn] = []
            stn_id_list = data['meta']['sids']
            for sid in stn_id_list:
                stn_id = str(sid.split(' ')[0])
                #Case: comma list of stations: if id is in input_stn_list, if so, delete from that list
                #any stn that is left over in input_stn_list after we run through all request data
                #had no data returned
                if 'station_ids' in form_input.keys():
                    if stn_id in stn_list_in:
                        idx = stn_list_in.index(stn_id)
                        #Omit duplicates
                        if not idx in idx_empty_list:
                            idx_empty_list.append(idx)
                network_id_name = WRCCData.NETWORK_CODES[str(sid.split(' ')[1])]
                ids = '%s %s' %(stn_id, network_id_name)
                #Put COOP upfront
                if network_id_name == "COOP":
                    resultsdict['stn_ids'][stn].insert(0, ids)
                else:
                    resultsdict['stn_ids'][stn].append(ids)
        except:
            resultsdict['stn_ids'][stn] = []
        try:
            resultsdict['stn_names'][stn] = str(data['meta']['name'])
        except:
            resultsdict['stn_names'][stn] = ''
        try:
            resultsdict['stn_data'][stn] = data['data']
        except:
            resultsdict['stn_data'][stn] = []

        if not resultsdict['stn_data'][stn]:
            resultsdict['stn_errors'][stn] = 'No data found!'
        #Add dates
        if dates and len(dates) == len(data['data']):
            for idx, date in  enumerate(dates):
                resultsdict['stn_data'][stn][idx].insert(0, date)

    #final check on station data if comma separated list of stations
    if 'station_ids' in form_input.keys():
        for idx in idx_empty_list:
            resultsdict['stn_ids'].insert(idx, [stn_list_in[idx] + ' '])
            resultsdict['stn_names'].insert(idx, '')
            resultsdict['stn_errors'].insert(idx, 'No data found!')
            resultsdict['stn_data'].insert(idx, [])
    return resultsdict

def get_grid_data(form_input, program):
    '''
    Retrieves Grid Data from ACIS.
    Keyword arguments:
    form_input -- parameter file for data request obtained from user of CSC pages
    program -- specifies program that is making the request.

    Returned is a resultsdictionary from ACIS with entries:
    'lats'   -- lists of latitudes for grid points
    'lons'   -- lists of longitudes for grid points
    'data'   -- lists of grid data for each lat, lon
    '''
    #datalist[date_idx] = [[date1,lat1, lon1, elev1, el1_val1, el2_val1, ...],
    #[date2, lat2, ...], ...]
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    #grid data calls do not except list of elements, need to be string of comma separated values
    el_list = WRCCUtils.get_element_list(form_input, program)
    if 'data_summary' in form_input.keys() and form_input['data_summary'] != 'none':
        elements = [{'name':str(el),'smry':str(form_input['data_summary']),'smry_only':1} for el in el_list]
    else:
        elements = ','.join(el_list)
    params = {'sdate': s_date, 'edate': e_date, 'grid': form_input['grid'], 'elems': elements, 'meta': 'll,elev'}
    if 'location' in form_input.keys():params['loc'] = form_input['location']
    if 'state' in form_input.keys():params['state'] = form_input['state']
    if 'bounding_box' in form_input.keys():params['bbox'] = form_input['bounding_box']
    request = {}
    try:
        request = GridData(params)
    except Exception, e:
        request['error'] = 'GridData request failed. Error: %s. Pameters: %s.' %(str(e), params)
    if not request:
        request = {'error':'GridData request did not return results. Please check your parameters: %s'  % str(params)}
    return request

#######################################
#APPLICATION modules
#######################################
def get_station_list(by_type, val):
    '''
    Finds all station ids that belong to a specific region

    Keyword arguments:
    by_type -- station selection argument.
               station selection is one of: county, climate_division,
               county_warning_area, basin, bounding_box, state or states
    val     -- Value of station selection argument, e.g, AL if by_type = state
    '''
    stn_list = []
    if by_type == 'county':
        params = dict(county=val)
    elif by_type == 'climate_division':
        params = dict(climdiv=val)
    elif by_type == 'county_warning_area':
        params = dict(cwa=val)
    elif by_type == 'basin':
        params = dict(basin=val)
    elif by_type == 'state':
        params = dict(state=val)
    elif by_type == 'bounding_box':
        params = dict(bbox=val)
    elif type == 'id':
        params = dict(sids=val)
    else:
        pass
    request=StnMeta(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

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

def get_us_meta():
    '''
    Retrieve meta data for all US states.
    '''
    states = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME'\
    ,'MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC'\
    ,'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
    params = {"state":["%s" % state for state in states]}
    request = StnMeta(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    return request

def get_sod_data(form_input, program):
    '''
    Data acquisition for Soddyrec, Soddynorm, Soddd, Sodpad, Sodsumm

    Keyword arguments:
    form_input -- parameter file for data request obtained from user of WRCC SOD pages
    program -- specifies program that is making the request.
    '''

    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    '''
    if program in ['Sodpiii']:
        #get an extra year of data previos and after s_date, e_date
        s_date = str(int(s_date[0:4]) - 1) + s_date[4:]
        e_date = str(int(e_date[0:4]) + 1) + e_date[4:]
    '''
    dates = WRCCUtils.get_dates(s_date, e_date, program)
    elements = WRCCUtils.get_element_list(form_input, program)
    els = [dict(name='%s' % el) for el in elements]
    if 'coop_station_id' in form_input.keys():
        coop_station_ids =[form_input['coop_station_id']]
    elif 'coop_station_ids' in form_input.keys():
        coop_station_ids = form_input['coop_station_ids']
    elif 'county' in form_input.keys():
        coop_station_ids = get_station_list('county', form_input['county'])
    elif 'climate_division' in form_input.keys():
        coop_station_ids = get_station_list('climate_division', form_input['climate_division'])
    elif 'county_warning_area' in form_input.keys():
        coop_station_ids = get_station_list('county_warning_area', form_input['county_warning_area'])
    elif 'basin' in form_input.keys():
        coop_station_ids = get_station_list('basin', form_input['basin'])
    elif 'state' in form_input.keys():
        coop_station_ids = get_station_list('state', form_input['state'])
    elif 'bounding_box' in form_input.keys():
        coop_station_ids = get_station_list('bounding_box', form_input['bounding_box'])
    else:
        coop_station_ids =[]
    #sort station id in ascending order
    coop_station_ids = WRCCUtils.strip_n_sort(coop_station_ids)
    station_names=['No Name found' for i in range(len(coop_station_ids))]
    #Since Acis may not return results for some stations, we need to initialize output dictionary
    datadict = defaultdict(list)
    for i, stn in enumerate(coop_station_ids):
        if program == 'Soddyrec':
            yr_list = [[['#', '#', '#', '#', '#', '#','#', '#'] for k in range(366)] for el in elements]
            datadict[i] = yr_list
        elif program in ['Sodrun', 'Sodrunr']:
            datadict[i] = []
        else:
            datadict[i] = [[] for el in elements]

    if program == 'Soddyrec':
        smry_opts = [{'reduce':'mean', 'add':'date,mcnt'}, {'reduce':'max', 'add':'date,mcnt'}, {'reduce':'min', 'add':'date,mcnt'}]
        elts = []
        for el in elements:
            for sry in smry_opts:
                elts.append(dict(name=str(el),smry=sry, groupby='year'))

        '''
        if len(elements) >1 and 'mint'in elements:
            mint_indx = elements.index('mint')
            elements.remove('mint')
            elts = [dict(name='%s' % el, interval='dly', duration='dly', smry=smry_opts\
            , groupby="year") for el in elements]
            elts.insert(mint_indx,dict(name='mint', interval='dly', duration='dly', \
            smry={'reduce':'min', 'add':'date,mcnt'}, groupby="year"))
            elements.insert(mint_indx, 'mint')
        elif len(elements) == 1 and elements[0] == 'mint':
            elts = [dict(name='mint', interval='dly', duration='dly',\
            smry={'reduce':'min', 'add':'date,mcnt'}, groupby="year")]
        else:
            elts = [dict(name='%s' % el, interval='dly', duration='dly', smry=smry_opts, \
            groupby="year") for el in elements]
        '''
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=elts)
    elif program in ['Soddynorm', 'Soddd', 'Sodpad', 'Sodsumm', 'Sodpct', 'Sodthr', 'Sodxtrmts', 'Sodpiii']:
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el,interval='dly',duration='dly',groupby='year')for el in elements])
    elif program in ['Sodlist', 'Sodcnv']:
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el,add='t')for el in elements])
    else:
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el)for el in elements])
    request = MultiStnData(params)
    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    try:
        request['data']#list of data for the stations
    except:
        if request['error']:
            print '%s' % str(request['error'])
            return datadict, dates, elements, coop_station_ids, station_names
            #sys.exit(1)
        else:
            'Unknown error ocurred when getting data'
            #sys.exit(1)
            return datadict, dates, elements, coop_station_ids, station_names

    for stn, stn_data in enumerate(request['data']):
        try:
            stn_data['meta']
            #find station_id, Note: MultiStnData call may not return the stations in order
            sids = stn_data['meta']['sids']
            for sid in sids:
                sid_split = sid.split(' ')
                if sid_split[1] == '2':
                    #station_id = str(stn_data['meta']['sids'][1].split()[0])
                    station_id = str(sid_split[0])
                    try:
                        index = coop_station_ids.index(str(station_id))
                        break
                    except:
                        continue
            index = coop_station_ids.index(str(station_id))
            try:
                index = coop_station_ids.index(str(station_id))
                station_names[index] = str(stn_data['meta']['name'])
                if program == 'Soddyrec':
                    try:
                        stn_data['smry']
                        datadict[index] = stn_data['smry']
                    except:
                        datadict[index] = []
                #sort data by element
                elif program in ['Soddynorm', 'Soddd', 'Sodpct']:
                    try:
                        stn_data['data']
                        for yr, el_data in enumerate(stn_data['data']):
                            for el_idx, dat in enumerate(el_data):
                                datadict[index][el_idx].append(dat)
                    except:
                        pass
                else:
                    try:
                        stn_data['data']
                        datadict[index] = stn_data['data']
                    except:
                        datadict[index] = []

            except ValueError:
                continue

        except:
            pass
    '''
    if program == 'Soddyrec':
        #need to get averages separately; add: date, mcnt fails if we ask for mean, max together
        elts_x = [dict(name='%s' % el, interval='dly', duration='dly', smry={'reduce':'mean'}, \
        groupby="year") for el in elements]
        params_x = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=elts_x)
        request_x = MultiStnData(params_x)
        if not request_x:
            request_x = {'error':'bad request, check params: %s'  % str(params_x)}

        try:
            request_x['data']#list of data for the stations
            #order results by stn id

            for stn, stn_data in enumerate(request_x['data']):
                sids = stn_data['meta']['sids']
                station_id = ' '
                for sid in sids:
                    sid_split = sid.split(' ')
                    if sid_split[1] == '2':
                        #station_id = str(stn_data['meta']['sids'][1].split()[0])
                        station_id = str(sid_split[0])
                        break
                if station_id == ' ':
                    continue

                try:
                    indx_x = coop_station_ids.index(station_id)
                    try:
                        for el_id, ave_list in enumerate(stn_data['smry']):
                            for date_id,ave in enumerate(ave_list):
                                datadict[indx_x][el_id][date_id].insert(0,ave)
                                #figure out the number of years that are in the record
                                val_list = [stn_data['data'][yr][el_id][date_id] for yr in range(len(stn_data['data']))]
                                yrs_in_record = len(filter(lambda a: a != 'M', val_list))
                                datadict[indx_x][el_id][date_id].append(yrs_in_record)
                    except:
                        pass
                except ValueError:
                    continue
        except:
            if 'error' in request_x.keys():
                print '%s' % str(request_x['error'])
                sys.exit(1)
            else:
                'Unknown error ocurred when getting data'
                sys.exit(1)
        '''
    return datadict, dates, elements, coop_station_ids, station_names


def get_sodsum_data(form_input):
    '''
    Data acquisition for sodsum

    Keyword arguments:
    form_input -- parameter file for data request obtained from user of WRCC SOD pages
    '''
    if 'element' not in form_input.keys() or 'coop_station_ids' not in form_input.keys():
        print 'element and coop_station_id options required!'
        sys.exit(0)
    if not form_input['element'] or not form_input['coop_station_ids']:
        print 'element and coop_station_id options required!'
        sys.exit(0)
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
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

        if not request:
            request = {'error':'bad request, check params: %s'  % str(params)}

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


def get_sodlist_data(form_input, program):
    '''
    Data acquisition for sodlist,sodmonline(my), sodcnv

    Keyword arguments:
    form_input -- parameter file for data request obtained from user of WRCC SOD pages
    program -- specifies program that is making the request.
    '''
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
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
        print 'Program %s not supported in get_sodlist_data. Program should be one out of [sodlist, sodcnv, sodmonline, sodmonlinemy]!' % program
        sys.exit(0)

    #Request evap, wind and water equivalent data
    #NOTE: these data need to be obtained via var major:
    if program == 'sodlist' and 'include_tobs_evap' in form_input.keys():
        request_evap = StnData(params_e)

        if not request_evap:
            request_evap = {'error':'bad request, check params: %s'  % str(params_e)}

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

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

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
