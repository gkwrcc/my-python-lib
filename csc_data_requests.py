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
import multiprocessing
from multiprocessing import Queue

import WRCCUtils, AcisWS

############
#hard codes:
#############
nprocs = 4 #number of data requests to be executed in parallel
ftp_server = 'pubfiles.dri.edu'
mail_server = 'owa.dri.edu'
from_address = 'csc-project@dri.edu'
base_dir = '/tmp/data_requests/'
pub_dir = '/pub/csc/test/'
#pipe errors to file
original_stderr = sys.stderr
f_err = open('/tmp/data_requests/data-request-stderr.txt', 'w+')
sys.stderr = f_err

now = datetime.datetime.now()
x_mins_ago = now - datetime.timedelta(minutes=5) #cron job checking for param files runs every 5 minutes
time_out = now - datetime.timedelta(hours=1) #timeout for data request
time_out_human = '1 hour'
##############
#Functions
###############
def worker_stn(params, stn_data_q,errors_q):
    name = multiprocessing.current_process().name
    error = None
    print "Starting:", name
    print "Parameters: ", params
    #Loop over parameter list and request data for each item in list
    try:
        stn_data_out = AcisWS.get_point_data(dict(params),'sodlist_web')
    except:
        stn_data_out = {}
        error = 'Process %s failed at data request. System info: %s' %(name, sys.exc_info())
    #Put results in queues
    stn_data_q.put(stn_data_out)
    if error:
        errors_q.put(error)
        print 'Error occurred during. Terminated: ', name
        multiprocessing.current_process().terminate
    else:
        errors_q.put('')
        print 'Ending successfully: ', name

def worker_grid(params, grid_data_q, errors_q):
    error = None
    name = multiprocessing.current_process().name
    print "Starting:", name
    print "Parameters: ", params
    #Loop over parameter list and request data for each item in list
    try:
        request = AcisWS.get_grid_data(dict(params),'sodlist_web')
        try:
            grid_data_out = WRCCUtils.format_grid_data(request, params)
        except:
            grid_data_out = {}
            error = 'Process %s failed at data request formatting. System info: %s' %(name, sys.exc_info())
    except:
        grid_data_out = {}
        error = 'Process %s failed at data request. System info: %s' %(name, sys.exc_info())

    #Put results in queues
    grid_data_q.put(grid_data_out)
    if error:
        errors_q.put(error)
        print 'Error occurred during. Terminated: ', name
        multiprocessing.current_process().terminate
    else:
        errors_q.put('')
        print 'Ending successfully: ', name


def write_error(error_dict, error, user_name, user_email):
    if 'user_name' in error_dict.keys():
        error_dict['user_name'][1].append(error)
    else:
        errror_dict['user_name'] = [user_email, [error]]

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
error_dict = {} #keys are the user names each entry will be a list two  entres [email, ['error message_list']]
files = filter(os.path.isfile, glob.glob(base_dir + '*_params.json'))
files.sort(key=lambda x: os.path.getmtime(x))
for params_file in files:
    print params_file
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
        print str(e)
        print 'Unable to open params file %s . Moving on to next file.' % params_file
        print >> sys.stderr,'Unable to open params file %s . Moving on to next file.' % params_file
        print >> sys.stderr, str(e)
        continue

    user_name, user_email = get_user_info(params)
    #check if results are in
    if 'data_format' in params.keys():
        if params['data_format'] == 'html':file_extension = 'txt'
        if params['data_format'] == 'clm':file_extension = 'txt'
        if params['data_format'] == 'json':file_extension = 'json'
        if params['data_format'] == 'dlm':file_extension = 'dat'
        if params['data_format'] == 'xl':file_extension = 'xls'
    else:
        file_extension = 'txt'

    results_file = params_file.rstrip('_params.json') + '.' + file_extension
    #sort files into categories: data request needed, results are in, error occurred
    if os.path.isfile(results_file):
        #results are in
        results_file_list.append([params,results_file])
    else:
        if mtime > x_mins_ago:
            #File is less than 5 minutes old or has been modified within last x mins
            #need to run data request
            params_list.append([params,params_file])
        elif mtime < time_out:
            #data request timed out
            error = 'Data request timed out. Please consider a smaller request.'+ \
            'Your parameters were: %s' %params
            write_error(error_dict, error, user_name, user_email)
        else:
            print 'Data request in progress for params_file %s' % params_file
            continue


