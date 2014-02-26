#!/usr/bin/python

'''
Module WRCCFormCheck

Checks input form parameters
'''
import datetime
import re
import WRCCData

def check_start_year(form):
    err = None
    yr = form['start_year']
    e_yr = form['end_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four digit entry. You entered %s' %yr
    try:
        if int(e_yr) < int(yr):
            return 'Start Year is later then End Year.'
    except:
        pass
    return err

def check_end_year(form):
    err = None
    yr = form['end_year']
    s_yr = form['start_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four didgit entry. You entered %s' %yr
    try:
        if int(yr) < int(s_yr):
            return 'End Year is earlier then Start Year.'
    except:
        pass
    return err

def check_start_date(form):
    err = None
    date = form['start_date'].replace('-','').replace('/','')
    e_date = form['end_date'].replace('-','').replace('/','')
    if date.lower() == 'por' and 'station_id' in form.keys():
        return err
    if len(date)!=8:
        if date.lower() == 'por':
            return '%s is not a valid option for a multi-station request.' %form['start_date']
        else:
            return 'Date should be of form yyyymmdd. You entered %s' %date
    try:
        int(date)
    except:
        return 'Date should be an eight digit entry. You entered %s' %date
    sd = datetime.datetime(int(date[0:4]), int(date[4:6].lstrip('0')), int(date[6:8].lstrip('0')))
    try:
        ed = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
    except:
        return err
    try:
        if ed < sd:
            return 'Start Date is later then End Year.'
    except:
        pass
    return err

def check_end_date(form):
    err = None
    s_date = form['start_date'].replace('-','').replace('/','')
    date = form['end_date'].replace('-','').replace('/','')
    if date.lower() == 'por' and 'station_id' in form.keys():
        return err
    if len(date)!=8:
        if date.lower() == 'por':
            return '%s is not a valid option for a multi-station request.' %form['end_date']
        else:
            return 'Date should be of form yyyymmdd. You entered %s' %date
    try:
        int(date)
    except:
        return 'Date should be an eight digit entry. You entered %s' %date
    try:
        sd = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
    except:
        return err
    ed = datetime.datetime(int(date[0:4]), int(date[4:6].lstrip('0')), int(date[6:8].lstrip('0')))
    try:
        if ed < sd:
            return 'Start Date is later then End Year.'
    except:
        pass

    return err

def check_elements(form):
    err = None
    el_list = form['elements'].replace(' ','').split(',')
    for el in el_list:
        #strip degree day digits
        el_strip = re.sub(r'(\d+)(\d+)', '', el)
        if el_strip[0:4] in ['yly_', 'mly_']:
            el_strip = el_strip[4:]
        if 'select_grid_by' in form.keys():
            if el_strip not in ['maxt','mint','avgt','pcpn','gdd','hdd','cdd']:
                err = '%s is not a valid element. Please consult with the helpful question mark!' %el
            if form['grid']=='21' and form['temporal_resolution'] in ['yly','mly'] and el_strip not in ['maxt','mint','avgt','pcpn']:
                err = '%s is not a valid PRISM element. Please choose from maxt,mint,avgt,pcpn!' %el_strip
        else:
            if el_strip not in ['maxt','mint','avgt','pcpn','snow','snwd','evap','wdmv','gdd','hdd','cdd','obst']:
                err = '%s is not a valid element. Please consult with the helpful question mark!' %el
    return err

def check_state(form):
    err = None
    if form['state'].upper() not in WRCCData.STATE_CHOICES:
        err = '%s is not a valid US state abbreviation.' %form['state']
    return err

def check_station_id(form):
    err = None
    s = form['station_id']
    return err

def check_station_ids(form):
    err = None
    s = form['station_ids']
    s_list = s.replace(' ','').split(',')
    if len(s_list) == 1:
        err = '%s is not a comma seperated list of two or more stations.' %s
    return err

def check_location(form):
    err = None
    ll_list = form['location'].replace(' ','').split(',')
    if len(ll_list) !=2:
        return '%s is not a valid longitude,latitude pair.' %form['location']
    for idx, s in enumerate(ll_list):
        try:
            float(s)
        except:
            return '%s is not a valid longitude,latitude pair.' %form['location']
        if idx == 0 and float(s) >0:
            return '%s is not a valid longitude.' %s
        if idx == 1 and float(s) < 0:
            return '%s is not a valid latitude.' %s
    return err

def check_county(form):
    err = None
    c = form['county'].replace(' ','')
    if len(c)!=5:
        return '%s is not a valid county FIPS code. County codes are 5 digit numbers.' %c
    try:
        int(str(c).lstrip('0'))
    except:
        return '%s is not a valid county FIPS code. County codes are 5 digit numbers.' %c
    return err

def check_climate_division(form):
    err = None
    climdiv = form['climate_division']
    if len(climdiv) != 4:
        return '%s is not a valid climate division.' %climdiv
    if climdiv[0:2].upper() not in WRCCData.STATE_CHOICES:
        return 'First two letters should be a two letter US state abreviation.'
    cd = str(climdiv[2:]).lstrip('0')
    if cd == '':
        return None
    try:
        int(cd)
    except:
        return '%s is not a valid climate division.' %climdiv
    return err

def check_county_warning_area(form):
    err = None
    cwa = form['county_warning_area']
    if len(cwa) != 3:
        return '%s is not a valid 3-letter county warning area code.' %cwa

    if not cwa.isalpha():
        return '%s is not a valid 3-letter county warning area code.' %cwa
    return err

def check_basin(form):
    err = None
    b = form['basin']
    if len(b)!=8:
        return '%s is not a valid basin code. Basin codes are 8 digit numbers.' %b
    try:
        int(str(b).lstrip('0'))
    except:
        return '%s is not a valid basin code. Basin codes are 8 digit numbers.' %b
    return err

def check_shape(form):
    err = None
    s_list = form['shape'].replace(' ','').split(',')
    for s in s_list:
        try:
            float(s)
        except:
            return 'Not a valid coordinate list. Please check you longitude, latitude pairs.'
    return err

###################
#Plot Options
####################
def check_graph_start_year(form):
    err = None
    t_yr = form['start_year']
    yr = form['graph_start_year']
    e_yr = form['graph_end_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four digit entry. You entered %s' %yr
    try:
        if int(e_yr) < int(yr):
            return 'Start Year is later then End Year.'
    except:
        pass

    if t_yr.lower() != 'por':
        try:
            if int(t_yr)>int(yr):
                return 'Graph Start Year must start later than Table Start Year.'
        except:
            pass
    return err

def check_graph_end_year(form):
    err = None
    yr = form['graph_end_year']
    t_yr = form['end_year']
    s_yr = form['graph_start_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four didgit entry. You entered %s' %yr
    s_yr = form['graph_start_year']
    try:
        if int(yr) < int(s_yr):
            return 'End Year is earlier then Start Year.'
    except:
        pass
    if t_yr.lower() != 'por':
        try:
            if int(t_yr)<int(yr):
                return 'Graph End Year must be earlier than Table End Year.'
        except:
            pass
    return err

def check_max_missing_days(form):
    err = None
    mmd = form['max_missing_days']
    try:
        int(mmd)
    except:
        return 'Max Missing Days should be an integer. You entered %s' %mmd
    if int(mmd) < 0:
        return 'Max Missing Days should be a positive integer. You entered %s' %mmd
    return err

def check_connector_line_width(form):
    err = None
    clw = form['connector_line_width']
    try:
        int(clw)
    except:
        return 'Connector Line Width should be an integer. You entered %s' %clw
    if int(clw) < 0:
        return 'Connector Line Width should be a positive integer. You entered %s' %clw
    if int(clw)>10:
        return 'Connector Line Width should be less than 10. You entered %s' %clw
    return err

def check_vertical_axis_min(form):
    err = None
    vam = form['vertical_axis_min']
    mx = form['vertical_axis_max']
    if vam == 'Use default':
        return err
    try:
        float(vam)
    except:
        return 'Axis minimum should be a number. You entered %s' %vam
    try:
        if float(vam) >= float(mx):
            return 'Axis minimum should be less than axis maximum. You entered %s' %vam
    except:
        pass
    return err

def check_vertical_axis_max(form):
    err = None
    vam = form['vertical_axis_max']
    mx = form['vertical_axis_min']
    if vam == 'Use default':
        return err
    try:
        float(vam)
    except:
        return 'Axis maximum should be a number. You entered %s' %vam
    try:
        if float(vam) <= float(mx):
            return 'Axis maximum should be greater than axis minimum. You entered %s' %vam
    except:
        pass
    return err

def check_level_number(form):
    err = None
    ln = form['level_number']
    try:
        int(ln)
    except:
        return 'Level number must be an integer. You entered: %s' %ln
    if int(ln)< 1:
        return 'Level number must at least 1. You entered: %s' %ln
    if int(ln)> 20:
        return 'Level number can be at most 20. You entered: %s' %ln
    return err

def check_cmap(form):
    err = None
    cmap = form['cmap']
    if cmap not in WRCCData.CMAPS:
        return 'Not a valid color map. Please refer to the list below to find your coor map name.'
    return err
