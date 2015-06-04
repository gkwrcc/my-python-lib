#!/usr/bin/python

'''
Module WRCCUtils
'''

import datetime, calendar, time, sys, os
import re
import json
import numpy as np
import scipy
import math
import re
from collections import defaultdict, Mapping, Iterable
import smtplib
from email.mime.text import MIMEText
from ftplib import FTP
from math import sqrt
import colorsys


import WRCCClasses, AcisWS, WRCCData

#########
#STATICS
########
thismodule =  sys.modules[__name__]

area_keys = ['station_id','station_ids','location','locations','state',\
'bounding_box','county','county_warning_area','basin','climate_division','shape']
special_station_areas = ['shape']
special_grid_areas = ['county', 'county_warning_area','basin','climate_division','shape']
station_reduction_areas = ['county', 'county_warning_area','basin',\
'climate_division','state','bounding_box']
grid_reduction_areas = ['state','bounding_box']
####################################
#FUNCTIONS
#####################################
####################################
#CLEANED FUNCTIONS
#####################################
###################################
#DATA  LSITER MODULES
###################################
def get_data_type(form):
    '''
    Sets data type as station or grid
    or stations or grids (if multi request)
    according to form
    Note that if data_type is in form, we
    have either a multi request(station_ids/locations)
    or an area request (cwa, county, climdiv,basin,shape)
    Args:
        form -- user form input dictionary
    Returns:
        data_type -- station or grid
    '''
    data_type = None
    if 'station_id' in form.keys() or 'station_ids' in form.keys():
        return 'station'
    elif 'location' in form.keys() or 'locations' in form.keys():
        return 'grid'
    else:
        if 'data_type' in form.keys():
            return str(form['data_type'])
    return data_type

def get_meta_keys(form):
    '''
    Sets meta params for ACIS query
    Args:
        from -- user form input dictionary
    Return:
        meta_keys -- list of metadata keys
    '''
    #Set meta keys according to data_type
    if 'data_type' in form.keys():
        if form['data_type'] == 'station':
            meta_keys = ['name', 'state', 'sids', 'elev', 'll', 'valid_daterange']
        else:
            meta_keys = ['ll','elev']
    else:
        if 'station_id' in form.keys() or 'station_ids' in form.keys():
            meta_keys = ['name', 'state', 'sids', 'elev', 'll', 'valid_daterange']
        else:
            meta_keys = ['ll','elev']
    return meta_keys

def convert_elements_to_list(elements):
    '''
    Args:
        elements -- list or string of climate elements
    Returns:
        el_list -- list of climate elements
    '''
    el_list = []
    if isinstance(elements, basestring):
        el_list = elements.replace(' ','').rstrip(',').split(',')
    elif isinstance(elements,list):
        el_list = [str(el) for el in elements]
    return el_list

def convert_elements_to_string(elements):
    '''
    Args:
        elements -- list or string of climate elements
    Returns:
        el_str -- comma separated string of climate elements
    '''
    el_str = ''
    if isinstance(elements, basestring):
        el_str = elements
    elif isinstance(elements,list):
        el_str = ','.join([str(el).rstrip(' ') for el in elements])
    return el_str


def set_acis_meta(data_type):
    '''
    Sets all meta string for data request
    Args:
        data_type  -- grid or station
    Returns:
        meta string for ACIS data request
    '''
    if data_type == 'station':
        #Note climidc, county giv error for Samoa
        #return 'name,state,sids,ll,elev,uid,county,climdiv,valid_daterange'
        return 'name,state,sids,ll,elev,uid,valid_daterange'
    if data_type == 'grid':
        return 'll,elev'

def set_acis_els(form):
    '''
    Sets element list for ACIS data request
    Args:
        form -- user form input dictionary
    Returns:
        acis_elems -- list of elements for ACIS data request
    '''
    data_type = get_data_type(form)
    acis_elems = []
    for el in form['elements']:
        el_strip, base_temp = get_el_and_base_temp(el)

        if data_type == 'grid' and form['grid'] == '21':
            if 'temporal_resolution' in form.keys() and form['temporal_resolution'] in ['mly','yly']:
                #Special case prims data
                l = {
                    'name':form['temporal_resolution'] + '_' + el_strip
                }
            else:
                l ={
                    'vX':WRCCData.ACIS_ELEMENTS_DICT[el_strip]['vX']
                }
        else:
            l ={
                'vX':WRCCData.ACIS_ELEMENTS_DICT[el_strip]['vX']
            }
        #Get smry if data_summary is temporal
        if 'data_summary' in form.keys() and form['data_summary'] == 'temporal':
            #For performance: Summary only requests for multi area requests
            #Of station data
            #For single requests always get data, too
            #Note: GridData does not support  basin, shape,cws,climdiv or county
            #We need to get the data to compute data summaries
            if data_type == 'station' and form['area_type'] != 'shape':
                if form['area_type'] not in special_station_areas:
                    if form['temporal_summary'] not in ['median']:
                        l['smry'] = form['temporal_summary']
                if form['area_type'] in station_reduction_areas:
                    l['smry_only'] = 1
            if data_type == 'grid':
                if form['area_type'] not in special_grid_areas:
                    l['smry'] = form['temporal_summary']
                if form['area_type'] in grid_reduction_areas:
                    l['smry_only'] = 1
        if el_strip in ['gdd', 'hdd', 'cdd']:
            if base_temp is None and el_strip in ['hdd','cdd']:
                base_temp = '65'
                '''
                if form['units'] == 'metric':
                    base_temp = '18'
                '''
            if base_temp is None and el_strip in ['gdd']:
                base_temp = '50'
                '''
                if form['units'] == 'metric':
                    base_temp = '10'
                '''
            l['base'] = int(base_temp)
            '''
            #Convert to english, ACIS station queries not possible in metric
            if form['units'] == 'metric':
                l['base'] = convert_to_english('base_temp', base_temp)
            '''
        #Add obs time if data_type is station
        '''
        if data_type == 'station':
            if 'show_flags' in form.keys() and 'show_observation_time' in form.keys():
                if form['show_flags'] == 'T' and form['show_observation_time'] =='F':
                    l['add'] = 'f'
                if form['show_flags'] == 'F' and form['show_observation_time'] =='T':
                    l['add'] = 't'
                if form['show_flags'] == 'T' and form['show_observation_time'] =='T':
                    l['add']= 'f,t'
        '''
        #Add obs time if data_type is station
        #NOTE: flags are always showing in the data so we never query for them separately
        if data_type == 'station':
            if 'show_observation_time' in form.keys() and form['show_observation_time'] =='T':
                l['add'] = 't'

        acis_elems.append(l)
    return acis_elems



def set_acis_params(form):
    '''
    Sets ACIS parameters according to:
        area_type: station_id, location, county, state, etc.
        data_type: station or grid
        and request_type: single, multi or area
    Args:
        form -- user form input dictionary
    Returns:
        params -- parameters for ACIS data request
    '''
    #Find data_type variable
    data_type = get_data_type(form)
    if not data_type:
        return {}
    #Format dates
    s_date, e_date = start_end_date_to_eight(form)
    params = {
            'sdate':s_date,
            'edate':e_date
    }
    p_key = None
    f_key = None
    #Set up area parameter
    #Convert form area key to ACIS area key
    if 'station_ids' in form.keys():
        #Special case station finder download data
        p_key = WRCCData.FORM_TO_PARAMS['station_ids']
        f_key = 'station_ids'
        params[p_key] = str(form['station_ids'])
    else:
        for area_key in area_keys:
            if area_key not in form.keys():
                continue
            if area_key in form.keys():
                p_key = WRCCData.FORM_TO_PARAMS[area_key]
                f_key = area_key
                params[p_key] = str(form[area_key])
                break
    if not p_key:
        return {}
    #Override area parameter if necessary
    #Override with enclosing bbox if data_type == grid
    special_shape = False
    if data_type == 'grid' and f_key in special_grid_areas:
        special_shape = True
    if data_type == 'station' and f_key in special_station_areas:
        special_shape = True
    if special_shape:
        del params[p_key]
        #Need to run request on enclosing bbox
        if f_key == 'shape':
            shape_type,bbox = get_bbox(form['shape'])
            if shape_type == 'location':params['loc'] = form['shape']
            else:params['bbox'] = bbox
        else:
            bbox = AcisWS.get_acis_bbox_of_area(p_key,form[area_key])
        params['bbox'] = bbox
    #Set elements
    params['elems'] = set_acis_els(form)
    #Set meta according to data_type
    params['meta'] = set_acis_meta(data_type)
    #Set grid_params
    if data_type =='grid':
        params['grid'] = form['grid']
    return params


def compute_statistic(vals,statistic):
    '''
    Args:
        statistic -- max,min, mean, median or  sum
        vals  --  list of floats to be summarized
    Returns:
        statistic
    '''
    if vals == []:
        return None
    np_array = np.array(vals, dtype = np.float)
    #remove nan
    np_array = np_array[np.logical_not(np.isnan(np_array))]
    #np_array = np_array[np_array != -9999]
    if statistic == 'max':
        return round(np.nanmax(np_array),4)
    if statistic == 'min':
        return round(np.nanmin(np_array),4)
    if statistic == 'mean':
        return round(np.nanmean(np_array),4)
    if statistic == 'sum':
        return round(np.nansum(np_array),4)
    if statistic == 'median':
        #return round(np.median(np_array),4)
        return round(scipy.stats.nanmedian(np_array),4);
    if statistic == 'std':
        return round(np.nanstd(np_array),4)
    if statistic == 'skew':
        return round(scipy.stats.skew(np_array),4)

def request_and_format_data(form):
    '''
    ACIS data request and data formatting.
    NOTE: since GridData does not support special area requests (shape, basin, cwa...)
    We need to compute the data summaries directly from the data for these shapes
    Args:
        form -- user form input dictionary
    Returns:
        resultsdict -- dictionary of results with keys:
            errors: List of errors encountered during request call
                    is empty for successful requests
            meta: meta data list
            data: data list (empty for summary requests)
            smry: data summary list (empty for data requests)
            form
    '''
    resultsdict = {
        'errors':[],
        'meta':[],
        'data':[],
        'smry':[],
        'form':form
    }
    data_type = get_data_type(form)
    #Set request parameters
    params = set_acis_params(form)
    #Find correct data call functions
    if not data_type:
        error = 'Not a valid request. Could not find request type.'
        resultsdict['errors'].append( error)
        return resultsdict
    if data_type == 'station':
        if 'station_id' in form.keys():
            request_data = getattr(AcisWS,'StnData')
        else:
            request_data = getattr(AcisWS,'MultiStnData')
    if data_type == 'grid':
        request_data = getattr(AcisWS,'GridData')
    #Make data request
    req = request_data(params)
    '''
    try:
        req = request_data(params)
    except Exception, e:
        error = 'Data request failed with error: %s.' %str(e)
        resultsdict['errors'].append( error)
        return resultsdict
    '''
    #Sanity check
    if not 'data' in req.keys() and not 'smry' in req.keys():
        error = 'No data found for these parameters.'
        resultsdict['errors'].append( error)
        return resultsdict
    #Format results
    #Grid data
    if data_type == 'grid':
        if form['area_type'] == 'location':
            #Single point request
            resultsdict = format_data_single_lister(req,form)
        elif form['area_type'] in special_grid_areas:
            #Irregular shape, data needs trimming
            resultsdict = grid_data_trim_and_summary(req,form)
        else:
            if form['data_summary'] == 'none':
                resultsdict = format_grid_no_summary(req,form)
            if form['data_summary'] == 'temporal':
                resultsdict = format_grid_temporal_summary(req,form)
            if form['data_summary'] == 'spatial':
                resultsdict = format_grid_spatial_summary(req,form)
            if form['data_summary'] == 'windowed_data':
                resultsdict = format_grid_windowed_data(req,form)
    #Station data
    elif data_type == 'station':
        #Single point request
        if form['area_type'] == 'station_id':
            resultsdict = format_data_single_lister(req,form)
        elif form['area_type'] in special_station_areas:
            #Irregular shape, data needs trimming
            resultsdict = station_data_trim_and_summary(req,form)
        else:
            if form['data_summary'] == 'none':
                resultsdict = format_station_no_summary(req,form)
            if form['data_summary'] == 'temporal':
                resultsdict = format_station_temporal_summary(req,form)
            if form['data_summary'] == 'spatial':
                resultsdict  = format_station_spatial_summary(req,form)
            if form['data_summary'] == 'windowed_data':
                resultsdict = format_station_windowed_data(req,form)
    return resultsdict


###################################
#DATA FORMATTING MODULES
###################################
def set_temporal_summary_header(form):
    header = [WRCCData.DISPLAY_PARAMS[form['area_type']],str(form[form['area_type']])]
    dates = get_dates(form['start_date'],form['end_date'])
    header+= ['Date Range',dates[0],dates[-1]]
    return header

def set_spatial_summary_header(form):
    header = [WRCCData.DISPLAY_PARAMS[form['area_type']],str(form[form['area_type']])]
    return header


def set_lister_headers(form):
    '''
    Sets data headers for html display and writing to file.
    Args:
        form -- user form input dictionary
    Returns:
        header_data -- header for the raw data
        header_summary -- header for the data summary
    '''
    data_type = get_data_type(form)
    el_list = form['elements']
    if isinstance(form['elements'], basestring):
        el_list = form['elements'].replace(' ','').split(',')
    header_data = ['Date']
    header_summary =[]
    if form['data_summary'] == 'temporal':
        if data_type == 'grid':
            header_smry=['Location(Lon,Lat)']
        if data_type == 'station':
            header_smry=['Station (IDs)']
    else:
        header_smry = ['Date']
    for el in el_list:
        el_strip,base_temp = get_el_and_base_temp(el)
        if base_temp:
            base_temp = str(base_temp)
        unit = WRCCData.UNITS_ENGLISH[el_strip]
        if form['units'] == 'metric':
            if el_strip not in ['gdd','hdd','cdd']:
                unit = WRCCData.UNITS_METRIC[el_strip]
            '''
            if base_temp:
                base_temp = str(convert_to_metric('base_temp',base_temp))
            '''
        el_name = WRCCData.MICHELES_ELEMENT_NAMES[el_strip]
        h = el_name
        #Add base temp and units
        if base_temp:h+=str(base_temp)
        if unit !='':
            h+=' (' + unit + ')'
        header_data+=[h]
        header_smry+=[h]
        '''
        if data_type == 'station' and 'show_flags' in form.keys():
            if form['show_flags'] == 'T':
                header_data+=['F']
        '''
        if data_type == 'station' and 'show_observation_time' in form.keys():
            if form['show_observation_time'] == 'T':
                header_data+=['hr']
    return header_data,header_smry


###############################
#Data formatters
##################################
def format_data_single_lister(req,form):
    '''
    Formats single point (station or lon,lat) data requests
    for html display or writing to file. Also takes care
    of unicode conversion to strings
    Args:
        req -- results of a make_data_request callfor single point
        form -- user form input dictionary
    Returns: dictionary with keys
        data -- [[[date1 stn1_data],[date2 stn1_data]...], [[date1 stn2_data], ...]}
        smry --
            format depends on summary:
                spatial summary: [[date1,el1smry,el2smry,...], [date2...]]
                temporal summary: [['stn_name1 (stn_ids)', el1smry,el2smry,...],['stn_name1 (stn_ids)',...]]
        meta -- [{point1_meta},{poin2_meta}]
        form -- user form input dictionary
    '''
    new_data = [];new_smry = [];new_meta = req['meta']
    els = form['elements']
    if not req['data'] and not req['smry']:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    #headers
    header_data, header_smry = set_lister_headers(form)
    d_data = [header_data]
    if 'station_id' in form.keys():
        if 'user_area_id' in form.keys():
            name = form['user_area_id']
        else:
            name = str(req['meta']['name'])
            ids = ','.join([sid.split(' ')[0] for sid in req['meta']['sids']])
            ids = ' (' + ids + ')'
            name+=ids
    if 'location' in form.keys():
        name=str(req['meta']['lon']) + ',' + str(req['meta']['lat'])
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    #Data Loop
    #Keep track of missing data
    flag_missing = True
    for date_idx,data in enumerate(req['data']):
        date = [format_date(str(data[0]),sep)]
        data = data[1:]
        #Note: format is different if flags/obs are asked for
        #Deal with non-flag/obs time requests first --> easy
        date_data = []
        smry_data = []
        for el_idx, el_data in enumerate(data):
            #Format Summary
            if 'smry' in req.keys() and req['smry']:
                try:
                    val = round(unit_convert(els[el_idx],float(req['smry'][el_idx])),4)
                except:
                    val = str(req['smry'][el_idx])
                smry_data.append(val)
            #Format data, note that if obs time is asked for el_data is a list
            obs_time = None
            if isinstance(el_data,list):
                val = el_data[0]
                if len(el_data) >1:obs_time = el_data[1]
            else:
                val = el_data

            #strip flag from data
            strp_val, flag = strip_data(val)
            try:
                val = round(unit_convert(els[el_idx],float(strp_val)),4)
            except:
                val = strp_val
            if 'show_flags' in form.keys() and form['show_flags'] == 'T':
                val = show_flag_on_val(val, flag)
            else:
                val = remove_flag_from_val(val, flag)
            date_data.append(val)
            #Attach Obs time
            if obs_time:
                date_data.append(obs_time)
        #check if all data is missing
        if all(v==-9999  for v in date_data) and flag_missing:
            pass
        else:
            #Record first data value and set flag_missing to false
            d_data.append(date + date_data)
            flag_missing = False

        new_data = d_data
        if smry_data:
            smry_data.insert(0,name)
            new_smry = [header_smry,smry_data]
    resultsdict = {
        'data':[new_data],
        'smry':new_smry,
        'meta':[new_meta],
        'form':form
    }
    return resultsdict

