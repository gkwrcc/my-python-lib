#!/usr/bin/python

'''
Module WRCCFormCheck

Checks input form parameters
'''

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
