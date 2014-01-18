#!/usr/bin/python

'''
This scripts run though /tmp/data_requests directory every 5 minutes so see if new data requests by
CSC users were made.
Files in /tmp/data_requests are of form username_timestamp.json and contain
parameter dictionary corresponding to the user data request.
The script catches files that were created less than= 5 mins ago (timestamp in file extension < 5 minutes old)
and runs the according data requests (via python script) in order of submission, appending the results to the file.
After the data request has been processed,
the data file will be made available on the ftp server pubfiles.dri.edu
The user will be notified via e-mail.
'''

import sys, os, glob, json
import datetime
import re
from time import sleep
import WRCCUtils, AcisWS
import logging

from celery import group
from CELERY.tasks import run_data_request
###############
#hard codes:
################
ftp_server = 'pubfiles.dri.edu'
mail_server = 'owa.dri.edu'
from_address = 'csc-project@dri.edu'
base_dir = '/tmp/data_requests/'
pub_dir = '/pub/csc/test/'
now = datetime.datetime.now()

x_mins_ago = now - datetime.timedelta(minutes=5) #cron job checking for param files runs every 5 minutes
time_out = 3600 #1hr
#time_out = 10800 #time out = 3hrs = 10800 seconds
time_out_time = now - datetime.timedelta(seconds=time_out) #timeout for data request
time_out_h = '1 hour'
####################
#End hard code

##########################
#Functions
##########################
def write_error(error_dict, error, user_name, user_email):
    if 'user_name' in error_dict.keys():
        error_dict['user_name'][1].append(error)
    else:
        error_dict['user_name'] = [user_email, [error]]

def get_user_info(params):
    if 'user_name' in params.keys():
        user_name = params['user_name']
    else:
        user_name = 'bdaudert'
    if 'email' in params.keys():
        user_email = params['email']
    else:
        user_email = 'bdaudert@dri.edu'
    return user_name, user_email

def get_file_extension_and_delimiter(params):
    if 'data_format' in params.keys():
        if params['data_format'] == 'html':file_extension = '.txt'
        if params['data_format'] == 'clm':file_extension = '.txt'
        if params['data_format'] == 'json':file_extension = '.json'
        if params['data_format'] == 'dlm':file_extension = '.dat'
        if params['data_format'] == 'xl':file_extension = '.xls'
    else:
        file_extension = '.txt'

    if 'delimiter' in params.keys():
        if params['delimiter'] == 'comma':delimiter = ','
        if params['delimiter'] == 'tab':delimiter = ' '
        if params['delimiter'] == 'colon':delimiter = ':'
        if params['delimiter'] == 'space':delimiter = ' '
        if params['delimiter'] == 'pipe':delimiter = '|'
    else:
        delimiter = ' '
    return file_extension, delimiter