def station_data_trim_and_summary(req,form):
    '''
    Trims and summarizes station data for printing/writing to file
    Some special shapes are not supported by ACIS
    E.G. Cumstom polygons for station data requests.
    Data is obtained for the enclosing bbox of the special shape.
    This function trims down the data of such a station
    request to the size of the custom shape.

    Args:
        req: ACIS data request dictionary
        form: user form input dictionary
    Returns: dictionary with keys
        data -- for printing/writing to file
              format: [[date1 stn1data],[date2 stn1data]...], [[date1 stn2data], ...]
        smry --
            format depends on summary:
                spatial summary: [[date1,el1smry,el2smry,...], [date2...]]
                temporal summary: [['stn_name1 (stn_ids)', el1smry,el2smry,...],['stn_name1 (stn_ids)',...]]
        meta -- [{stn1_meta},{stm2_meta}]
        form -- user form input dictionary
    '''
    try:
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    header_data, header_smry = set_lister_headers(form)
    #MultiStnData calls return no dates
    dates = get_dates(form['start_date'],form['end_date'])
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    if form['data_summary'] == 'spatial':
        new_smry = [[format_date(dates[d_idx],sep)] for d_idx in range(len(dates))]
        smry_data = [[[] for el in form['elements']] for date_idx in range(len(dates))]
    elif form['data_summary'] == 'temporal':
        new_smry =[]
        smry_data = [[] for el in els]
    else:
        new_smry = []
    #find the polygon of the special shape
    #and the function to test if a point lies within the shape
    poly, PointIn = set_poly_and_PointIn(form)
    new_data = [];new_meta = []
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Station loop over data
    for stn_idx, stn_data in enumerate(req['data']):
        try:
            lon = stn_data['meta']['ll'][0]
            lat = stn_data['meta']['ll'][1]
        except:
            continue
        point_in = PointIn(lon, lat, poly)
        if not point_in:
            continue
        #point is in shape, add to data and compute summary
        new_meta.append(stn_data['meta'])
        stn_name = str(stn_data['meta']['name'])
        new_data.append([])
        for date_idx, date_data in enumerate(stn_data['data']):
            d_data = [format_date(dates[date_idx],sep)]
            for el_idx, el_data in enumerate(date_data):
                #If user asked for flags/obstime
                #data el_data is a list and we need to pick the correct value
                obs_time = None
                if isinstance(el_data, list):
                    val = el_data[0]
                    if len(el_data) >1:
                        obs_time = el_data[1]
                else:
                    val = el_data
                #Strip flag from data
                strp_val, flag = strip_data(val)
                try:
                    val = round(unit_convert(els[el_idx],float(strp_val)),4)
                    #Don't include -9999 (Missing) values
                    if str(strp_val) != '-9999':
                        if form['data_summary'] == 'spatial':
                            smry_data[date_idx][el_idx].append(val)
                        if form['data_summary'] == 'temporal':
                            smry_data[el_idx].append(val)
                except:
                    val = strp_val
                if 'show_flags' in form.keys() and form['show_flags'] == 'T':
                    val = show_flag_on_val(val, flag)
                else:
                    val = remove_flag_from_val(val, flag)

                d_data.append(val)
                #Append obs time
                if obs_time:
                    d_data.append(str(obs_time))
            new_data[-1].append(d_data)
        #Wndowed Data
        if form['data_summary'] == 'windowed_data':
            sd = form['start_date']
            ed = form['end_date']
            sw = form['start_window']
            ew = form['end_window']
            new_data[-1] = get_windowed_data(new_data[-1], sd, ed, sw, ew)
        new_data[-1].insert(0,header_data)
        #Temporal summary
        if form['data_summary'] == 'temporal':
            try:
                stn_ids = ','.join([sid.split(' ')[0] for sid in stn_data['meta']['sids']])
                stn_ids = ' (' + stn_ids + ')'
            except:
                stn_ids = ' ()'
            row = [stn_name + stn_ids]
            if point_in:
                for el_idx, el in enumerate(els):
                    row.append(compute_statistic(smry_data[el_idx],form['temporal_summary']))
                new_smry.append(row)
    #Compute spatial summary
    if form['data_summary'] == 'spatial':
        for date_idx in range(len(dates)):
            for el_idx in range(len(els)):
                new_smry[date_idx].append(compute_statistic(smry_data[date_idx][el_idx],form['spatial_summary']))
    #Insert summary header
    if new_smry:
        new_smry.insert(0,header_smry)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def grid_data_trim_and_summary(req,form):
    '''
    Trims and summarizes grid data for printing/writing to file
    Some special shapes are not supported by ACIS
    E.G. Cumstom polygons or basin,cwa,climdiv,county for grid requests
    req is data opbtained for the enclosing bbox of the special shape.
    This function trims down the data of such a grid
    request to the size of the custom shape.

    Args:
        req -- ACIS data request dictionary
        form --  user form input dictionary
    Returns:
        dictionary with keys:
        data -- format: [[[date1 p1_data],[date2 p1_data]...], [[date1 p2_data], ...]
        smry --
            format depends on summary:
                spatial summary: [[date1,el1smry,el2smry,...], [date2...]]
                temporal summary: [['lon1,lat1', el1smry,el2smry,...],['lon2,lat2',...]]
        meta -- [{'lat':lat1,lon:'lon1','elev':elev1}, {'lat':lat2,lon:'lon2','elev':elev2},...]
        form -- user form input dictionary
    '''
    try:
        lats = req['meta']['lat']
        lons = req['meta']['lon']
        elevs = req['meta']['elev']
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    header_data, header_smry = set_lister_headers(form)
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    if form['data_summary'] == 'spatial':
        new_smry = [[format_date(str(data[date_idx][0]),sep)] for date_idx in range(len(data))]
        smry_data = [[[] for el in els] for date_idx in range(len(data))]
    elif form['data_summary'] == 'temporal':
        smry_data = [[] for el in els]
        new_smry = []
    else:
        new_smry = []
    new_data = [];new_meta = []
    #find the polygon of the special shape
    #and the function to test if a point lies within the shape
    poly, PointIn = set_poly_and_PointIn(form)
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #lat,lon loop over data
    generator_lat =  ((grid_idx, lat_grid) for grid_idx, lat_grid in enumerate(lats))
    for (grid_idx, lat_grid) in generator_lat:
        generator_lon = ((lon_idx, lon) for lon_idx, lon in enumerate(lons[grid_idx]))
        lat = lat_grid[0]
        new_lons = []
        new_elevs = []
        for (lon_idx, lon) in generator_lon:
            #lon_data = [[[] for el in els] for d in range(len(data))]
            point_in = PointIn(lon, lat, poly)
            if not point_in:
                continue
            #points is in shape, add tp data and compute summary
            meta_dict = {'lon':lon,'lat':lat,'elev':unit_convert('elev',req['meta']['elev'][grid_idx][lon_idx])}
            new_meta.append(meta_dict)
            new_lons.append(lon)
            new_elevs.append(elevs[grid_idx][lon_idx])
            new_data.append([])
            for date_idx, date_data in enumerate(data):
                d_data = [format_date(date_data[0],sep)]
                for el_idx,el in enumerate(els):
                    try:
                        d = unit_convert(el, float(date_data[el_idx+1][grid_idx][lon_idx]))
                        d_data.append(round(d,4))
                        if form['data_summary'] == 'spatial':
                            smry_data[date_idx][el_idx].append(d)
                        if form['data_summary'] == 'temporal':
                            smry_data[el_idx].append(d)
                    except:
                        d_data.append(date_data[el_idx+1][grid_idx][lon_idx])
                new_data[-1].append(d_data)
            #Wndowed Data
            if form['data_summary'] == 'windowed_data':
                sd = form['start_date']
                ed = form['end_date']
                sw = form['start_window']
                ew = form['end_window']
                new_data[-1] = get_windowed_data(new_data[-1], sd, ed, sw, ew)
            new_data[-1].insert(0,header_data)

            #Temporal summary
            if form['data_summary'] == 'temporal':
                row = [str(round(lon,4)) + ',' + str(round(lat,4))]
                if point_in:
                    for el_idx, el in enumerate(els):
                        row.append(compute_statistic(smry_data[el_idx],form['temporal_summary']))
                new_smry.append(row)

    #Compute spatial summary
    if form['data_summary'] == 'spatial':
        for date_idx in range(len(data)):
            for el_idx in range(len(form['elements'])):
                new_smry[date_idx].append(compute_statistic(smry_data[date_idx][el_idx],form['spatial_summary']))
    #Insert summary header
    if new_smry:
        new_smry.insert(0,header_smry)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_grid_spatial_summary(req,form):
    '''
    Formats spatial summary grid data request for printing or writing to file.
    Args:
        req -- ACIS data request dictionary
        form -- user form input dictionary
    Returns:
        new_data -- []
        smry -- [[date1,el1smry,el2smry,...], [date2...]]
        new_meta -- [{'lat':lat1,lon:'lon1','elev':elev1}, {'lat':lat2,lon:'lon2','elev':elev2},...]

    '''
    try:
        lats = req['meta']['lat']
        lons = req['meta']['lon']
        elevs = req['meta']['elev']
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    header_data, header_smry = set_lister_headers(form)
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    new_smry = [[format_date(str(data[date_idx][0]),sep)] for date_idx in range(len(data))]
    smry_data = [[[] for el in form['elements']] for date_idx in range(len(data))]
    new_data = [];new_meta = []
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #lat,lon loop over data
    generator_lat =  ((grid_idx, lat_grid) for grid_idx, lat_grid in enumerate(lats))
    for (grid_idx, lat_grid) in generator_lat:
        generator_lon = ((lon_idx, lon) for lon_idx, lon in enumerate(lons[grid_idx]))
        lat = lat_grid[0]
        for (lon_idx, lon) in generator_lon:
            meta_dict = {'lon':lon,'lat':lat,'elev':unit_convert('elev',req['meta']['elev'][grid_idx][lon_idx])}
            new_meta.append(meta_dict)
            for date_idx,date_data in enumerate(data):
                for el_idx,el in enumerate(els):
                    try:
                        val = unit_convert(el,float(date_data[el_idx+1][grid_idx][lon_idx]))
                        smry_data[date_idx][el_idx].append(float(val))
                    except:
                        pass
                    #Compute spatial summary at last gridpoint iteration
                    if grid_idx == len(lats) -1 and lon_idx == len(lons[grid_idx]) -1:
                        s = smry_data[date_idx][el_idx]
                        new_smry[date_idx].append(compute_statistic(s,form['spatial_summary']))
    #Insert summary header
    if new_smry:
        new_smry.insert(0,header_smry)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_grid_no_summary(req,form):
    '''
    Formats raw grid data request for printing or writing to file.
    Args:
        req -- ACIS data request dictionary
        form -- user form input dictionary
    Returns: dictionary with keys
        data -- [[[date1 data],[date2 data]...], ['lon2,lat2'],[date1 data], ...]
        smry -- []
        meta -- [{'lon':lon1,'lat':lat1,'elev':elev1},{'lon':lon1,'lat':lat1,'elev':elev1}...]
        form -- user form input dictionary
    '''
    #Sanity check
    try:
        lats = req['meta']['lat']
        lons = req['meta']['lon']
        elevs = req['meta']['elev']
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    #Set headers
    header_data, header_smry = set_lister_headers(form)
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    new_data = [];new_smry = [];new_meta = []
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Lat/lon loop
    generator_lat =  ((grid_idx, lat_grid) for grid_idx, lat_grid in enumerate(lats))
    for (grid_idx, lat_grid) in generator_lat:
        generator_lon = ((lon_idx, lon) for lon_idx, lon in enumerate(lons[grid_idx]))
        lat = lat_grid[0]
        for (lon_idx, lon) in generator_lon:
            meta_dict = {'lon':lon,'lat':lat,'elev':unit_convert('elev',req['meta']['elev'][grid_idx][lon_idx])}
            new_meta.append(meta_dict)
            new_data.append([header_data])
            for date_data in data:
                d_data = [format_date(str(date_data[0]),sep)]
                for el_idx,el in enumerate(els):
                    try:
                        val = unit_convert(el, float(date_data[el_idx+1][grid_idx][lon_idx]))
                        d_data.append(round(val,4))
                    except:
                        d_data.append(date_data[el_idx+1][grid_idx][lon_idx])
                new_data[-1].append(d_data)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_grid_windowed_data(req,form):
    '''
    Formats windowed grid data request for printing or writing to file.
    Args:
        req -- ACIS data request dictionary
        form -- user form input dictionary
    Returns:
        dictionary with keys
        data -- [[[date1 p1_data],[date2 p1_data]...], [[date1 [p2_data], ...]
        smry -- []
        meta -- [{'lon':lon1,'lat':lat1,'elev':elev1},{'lon':lon1,'lat':lat1,'elev':elev1}...]
        form -- user form input dictionary
    '''
    #Sanity check
    try:
        lats = req['meta']['lat']
        lons = req['meta']['lon']
        elevs = req['meta']['elev']
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    #Set headers
    header_data, header_smry = set_lister_headers(form)
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    new_data = [];new_smry = [];new_meta = []
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Lon/Lat Loop
    generator_lat =  ((grid_idx, lat_grid) for grid_idx, lat_grid in enumerate(lats))
    for (grid_idx, lat_grid) in generator_lat:
        generator_lon = ((lon_idx, lon) for lon_idx, lon in enumerate(lons[grid_idx]))
        lat = lat_grid[0]
        for (lon_idx, lon) in generator_lon:
            meta_dict = {'lon':lon,'lat':lat,'elev':unit_convert('elev',req['meta']['elev'][grid_idx][lon_idx])}
            new_meta.append(meta_dict)
            new_data.append([])
            for date_data in data:
                d_data = [format_date(str(date_data[0]),sep)]
                for el_idx,el in enumerate(els):
                    try:
                        val = unit_convert(el,float(date_data[el_idx+1][grid_idx][lon_idx]))
                        d_data.append(round(val,4))
                    except:
                        d_data.append(date_data[el_idx+1][grid_idx][lon_idx])
                new_data[-1].append(d_data)
            #get windowed data
            sd = form['start_date']
            ed = form['end_date']
            sw = form['start_window']
            ew = form['end_window']
            new_data[-1] = get_windowed_data(new_data[-1], sd, ed, sw, ew)
            new_data[-1].insert(0,header_data)

    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_grid_temporal_summary(req,form):
    '''
    Formats temporal summary grid data request for printing or writing to file.
    Args:
        req -- ACIS data request dictionary
        form -- user form input dictionary
    Returns:
        dictionary with keys
        data -- []
        smry -- [['lon1,lat1', el1smry,el2smry,...],['lon2,lat2',...]]
        meta -- [{'lat':lat1,lon:'lon1','elev':elev1}, {'lat':lat2,lon:'lon2','elev':elev2},...]
        form -- user form input dictionary
    '''
    try:
        lats = req['meta']['lat']
        lons = req['meta']['lon']
        elevs = req['meta']['elev']
        data = req['smry']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    header_data, header_smry = set_lister_headers(form)
    new_smry = []
    new_data=[];new_meta = []
    smry_data = [[] for el in form['elements']]
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #lat,lon loop over data
    generator_lat =  ((grid_idx, lat_grid) for grid_idx, lat_grid in enumerate(lats))
    for (grid_idx, lat_grid) in generator_lat:
        generator_lon = ((lon_idx, lon) for lon_idx, lon in enumerate(lons[grid_idx]))
        lat = lat_grid[0]
        for (lon_idx, lon) in generator_lon:
            meta_dict = {'lon':lon,'lat':lat,'elev':unit_convert('elev',req['meta']['elev'][grid_idx][lon_idx])}
            new_meta.append(meta_dict)
            for date_data in data:
                for el_idx,el in enumerate(els):
                    try:
                        val = unit_convert(el,float(date_data[el_idx+1][grid_idx][lon_idx]))
                        smry_data[el_idx].append(float(val))
                    except:
                        pass
                new_data[-1].append(d_data)
            #Temporal summary
            row = [str(lon) + ',' + str(lat)]
            for el_idx, el in enumerate(els):
                row.append(compute_statistic(smry_data[el_idx],form['temporal_summary']))
            new_smry.append(row)
    if new_smry:
        new_smry.insert(0,header_smry)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_station_spatial_summary(req,form):
    '''
    Formats spatial summary station data request for printing or writing to file.
    Args:
        req: ACIS data request dictionary
        form: user form input dictionary
    Returns:
        data -- []
        smry -- [[date1,el1smry,el2smry,...], [date2...]]
        meta -- [{stn1_meta},{stn2_meta}, ...]
        form -- user form input dictionary
    '''
    try:
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],'meta':[],'form':form,'errors':error}
    #Headers
    header_data, header_smry = set_lister_headers(form)
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    dates = get_dates(form['start_date'],form['end_date'])
    #Sanity check on dates
    if len(dates) != len(data[0]['data']):
        error = 'Dates mismatch.'
        return {'data':[],'smry':[],'meta':[],'form':form,'errors':error}
    new_data = [];new_meta = []
    smry_data = [[[] for el in form['elements']] for date_idx in range(len(dates))]
    new_smry = [[format_date(str(dates[date_idx]),sep)] for date_idx in range(len(dates))]
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Station loop over data
    for stn_idx, stn_data in enumerate(req['data']):
        new_meta.append(stn_data['meta'])
        for date_idx,date_data in enumerate(stn_data['data']):
            for el_idx, el_data in enumerate(date_data):
                strp_val, flag = strip_data(el_data)
                #Don't include -9999 (Missing) values
                if str(strp_val) == '-9999':strp_val = ''
                try:
                    val = unit_convert(els[el_idx],float(strp_val))
                    #val = unit_convert(els[el_idx],float(el_data))
                    smry_data[date_idx][el_idx].append(val)
                except:
                    pass
                #Compute spatial summary at last station iteration
                if stn_idx == len(req['data']) -1:
                    new_smry[date_idx].append(compute_statistic(smry_data[date_idx][el_idx],form['spatial_summary']))
    if new_smry:
        new_smry.insert(0,header_smry)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_station_no_summary(req,form):
    '''
    Formats raw station data request for printing or writing to file.
    Args:
        req -- ACIS data request dictionary
        form --user form input dictionary
    Returns:
        dictionar with keys
        data -- [[[date1 stn1_data],[date2 stn1_data]...], [[date1 stn2_data], ...]
        smry --[]
        meta -- [{stn1_meta},{stn2_meta}, ...]
        form -- user form input dictionary
    '''
    try:
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    #Headers
    header_data, header_smry = set_lister_headers(form)
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    new_data = [];new_smry = [];new_meta = []
    #MultiStnData calls return no dates
    dates = get_dates(form['start_date'],form['end_date'])
    #Sanity check on dates
    if len(dates) != len(data[0]['data']):
        return new_data,new_smry,new_meta
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Station loop over data
    for stn_idx, stn_data in enumerate(req['data']):
        #point is in shape, add to data and compute summary
        new_meta.append(stn_data['meta'])
        new_data.append([header_data])
        for date_idx,date_data in enumerate(stn_data['data']):
            d_data = [format_date(dates[date_idx],sep)]
            for el_idx, el_data in enumerate(date_data):
                #If user asked for flags/obstime
                #data el_data is a list and we need to pick the correct value
                obs_time = None
                if isinstance(el_data, list):
                    val = el_data[0]
                    if len(el_data) >1:
                        obs_time = el_data[1]
                else:
                    val = el_data
                #Strip flag from data
                strp_val, flag = strip_data(val)
                try:
                    val = round(unit_convert(els[el_idx],float(strp_val)),4)
                except:
                    val = strp_val
                if 'show_flags' in form.keys() and form['show_flags'] == 'T':
                    val = show_flag_on_val(val, flag)
                else:
                    val = remove_flag_from_val(val, flag)
                d_data.append(val)
                if obs_time:
                    d_data.append(obs_time)
            new_data[-1].append(d_data)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_station_windowed_data(req,form):
    '''
    Formats windowed station data request for printing or writing to file.
    Args:
        req: ACIS data request dictionary
        form: user form input dictionary
    Returns: dictionar with keys
        data: [[[date1 stn1_data],[date2 stn1_data]...], [[date1 stn2_data], ...]
        smry = []
        meta -- [{stn1_meta},{stn2_meta}, ...]
        form -- user form input dictionary
    '''
    try:
        data = req['data']
        els = form['elements']
    except:
        error = 'No data found for these parameters.'
        return {'data':[],'smry':[],meta:[],'form':form,'errors':error}
    header_data, header_smry = set_lister_headers(form)
    #Set date converter
    format_date = getattr(thismodule,'format_date_string')
    sep = form['date_format']
    new_data = [];new_smry = [];new_meta = []
    #MultiStnData calls return no dates
    dates = get_dates(form['start_date'],form['end_date'])
    #Sanity check on dates
    if len(dates) != len(data[0]['data']):
        return {'data':[],'smry':[],meta:[],'form':form}
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Station loop over data
    for stn_idx, stn_data in enumerate(req['data']):
        new_meta.append(stn_data['meta'])
        sd = form['start_date']
        ed = form['end_date']
        sw = form['start_window']
        ew = form['end_window']
        new_data.append([])
        for date_idx,date_data in enumerate(stn_data['data']):
            d_data = [format_date(dates[date_idx],sep)]
            for el_idx, el_data in enumerate(date_data):
                #If user asked for flags/obstime
                #data el_data is a list and we need to pick the correct value
                obs_time = None
                if isinstance(el_data, list):
                    val = el_data[0]
                    if len(el_data) >1:
                        obs_time = el_data[1]
                else:
                    val = el_data
                #Strip flag from data
                strp_val, flag = strip_data(val)
                try:
                    val = round(unit_convert(els[el_idx],float(strp_val)),4)
                    if form['data_summary'] == 'spatial':
                        smry_data[date_idx][el_idx].append(val)
                    if form['data_summary'] == 'temporal':
                        smry_data[el_idx].append(val)
                except:
                    val = strp_val
                if 'show_flags' in form.keys() and form['show_flags'] == 'T':
                    val = show_flag_on_val(val, flag)
                else:
                    val = remove_flag_from_val(val, flag)
                d_data.append(val)
                if obs_time:
                    d_data.append(obs_time)
            new_data[-1].append(d_data)
        #Windowed data
        new_data[-1] = get_windowed_data(new_data[-1], sd, ed, sw, ew)
        new_data[-1].insert(0,header_data)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def format_station_temporal_summary(req,form):
    '''
    Formats temporal summary station data request for printing or writing to file.
    Args:
        req -- ACIS data request dictionary
        form -- user form input dictionary
    Returns:
        dictionary with keys
        data -- []
        smry -- [['stn_name1 (stn_ids)', el1smry,el2smry,...],['stn_name1 (stn_ids)',...]]
        meta -- [{stn1_meta},{stn2_meta}, ...]
        form -- user form input dictionary
    '''
    try:
        data = req['data']
        els = form['elements']
    except:
        return [],[],[]
    header_data, header_smry = set_lister_headers(form)
    new_smry = []
    #MultiStnData calls return no dates
    dates = get_dates(form['start_date'],form['end_date'])
    new_data = [];new_meta = []
    #Set unit converter
    unit_convert = getattr(thismodule,'convert_nothing')
    if 'units' in form.keys() and form['units'] == 'metric':
        unit_convert = getattr(thismodule,'convert_to_metric')
    #Station loop over data
    for stn_idx, stn_data in enumerate(req['data']):
        new_meta.append(stn_data['meta'])
        stn_name = str(stn_data['meta']['name'])
        try:
            stn_ids = ','.join([sid.split(' ')[0] for sid in stn_data['meta']['sids']])
            stn_ids = ' (' + stn_ids + ')'
        except:
            stn_ids = ' ()'
        #Tempral summary
        ss = [unit_convert(els[el_idx],stn_data['smry'][el_idx]) for el_idx in range(len(els))]
        row = [stn_name + stn_ids] + ss
        new_smry.append(row)
    if new_smry:
        new_smry.insert(0,header_smry)
    resultsdict = {
        'data':new_data,
        'smry':new_smry,
        'meta':new_meta,
        'form':form
    }
    return resultsdict