'''
#Upload result files if any and notify user
for param_result_f in results_file_list:
    upload_error = WRCCUtils.upload(ftp_server, pub_dir, param_result_f[1])
    user_name = param_result_f[0]['user_name']
    user_email = param_result_f[0]['email']
    if upload_error:
        error = 'Data request: %s. Error while loading to ftp. Error: %s' % (param_result_f[1], str(upload_error))
        print >> sys.stderr, error
    else:
        user_name = param_result_f[0]['user_name']
        user_email = param_result_f[0]['email']
        print 'File %s successfully upoaded to ftp server. Notifying user' % param_result_f[1]

        #NOTIFY_USER
        fromaddr = from_address
        toaddr = user_email
        subj = 'Data request %s' % param_result_f[1]
        now = datetime.datetime.now()
        date = now.strftime( '%d/%m/%Y %H:%M' )
        pick_up_latest = (now + datetime.timedelta(days=25)).strftime( '%d/%m/%Y' )
        message_text = 'Your data requests has been processed :-).\nThe data is available at ftp://' + \
        ftp_server  + pub_dir + \
        ' The name of your file is:' + os.path.split(results_file)[1] + \
        '\nYou can pick up your data until: ' + str(pick_up_latest) + '.\nYour parameters were:' + str(params)
        msg = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( fromaddr, toaddr, subj, date, message_text )
        email_error = WRCCUtils.write_email(mail_server, fromaddr,toaddr,msg)
        if email_error:
            error =  'Data request: %s. Data on ftp but user email notification failed. Error: %s' % (param_result_f[1], str(email_error))
            print >> sys.stderr, error
        else:
            print 'Notified user %s' % toaddr
            #os.remove(params_file)
            #os.remove(results_file)
'''

