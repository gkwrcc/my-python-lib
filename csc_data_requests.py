#!/usr/bin/python

'''
This script run though /tmp/data_requests directory every 5 minutes so see if new data requests by
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
import multiprocessing
from multiprocessing import Queue, JoinableQueue
from time import sleep
import WRCCUtils, AcisWS
import logging

from django.conf import settings

#Settings
nprocs = 4 #number of data requests to be executed in parallel
ftp_server = settings.DRI_FTP_SERVER
mail_server = settings.DRI_MAIL_SERVER
from_address = settings.CSC_FROM_ADDRESS
base_dir = settings.DATA_REQUEST_BASE_DIR
pub_dir = settings.DRI_PUB_DIR

now = datetime.datetime.now()
x_mins_ago = now - datetime.timedelta(minutes=5) #cron job checking for param files runs every 5 minutes
time_out = 3600 #1hr
#time_out = 10800 #time out = 3hrs = 10800 seconds
time_out_time = now - datetime.timedelta(seconds=time_out) #timeout for data request
time_out_h = '1 hour'

#Set up logger
#start new log file for each day:
today = datetime.datetime.today()
day_stamp = '%s%s%s' %(str(today.year), str(today.month), str(today.day))
log_file_test  = 'csc_data_requests_' + day_stamp + '.log'
#Check if we need to create a new log file
#look at most recent log file
log_files = logfiles = sorted([ f for f in os.listdir(base_dir) if f.endswith('.log')])
if not log_files:
    log_file = ''
else:
    log_file = logfiles[-1]
if log_file_test != log_file:
    log_file = log_file_test
logger = logging.getLogger('csc_data_requests')
logger.setLevel(logging.DEBUG)
#Create file and shell handlers
fh = logging.FileHandler(base_dir + log_file)
sh = logging.StreamHandler()
fh.setLevel(logging.DEBUG)
sh.setLevel(logging.DEBUG)
#create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d in %(filename)s - %(message)s')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)
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
    if not s_date or not e_date:
        logger.error('Not a valid daterange: %s - %s' %(s_date, e_date))
    else:
        logger.info('Valid daterange found: %s - %s' %(s_date, e_date))
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
        logger.info('Number of requests: %s' %str(num_requests))
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

def worker(params,params_file,data_q, errors_q):
    if params is None:
        #signal end of processing loop
        data_q.put([None, None, None])
        errors_q.put(None)
        logger.info('End of processing loop signalled')
    else:
        name = multiprocessing.current_process().name
        logger.info('Starting: ' +  str(name))
        logger.info('Parameters: ' +  str(params))

        #Check if we need to split up the data request:
        params_list = split_data_request(params)
        #logger.info('parameters: ' + str(params_list))
        #Determine weather we have station or grid requests
        if 'select_grid_by' in params_list[0].keys():
            data_request = getattr(AcisWS, 'get_grid_data')
            request_type ='grid'
        else:
            data_request = getattr(AcisWS, 'get_station_data')
            request_type = 'station'
        if request_type == 'grid':
            results = []
        else:
            results = {}
        error =  ''
        #Loop over params list, get data, patch results into one dict
        for idx, p in enumerate(params_list):
            logger.info('Executing %s out of %s requests. Params: %s' %(str(idx), str(len(params_list)), str(p)))
            error_out = ''
            if request_type == 'grid':data_out = []
            if request_type == 'station':data_out = {}
            data_out = data_request(dict(p), 'sodlist_web')
            if not data_out:
                logger.info('No data found!')
                error_out = 'Process failed at data request.'
            elif 'error' in data_out.keys():
                logger.info('Error when requesting data. Error: %s.' % (str(data_out['error'])))
                error_out = 'Process failed at data request.'
            elif 'errors' in data_out.keys():
                logger.info('Error when requesting data. Error: %s.' % (str(data_out['errors'])))
                error_out = 'Process failed at data request.'
            if request_type == 'grid':
                try:
                    data_out = WRCCUtils.format_grid_data(data_out, p)
                except:
                    logger.error('Could not format grid data. Parameters: %s ' %str(p))
                    error_out = 'Process %s failed at datta formating. Parameters: %s' %str(p)

            if error_out is not '':
                if error is '':
                    error+=error_out
                else:
                    error = error + ', ' + error_out
            #Add data output to results
            if request_type == 'grid':
                results=results + data_out
            if request_type == 'station':
                if idx == 0:
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
        #Put results in queues
        try:
            errors_q.put(error)
        except:
            logger.error('Cant iput output error into queue.')
        try:
            data_q.put([results,params, params_file])
            logger.info('Putting results in queue.')
        except:
            logger.error('Cant data into queue.')

        if error:
            logger.error('Error occurred during processing. Terminated: ' + str(name))
            logger.error('Error:' + str(error))
            multiprocessing.current_process().terminate
        else:
            logger.info('Ending successfully: ' + str(name))

def proc_runner(params_list):
    procs=[]
    data_q = JoinableQueue()
    errors_q = JoinableQueue()
    #Loop over parameter list and start processes
    for p in range(len(params_list)):
        params = params_list[p][0]
        params_file = params_list[p][1]
        p_name = '%s_out_of_%s' % (str(p+1), len(params_list))
        #start stn_request or grid_request process
        proc = multiprocessing.Process(name=p_name, target=worker,args=(params, params_file, data_q,errors_q,))
        proc.start()
        procs.append(proc)

    #Collect results and write to file
    jobs_gotten = 0
    user_name = 'bdaudert'
    user_email = 'bdaudert@dri.edu'
    while jobs_gotten != len(procs):
        try:
            result= data_q.get()
        except Queue.Empty:
            logger.info('Queue empty!')
            sleep(5)
            continue
        except Exception, e:
            print "Exception:" , e
            continue
        data = result[0]
        params = result[1]
        params_file = result[2]
        jobs_gotten+=1
        data_q.task_done()
        #find delimiter and file_extension from params
        file_extension, delimiter = get_file_extension_and_delimiter(params)
        results_file = params_file.rstrip('_params.json') + file_extension
        if 'elements' in params.keys():
            elements = params['elements']
        else:
            elements = []
        #Write results to file
        #NOTE: not tested after script change 03/02/2014
        if 'select_grid_by' in params.keys():
            logger.info('Retrieved grid results.')
            save_error = write_station_data_to_file(results, params, f=results_file)
            #save_error = WRCCUtils.write_griddata_to_file(data, elements,delimiter, file_extension, f=results_file)
            logger.info('Wrote grid results to file.')
        elif 'select_stations_by' in params.keys():
            logger.info('Retrieved station results.')
            save_error = write_station_data_to_file(data, params, f=results_file)
            #save_error = WRCCUtils.write_station_data_to_file(data['stn_data'], data['dates'],data['stn_names'], data['stn_ids'], elements,delimiter, file_extension,f=results_file, show_flags=params['show_flags'], show_observation_time=params['show_observation_time'])
            logger.info('Wrote station results to file.')
        else:
            save_error = 'Weirdo error. This should never happen.'
            logger.error('Weirdo error. This should never happen.')
        logger.info('Writing to file error:' + str(save_error))
        if save_error:
            error = 'Error when writing data to file. Parameters: %s, Error message: %s' %(params, save_error)
            logger.error('Error when writing data to file. Parameters: ' + str(params) + 'Error message: ' + str(save_error))
            write_error(error_dict, error, user_name, user_email)
        else:
            logger.info('File ' + str(results_file) + ' successfully saved.')


    # Wait for all worker processes to finish
    #within give timeout limit1 hr
    #if process doesn't finish in time, terminate it and send error message
    for p, proc in enumerate(procs):
        logger.info('Joining process: ' +  str(p))
        params = params_list[p][0]
        params_file = params_list[p][1]
        #user_name, user_email = get_user_info(params)
        user_name = 'bdaudert'
        user_email = 'bdaudert@dri.edu'
        p_name = '%s_out_of_%s' % (str(p+1), len(procs))
        proc.join(time_out)
        if proc.is_alive():
            logger.warning('Time out for process ' + str(p_name) + ', parameter file: ' + str(params_file))
            error = 'Data could not be retrieved within timeout limit of %i. Params file ' % (time_out_h, params_file)
            logger.error('Data could not be retrieved within timeout limit of' + time_out_h + ', parameter file: ' + str(params_file))
            write_error(error_dict, error, user_name, user_email)
            proc.terminate()
    #Close the queues!!
    errors_q.close()
    data_q.close()

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
if not files:
    logger.info('No params files found!')
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
        logger.error('Unable to open params file: ' + str(params_file) + 'Errror: ' + str(e))
        continue

    user_name, user_email = get_user_info(params)
    #check if results are in
    file_extension, delimiter =  get_file_extension_and_delimiter(params)
    results_file = params_file.rstrip('_params.json') + file_extension
    #sort files into categories: data request needed, results are in, error occurred
    if os.path.isfile(results_file):
        #results are in
        logger.info('Results found!: ' +  str(results_file))
        results_file_list.append([params,results_file])
    else:
        logger.info('New parameter file found!: ' + str(params_file))
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
            logger.info('Data request in progress for params_file: ' + str(params_file))
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
        logger.error('Data request: ' + str(param_result_f[1]) + '. Error while loading to ftp. Error: '  + str(upload_error))
    else:
        user_name = param_result_f[0]['user_name']
        user_email = param_result_f[0]['email']
        logger.info('File ' + str(param_result_f[1]) + ' successfully upoaded to ftp server. Notifying user.')

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
            logger.error('Data request: ' + str(param_result_f[1]) + 'E-mail error: ' + str(email_error))
        else:
            logger.info('Notified user: ' + str(toaddr) + ' of successful data upload')
            os.remove(param_result_f[1])
            os.remove(params_file)

#Multi process data requests:
num_requests = len(params_list)
if num_requests >0:
    logger.info('Starting to multiprocess data requests.')
    logger.info('Number of requests: ' +  str(num_requests))
else:
    logger.info('Nothing to process.')
loop_no = num_requests / nprocs #number of loops with nprocs processes each to be executed
left_procs = num_requests % nprocs
if left_procs !=0:loop_no+=1
if loop_no > 0:
    logger.info( 'loop number:' + str(loop_no))
if left_procs > 0:
    logger.info('leftover processes' + str(left_procs))
for l in range(loop_no):
    if l == loop_no -1 and left_procs != 0:
        n = left_procs
    else:
        n = nprocs
    start = l*n;end = start + n
    proc_runner(params_list[start:end])

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
        if error:
            logger.error('Email error when notifying: ' + str(toaddr) + ' Error: ' + str(error))
        else:
            logger.info('Notified user ' + str(toaddr) +  ' of data errors.')