def get_window_data(data, start_date, end_date, start_window, end_window):
    '''
    Routine to filter out data according to window specification
    Args:
        data         -- data array
        start_date   -- start date of data array
        end_date     -- end date of data array
        start_window -- start date of window
        end_window   -- end date of window
    Returns:
        list of windowed data
    '''
    if start_window == '0101' and end_window == '1231':
        windowed_data = data
    else:
        windowed_data = []
        start_indices=[]
        end_indices=[]
        #Pick first and last data from data array,
        #Note: data[0] is header so we start with index 1
        start_d = ''.join(data[1][0].split('-'))
        end_d = ''.join(data[-1][0].split('-'))
        st_yr = int(start_d[0:4])
        st_mon = int(start_d[4:6])
        st_day = int(start_d[6:8])
        end_yr = int(end_d[0:4])
        end_mon = int(end_d[4:6])
        end_day = int(end_d[6:8])
        #Date formatting needed to deal with end of data and window size
        #doy = day of year
        if is_leap_year(st_yr) and st_mon > 2:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday -1
        else:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday
        if is_leap_year(end_yr) and end_mon > 2:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday - 1
        else:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday
        doy_window_st = compute_doy(start_window[0:2], start_window[2:4])
        doy_window_end = compute_doy(end_window[0:2], end_window[2:4])
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
            return []
        for j in range(len(start_indices)):
            add_data = data[start_indices[j]:end_indices[j]+1]
            windowed_data = windowed_data + add_data
    return windowed_data

################################
# INTERANNUAL DATA MODULES
############################
def get_single_interannaul_data(form):
    '''
    Interannual data
    Args: cleaned form field entries
    Returns: yearly summarized values and highcarts data
    '''
    year_data = []; hc_data = []
    today_str = set_back_date(0)
    today_year = today_str[0:4]
    start_date = form['start_year'] + '0101'
    if form['units'] == 'metric':
        unit_convert = getattr(tismodule, 'convert_to_metric')
    else:
        unit_convert =  getattr(thismodule,'convert_nothing')
    if today_year == form['end_year'] :
        end_date = ''.join(today_str.split('-'))
    else:
        end_date = form['end_year'] + '1231'
    el_vX = WRCCData.ACIS_ELEMENTS_DICT[form['element']]['vX']
    acis_params = {
        'sdate':start_date,
        'edate':end_date,
        'elems': [{'vX':el_vX}],
    }
    #Data request
    if 'station_id' in form.keys():
        acis_params['sid'] = form['station_id']
        req = AcisWS.StnData(acis_params)
    if 'location' in form.keys():
        acis_params['loc'] = form['location']
        acis_params['grid'] = form['grid']
        req = AcisWS.GridData(acis_params)
    if 'data' not in req.keys():
        return year_data, hc_data
    data = req['data']
    #Format windows, need to be four characters long
    sm = form['start_month'];sd = form['start_day']
    em = form['end_month'];ed = form['end_day']
    if len(sm) == 1:sm='0' + sm
    if len(em) == 1:em='0' + em
    if len(sd) == 1:sd='0' + sd
    if len(ed) == 1:ed='0' + ed
    start_window = sm + sd; end_window = em + ed
    #check if we skip a year
    year_change = False
    doy_start = compute_doy_leap(start_window[0:2], start_window[0:4])
    doy_end = compute_doy_leap(end_window[0:2], end_window[0:4])
    if doy_end < doy_start:year_change = True
    #Get windowed data
    windowed_data = get_windowed_data(data, start_date, end_date, start_window, end_window)
    print windowed_data
    #Sort data by year
    smry_data = []; smry = None
    yr = windowed_data[0][0][0:4]
    for d in windowed_data:
        date = d[0]
        date_eight = date_to_eight(date)
        data_yr = d[0][0:4]
        data_doy = compute_doy_leap(date_eight[4:6],date_eight[6:8])
        val = d[1]
        if not year_change and int(data_yr) == int(yr):
            try:smry_data.append(float(d[1]))
            except:pass
            continue
        if year_change:
            if  int(data_yr) == int(yr):
                try:smry_data.append(float(d[1]))
                except:pass
                continue
            if int(data_yr) == int(yr) + 1 and 1 <= data_doy  and data_doy < doy_end:
                try:smry_data.append(float(d[1]))
                except:pass
                continue
            if int(data_yr) == int(yr) + 1 and data_doy == doy_end:
                try:smry_data.append(float(d[1]))
                except:pass
        #Compute Summary for this year
        if smry_data:
            smry = compute_statistic(smry_data,form['temporal_summary'])
        if smry:
            s_val = unit_convert(form['element'],smry)
            year_data.append([yr,s_val])
            date = yr + '-01-01'
            d = calendar.timegm(datetime.datetime.strptime(date, '%Y-%m-%d').timetuple())
            int_time = 1000 * d
            hc_data.append([int_time, s_val])
        else:
            year_data.append([yr,-9999])
        #reset
        smry_data = []
        yr = data_yr
    return year_data, hc_data

################################
# HIGHCARTS DATA EXTRACTION
############################
def extract_highcarts_data_monann(data,form):
    '''
    Format monann data for highcarts plotting
    Args:
        data: data list containing data for all elements
        el_idx: index of element data in data
        element: element short name
    Returns:
        highcharts series data
        Each month is its own series
    '''
    hc_data = [[] for m in range(0,12)]
    #Sort data by month
    zipped = zip(*data)
    years = zipped[0]
    for m_idx in range(0,12):
        data_idx = 2 * m_idx + 1
        mon_data = zipped[data_idx]
        for d_idx, data in enumerate(mon_data[1:-6]):
            date = years[d_idx+1] + '-01-01'
            d = calendar.timegm(datetime.datetime.strptime(date, '%Y-%m-%d').timetuple())
            int_time = 1000 * d
            try:
                val = round(float(data),2)
            except:
                val = None
            hc_data[m_idx].append([int_time,val])
    return hc_data


def extract_highcarts_data_spatial_summary(data,el_idx, element, form):
    '''
    Format data for highcarts plotting
    Args:
        data: data list containing data for all elements
        el_idx: index of element data in data
        element: element short name
    Returns:
        highcharts series data
    '''
    #strip header

    req_data = data[1:]
    hc_data = []
    num_nulls = None
    for idx,row_data in enumerate(req_data):
        date = format_date_string(row_data[0],'dash')
        d = calendar.timegm(datetime.datetime.strptime(date, '%Y-%m-%d').timetuple())
        int_time = 1000 * d
        try:
            val = round(float(row_data[el_idx + 1]),4)
            #deal with ACIS non-data
            if abs(val + 999.0) < 0.0001:
                val = None
        except:
            val = None
        hc_data.append([int_time,val])
    return hc_data

########################

#HEADER FORMATTING
########################
def elements_to_display(elements,units,valid_daterange=None):
    '''
    Converts form elements for display
    Args:
        elements -- list or string of abbreviated elements
        units -- english or metric
        vd -- list of valid dateranges for elements
    Returns:
        element list for display
    '''
    el_list_long = []
    el_list = convert_elements_to_list(elements)
    for el_idx,el in enumerate(el_list):
        el_strip,base_temp = get_el_and_base_temp(el)
        unit = WRCCData.UNITS_ENGLISH[el_strip]
        if units == 'metric':
            unit = WRCCData.UNITS_METRIC[el_strip]
            #form cleaned has english units
            #base_temp = convert_to_metric(el_strip,base_temp)
        if not base_temp or base_temp == ' ':
            el_list_long.append(WRCCData.DISPLAY_PARAMS[el_strip] + ' (' + unit + ')')
        else:
            el_list_long.append(WRCCData.DISPLAY_PARAMS[el_strip] + ' (' + unit + '), Base: ' + str(base_temp))
        if valid_daterange:
            try:
                vd = [str(valid_daterange[el_idx][0]),str(valid_daterange[el_idx][1])]
            except:
                vd =[]
            el_list_long[-1]+= ' ' + str(vd)
    return el_list_long

def elements_to_table_headers(elements,units):
    el_list = convert_elements_to_list(elements)
    el_list_header = []
    for el_idx,el in enumerate(el_list):
        el_strip,base_temp = get_el_and_base_temp(el)
        unit = WRCCData.UNITS_ENGLISH[el_strip]
        if units == 'metric':
            unit = WRCCData.UNITS_METRIC[el_strip]
            #form cleaned has english units
            #base_temp = convert_to_metric(el_strip,base_temp)
        if not base_temp or base_temp == ' ':
            el_list_header.append(WRCCData.MICHELES_ELEMENT_NAMES[el_strip] + ' (' + unit + ')')
        else:
            el_list_header.append(WRCCData.MICHELES_ELEMENT_NAMES[el_strip] + ' (' + unit + '), Base: ' + str(base_temp))
    return el_list_header

def sids_to_display(sids):
    '''
    sid_list = []
    for sid in sids:
        sid_l = sid.split()
        sid_list.append(str(sid_l[0]) + '/' + WRCCData.NETWORK_CODES[str(sid_l[1])])
    return sid_list
    '''
    sid_str = ''
    for sid in sids:
        sid_l = sid.split()
        sid_str+=str(sid_l[0]) + '/' + WRCCData.NETWORK_CODES[str(sid_l[1])] + ', '
    #Remove last comma
    sid_str = sid_str.rstrip(', ')
    return sid_str