#Multi process stn data requests:
num_requests = len(params_list)
loop_no = num_requests / nprocs #number of loops with nprocs processes each to be executed
left_procs = num_requests % nprocs
if left_procs !=0:loop_no+=1
for l in range(loop_no):
    stn_data_q = Queue();stn_errors_q=Queue()
    grid_data_q = Queue();grid_errors_q = Queue()
    procs = []
    proc_errors = []
    if l < len(loop_no) -1 and left_procs != 0:
        n = lef_procs
    else:
        n = nprocs
    for p in range(n):
        idx =l*nprocs + p
        params = params_list[idx][0]
        params_file = params_list[idx][1]
        user_name, user_email = get_user_info(params)
        p_name = '%s_out_of_%s' % (str(idx+1), loop_no*nprocs)
        #start stn_request or grid_request process
        if not 'select_grid_by' in params.keys() and not 'select_stations_by' in params.keys():
            error = 'Invalid parameter file %s. Need select_grid_by or select_stations_by parameter. Params: %s' % (params_file, str(params))
            write_error(error_dict, error, user_name, user_email)
            print >> sys.stderr, error
            continue

        if 'select_grid_by' in params.keys():
            proc = multiprocessing.Process(name=p_name, target=worker_grid,args=(params,grid_data_q, grid_errors_q))
        else:
            proc = multiprocessing.Process(name=p_name, target=worker_stn,args=(params,stn_data_q, stn_errors_q))
        procs.append(proc)
        proc.start()

    for p in range(n):
        idx =l*nprocs + p
        params = params_list[idx][0]
        params_file = params_list[idx][1]
        user_name, user_email = get_user_info(params)
        p_name = '%s_out_of_%s' % (str(idx+1), loop_no*nprocs)
        #find delimiter and file_extension from params
        if 'data_format' in params.keys():
            if params['data_format'] == 'html':file_extension = 'txt'
            if params['data_format'] == 'clm':file_extension = 'txt'
            if params['data_format'] == 'json':file_extension = 'json'
            if params['data_format'] == 'dlm':file_extension = 'dat'
            if params['data_format'] == 'xl':file_extension = 'xls'
        else:
            file_extension = 'txt'

        if 'delimiter' in params.keys():
            if params['delimiter'] == 'comma':delimiter = ','
            if params['delimiter'] == 'tab':delimiter = '  '
            if params['delimiter'] == 'colon':delimiter = ':'
            if params['delimiter'] == 'space':delimiter = ' '
            if params['delimiter'] == 'pipe':delimiter = '|'
        else:
            delimiter = ' '
        if 'data_format' in params.keys():
            if params['data_format'] == 'html':file_extension = 'txt'
            if params['data_format'] == 'clm':file_extension = 'txt'
            if params['data_format'] == 'json':file_extension = 'json'
            if params['data_format'] == 'dlm':file_extension = 'dat'
            if params['data_format'] == 'xl':file_extension = 'xls'
        else:
            file_extension = 'txt'

        if 'elements' in params.keys():
            elements = params['elements']
        else:
            elements = []

        if request_type_list[idx] =='grid':
            grid_data = grid_data_q.get();errs = grid_errors_q.get()
            if errs:
                save_error = 'Error during data request: %s. Error: %s' % (results_file, str(errs))
            else:
                save_error = WRCCUtils.write_griddata_to_file(grid_data, elements,delimiter, file_extension, f=results_file)
        elif request_type_list[idx] =='stn':
            stn_data = stn_data_q.get();errs = stn_errors_q.get()
            if errs:
                save_error = 'Error during data request: %s. Error: %s' % (results_file, str(errs))
            else:
                save_error = WRCCUtils.write_point_data_to_file(datadict, dates_dict, stn_names_dict, stn_ids_dict, elements,delimiter, file_extension,f=results_file)
        else:
            save_error = 'Weirdo error. This should never happen.'

        if save_error:
            error = 'Error when writing data to file. Parameter file: %s, Error message: %s' %(params_list[idx][1], save_error)
            print >> sys.stderr, error
            write_error(error_dict, error, user_name, user_email)
        else:
            print 'File %s successfully saved.' %results_file

        # Wait for all worker processes to finish
        #within give timeout limit 10 minutes
        #if process doesn't finish in time, terminate it and send error message
        for p in procs:
            idx =l*nprocs + p
            params = params_list[idx][0]
            params_file = params_list[idx][1]
            user_name, user_email = get_user_info(params)
            p_name = '%s_out_of_%s' % (str(idx+1), loop_no*nprocs)
            p.join(time_out)
            if proc.is_alive():
                error = 'Data could not be retrieved within timeout limit of %i. Params file ' % (time_out_h, params_file)
                print >> sys.stderr, save_error
                write_error(error_dict, error, user_name, user_email)
                proc.terminate()

#Write e-mails to users if needed:
for user_name, err_list in error_dict.iteritems():
        fromaddr = from_address
        toaddr = err_list[0]
        subj = 'Data request Error'
        now = datetime.datetime.now()
        date = now.strftime( '%d/%m/%Y %H:%M' )
        message_text = 'The following errors occurred:' + (err for err in err_list[1])
        msg = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( fromaddr, toaddr, subj, date, message_text )
        error = WRCCUtils.write_email(mail_server, fromaddr,toaddr,msg)
        if error:
            print >> sys.stderr, error
        else:
            print 'Notified user %s of data errors.' % toaddr


##########################
#Final Check for errors:
errs = sys.stderr.read()
if errs:
    #Notify me of error
    fromaddr = 'bdaudert@dri.edu'
    toaddr = 'bdaudert@dri.edu'
    subj = 'Data request errors'
    now = datetime.datetime.now()
    date = now.strftime( '%d/%m/%Y %H:%M' )
    message_text = 'Data request error!!\n File:' + params_file + '\n Params: ' + str(params) + \
    '\n System errors' + str(errs)
    msg = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( fromaddr, toaddr, subj, date, message_text )
    error = WRCCUtils.write_email(mail_server, fromaddr,toaddr,msg)
    if error:
        print >> sys.stderr, error
    else:
        print 'Notified bdaudert at  %s of data request error' % toaddr

##################################
sys.stderr = original_stderr
f_err.close()