'''
Note: current criteria for data reqest split up are:
for station  data request:
        if data for multiple stations is requested
        we ask for one year at a time
for grid data requests:
        if data for multiple gridpoints is requested
        we ask for 7 days at a time
'''
def split_data_request(params):
    #Find time period and determine number of data requests to be made
    s_date = ''.join(params['start_date'].split('-'))
    e_date = ''.join(params['end_date'].split('-'))
    if s_date.lower() == 'por' or e_date.lower() == 'por':
        s_date,e_date = WRCCUtils.find_valid_daterange(sid, el_list=params['elements'], max_or_min='max')
    day_limit = None
    params_list = [params]
    #find out if we need to split up the request
    if 'select_stations_by' in params.keys() and params['select_stations_by'] not in ['stnid', 'stn_id']:
        day_limit = 365
    elif 'select_grid_by' in params.keys() and 'location' not in params.keys():
        day_limit = 7

    if day_limit is not None:
        #split up data request and mutliprocess them
        #request one year at a time
        start = WRCCUtils.date_to_datetime(s_date)
        end = WRCCUtils.date_to_datetime(e_date)
        #Find days between start/end date
        try:
            days = (end -  start).days
        except:
            days = 0
        if 'select_stations_by' in params.keys():
            num_requests = days / (day_limit + 1)
        else:
            num_requests = days / day_limit

        if 'select_stations_by' in params.keys() and days%(day_limit) != 0:num_requests+=1
        #contstruct params dict for the different requests
        params_list = [dict(params) for k in range(num_requests)]
        #Change start/end dates for the individual reuests
        for k in range(num_requests):
            if k==0:
                start_new = start
            else:
                start_new = start + k*datetime.timedelta(days=day_limit + 1)
            if k < num_requests - 1:
                end_new = start_new + datetime.timedelta(days=day_limit)
            else:
                end_new = end
            start_yr = str(start_new.year);end_yr = str(end_new.year)
            start_month = str(start_new.month);end_month = str(end_new.month)
            start_day = str(start_new.day);end_day = str(end_new.day)
            if len(str(start_new.month)) == 1:start_month = '0%s' %str(start_new.month)
            if len(str(end_new.month)) == 1:end_month = '0%s' %str(end_new.month)
            if len(str(start_new.day)) == 1:start_day = '0%s' %str(start_new.day)
            if len(str(end_new.day)) == 1:end_day = '0%s' %str(end_new.day)
            params_list[k]['start_date'] = ''.join([start_yr, start_month, start_day])
            params_list[k]['end_date'] = ''.join([end_yr, end_month, end_day])
    return params_list

def concatenate_results(results, data, request_type):
    if request_type == 'grid':
        results=results + data_out
    if request_type == 'station':
        if not results:
            results = {'stn_names':data_out['stn_names'], 'stn_ids':data_out['stn_ids'], \
            'stn_data':data_out['stn_data'], 'dates':data_out['dates'], 'stn_errors':data_out['stn_errors']}
        else:
            for stn_idx, stn_data in enumerate(data_out['stn_data']):
                stn_name = data_out['stn_names'][stn_idx]
                try:
                    results_idx = results['stn_names'].index(stn_name)
                except:
                    results_idx = None
                if results_idx is None:
                    data_empty = []
                    for date in results['dates']:
                        vals_empty = ['M' for el in p['elements']]
                        data_empty.append(vals_empty)

                    results['stn_data'].append(data_empty + data_out['stn_data'][stn_idx])
                    results['stn_errors'].append(data_out['stn_errors'][stn_idx])
                    results['stn_names'].append(data_out['stn_names'][stn_idx])
                    results['stn_ids'].append(data_out['stn_ids'][stn_idx])
                else:
                    results['stn_data'][results_idx] = results['stn_data'][results_idx] + data_out['stn_data'][stn_idx]
                    results['stn_errors'][results_idx] = results['stn_errors'][results_idx] + ', ' + data_out['stn_errors'][stn_idx]

        results['dates']= results['dates'] + data_out['dates']

###################
#M A I N
#####################


#Find all parameter files in /tmp/data_requests,
#Check if results are in
#If so, send to ftp server and notify user,
#If not, check if params file is older than timeout limit,
#If so --> error,
#if not, run data request
results_file_list =[]
params_list= []
error_dict = {} #keys are the user names each entry will be a list two  entries [email, ['error message_list']]
files = filter(os.path.isfile, glob.glob(base_dir + '*_params.json'))
files.sort(key=lambda x: os.path.getmtime(x))
for params_file in files:
    #if file was created less than five minutes ago, it is a new parameter file
    #and we need to run the data request:
    #path = os.path.join(base_dir,fname)
    st=os.stat(params_file)
    mtime=datetime.datetime.fromtimestamp(st.st_mtime)
    try:
        with open(params_file, 'r') as json_f:
            #need unicode converter since json.loads writes unicode
            params = WRCCUtils.u_convert(json.loads(json_f.read()))
    except Exception, e:
        #error handling, write result file with error message
        continue

    user_name, user_email = get_user_info(params)
    #check if results are in
    file_extension, delimiter =  get_file_extension_and_delimiter(params)
    results_file = params_file.rstrip('_params.json') + file_extension
    #sort files into categories: data request needed, results are in, error occurred
    if os.path.isfile(results_file):
        #results are in
        results_file_list.append([params,results_file])
    else:
        params_list.append([params,params_file])
        if mtime > x_mins_ago:
            #File is less than 5 minutes old or has been modified within last x mins
            #need to run data request
            params_list.append([params,params_file])
        elif mtime < time_out_time:
            #data request timed out
            error = 'Data request timed out. Please consider a smaller request.'+ \
            'Parameter File: ' + params_file + \
            '. Your parameters were: %s' %params
            write_error(error_dict, error, user_name, user_email)
            os.remove(params_file)
        else:
            continue