def form_to_display_list(key_order_list, form):
    '''
    Converts form parameters
    for display in html/file headers
    Args:
        key_order_list -- keys to be converted for display
        form -- user form input dictionary
    Returns: List of [key,val] pairs
    '''
    keys = [k for k in key_order_list]
    display_list = [[WRCCData.DISPLAY_PARAMS[key]] for key in keys]
    #Special case window for interannual
    if 'window' in keys:
        idx = keys.index(str(key))
        window = 'From ' + WRCCData.NUMBER_TO_MONTH_NAME[str(form['start_month'])] + '-' + str(form['start_day'])
        window+=' to ' + WRCCData.NUMBER_TO_MONTH_NAME[str(form['end_month'])] + '-' + str(form['end_day'])
        display_list[idx].append(window)
    for key, val in form.iteritems():
        if str(key) not in keys:
            continue
        idx = keys.index(str(key))
        if key == 'data_summary':
            if 'data_summary' in form.keys() and form['data_summary'] !='none':
                s_type = WRCCData.DISPLAY_PARAMS[form['data_summary']]
                if form['data_summary'] == 'windowed_data':
                    display_list[idx]= ['Window',form['start_window'] + ' - ' + form['end_window']]
                else:
                    s = WRCCData.DISPLAY_PARAMS[form[form['data_summary']+'_summary']]
                    display_list[idx]= [s_type, s]
        elif key in ['spatial_summary','temporal_summary']:
            display_list[idx].append(WRCCData.DISPLAY_PARAMS[form[key]])
        elif key in ['elements', 'element']:
            el_list_long = elements_to_display(form[key],form['units'])
            display_list[idx].append(', '.join(el_list_long))
        elif key in ['data_type','units']:
            display_list[idx].append(WRCCData.DISPLAY_PARAMS[form[key]])
        elif key == 'grid':
            display_list[idx].append(WRCCData.GRID_CHOICES[form['grid']][0])
        else:
            display_list[idx].append(str(val))
    return display_list

def metadict_to_display_list(metadata, key_order_list,form):
    '''
    Converts metadata from ACIS lister call
    for display in html/file headers
    metadata is list of stn metadicts with keys:
        name, state,sids, uid, ll,elev
    or
    list of grid metadicts with keys:
        lat,lon,elev
    Args:
        metadata -- station of grid metadata list
        key_order_list -- keys to be converted for display
        form -- user form input dictionary
    Returns: List of [key,val] pairs
    '''
    keys = [k for k in key_order_list]
    #grid meta ll transforms to lat/lon keys
    if 'll' in keys:
        ll_idx = keys.index('ll')
        if 'lat' in metadata.keys():
            #replace ll with lat, lon keys
            keys[ll_idx] = 'lat'
            keys.insert(ll_idx + 1,'lon')
    #Initialize results
    meta = [[WRCCData.DISPLAY_PARAMS[key]] for key in keys]
    #Sanity check:
    for i,k in enumerate(keys):
        if not k in metadata.keys():
            if k == 'data_summary':
                if form['data_summary'] !='none':
                    metadict[i].append([WRCCData.DISPLAY_PARAMS[form[form['data_summary']]]])
            else:
                meta[i].append([' '])
    for key, val in metadata.iteritems():
        try:
            idx = keys.index(str(key))
        except:
            continue
        if key == 'sids':
            #sid_list = sids_to_display(metadata['sids'])
            sid_str = sids_to_display(metadata['sids'])
            meta[idx].append([sid_str])
        elif key == 'valid_daterange':
            els = form['elements']
            units = form['units']
            vd = metadata['valid_daterange']
            el_list_long = elements_to_display(els, units, valid_daterange=vd)
            meta[idx].append(el_list_long)
        else:
            meta[idx].append([str(val)])
    if 'units' in form.keys():
        meta.append(['Units', [form['units']]])
    return meta


##########################
#DATE/TIME FUNCTIONS
##########################
def format_date_string(date,separator):
    '''
    Args:
        date datestring, can be of varying format
        separator
    Returns
        date string where year,month and day are
        separated by separator
    '''
    d = str(date).replace('-','').replace(':','').replace('/','')
    y = d[0:4]
    m = d[4:6]
    d = d[6:8]
    s = separator
    if separator == 'dash':s = '-'
    if separator == 'colon':s = ':'
    if separator == 'slash':s = '/'
    return y + s + m + s + d

def date_to_eight(date,se=None):
    '''
    Converts dates of form
    yyyy
    yyyy-mm, yyyy:mm, yyyy/mm
    yyyy-mm-dd, yyyy/mm/dd, yyyy:mm:dd

    to yyyymmdd

    se =='start' --> start_date
    se == 'end' --> end_date
    '''
    mon_lens = ['31', '28', '31','30','31','30', '31','31','30','31','30','31']
    d8 = date.replace('-','').replace('/','').replace(':','').replace(' ','')
    mmdd = '0101';dd='01'
    if se == 'end':
        mmdd = '1231'
        if len(d8) == 6:
            if d8[4:6] == '02' and is_leap_year(d8[0:4]):
                mon_len = '29'
            else:
                mon_len = mon_lens[int(d8[4:6]) - 1]
            dd = mon_len
    if len(d8) == 4:d8+=mmdd
    if len(d8) == 6:d8+=dd
    return d8

def date_to_datetime(date_str):
    '''
    Function to convert acis date_str of forms
    yyyy-mm-dd
    yyyy/mm/dd
    yyyy:mm:dd
    yyyymmdd
    to datetime. The datetime object is returned
    '''
    eight_date = date_str.replace('-','').replace('/','').replace(':','')
    if len(eight_date) != 8:
        return None
    dt = datetime.datetime(int(eight_date[0:4]),int(eight_date[4:6]), int(eight_date[6:8]))
    return dt

def datetime_to_date(dt, seperator):
    '''
    yyyy-mm-dd
    yyyy/mm/dd
    yyyy:mm:dd
    yyyymmdd
    '''
    if type(dt) != datetime.datetime:
        return '0000' + str(seperator) + '00' + str(seperator) + '00'
    try:y = str(dt.year)
    except:y = '0000'
    try:
        m =str(dt.month)
        if len(m) ==1:m = '0' + m
    except:
        m = '00'
    try:
        d =str(dt.day)
        if len(d) ==1:d = '0' + m
    except:
        d = '00'
    return y + str(seperator) + m + str(seperator) + d

def get_start_date(time_unit, end_date, number):
    '''
    Given a time unit (days, months or years),
    an end date and the number of days/months/years to
    go back, this routine calculates the start date.
    Leap years are taken into consideratiion. start date is given as
    string of length 8, eg: "20000115", the resulting end date is of same format
    '''
    x = int(number)
    yr = int(end_date[0:4])
    mon = int(end_date[4:6])
    day = int(end_date[6:8])
    if time_unit == 'years':
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=x*365)
    elif time_unit == 'months':
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=(x*365)/12)
    else:
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=x)
    yr_start = str(start.year)
    mon_start = str(start.month)
    day_start = str(start.day)
    if len(mon_start) == 1:mon_start = '0%s' % mon_start
    if len(day_start) == 1:day_start = '0%s' % day_start
    start_date = '%s%s%s' %(yr_start, mon_start,day_start)
    return start_date

def start_end_date_to_eight(form):
    '''
    Converts form['start_date'] and form['end_date']
    to 8 digit start, end dates of format yyyymmdd.
    '''
    mon_lens = ['31', '28', '31','30','31','30', '31','31','30','31','30','31']
    if 'start_date' not in form.keys():
        s_date = 'por'
    elif form['start_date'].lower() == 'por':
        s_date = 'por'
    else:
        s_date = date_to_eight(str(form['start_date']),se='start')
        if len(s_date)!=8:
            s_date = None
    if 'end_date' not in form.keys():
        e_date = 'por'
    elif form['end_date'].lower() == 'por':
        e_date = 'por'
    else:
        e_date = date_to_eight(str(form['end_date']),se='end')
        if len(e_date)!=8:
            e_date = None
    return s_date, e_date

##############
#Day of Year
##############
def compute_doy(mon,day):
    '''
    Routine to compute day of year ignoring leap years
    '''
    mon_len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(str(mon).lstrip('0'))
    nday = int(str(day).lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

def compute_doy_leap(mon, day):
    '''
    Routine to compute day of leap years
    '''
    mon_len = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(str(mon).lstrip('0'))
    nday = int(str(day).lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

def compute_mon_day(doy):
    '''
    Reverse of compute_doy but counting every feb as having 29 days
    '''
    ndoy = int(doy)
    mon = 0
    day = 0
    if ndoy >366 or ndoy < 1:
        return None,None
    mon_day_sum = [31,60,91,121,152,182,213,244,274,305,335,366]
    for i in range(12):
        if i == 0:
            if ndoy <=31:
                mon = 1
                day = ndoy
                break
        else:
            if mon_day_sum[i-1] < ndoy and ndoy <= mon_day_sum[i]:
                mon = i+1
                day = ndoy - mon_day_sum[i-1]
                break
            else:
                continue

    return mon,day

#############
#Leap Years
#############
def is_leap_year(year):
    '''
    Check if year is leap year.
    '''
    yr = int(year)
    if yr % 100 != 0 and yr % 4 == 0:
        return True
    elif yr % 100 == 0 and yr % 400 == 0:
        return True
    else:
        return False

###############################
#Coordinate system conversions
##############################
def geoll2ddmmss(lat,lon):
    try:
        latitude = float(lat)
        longitude = float(lon)
    except:
        latitude = 99.99
        longitude = -999.99
    #Convert lat/lon to ddmmss
    for idx, l in enumerate([lat,lon]):
        dd = int(abs(float(l)))
        d_60 = abs((abs(float(l)) - dd))*60
        mm = int(d_60)
        ss = int(abs((mm - d_60))*60)
        if len(str(ss)) == 1:ss = '0' + str(ss)
        if len(str(mm))==1:mm = '0' + str(mm)
        if idx ==0:
            lat_ddmmss = '%s%s%s' %(str(dd),str(mm),str(ss))
        if idx ==1:
            lon_ddmmss = '%s%s%s' %(str(dd),str(mm),str(ss))
    return [lat_ddmmss,lon_ddmmss]

####################################
#NEED CLEANUP
#####################################
##########################
#SPECIAL FUNCTIONS
##########################


def find_valid_daterange(sid, start_date='por', end_date='por', el_list=None, max_or_min='max'):
    '''
    This function makes a StnMeta call to find either the
    maximum or minimum valid daterange for a
    station with station ID sid and elements in the list of climate elements el_list.

    Keyword arguments:
    sid  -- station ID
    el_list -- list of elements required.
               If el-list==None, we query for the 8 base elements
               [maxt,mint,pcpn,snow,snwd, hdd,cdd,gdd]

    Each element has its own valid daterange.
    If max_or_min == max, the largest daterange is returned.
    If max_or_min == min, the smallest daterange is returned.
    '''
    #Format start/end date into 8 digit strings
    s_date = date_to_eight(start_date)
    e_date = date_to_eight(end_date)
    if s_date.lower() != 'por' and e_date.lower() != 'por':
        return [s_date, e_date]

    if el_list is None:
        #el_tuple = 'maxt,mint,pcpn,snow,snwd,hdd,gdd,cdd'
        el_tuple = '1,2,4,10,11,45'
    else:
        el_tuple =''
        for idx, el in enumerate(el_list):
            el_tuple+=str(WRCCData.ACIS_ELEMENTS_DICT[el]['vX'])
            if idx < len(el_list) - 1:
                el_tuple+=','

        #el_tuple = ','.join(el_list)
    meta_params = {'sids':sid, 'elems':el_tuple, 'meta':'name,state,sids,ll,elev,uid,valid_daterange'}
    try:
        request = AcisWS.StnMeta(meta_params)
    except:
        return ['', '']
    if 'error' in request.keys() or not 'meta' in request.keys():
        return ['', '']
    #Find valid daterange
    #format first test date
    el_idx = 0
    vd_start = None;vd_end = None
    idx_start = 0
    if not request['meta']:
        return ['', '']
    for el_idx, el_vdr in enumerate(request['meta'][0]['valid_daterange']):
        if s_date.lower() != 'por':
            vd_start = date_to_datetime(s_date)
        else:
            if request['meta'][0]['valid_daterange'][el_idx]:
                vd_start = date_to_datetime(request['meta'][0]['valid_daterange'][el_idx][0])
        if e_date.lower() != 'por':
            vd_end = date_to_datetime(e_date)
        else:
            if request['meta'][0]['valid_daterange'][el_idx]:
                vd_end =  date_to_datetime(request['meta'][0]['valid_daterange'][el_idx][1])
        if vd_start is not None and vd_end is not None and vd_start <= vd_end:
            idx_start = el_idx + 1
            break
    if vd_start is None or vd_end is None:
        return ['', '']
    vd_start_date = ''
    vd_end_date = ''
    #loop over valid dateranges for each elements and find max or min valid daterange
    for el_idx, el_vdr in enumerate(request['meta'][0]['valid_daterange'][idx_start:]):
        vd_start_test = None;vd_end_test = None
        if s_date.lower() == 'por':
            if el_vdr:
                vd_start_test = date_to_datetime(el_vdr[0])
        if e_date.lower() == 'por':
            if el_vdr:
                vd_end_test = date_to_datetime(el_vdr[1])
        if max_or_min == 'min':
            if vd_start_test is not None and vd_start_test > vd_start and vd_start_test <= vd_end:
                vd_start = vd_start_test
            if vd_end_test is not None and vd_end_test < vd_end and vd_end_test >= vd_start:
                vd_end = vd_end_test
        elif max_or_min == 'max':
            if vd_start_test is not None and vd_start_test < vd_start and vd_start_test <= vd_end:
                vd_start = vd_start_test
            if vd_end_test is not None and vd_end_test > vd_end and vd_end_test >= vd_start:
                vd_end = vd_end_test
    #convert back to date string
    if s_date.lower() == 'por':
        yr_start = str(vd_start.year);mon_start=str(vd_start.month);day_start = str(vd_start.day)
    else:
        yr_start = s_date[0:4];mon_start = s_date[4:6];day_start = s_date[6:8]
    if e_date.lower() == 'por':
        yr_end = str(vd_end.year);mon_end=str(vd_end.month);day_end = str(vd_end.day)
    else:
        yr_end = e_date[0:4];mon_end = e_date[4:6];day_end = e_date[6:8]

    if len(mon_start) ==1:mon_start='0' + mon_start
    if len(day_start) ==1:day_start='0' + day_start
    if len(mon_end) ==1:mon_end='0' + mon_end
    if len(day_end) ==1:day_end='0' + day_end
    vd_start_date = '%s%s%s' %(yr_start, mon_start, day_start)
    vd_end_date = '%s%s%s' %(yr_end, mon_end, day_end)
    return [vd_start_date, vd_end_date]

def get_dates(s_date, e_date, app_name=None):
    '''
    This function is in place because Acis_WS's MultiStnCall does not return dates
    it takes as arguments a start date and an end date (format yyyymmdd)
    and returns the list of dates [s_date, ..., e_date] assuming that there are no gaps in the data
    '''
    if not s_date or not e_date:
        dates = []
    elif s_date.lower() == 'por' or e_date.lower() == 'por':
        dates = []
    else:
        dates = []
        #convert to datetimes
        start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
        end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
        for n in range(int ((end_date - start_date).days +1)):
            next_date = start_date + datetime.timedelta(n)
            n_year = str(next_date.year)
            n_month = str(next_date.month)
            n_day = str(next_date.day)
            if len(n_month) == 1:n_month='0%s' % n_month
            if len(n_day) == 1:n_day='0%s' % n_day
            acis_next_date = '%s%s%s' %(n_year,n_month,n_day)
            dates.append(acis_next_date)
            #dates.append(str(time.strftime('%Y%m%d', next_date.timetuple())))
            #note, these apps are grouped by year and return a 366 day year even for non-leap years
            if app_name in ['Sodpad', 'Sodsumm', 'Soddyrec', 'Soddynorm', 'Soddd']:
                if dates[-1][4:8] == '0228' and not is_leap_year(int(dates[-1][0:4])):
                    dates.append(dates[-1][0:4]+'0229')
    return dates


def get_station_ids(stn_json_file_path):
    '''
    finds all station ids of the
    stations listed in the json file
    Used in station locator app to set initial station ids for
    link to data find
    '''
    stn_ids = ''
    json_data = load_json_data_from_file(stn_json_file_path)
    if not json_data:json_data = {'stations':[]}
    if not 'stations' in json_data.keys():json_data['stations']=[]
    name_previous = ''
    for idx,stn in enumerate(json_data['stations']):
        if stn['name'] == name_previous:
            continue
        name_previous = stn['name']
        stn_ids+=stn['sids'][0]
        if idx < len(json_data['stations']) - 2:
            stn_ids+=','
    return stn_ids

def convert_nothing(element,value):
    return value

def convert_to_metric(element, value):
    el,base_temp = get_el_and_base_temp(element)
    try:
        float(value)
    except:
        return value
    if el in ['maxt','mint','avgt','obst', 'yly_maxt', 'yly_mint', 'mly_maxt', 'mly_mint', 'dtr','base_temp']:
        v = int(round((float(value) - 32.0)*5.0/9.0))
    elif el in ['hdd','cdd','gdd']:
        '''
        Note that, because HDD are relative to a
        base temperature (as opposed to being relative to zero),
        it is incorrect to add or subtract 32 when converting
        degree days.
        '''
        v = int(round(float(value)*5.0/9.0))
    elif el in ['pcpn','snow','snwd','evap','yly_pcpn', 'mly_pcpn', 'pet', 'evap']:
        v = round(float(value)*25.4,2)
    elif el in ['wdmv']:
        v = round(float(value)*1.60934,1)
    elif el =='elev':
        #Feet to meter
        v = round(float(value)/3.280839895,1)
    else:
        v = value
    return v

def convert_to_english(element, value):
    el,base_temp = get_el_and_base_temp(element)
    try:
        float(value)
    except:
        return value
    if el in ['maxt','mint','avgt','obst','yly_maxt', 'yly_mint', 'mly_maxt', 'mly_mint','base_temp']:
        v = int(round(9.0/5.0*float(value) + 32.0,1))
    elif el in ['hdd','cdd','gdd']:
        '''
        Note that, because HDD are relative to a
        base temperature (as opposed to being relative to zero),
        it is incorrect to add or subtract 32 when converting degre days
        '''
        v = int(round(float(value)*9.0/5.0))
    elif el in ['pcpn','snow','snwd','evap','mly_pcpn', 'yly_pcpn']:
        v = round(float(value)/25.4,2)
    elif el in ['wdmv']:
        v = int(round(float(value)/1.60934,1))
    elif el =='elev':
        #meter to feet
        v = round(float(value)*3.280839895,1)
    else:
        v = value
    return v

def set_back_date(days_back):
    '''
    Calculates today - days_back
    and returns the back date in format
    yyyymmdd
    '''
    try:
        int(days_back)
    except:
        return '99990101'
    tdy = datetime.datetime.today()
    #Choose default start_date 4 weeks back
    b = datetime.datetime.today() - datetime.timedelta(days=int(days_back))
    yr_b = str(b.year);mon_b = str(b.month);day_b = str(b.day)
    if len(mon_b) == 1:mon_b = '0%s' % mon_b
    if len(day_b) == 1:day_b = '0%s' % day_b
    back_date = '%s%s%s' % (yr_b, mon_b, day_b)
    return back_date

def get_N_HexCol(N=5):
    '''
    Generates HEX color list of size N
    '''
    HSV_tuples = [(x*1.0/N, 0.5, 0.5) for x in range(N)]
    RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
    RGB_tuples = map(lambda x: tuple(map(lambda y: int(y * 255),x)),RGB_tuples)
    HEX_tuples = map(lambda x: tuple(map(lambda y: chr(y).encode('hex'),x)), RGB_tuples)
    HEX_list = map(lambda x: "".join(x), HEX_tuples)

    return HEX_list


def check_for_file(dir_location, file_name):
    '''
    Checks if file exists in dir_location
    '''
    #Check if kml file exists, if not generate it
    file_path =  dir_location + file_name
    file_exists = True
    try:
        with open(file_path, 'r') as kml_f:
            pass
    except:
        file_exists = False
    return file_exists


def generate_kml_file(area_type, state, kml_file_name, dir_location):
    '''
    This functions makes a call to ACIS General
    Server=/General/<area_type>   params={"state":<state>,"meta":"id,name,bbox,geojson"}
    Then uses the information to generate a kml
    file with name kml_file, that is used to generate an overlay map
    of the area_type in the state.
    Returned is a status update. If file already existed or was successfully
    created, a 'Success' string is returned. Else and error message string is returned
    The kml file is put into dir_location. dir_location is an
    absolute path on local host
    '''
    if str(dir_location)[-1]!='/':
        dr = str(dir_location) + '/'
    elif str(dir_location)[0]!='/':
        return 'Need absolute path of directory. You entered: %s' %str(dir_location)
    else:
        dr = str(dir_location)
    #Check if kml file already exists in dir_loc
    try:
        with open(dr + kml_file_name):
            if os.stat(dr + kml_file_name).st_size==0:
                os.remove(dr + kml_file_name)
            else:
                return 'Success'
    except IOError:
        pass
    #Make General call to get the geojson for the input params
    req = AcisWS.make_gen_call_by_state(WRCCData.SEARCH_AREA_FORM_TO_ACIS[str(area_type)], str(state))
    #Sanity Check:
    if 'error' in req.keys():
        return str(req['error'])
    else:
        if not 'meta' in req.keys():
            return 'No meta data found for search area %s and state %s' %(str(area_type), str(state))
    json_data = req['meta']
    if not isinstance(json_data, list):
        return 'Not a valid json_data list: %s' % str(json_data)
    #Write kml file
    try:
         kml_file = open(dr + kml_file_name, 'w+')
    except:
        return 'Could not open kml file: %s' %(dr + kml_file_name)
    num = len(json_data)
    colors = get_N_HexCol(N=num)

    #Header
    kml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    kml_file.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    kml_file.write('  <Document>\n')
    #Styles
    for poly_idx, poly in enumerate(json_data):
        kml_file.write('    <Style id="poly%s">\n' %poly_idx)
        kml_file.write('      <LineStyle>\n')
        #kml_file.write('        <color>%s</color>\n' %str(colors[poly_idx]))
        kml_file.write('        <width>1.5</width>\n')
        kml_file.write('      </LineStyle>\n')
        kml_file.write('      <PolyStyle>\n')
        #kml_file.write('        <color>%s</color>\n' %str(colors[poly_idx]))
        kml_file.write('        <color>0000FF</color>\n')
        #kml_file.write('        <colorMode>normal</colorMode>\n')
        kml_file.write('        <fill>1</fill>\n')
        #kml_file.write('        <outline>1</outline>\n')
        kml_file.write('      </PolyStyle>\n')
        kml_file.write('    </Style>\n')
    #Polygons
    for poly_idx, poly in enumerate(json_data):
        poly_bbox = poly['bbox']
        if 'state' in poly.keys():
            poly_state = poly['state']
        else:
            poly_state = ''
        coords = poly['geojson']['coordinates'][0][0]
        #Remove special characters from name
        #Overlay maps and url bars do not like hashes and other weird chars
        name = re.sub('[^a-zA-Z0-9\n\.]', ' ', poly['name'])

        kml_file.write('    <Placemark>\n')
        kml_file.write('      <name>%s</name>\n' %poly['id'])
        kml_file.write('      <description>%s, %s</description>\n' %(name, poly['id']))
        kml_file.write('      <styleUrl>#poly%s</styleUrl>\n' %poly_idx)
        kml_file.write('      <Polygon>\n')
        kml_file.write('      <tessellate>1</tessellate>\n')
        kml_file.write('        <extrude>1</extrude>\n')
        kml_file.write('        <altitudeMode>relativeToGround</altitudeMode>\n')
        kml_file.write('        <outerBoundaryIs>\n')
        kml_file.write('          <LinearRing>\n')
        kml_file.write('            <coordinates>\n')

        for idx, lon_lat in enumerate(coords):
            kml_file.write('              %s,%s,%s\n' %(lon_lat[0], lon_lat[1],0))
        #Add first coordinate to close polygon
        #kml_file.write('              %s,%s,%s\n' %(coords[0][0], coords[0][1],0))
        kml_file.write('            </coordinates>\n')
        kml_file.write('          </LinearRing>\n')
        kml_file.write('        </outerBoundaryIs>\n')
        kml_file.write('      </Polygon>\n')
        kml_file.write('    </Placemark>\n')

    #Footer
    kml_file.write('  </Document>\n')
    kml_file.write('</kml>\n')
    kml_file.close

    return 'Success'


def find_bbox_of_shape(shape):
    '''
    Given a shape, i.e., a list of lon, lat coordinates
    defining the shape, this function find the enclosing bounding box
    '''
    lons_shape = [s for idx,s in enumerate(shape) if idx%2 == 0]
    lats_shape = [s for idx,s in enumerate(shape) if idx%2 == 1]
    try:
        bbox = str(min(lons_shape)) + ',' + str(min(lats_shape)) + ',' + str(max(lons_shape)) + ',' + str(max(lats_shape))
    except:
        bbox= ''
    return bbox

def find_bbox_of_circle(lon, lat, r):
    '''
    Given center coordinates lon, lat of a circle
    and radius r in meters, this function returns the W,S,E,N
    coordinates of the enclosing bounding box
    lon, lat are given in degrees
    r is given in meters
    '''
    R = 6378.1 #Radius of the Earth in km
    brngs = [3*math.pi/2,math.pi,math.pi/2,0]  #Bearing radians W,S,E,N.
    d = r / 1000.0  #Distance in km

    lat1 = math.radians(lat) #Current lat point converted to radians
    lon1 = math.radians(lon) #Current long point converted to radians

    bbox = ''
    for idx,brng in enumerate(brngs):
        lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +math.cos(lat1)*math.sin(d/R)*math.cos(brng))
        if idx %2 == 0: #90, 180%, want to pick up lon
            coord = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),math.cos(d/R)-math.sin(lat1)*math.sin(lat2))
        else:#pick lat
            coord = lat2
        #Convert back to degrees
        coord = math.degrees(coord)
        if idx == 0:
            bbox+=str(coord)
        else:
            bbox+=',' + str(coord)
    return bbox

