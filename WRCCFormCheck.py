#!/usr/bin/python

'''
Module WRCCFormCheck

Checks input form parameters
'''

def check_start_year(form):
    err = None
    yr = form['start_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four digit entry. You entered %s' %yr
    e_yr = form['end_year']
    try:
        if int(e_yr) < int(yr):
            return 'Start Year is later then End Year.'
    except:
        pass
    return err

def check_end_year(form):
    err = None
    yr = form['end_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four didgit entry. You entered %s' %yr
    s_yr = form['start_year']
    try:
        if int(yr) < int(s_yr):
            return 'End Year is earlier then Start Year.'
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