#Upload result files if any and notify user
for param_result_f in results_file_list:
    params_file = param_result_f[1].split('.')[0] + '_params.json'
    upload_error = WRCCUtils.upload(ftp_server, pub_dir, param_result_f[1])
    #upload_error=[]
    user_name = param_result_f[0]['user_name']
    user_email = param_result_f[0]['email']
    if upload_error:
        error = 'Data request: %s. Error while loading to ftp. Error: %s' % (param_result_f[1], str(upload_error))
    else:
        user_name = param_result_f[0]['user_name']
        user_email = param_result_f[0]['email']

        #NOTIFY_USER
        fromaddr = from_address
        toaddr = user_email
        subj = 'Data request %s' % param_result_f[1]
        now = datetime.datetime.now()
        date = now.strftime( '%d/%m/%Y %H:%M' )
        pick_up_latest = (now + datetime.timedelta(days=25)).strftime( '%d/%m/%Y' )
        message_text ='''
        Date: %s
        Your data requests has been processed :-).
        The data is available here:
        %s
        The name of your file is:
        %s
        You can pick up your data until: %s.
        Your parameters were:
        %s
        '''%(date, 'ftp://' + ftp_server  + pub_dir, os.path.split(results_file)[1], str(pick_up_latest), str(params))
        #msg = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( fromaddr, toaddr, subj, date, message_text )
        email_error = WRCCUtils.write_email(mail_server, fromaddr,toaddr,subj, message_text)
        if email_error:
            error =  'Data request: %s. Data on ftp but user email notification failed. Error: %s' % (param_result_f[1], str(email_error))
        else:
            os.remove(param_result_f[1])
            os.remove(params_file)

#Multi process data requests:
num_requests = len(params_list)
#Loop over data requests, split data request and execute as
#celery group job
for idx, req_params_file in enumerate(params_list):
    req_params = req_params_file[0]
    file_extension, delimiter = get_file_extension_and_delimiter(req_params)
    results_file = req_params_file[1].rstrip('_params.json') + file_extension
    elements = req_params['elements']
    if 'select_grid_by' in req_params.keys():request_type ='grid';results = []
    if 'select_station_by' in req_params.keys():request_type ='station';results = {}
    req_params_list = split_data_request(req_params)
    data = group(celery_data_job(params for params in req_params_list)
    for i in range(len(req_params_list)):
        concatenate_results(results, data(i).get, request_type):
    if 'select_grid_by' in req_params.keys():
        save_error = WRCCUtils.write_griddata_to_file(results, elements,delimiter, file_extension, f=results_file)
    if 'select_station_by' in req_params.keys():
        save_error = WRCCUtils.write_station_data_to_file(results['stn_data'], results['dates'],results['stn_names'], results['stn_ids'], elements,delimiter, file_extension,f=results_file, show_flags=params['show_flags'], show_observation_time=params['show_observation_time'])


#Write e-mails to users if needed:
for user_name, err_list in error_dict.iteritems():
        fromaddr = from_address
        toaddr = err_list[0]
        subj = 'Data request Error'
        now = datetime.datetime.now()
        date = now.strftime( '%d/%m/%Y %H:%M' )
        message_text = '''
        The following errors occurred:
        %s
        '''%( str(err_list[1]))
        #msg = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( fromaddr, toaddr, subj, date, message_text )
        error = WRCCUtils.write_email(mail_server, fromaddr,toaddr,subj, message_text)