def get_bbox(shape):
    '''
    shape is a str of lon, lat coordinates of
    a polygon or lon, lat, r of a circle
    output is the type of the shape (circle or polygon)
    and the enclosing bounding_box of the polygon or circle
    '''
    s = shape.split(',')
    s = [float(k) for k in s]
    if len(s)==3:
        t = 'circle'
        bbox = find_bbox_of_circle(s[0], s[1], s[2])
    elif len(s) == 4: #bbox
        t = 'bbox'
        bbox = find_bbox_of_shape(s)
    elif len(s) == 2:
        t = 'location'
        bbox = str(s[0] - 0.3) + ',' + str(s[1] - 0.3) + ',' + str(s[0] + 0.3) + ',' + str(s[1] + 0.3)
    else:
        t = 'polygon'
        bbox = find_bbox_of_shape(s)

    return t, bbox


def find_num_lls(bbox,grid):
    '''
    Computes number of latitudes and longitudes of
    bounding box bbox
    grid -- PRISM 4km
            NRCC/NRCC INT 5km
            NARCCAP 50km
    '''
    box = bbox
    if isinstance(bbox, basestring):
        box = bbox.replace(' ','').split(',')
    try:
        box = [float(b) for b in box]
    except:
        return 1,1
    if len(box)!=4:return 1,1
    #1 degree ~ 111km
    spatial_res = float(WRCCData.GRID_CHOICES[grid][2])
    num_lats = math.ceil(111 * (abs(box[3]) - abs(box[1])) / spatial_res)
    num_lons = math.ceil(111 *(abs(box[0]) - abs(box[2])) / spatial_res)
    return num_lats, num_lons


def point_in_circle(x,y,circle):
    '''
    Determine if a point is inside a given cicle
    [lon, lat, radius]
    lon, lat are given in degrees, r is given in meters
    the distance between the point and the center of the circle is
    computed via the Haversine formula
    '''
    R = 6378.1 #Radius of the Earth in km
    #Find distance between point and center of circle
    try:
        dlat = math.radians((y - circle[1]))
        dlon = math.radians((x - circle[0]))
        lat1 = math.radians(y)
        lat2 = math.radians(circle[1])
        #Haversine Formula
        a = math.sin(dlat/2)**2 + math.sin(dlon/2)**2 * math.cos(lat1)*math.cos(lat2)
        c = 2*math.atan2(math.sqrt(a),math.sqrt(1-a))
        dist = R*c
        if dist <= circle[2] / 1000.0:
            return True
        else:
            return False
    except:
        return False

def point_in_poly(x,y,poly):
    '''
    Determine if a point is inside a given polygon or not
    Polygon is a list of (x,y) or [x,y] pairs.
    Points lying on the boundary are excluded.
    This function returns True or False. The algorithm is called
    the "Ray Casting Method".
    '''
    n = len(poly)
    inside = False
    try:
        p1x,p1y = poly[0]
        for i in range(n+1):
            p2x,p2y = poly[i % n]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x,p1y = p2x,p2y
    except:
        pass
    return inside

def set_poly_and_PointIn(prms):
    poly = None;PointIn=None
    if 'shape' in prms.keys():
        shape = prms['shape']
        if isinstance(shape, basestring):
            shape = shape.replace(' ','').split(',')
        if not isinstance(shape, list):
            shape = list(shape)
        shape = [float(sh) for sh in shape]
        if len(shape) == 3:#circle
            poly = shape
            PointIn = getattr(thismodule,'point_in_circle')
        elif len(shape)== 4:#bbox
            poly = [(shape[0],shape[1]),(shape[0],shape[3]),(shape[2],shape[3]),(shape[2],shape[1])]
            PointIn = getattr(thismodule,'point_in_poly')
        else:
            poly = [(shape[2*idx],shape[2*idx+1]) for idx in range(len(shape)/2)]
            PointIn = getattr(thismodule,'point_in_poly')
    else:
        if 'basin' in prms.keys():
            sh = AcisWS.find_geojson_of_area('basin', prms['basin'])
        if 'location' in prms.keys():
            s = prms['location'].replace(' ','').split(',')
            sh = [(s[0],s[1])]
        if 'county_warning_area' in prms.keys():
            sh = AcisWS.find_geojson_of_area('cwa', prms['county_warning_area'])
        if 'climate_division' in prms.keys():
            sh = AcisWS.find_geojson_of_area('climdiv', prms['climate_division'])
        if 'county' in prms.keys():
            sh = AcisWS.find_geojson_of_area('county', prms['county'])
        if 'bounding_box' not in prms.keys() and not 'state' in prms.keys():
            poly = [(s[0],s[1]) for s in sh]
            PointIn = getattr(thismodule,'point_in_poly')
    return poly, PointIn

def check_for_int(string):
    try:
        int(string)
        return True
    except:
        return False

def convert_db_dates(messy_date):
    '''
    Converts postgres dates into format yyyy-mm-dd
    For metadata tool: metadata load tables population
    '''
    #Check if input is datetime object, convert if necessary
    if type(messy_date) is datetime.date or type(messy_date) is datetime.datetime:
        y = str(messy_date.year);m = str(messy_date.month);d=str(messy_date.day)
        if len(y) != 4:y='9999'
        if len(m) == 1:m='0'+m
        if len(d)==1:d='0'+d
        return y+'-'+m+'-'+d
        #return datetime.datetime.strftime(messy_date,"%Y-%m-%d")
    #Check if data is already in form yyyy-mm-dd
    date_list = messy_date.split('-')
    if len(date_list) == 3 and len(date_list[0]) == 4:
        if check_for_int(date_list[0]) and check_for_int(date_list[1]) and check_for_int(date_list[2]):
            for idx,dat in enumerate(date_list[1:3]):
                if len(dat) ==1:date_list[idx] = '0' + dat
            return '-'.join(date_list)
    date_list = messy_date.split(' ')
    #Sanity check
    if len(date_list)!= 3:
        return '0000-00-00'

    try:
        mon = WRCCData.MONTH_NAME_TO_NUMBER[date_list[0][0:3]]
    except:
        mon = '00'
    try:
        day = date_list[1][0:2]
        if day[-1] == ',' or len(day) ==1:
            day = '0' + day[0]
    except:
        day = '00'
    year = date_list[2]
    if len(year) != 4:
        year = '0000'
    try:
        int(year)
    except:
        year = '0000'

    return '-'.join([year, mon, day])



def u_convert(data):
    '''
    Unicode converter, needed to write json files
    '''
    if isinstance(data, unicode):
        return str(data)
    elif isinstance(data, Mapping):
        return dict(map(u_convert, data.iteritems()))
    elif isinstance(data, Iterable):
        return type(data)(map(u_convert, data))
    else:
        return data

def check_dir_path(path,rwx=False):
    '''
    Checks if dir_pathexists and has correct permissions
    Creates path if needed and sets permissions
    This function swas created to avoid permission errors
    in /tmp/data_requests after reboot.
    reboot cleans out /tmp
    '''
    path_error = None
    #create directories
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception, e:
        path_error = str(e)
    #change permissions to 777 if rwx= True
    if rwx:
        for root,dirs,files in os.walk(path):
            for d in dirs:
                '''
                try:
                    os.chmod(d,0777)
                except Exception, e:
                    path_error = str(e)
                    break
                '''
                os.chmod(d,0777)
    return path_error

def load_data_to_json_file(path_to_file, data):
    '''
    It's better to fail than to pass so that users and I know something is up
    when this call fails --> Nov 3 2014 --> premission issue after
    sofware upgrades on cyclone1 and blizzard
    '''
    with open(path_to_file, 'w+') as f:
        json.dump(data, f)
    '''
    try:
        with open(path_to_file, 'w+') as f:
            json.dump(data, f)
    except:
        pass
    '''

def load_json_data_from_file(path_to_json_file):
    json_data = None
    try:
        with open(path_to_json_file, 'r') as json_f:
            json_data = u_convert(json.loads(json_f.read()))
    except:
        pass
    return json_data

def find_mon_len(year,mon):
    if is_leap_year(int(year)):
        feb = 29
    else:
        feb = 28
    mon_lens = [31,feb, 31,30, 31,30, 31, 31,30, 31, 30, 31]
    m_idx = int(str(mon).lstrip('0')) -1
    return mon_lens[m_idx]


def get_station_meta(station_id):
    meta_params = {"sids":station_id,"meta":"name,state,sids,ll,elev,uid"}
    try:
        stn_meta = AcisWS.StnMeta(meta_params)
    except:
        stn_meta = {'name':'', 'sids':[], 'state':'', \
        'elev':-999, 'uid':-999, 'll':''}
    return stn_meta

def format_station_meta(meta_data):
    '''
    Formats meta data coming out of ACIS
    Deals with unicoe issues and assigns networks to each station id
    '''
    meta = {}
    if not meta_data:
        return {}
    if not isinstance(meta_data, dict):
        return {}
    for key,val in meta_data.iteritems():
        if key == 'name':
            #strip apostrophes from name
            meta['name'] = str(meta_data['name']).replace("\'"," ")
        elif key == 'sids':
            #find networks
            meta['sids'] = []
            for sid in meta_data['sids']:
                sid_split = sid.split(' ')
                #put coop id up front (for csc application metagraph  and possibly others)
                if str(sid_split[1]) == '2':
                    meta['sids'].insert(0,[str(sid_split[0]).replace("\'"," "), 'COOP'])
                else:
                    if str(sid_split[1]) in WRCCData.NETWORK_CODES.keys():
                        meta['sids'].append([str(sid_split[0]).replace("\'"," "),WRCCData.NETWORK_CODES[str(sid_split[1])]])
                    else:
                        meta['sids'].append([str(sid_split[0]).replace("\'"," "),'Misc'])
        elif key == 'll':
            meta[str(key)]=val
        elif key == 'valid_daterange':
            meta['valid_daterange']=[]
            for date_range in meta_data['valid_daterange']:
                if not date_range or len(date_range) != 2:
                    meta['valid_daterange'].append([])
                else:
                    meta['valid_daterange'].append([str(date_range[0]), str(date_range[1])])
        else:
            meta[str(key)] = str(val)
    return meta

#DELETE??? -- replaced by metadict_to_display_list
def metadict_to_display(metadata, key_order_list):
    meta = [[WRCCData.DISPLAY_PARAMS[key]] for key in key_order_list]
    for key, val in metadata.iteritems():
        try:
            idx = key_order_list.index(str(key))
        except:
            continue
        if key == 'sids':
            sid_str = ''
            for sid in val:
                sid_l = sid.split()
                sid_str+='%s/%s, ' %(str(sid_l[0]), WRCCData.NETWORK_CODES[str(sid_l[1])])
                #sid_list.append(sid.encode('ascii', 'ignore'))
            meta[idx].append(sid_str)
        else:
            meta[idx].append(str(val))

    return meta

def get_el_and_base_temp(el, units='english'):
    '''
    strips base temp xx from gddxx ( hddxx, cddxx)
    return element name gdd( hdd, cdd) and base temp xx

    Keyword arguments:
    el -- climate element abbreviation
    '''
    element = el
    base_temp = None
    el_strip = re.sub(r'(\d+)(\d+)', '', el)   #strip digits from gddxx, hddxx, cddxx
    #el_strip = re.sub(r'(\d+)(\.?)(\d+)', '', el)
    #b = el[-2:len(el)]
    try:
        b = el[3:]
    except:
        b = None
    try:
        float(b)
        base_temp = b
        element = el_strip
    except:
        if not b and el in ['hdd', 'cdd']:
            base_temp = '65'
            if units == 'metric':
                base_temp = '18'
        elif not b and el == 'gdd':
            base_temp = '50'
            if units == 'metric':
                base_temp = '10'
    return element, base_temp




def format_stn_meta(meta_dict):
    '''
    This routine deals with meta data issues:
    1)jQuery does not like ' in station names
    2) unicode output can cause trouble
    '''
    #deal with meta data issues:
    #1)jQuery does not like ' in station names
    #2) unicode output can cause trouble
    Meta = {}
    for key, val in meta_dict.items():
        if key == 'sids':
            Val = []
            for sid in val:
                Val.append(str(sid).replace("\'"," "))
        elif key == 'valid_daterange':
            Val = []
            for el_idx, rnge in enumerate(val):
                if rnge and len(rnge) == 2:
                    start = str(rnge[0])
                    end = str(rnge[1])
                else:
                    start = '00000000'
                    end = '00000000'
                dr = [start, end]
                Val.append(dr)
        else:
            Val = str(val)
        Meta[str(key)] = Val
    return Meta

def strip_data(val):
    '''
    Routine to strip data of attached flags
    '''
    v = str(val)
    if not v:
        return ' ', ' '

    if v[0] == '-':
        pos_val = v[1:]
    else:
        pos_val = v
    strp_val = ' ';flag = ' '
    if len(pos_val) == 1:
        if pos_val.isdigit():
            strp_val = v
            flag = ' '
        else:
            strp_val = ' '
            if pos_val in ['M', 'T', 'S', 'A', ' ']:
                flag = pos_val
                if flag in ['S','T']:
                    strp_val = 0.0
                if flag == 'M': strp_val = '-9999'
            else:
                flag = ' '
    else: #len(pos_val) >1
        if not pos_val[-1].isdigit():
            flag = v[-1]
            strp_val = v[0:-1]
        else:
            flag = ' '
            strp_val = v
    return strp_val, flag

def show_flag_on_val(val, flag):
    '''
    Add flags to data vals:
    If flag A, we add A   ty data val
    If flag M,S or T, replace data val with flag
    '''
    v = str(val)
    if flag in ['M','S','T']:v = flag
    if flag in ['A']:v = str(val) + flag
    return v

def remove_flag_from_val(val,flag):
    '''
    Removes flags from data vals
    If flag M, replace with -9999
    If flag S or T, replace val with 0.0
    If flag A, remove A from val
    '''
    v = str(val)
    if not v:
        return ' '
    if flag == 'M':v = -9999
    if flag in ['S','T']:v= 0.0
    if flag == 'A':
        if v[-1] == 'A':
            v = v[0:-1]
    return v

def get_dates(s_date, e_date, app_name=None):
    '''
    This function is in place because Acis_WS's MultiStnCall does not return dates
    it takes as arguments a start date and an end date (format yyyymmdd)
    and returns the list of dates [s_date, ..., e_date] assuming that there are no gaps in the data
    '''
    if not s_date or not e_date:
        dates = []
    elif s_date.lower() == 'por' or e_date.lower() == 'por':
        dates = []
    else:
        dates = []
        #convert to datetimes
        start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
        end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
        for n in range(int ((end_date - start_date).days +1)):
            next_date = start_date + datetime.timedelta(n)
            n_year = str(next_date.year)
            n_month = str(next_date.month)
            n_day = str(next_date.day)
            if len(n_month) == 1:n_month='0%s' % n_month
            if len(n_day) == 1:n_day='0%s' % n_day
            acis_next_date = '%s%s%s' %(n_year,n_month,n_day)
            dates.append(acis_next_date)
            #dates.append(str(time.strftime('%Y%m%d', next_date.timetuple())))
            #note, these apps are grouped by year and return a 366 day year even for non-leap years
            if app_name in ['Sodpad', 'Sodsumm', 'Soddyrec', 'Soddynorm', 'Soddd']:
                if dates[-1][4:8] == '0228' and not is_leap_year(int(dates[-1][0:4])):
                    dates.append(dates[-1][0:4]+'0229')
    return dates

def strip_n_sort(station_list):
    '''
    Strips station ids of leading zero,
    sorts in ascending order, re-inserts leading zeros.
    '''
    c_ids_strip_list = [int(stn.lstrip('0')) for stn in station_list]
    stn_list = sorted(c_ids_strip_list)
    for i, stn in enumerate(stn_list):
        if len(str(stn)) == 5:
            stn_list[i] = '0' + str(stn)
        else:
            stn_list[i] = str(stn)
    return stn_list

def convert_to_list(item):
    if isinstance(item, basestring):lst = item.replace(' ', '').split(',')
    elif isinstance(item, list):lst = [str(it) for it in item]
    else:lst = item
    return lst

def get_element_list(form, program=None):
    '''
    Finds element list for SOD program data query

    Keyword arguments:
    form -- webpage user form fields
    program    -- application name
    '''
    element_list = []
    if program in ['Soddynorm', 'Sodlist', 'Sodcnv','Soddd','Sodpad']:
        element_list = WRCCData.SOD_ELEMENT_LIST_BY_APP[program]['all']
    else:
        if 'element' in form.keys():
            element_list = WRCCData.SOD_ELEMENT_LIST_BY_APP[program][form['element']]
        elif 'elements' in form.keys():
            #Check if elements is given as string, if so, convert to list
            element_list = convert_to_list(form['elements'])
    return element_list


def format_sodlist_data(data_flag_tobs):
    '''
    Formats the data coming out of ACIS
    to conform with Kelly's sodlist output
    data_flags_tobs = [data_val, flag, time_obs]
    data_val and flag are strings
    time _obs is an interger
    output is a list with 4 objects
    [wrcc_data_val, flag_1= ACIS flag, flag_2='', str(time_obs)]
    '''
    wrcc_data = ['', ' ',' ', '-1']
    if not isinstance(data_flag_tobs, list):
        return wrcc_data
    if len(data_flag_tobs)!= 3:
        return wrcc_data
    data = str(data_flag_tobs[0])
    acis_flag = str(data_flag_tobs[1])
    tobs = str(data_flag_tobs[2])
    if acis_flag in ['M', 'T', 'S']:
        if data in ['M','S','T','',' ']:
            wrcc_data[0] = '0'
        else:
            try:
                float(data)
                wrcc_data[0] = data
            except:
                pass
    elif acis_flag in ['',' ']:
        try:
            float(data)
            wrcc_data[0] = data
        except:
            pass
    if acis_flag not in ['',' ']:
        wrcc_data[1] = acis_flag
    if tobs not in ['',' ','-1']:
        if len(tobs) ==1:
            wrcc_data[3] = '0'+tobs
        else:
            wrcc_data[3] = tobs
    return wrcc_data

def get_windowed_indices(dates, start_window, end_window):
    '''
    Finds start and end incdices for windowed data
    start_date   -- start date of data array
    end_date     -- end date of data array
    start_window -- start date of window
    end_window   -- end date of window
    output: list of start_indices, list of end_indices
    '''
    if start_window == '0101' and end_window == '1231':
        return [0],[len(dates)- 1]
    start_indices = [];end_indices = []
    for idx, date in enumerate(dates):
        #put date in format yyyymmdd
        d = ''.join(date.split('-'))
        d = ''.join(d.split('/'))
        if d[4:] == start_window:
            start_indices.append(idx)
        #deal with Feb 29 start
        if start_window == '0229':
            if end_window != '0229' and not is_leap_year(d[0:4]) and d[4:] == '0301':
                start_indices.append(idx)
        if d[4:] == end_window:
            end_indices.append(idx)
    #Date formatting needed to deal with end of data and window size
    start_d = dates[0];end_d = dates[-1]
    start_yr = int(start_d[0:4]);start_mon = int(start_d[4:6]);start_day = int(start_d[6:8])
    end_yr = int(end_d[0:4]);end_mon = int(end_d[4:6]);end_day = int(end_d[6:8])
    #Date formatting needed to deal with end of data and window size
    #doy = day of year
    if is_leap_year(start_yr) and start_mon > 2:
        doy_first = datetime.datetime(start_yr, start_mon, start_day).timetuple().tm_yday -1
    else:
        doy_first = datetime.datetime(start_yr, start_mon, start_day).timetuple().tm_yday

    if is_leap_year(end_yr) and end_mon > 2:
        doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday - 1
    else:
        doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday
    doy_window_st = compute_doy(start_window[0:2], start_window[2:4])
    doy_window_end = compute_doy(end_window[0:2], end_window[2:4])
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
        return [],[]
    return start_indices, end_indices

def get_windowed_data(data, start_date, end_date, start_window, end_window):
    '''
    Routine to filter out data according to window specification(sodlist)

    Keyword arguments:
    data         -- data array
    start_date   -- start date of data array
    end_date     -- end date of data array
    start_window -- start date of window
    end_window   -- end date of window
    '''
    if start_window == '0101' and end_window == '1231':
        windowed_data = data
    else:
        windowed_data = []
        start_indices=[]
        end_indices=[]
        if start_date.lower() == 'por':
            start_d = ''.join(data[0][0].split('-'))
        else:
            start_d = start_date
        if end_date.lower() == 'por':
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
        if is_leap_year(st_yr) and st_mon > 2:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday -1
        else:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday
        if is_leap_year(end_yr) and end_mon > 2:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday - 1
        else:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday
        doy_window_st = compute_doy(start_window[0:2], start_window[2:4])
        doy_window_end = compute_doy(end_window[0:2], end_window[2:4])
        dates = [data[i][0] for i  in range(len(data))]
        #match dates and window formats
        if len(dates[0]) == 8:
            start_w = start_window;end_w = end_window
        else:
            start_w = '%s-%s' % (start_window[0:2], start_window[2:4])
            end_w = '%s-%s' % (end_window[0:2], end_window[2:4])
        #silly python doesn't have list.indices() method
        #Look for windows in data
        for i, date in enumerate(dates):
            if len(date) == 8:sidx = 4
            else:sidx = 5
            if date[sidx:] == start_w:
                start_indices.append(i)
            if date[sidx:] == end_w:
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
            return []
        for j in range(len(start_indices)):
            add_data = data[start_indices[j]:end_indices[j]+1]
            windowed_data = windowed_data + add_data
    return windowed_data

###########################################################
#KELLY's routines
#These are mostly copied directly from Kelly's Fortran code
###########################################################

def JulDay(year, mon, day):
    '''
    JulDay; Function utilized to check for gap in data
    This program is based on and algorithm presented in 'Sky And Telescope Magazine, March 1984.'
    It will correctly calculate any date A.D. to the correct Julian date through at least 3500 A.D.
    Note that Julain dates begin at noon GMT. For this reason, the number is incremented by one to
    correspond to a day beginning at midnight.
    '''
    jd = 367 * year - 7 * (year + (mon + 9) / 12) / 4\
    - 3 * ((year + (mon - 9) / 7) / 100 +1) / 4\
    + 275 * mon / 9 + day + 1721029

    jd+=1
    return int(jd)

def Catoju(mnth, dy):
    '''
    Routine  to convert calendar days to yearly Julian days,
    All years are leap years, used in Sodthr
    '''
    month = int(mnth.lstrip('0'))
    nday = int(dy.lstrip('0'))
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ndoy =0
    for  mon in range(1,month+1):
        if mon < month:ndoy+=mon_lens[mon -1]
        if mon == month: ndoy+=nday
    if month == -1 and nday == -1:ndoy = -1
    return ndoy

def Jutoca(ndoy):
    '''
    Routine to convert yearly Julian Days to Calenday days,
    All years are leap years, used in Sodthr
    '''
    jstart = [1, 32, 61, 92, 122, 153, 183, 214, 245, 275, 306, 336]
    month = 0
    for mon in range(1,13):
        if ndoy >= jstart[mon-1]:
            month = mon
            if month == 12:
                if ndoy < 367:
                    nday = ndoy - 336 +1
                else:
                    month = -1
                    nday = -1
        else:
            nday = ndoy - jstart[month-1] +1
            break

    nday = str(nday)
    month = str(month)
    if len(nday)== 1:
        nday = '0%s' % nday
    if len(month) == 1:
        month = '0%s' % month
    return month, nday

def Doymd(idoy, most, iyear):
    '''
    Routine to find the month and day given the day of the year,
    the start month and the year of the starting month
    Used in WRCCDataApps.Sodpiii
    '''
    lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #n732 has no blank spaces so we set February to have length 28
    iidoy = idoy
    iyeart = iyear
    imo = most
    while imo < 13:
        if imo == 2 and is_leap_year(iyeart):
            length = 29
        else:
            length = lens[imo - 1]

        if iidoy <= length:
            imon = imo
            iday = iidoy
        else:
            iidoy = iidoy - length
            imo+=1
            if imo == 13:
                imo = 1
                iyear+=1
            continue

        idate = 100 * imon + iday
        return idate

def bcof(n, normlz=True):
    '''
    Routine to compute binomial coefficients for Soddynorm
    '''
    C = []
    S = 0
    for k in range(n+1):
        bc = [1 for i in range(0,k+1)]
        for j in range(1,n-k+1):
            for i in range(1,k+1):
                bc[i] = bc[i-1]+bc[i]
        C.append(bc[k])
        S+=bc[k]
    if normlz:
        C = ['%.6f' % (c/float(S)) for c in C ]
    return C

def pctil(app_name, data, number, npctil):
    '''
    Routine to compute percentiles, needed for Sodpct

    Keyword arguments:
    app_name -- application name
    data     -- data array
    number   -- number of data elements
    npctil   -- number of percentiles
    '''
    xmax = -100000000.0
    dummy = [data[i] for i in range(number)]
    sort = [0.0 for i in range(number)]
    pctile = [0.0 for i in range(npctil-1)]
    for i in range(number):
        try:
            xmax = max(xmax,dummy[i])
        except:
            pass
    for islow in range(number):
        xmin = 100000000.0
        # For each element of sort, find lowest of the vaues
        iskip = None
        for ifast in range(number):
            if dummy[ifast] <= xmin:
                xmin = dummy[ifast]
                iskip = ifast

        sort[islow] = xmin
        if iskip is not None:
            dummy[iskip] = xmax + 1
    #Find the median:
    if number % 2  == 0:
        xmed = (sort[number/2 - 1 ] + sort[(number/2)]) / 2
    else:
        xmed = sort[(number/2)]

    #Find percentiles
    frac = float(number) /  float(npctil)

    # Note that there are one less percentile separators than percentiles
    for i in range(npctil -1 ):
        dum = frac * float(i+1) + 0.5
        idum = int(dum)

        if app_name == 'Sodthr':
            if sort[idum - 1] < -0.5 or sort[idum] < -0.5:
                pctile[i] = -1
            elif sort[idum - 1] > 366.5 or sort[idum] > 366.5:
                pctile[i] =  367
            else:
                pctile[i] = sort[idum -1] + (dum - float(idum)) * (sort[idum] - sort[idum-1])
        else:
            pctile[i] = sort[idum -1] + (dum - float(idum)) * (sort[idum] - sort[idum-1])
    if app_name == 'Sodpct':
        return pctile, sort
    elif app_name == 'Sodthr':
        return pctile, sort, xmed

##################
#Sodxrmts routines
##################

####################################
#PearsonIII routines: Pintp3, Capiii
####################################
def Pintp3(prnoex, piii, piiili, npiili,skew):
    '''
    This routine interpolates in the piii table.

    Keyword arguments:
    prnoex -- probability of non-exceedance
    averag -- average of the distribution
    stdev  -- standard deviation of the distribution
    skew   -- skewness of the distribution
    piii   -- input array of PearsonIII frequency distribution
    piiili -- list of probabilities in piii array
    npiili -- len(piiili)

    Output:
    psdout -- probability of non-exceedance expressed in standard deviations
    '''
    if skew > 9.0:skew = 9.0
    if skew < -9.0:skew = -9.0
    nsklo = int(round(10.0*skew))
    if nsklo < -90:nsklo = -90
    nskhi = nsklo + 1
    if nskhi > 90:nskhi = 90
    #Index if non-exceedace probabilty
    iretrn = 0
    while iretrn <= 26:
        iretrn+=1
        test = piiili[iretrn - 1]
        if test > prnoex:
            if iretrn == 1:
                npnolo = iretrn - 1
                pnoxlo = piiili[npnolo] - 0.00001
            else:
                npnolo = iretrn - 2
                pnoxlo = piiili[npnolo]
            npnohi = iretrn - 1
            pnoxhi = piiili[npnohi]
            break
        else:
            if iretrn != 27:
                continue
            else:
                npnolo = 25 # Check this whole section, Kelly's does not make sense to me
                npnohi = 26
                pnoxlo = piiili[npnolo]
                pnoxhi = piiili[npnohi]
    if nsklo < -90:
        y1 = piii[-90][npnolo]
        y2 = piii[-90][npnolo]
        y3 = piii[-90][npnohi]
        y4 = piii[-90][npnohi]
    elif nskhi > 90:
        y1 = piii[90][npnolo]
        y2 = piii[90][npnolo]
        y3 = piii[90][npnohi]
        y4 = piii[90][npnohi]
    else:
        y1 = piii[nsklo][npnolo]
        y2 = piii[nskhi][npnolo]
        y3 = piii[nskhi][npnohi]
        y4 = piii[nsklo][npnohi]
    y1 = y1 / 1000.0
    y2 = y2 / 1000.0
    y3 = y3 / 1000.0
    y4 = y4 / 1000.0
    if abs(pnoxhi - pnoxlo) > 0.000001:
        t = (prnoex - pnoxlo) / (pnoxhi - pnoxlo)
    else:
        t = 0.0
    nskhi = nsklo +1
    u = (10.0 * skew - float(nsklo)) / (float(nskhi) - float(nsklo))
    a1 = u * (y2 - y1) + y1
    a2 = u * (y3 - y4) + y4
    psdout = t * (a2 - a1) + a1
    #psdout =  (1.0 - t)*(1.0 - u)*y1 + t*(1.0 - u)*y2 + t*u*y3 + (1.0 - t)*u*y4
    return psdout

def Capiii(xdata, numdat, piii, piiili,npiili, pnlist,numpn):
    '''
    Subroutine adapted from old Fortran program, mixture of cases thus results.
    Finds values of the Pearson III distribution from lookup tables calculated
    by Jim Goodridge.  For non-exceedance probabilities not in these tables,
    simple linear interpolation is used.
    Reference:  Selection of Frequency Distributions, with tables for
    Pearson Type III, Log-Normal, Weibull, Normal and Gumbel
    Distributions.  Baolin Wu and Jim Goodridge, June 1976,
    California Department of Water Resources, 85 pp.
    data is a large array (n=50000) containing the data
    numdat is the actual number of data points in the array 'data'
    pnlist is an array with the list of nonexceedance probabilities desired
    piii is a 2-dimensional array containing the Pearson III look-up tables
    piiili is an array containing the npiili nonexceedance values in the tables
    npiili is the number (27) of values in piiili
    ave is the average
    sk is the skewness
    cv is the coefficient of variation
    xmax is the max value
    xmin is the min value
    psd is an array containing the numpn nonexceedance values
    '''
    xmax = -9999.0
    xmin = 9999.0
    summ = 0.0
    summ2 = 0.0
    summ3 = 0.0
    count = 0.0
    #loop over the number of values in the array
    for ival in range(numdat):
        value = xdata[ival]
        if value >= -9998.0:
            summ+=value
            summ2+=value*value
            summ3+=value*value*value
            count+=1
            if value > xmax:xmax = value
            if value < xmin:xmin = value
    if count > 0.5:
        ave = summ / count
    else:
        ave = 0.0
    if count > 1.5:
        try:
            stdev = np.sqrt((summ2 - summ*summ/count)/(count - 1.0))
        except:
            stdev = 0.0
    else:
        stdev = 0.0

    if abs(ave) > 0.00001:
        cv = stdev / ave
    else:
        cv = 0
    if count > 1.5:
        h1 = summ / count
        h2 = summ2 / count
        h3 = summ3 /count
        xm2 = h2 - h1*h1
        xm3 = h3 - 3.0*h1*h2 + 2.0*h1*h1*h1
        if abs(xm2) > 0.000001:
            try:
                sk = xm3 / (xm2*np.sqrt(xm2))
            except:
                sk = 0.0
        else:
            sk = 0.0
    else:
        sk = 0.0
    #loop over the desired non-exceedance probabilities
    psd = [0 for k in range(numpn)]
    for ipn in range(numpn):
        prnoex  = pnlist[ipn]
        psd[ipn] = Pintp3(prnoex, piii, piiili, npiili, sk)

    return psd, ave, stdev, sk, cv, xmax, xmin

###########################################################################
#GEV routines: Samlmr Gev, Quantgev, Cdfgev, Lmrgev, Pelgev, Quagev, Reglmr, Salmr,
#Ampwm, Derf, Diagmd, Dlgama, Durand, Gamind, Quastn, Sort
##########################################################################
#Obtained from Jim Angel @ MrCC in Champaign, Illinois

def Samlmr(x, n, nmom, a, b):
    '''
    SAMPLE L-MOMENTS OF A DATA ARRAY

    PARAMETERS OF ROUTINE:
    X      * INPUT* ARRAY OF LENGTH N. CONTAINS THE DATA, IN ASCENDING
             ORDER.
    N      * INPUT* NUMBER OF DATA VALUES
    XMOM   *OUTPUT* ARRAY OF LENGTH NMOM. ON EXIT, CONTAINS THE SAMPLE
           L-MOMENTS L-1, L-2, T-3, T-4, ... .
    NMOM   * INPUT* NUMBER OF L-MOMENTS TO BE FOUND. AT MOST MAX(N,20).
    A      * INPUT* ) PARAMETERS OF PLOTTING
    B      * INPUT* ) POSITION (SEE BELOW)

    FOR UNBIASED ESTIMATES (OF THE LAMBDA'S) SET A=B=ZERO. OTHERWISE,
    PLOTTING-POSITION ESTIMATORS ARE USED, BASED ON THE PLOTTING POSITION
    (J+A)/(N+B)  FOR THE J'TH SMALLEST OF N OBSERVATIONS. FOR EXAMPLE,
    A=-0.35D0 AND B=0.0D0 YIELDS THE ESTIMATORS RECOMMENDED BY
    HOSKING ET AL. (1985, TECHNOMETRICS) FOR THE GEV DISTRIBUTION.
    '''

    summ = [0.0 for k in range(nmom)]
    xmom = [0.0 for k in range(nmom)]

    #if a <= -1 or a > b:
    #    xmom = [-99999 for k in range(nmom)]

    if a != 0 or b != 0:
        #Plotting-Position estimates of PWM's
        for i in range(n):
            ppos = (i+1 + a) / (n + b)
            term = x[i]
            summ[0]+=term
            for j in range(1,nmom):
                term*=ppos
                summ[j]+=term
        for j in range(nmom):
            summ[j] = summ[j] /n

    else: #a and b are zero
        #Unbiased estimates of of pwm's
        for i in range(n):
            z = i+1
            term = x[i]
            summ[0]+=term
            for j in range(1,nmom):
                z-=1
                term*=z
                summ[j]+=term
        y = n
        z = n
        summ[0] = summ/z
        for j in range(1,nmom):
            y-=1
            z*=y
            summ[j] = summ[j]/z

    #L-Moments
    k = nmom
    p0 = 1
    if nmom - nmom / 2 * 2 == p0:p0 = -1
    for kk in range(1,nmom):
        ak = k
        p0 = -p0
        p =  p0
        temp = p * summ[0]
        for i in range(k-1):
            ai = i+1
            p = -p*(ak+ai-1) * (ak - ai) / (ai**2)
            temp+=p*summ[i+1]
        summ[k-1] = temp
        k-=1
    xmom[0] = summ[0]
    xmom[1] = summ[1]
    if abs(summ[1] - 0.0) > 0.001:
        for k in range(2, nmom):
            xmom[k] = summ[k] / summ[1]
    return xmom

def Dlgama(x):
    '''
    Logarithm of Gamma function
    '''
    #c[0] - c[7] are the coeffs of the asymtotic expansion of dlgama
    c = [0.91893, 0.83333, -0.27777, 0.79365, \
        -0.59523, 0.84175, -0.19175, 0.64102]
    s1 = -0.57721 #Euler constant
    s2 = 0.82246  #pi**2/12
    dlgama =  0
    if x < 0 or x > 2.0e36:
        pass
    #Use small-x approximation if x is near 0,1 or 2
    if abs(x - 2)  <= 1.0e-7:
        dlgama = np.log(x - one)
        xx = x - 2
        dlgama+=xx*(s1+xx*s2)
    elif abs(x - 1) <= 1.0e-7:
        xx = x - 1
        dlgama+=xx*(s1+xx*s2)
    elif abs(x) <= 1.0e-7:
        dlgama = -np.log(x) + s1*x
    else:
        #Reduce to dlgama(x+n) where x+n >= 13
        sum1 = 0
        y = x
        if y <13:
            z =1
            while y < 13:
                z*=y
                y+=1
            sum1+= - np.log(z)
        #Use asymtotic expansion if y >=13
        sum1+=(y - 0.5)* np.log(y) -y +c[0]
        sum2 = 0
        if y < 1.0e9:
            z = 1 / y*y
            sum2 = ((((((c[7]*z + c[6])*z + c[5])*z + c[4])*z + c[3])*z + c[2])*z +c[1]) / y

        dlgama = sum1 + sum2
    return dlgama

def Pelgev(xmom):
    '''
    Parameter Estomation via L-Moments for the generalized extreme value distribution
    XMOM   * INPUT* ARRAY OF LENGTH 3. CONTAINS THE L-MOMENTS LAMBDA-1,
    LAMBDA-2, TAU-3.
    PARA   *OUTPUT* ARRAY OF LENGTH 3. ON EXIT, CONTAINS THE PARAMETERS
    IN THE ORDER XI, ALPHA, K (LOCATION, SCALE, SHAPE).
    Uses Dlgama
    '''
    eu = 0.57721566
    dl2 = 0.69314718
    dl3 = 1.0986123
    z0 = 0.63092975
    c = [7.817740,2.930462,13.641492,17.206675]
    maxit = 20
    #Initial estimate of k
    t3 = xmom[2]
    if xmom[1] <= 0 or abs(t3) > 1:
        para = [-9999, -9999, -9999]
    else:
        z = 2 /(t3 + 3) - z0
        g = z*(c[0] + z*(c[1] + z*(c[2] + z*c[3])))

        #Newton-Raphson, if required

        if t3 < - 0.1 or t3 > 0.5:
            if t3 < -0.9: g = 1 - np.log(1 + t3) / dl2
            t0 = (t3 + 3) / 2
            for it in range(1, maxit+1):
                x2 = 2**(-g)
                x3 = 3**(-g)
                xx2 = 1 - x2
                xx3 = 1 - x3
                t = xx3 / xx2
                deri = (xx2*x3*dl3 - xx3*x2*dl2) / (xx2*xx2)
                gold = g
                g = g - (t -t0) / deri
                if abs(g - gold)< 1.0e-6: break
                if g > 1 and abs(g - gold) <= 1.0e-6*g:break
        para = [0, 0, 0]
        if abs(g) >= 1.0e-5:
            para[2] = g
            gam = np.exp(Dlgama(1+g))
            para[1] = xmom[1]*g / (gam*(1 - 2**(-g)))
            para[0] = xmom[0] -para[1]*(1 - gam) / g
        else:
            para[2] = 0
            para[1] = xmom[1] / dl2
            para[0] = xmom[0] - eu * para[1]
    return para

def Quagev(f,para):
    '''
    Quantile function of the generalized extreme value distribiution
    '''
    u = para[0]
    a = para[1]
    g = para[2]
    if a > 0:
        if f > 0 and f < 1:
            y = -np.log(f)
            if g != 0:
                y = 1.0 - np.exp(-g*y) / g
                quagev = u + a*y
            else:
                quagev = 0
        else:
            if (f == 0 and g < 0) or (f== 1 and g > 0):
                quagev = u + a / g
            else:
                quagev = 0
    else:
        quagev = 0
    return quagev

def Quantgev(para, probs, nprobs):
    results = [0.0 for iq in range(nprobs)]
    for iq in range(nprobs):
        results[iq] = Quagev(probs[iq], para)
    return results
#Gev
#Subroutine to calculate the three parameters of the Gev
def Gev(x, n):
    x_sorted = []
    x_sorted_keys = sorted(x, key=x.get)
    for key in x_sorted_keys:
        x_sorted.append(x[key])
    nmom = 3
    xmom = Samlmr(x_sorted, n, nmom, -0.35, 0)
    para = Pelgev(xmom)
    return para

################
#beta-p routines
################
def Sortb(rdata, n):
    ra = rdata
    l = n/2 + 1
    ir = n
    while l >1:
        if l > 1:
            l-=1
            rra = ra[l-1]
        else:
            rra = ra[ir -1]
            ra[ir-1] = ra[0]
            ir-=1
            if ir ==1:
                ra[0] = rra
                break
        i = l
        j = l + l
        while j <= ir:
            if j < ir:
                if ra[j-1] < ra[j]:j+=1
            if rra < ra[j-1]:
                ra[i-1] = ra[j-1]
                i = j
                j+=j
            else:
                j = ir +1
        ra[i-1] = rra
    return ra

def Dda(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    dda = rn/alpha
    for i in range(n):
        xb = x[i]/beta
        if np.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            dda-= float(np.log(1.0 + xbt))
        else:
            dda-=theta*np.log(xb)
    return dda

def Ddt(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    ddt = rn/beta
    for i in range(n):
        xb = float(x[i]/beta)
        if np.log(xb) <= 85.0/theta:
            xbt = xb**theta
            ddt+=float(np.log(xb)) - (alpha + 1.0)*float(np.log(xb)/(1.0 + xbt))*float(xbt)
        else:
            ddt-=alpha*float(np.log(xb))
    return ddt

def Ddb(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    ddb = -rn
    for i in range(n):
        xb = x[i]/beta
        if np.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            ddb+= (alpha + 1.0)*float(xbt/(1.0 + xbt))
        else:
            ddb+=alpha + 1
    ddb = theta*ddb/beta
    return ddb


def Betapll(alpha, theta, beta, n, x, ndim):
    betapll = float(n)*np.log(alpha*theta/beta)
    for i in range(n):
        xb = x[i]/beta
        if np.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            betapll+=(theta - 1.0)*np.log(xb) - (alpha + 1.0)*float(np.log(1+xbt))
        else:
            betapll-=(1.0 + alpha*theta)*np.log(xb)
    return betapll



def Fitbetap(x, n, ndim):
    '''
    Maximum likelihood fit for the "Beta-P" distribution
    Data x assumed to be sorted in ascending order.
    '''
    itmax = 2000
    epsilon = 0.0005
    efd = 0.00001
    pinit = [.1, .2, .5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
    trllbst = -1.0e20
    tbeta = 1.01*x[0]
    ig = int(round(0.8*float(n+1)))
    factor = -np.log(1.0 - 0.8)/np.log(x[ig-1]/tbeta)
    alpha0 = 0.0
    beta0 = 0.0
    theta0 = 0.0
    for ith in range(13):
        tthet = pinit[ith]*100.0
        talph = factor / tthet
        test = Betapll(talph, tthet, tbeta, n , x, ndim)
        if test > trllbst:
            trllbst = test
            alpha0 = talph
            beta0 = tbeta
            theta0 = tthet
            break
    #Begin iterations
    rll0 = Betapll(alpha0, theta0, beta0, n, x, ndim)
    bestll = rll0
    besta = alpha0
    bestb = beta0
    bestt = theta0
    dlambda = 0.001
    score = [0.0 for k in range(3)]
    #finf = [[0.0 for j in range(3)] for k in range(3)]
    finf = np.zeros((3,3))
    adj = [0.0 for k in range(3)]
    for it in range(itmax):
        itact = it
        ea = efd*alpha0
        et = efd*theta0
        eb = efd*beta0
        score[0] = Dda(alpha0, theta0, beta0, n, x, ndim)
        score[1] = Ddt(alpha0, theta0, beta0, n, x, ndim)
        score[2] = Ddb(alpha0, theta0, beta0, n, x, ndim)

        finf[0][0] = (Dda(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Dda(alpha0-ea, theta0, beta0, n, x, ndim))/2.0*ea
        finf[1][1] = (Ddt(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Ddt(alpha0, theta0 -et, beta0, n, x, ndim))/2.0*et
        finf[2][2] = (Ddb(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Ddb(alpha0, theta0, beta0 - eb, n, x, ndim))/2.0*eb

        finf[0][1] = (Dda(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Dda(alpha0, theta0 + et, beta0, n, x, ndim))/4.0*et +\
                    (Ddt(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Ddt(alpha0-ea, theta0, beta0, n, x, ndim))/4.0*ea

        finf[1][0] = finf[0][1]

        finf[0][2] = (Ddb(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Ddb(alpha0 + ea, theta0, beta0, n, x, ndim))/4.0*ea +\
                    (Dda(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Dda(alpha0, theta0, beta0 + eb, n, x, ndim))/4.0*eb

        finf[2][0] = finf[0][2]

        finf[1][2] = (Ddb(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Ddb(alpha0, theta0 + et, beta0, n, x, ndim))/4.0*et +\
                    (Ddt(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Ddt(alpha0, theta0, beta0 + eb, n, x, ndim))/4.0*eb

        finf[2][1] = finf[1][2]

        for i in range(3):
            finf[i][i]*=(1.0 + dlambda)

        #invert
        finv = np.linalg.inv(finf)
        for i in range(3):
            for j in range(3):
                adj[j] = adj[i] + finv[i][j]*score[j]
        alpha = abs(alpha0 - adj[0])
        if alpha/alpha0 > 1.1:alpha = 1.1*alpha0
        if alpha/alpha0< 0.9:alpha = 0.9*alpha0
        beta = abs(beta0 - adj[2])
        if beta/beta0 > 1.1:beta = 1.1*beta0
        if beta/beta0< 0.9:beta = 0.9*beta0
        theta = abs(theta0 - adj[1])
        if theta/theta0 > 1.1:theta = 1.1*theta0
        if theta/theta0< 0.9:theta = 0.9*theta0

        #Try to ensuer that this is an improvement
        iflag = 0
        for iback in range(4):
            rll = Betapll(alpha, theta, beta, n, x, ndim)
            if rll > bestll:
                bestll = rll
                besta = alpha
                bestb = beta
                bestt = theta

            if rll < rll0:
                iflag = 1
                alpha = (alpha + alpha0)/2
                beta = (beta + beta0)/2
                theta = (theta + theta0)/2
                dlambda=dlambda*2
            else:
                if iflag == 0:
                    dlambda = dlambda/2
                    break

        #Test for convergenceif no backing off the parameter estimates
        #was necessary
        if iflag == 0:
            if abs((alpha -alpha0)/alpha0) >= epsilon or \
            abs((beta -beta0)/beta0) >= epsilon or \
            abs((theta -theta0)/theta0) >= epsilon:
                alpha0 = alpha
                theta0 = theta
                beta0 = beta
                ll0 = rll
            else:
                break
    #end it loop
    rll = bestll
    alpha = besta
    beta = bestb
    theta = bestt
    return alpha, theta,beta, rll, itact

def Pintbetap(alpha, beta, theta, prob):
    #Check for conditions that will lead to floating overflow
    check1 = -1.0*np.log(1.0 - prob)
    check2 = 31.0*alpha*np.log(2.0)
    if check1 < check2:
        psd = (1.0 - prob)**(-1.0/alpha)
        psd = (psd - 1.0)**(1.0/theta)
        psd = psd * beta
    else:
        power = -1.0/(alpha*theta)
        psd = beta*((1.0 - prob)**power)
    return psd

def Cabetap(rdata, numdat, pnlist, numpn):
    #rdata = Sortb(rdata, numdat)
    r_sorted = []
    r_sorted_keys = sorted(rdata, key=rdata.get)
    for key in r_sorted_keys:
        r_sorted.append(rdata[key])
    alpha, theta, beta, rll, itact = Fitbetap(r_sorted, numdat, numdat)
    psd = [0.0 for i in range(numpn)]
    for i in range(numpn):
        psd[i] = Pintbetap(alpha, beta, theta, pnlist[i])
    return psd
########################
#Censored Gamma routines
########################
def Func(beta, alpha, p):
    func = Gammp(alpha, x/beta) - p
    return func

def Gammln(z):
    stp = 2.50662827465
    cof = [76.18009173,-86.50532033,24.01409822, -1.231739516,.120858003e-2,-.536382e-5]
    fpf = 5.5
    if z < 1.0:
        xx = z + 1.0
    else:
        xx = z
    x = xx - 1.0
    tmp = x + fpf
    tmp = (x + 0.5)*np.log(tmp) - tmp
    ser = 10
    for j in range(6):
        x+=1.0
        ser+=cof[j]/x
    gammln = tmp + np.log(stp*ser)
    if z < 1.0:
        gammln-=np.log(z)
    return gammln

def Gcf(a,x):
    itmax = 100
    eps = 3.0e-7
    gln = Gammln(a)
    gold = 0.0
    a0 = 1.0
    a1 = x
    bo = 0.0
    b1 = 1.0
    fac = 1.0
    for n in range(itmax):
        an = float(n)
        ana = an - a
        a0 = (a1 + a0*ana)*fac
        b0 = (b1 + b0*ana)*fac
        anf = an*fac
        a1 = x*a0 + anf*a1
        b1 = x*b0 + anf*b1
        if abs(a1) >  0.00001:
            ffac = 1.0/a1
            g = b1*fac
            if abs((g - gold)/g) >= eps:
                gold = g
    gammfc = np.exp(-z + a*np.log(x) - gln)*g
    return gammfc


def Gser(a,x):
    itmax = 100
    eps = 3.0e-7
    gln = Gammln(a)
    gamser = 0.0
    if x >= 0.0:
        ap =a
        summ = 1.0/a
        dl = summ
        for n in range(maxit):
            ap+=1
            dl*=x/ap
            summ+=dl
            if abs(dl) < abs(summ)*eps:
                gamser = summ*np.exp(-x + a*np.log(x) -gln)
                break
    return gamser

def Gammp(a,x):
    if x < 0.0 or a <= 0.0:
        gammp = 0.0
    if x < a + 1:
        gammp, gln = Gser(a,x)
    else:
        gammcf, gln = Gcf(a,x)
        gammp = 1.0 - gammcf
    return gammp


def Zbrent(beta, alpha, prob, x1, x2, tol):
    itmax = 100
    eps = 3.0e-8
    a = x1
    b = x2
    fa = Func(a, beta,alpha, prob)
    fb = func(b, beta, alpha, prob)
    fc =  fb
    for it in range(itmax):
        if fb*fc > 0.0:
            c = a
            fc = fa
            d = b - a
            e = d
        if abs(fc) < abs(fb):
            a = b
            b = c
            c = a
            fa = fb
            fb = fc
            fc = fa
        tol1 = 2.0*eps*abs(b) + 0.5*tol
        xm = 0.5*(c-b)
        if abs(xm) <= tol1 or fb == 0.0:
            zbrent = b
            break
        if abs(e) > tol1 and abs(fa) > abs(fb):
            s = fb/fa
            if abs(a-c) < 0.00001:
                p = 2.0*xm*s
                q =  1.0 - s
            else:
                q = fa/fc
                r = fb/fc
                p = s*(2.0*xm*q*(q - r) - (b - a)*(r - 1.0))
                q = (q - 1.0)*(r - 1.0)*(s - 1.0)
            if p > 0.0:q = -q
            p = abs(p)
            if 2.0*p < min(3.0*xm*q - abs(tol1*q), abs(e*q)):
                e = d
                d = p/q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d
        a = b
        fa = fb
        if abs(d) > tol1:
            b+=d
        else:
            if xm < 0.0:
                b-= tol1
            else:
                b+=tol1
            fb = Func(b, beta, alpha, prob)

    zbrent = b
    return zbrent

def Rloglike(nc, nw,sumx, sumlnx, a, b):
    try:
        ff = Gammp(a, nc/b)
    except:
        ff = 1.0
    rloglike = -nw*(a*np.log(b) + Gammln(a)) + (a - 1.0)*sumlnx - sumx/b
    if nc > 0.0: rloglike+=float(nc)*np.log(ff)
    return rloglike

def Psi(shape):
    z = shape
    if z < 1.0:
        a = z + 1.0
    else:
       a = z
    psi = np.log(a)-1.0/(2.0*a)-1.0/(12.0*a**2)+1.0/(120.0*a**4) - \
    1.0/(256.0*a**6)+1.0/(240.0*a**8)
    return psi

def Psipr(shape):
    z = shape
    if z < 1.0:
        a = z + 1.0
    else:
       a = z
    psipr=1.0/a+1.0/(2.0*a**2)+1.0/(6.0*a**3)-1.0/(30.0*a**5) + \
    1.0/(42.0*a**7)-1.0/(30.0*a**9)
    if z < 1.0:psipr+=1.0/z**2
    return psipr

def Dcdf(c, shape, scale, iflag):
    dp = 0.1
    ff = Gammp(shape, c/scale)
    da = shape*dp
    db = scale*dp

    fp = f(c, shape + da, scale)
    fm = f(c, shape - da, scale)
    dfda = (fp - fm)/(2.0*da)
    d2fda2 = (fp -2.0*ff + fm)/db**2

    fp=f(c,shape,scale+db)
    fm=f(c,shape,scale-db)
    dfdb=(fp-fm)/(2.0*db)
    d2fdb2=(fp-2.0*ff+fm)/db**2

    fapbp = f(c,shape+da,scale+db)
    fapbm=f(c,shape+da,scale-db)
    fambp=f(c,shape-da,scale+db)
    fambm=f(c,shape-da,scale-db)
    d2fdab=(fapbp-fambp-fapbm+fambm)/(4.0*da*db)
    return  ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp

def Dlda(nc, nw, sumlnx, shape, scale, ff, dfda): #dfda, ff extra coming from Dcdf
    dlda=sumlnx-float(nw)*(np.log(scale)+Psi(shape))
    if nc < 0.0:dlda== float(nc)*dfda/ff
    return dlda

def Dldb(nc,nw,sumx,shape,scalei, ff, dfdb):
    dldb=-shape*float(nw)/scale+sumx/(scale**2)
    if nc < 0.0:dldb+=float(nc)*dfdb/ff
    return dldb

def D2lda2(nc,nw,shape, ff, d2fda2, dfda):#ff, d2fda2, dfda from Dcdf
    d2lda2=-float(nw)*Psipr(shape)
    if nc < 0.0: d2lda2+=float(nc)*(ff*d2fda2-dfda**2)/ff**2
    return d2lda2

def D2ldb2(nc,nw,sumx,shape,scale, ff, d2fdb2, dfdb):
    d2ldb2=shape*float(nw)/scale**2-2.0*sumx/scale**3
    if nc < 0.0:d2ldb2+=float(nc)*(ff*d2fdb2-dfdb**2)/ff**2
    return d2ldb2

def D2ldab(nc,nw,scale, ff, d2fdab,dfdb):
    d2ldab=-float(nw)/scale
    if nc < 0.1:d2ldab+=float(nc)*(ff*d2fdab-dfda*dfdb)/ff**2
    return d2ldab


def Cengam(nc, nw, c, sumx, sumlnx):
    fininv = [[0.0 for k in range(2)] for j in range(2)]
    score = [0.0 for k in range(2)]
    itmax = 1000
    epsilon = 0.001
    dp = 0.1

    #Initial parameter guesses
    if nc == 0:
        sx = sumx
        slx = sumlnx
    else:
        sx = sumx + float(nc)*c/10.0
        slx = sumlnx + float(nc)*np.log(c/10)
    amean = sx/float(nc + nw)
    gmean = np.exp(slx/float(nc + nw))
    y = np.log(amean/gmean)
    if y > 17.0:
        shape = 0.05
    elif y <= 0:
        shape = np.sqrt(amean)
    elif y <= 0.5772:
        shape = (.5000876+.1648852*y-.0544274*y**2)/y
    else:
        shape=(8.898919+9.05995*y+.9775373*y**2)/(y*(17.79728+11.968477*y+y**2))
    scale = amean/shape

    #Begin iterations
    nocon = 0
    shapen = 0.0
    scale = 0.0
    shapen = 0.0
    scalen = 0.0
    for it in range(itmax):
        ki = 0
        if nc > 0:
            ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp = Dcdf(c,shape,scale,1)
            oldll = Rloglike(nc, nw, sumx, sumlnx, shape, scale)
            a = D2lda2(nc,nw,shape, ff, d2fda2, dfda)
            b = D2ldab(nc,nw,scale, ff, d2fdab,dfdb)
            d = D2ldb2(nc,nw,sumx,shape,scale,ff, d2fdb2, dfdb)
            det = a*d - b**2
            fininv[0][1] = b/det
            fininv[1][0] = fininv[0][1]
            score[0] = Dlda(nc, nw, sumlnx, shape, scale, ff, dfda)
            score[1] = Dldb(nc,nw,sumx,shape,scalei, ff, dfdb)
            fininv[0][0] = d/det
            fininv[1][1] = a/det

            shapen = shape - fininv[0][0]*score[1] - fininv[0][1]*score[1]
            if shapen < 0.001:shapen = 0.001
            scalen = scale - fininv[1][0]*score[1] - fininv[1][1]*score[1]
            if scalen < 0.001:scalen = 0.001

        #Test whether this is an improvement
        ki = 0
        while ki < 5:
            if nc > 0.0:
                ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp = Dcdf(c,shapen,scalen,0)
            if Rloglike(nc,nw,sumx,sumlnx,shapen,scalen) < oldll:
                ki+=1
                scalen = (scale+scalen)/2.
                shapen=(shape+shapen)/2.
        #Test for convergence
        if ki != 0 or abs(shape-shapen) > epsilon or abs(scale-scalen) > epsilon:
            shape = shapen
            scale = scalen
            nocon = 1
        else:
            shape = shapen
            scale = scalen
            nocon = 0
            break
    return shape, scale, nocon

def Gampctle(pcentile, beta, alpha):
    '''
    Returns as x the value of the gamma distribution variate corresponding to the decimal
    fraction pcentile
    '''
    x1 = 0
    x2 = 100.0*beta
    x = Zbrent(beta, alpha, pcentile, x1, x2, 1.0e-7)
    return x

def Cagamma(rdata, numdat, pnlist, numpn):
    cen_level = 0.004
    #Initialize counters
    sumx = 0.0
    sumlnx = 0.0
    num_cen = 0
    num_wet = 0

    for i in range(numdat):
        if rdata[i] > cen_level:
            sumx+=rdata[i]
            sumlnx+= np.log(rdata[i])
            num_wet+=1
        else:
            num_cen+=1
    #Calculate parameters
    shape = -999
    scale = -999
    shape, scale, nocon = Cengam(num_cen, num_wet, cen_level, sumx, sumlnx)
    #Calculate values
    for i in range(numpn):
        psd[i] = Gampctle(pnlist[i], scale, shape)
    return psd

def compute_pet(lat,lon,maxt,mint,doy,units):
    '''
    Hargreaves P.E.T. Calculation
    Adopted from Kelly's program sodxtrmtsE.f
    lat,lon -- geo lat, lon
    maxt    -- maximum temperature
    mint    -- minimum temperature
    units   -- english or metric
    '''
    lat_ddmmss, lon_ddmmss = geoll2ddmmss(lat,lon)
    latd = int(lat_ddmmss[0:2])
    latm = int(lat_ddmmss[2:4])
    slat = latd - latm /60.0
    #slat = lat
    pi = 3.141592653589793
    tx = maxt
    tn = mint
    if units == 'english':
        tx = ((tx-32)*5.0/9)
        tn = ((tn-32)*5.0/9)
    td = tx-tn
    ta = (tx+tn)/2
    theta = slat*pi/180
    dec = 23.5*math.cos(2*pi*(doy-172)/365)*pi/180
    a = -math.tan(theta)*math.tan(dec)
    h = math.acos(a)
    rvec = 1-0.01676*math.cos(2*pi*(doy-3)/365)
    itd1 = (1440/pi)*1.959/(rvec*rvec)
    itd2 = h*math.sin(theta)*math.sin(dec)+math.cos(theta)*math.cos(dec)*math.sin(h)
    ra = itd1*itd2
    harg = 0.0023*ra*sqrt(td)*(ta+17.8)
    xl = 595-0.51*ta
    #harg : PeT in mm/day
    harg = 10*harg/xl
    if units == 'english':
        value = harg / 25.4
    else:
        value = harg
    return value
