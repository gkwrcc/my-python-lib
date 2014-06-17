#!/usr/bin/python

import sys, os, datetime, glob
import my_acis.settings as settings

import WRCCClasses, WRCCUtils, WRCCData

'''
scenic_data_request.py
required input argument:
base_dir -- directory on server that contains user parameter files
'''

def start_logger(base_dir):
    #Set up Logging
    #Start new log file for each day:
    today = datetime.datetime.today()
    day_stamp = WRCCUtils.datetime_to_date(today,'')
    #day_stamp = '%s%s%s' %(str(today.year), str(today.month), str(today.day))
    log_file_test  = 'scenic_data_requests_' + day_stamp + '.log'
    #Check if we need to create a new log file
    #Look at most recent log file
    log_files = sorted([ f for f in os.listdir(base_dir) if f.endswith('.log')])
    if not log_files:log_file_name = ''
    else:log_file_name = log_files[-1]
    if log_file_test != log_file_name:log_file_name = log_file_test
    #Start Logging
    LOGGER = WRCCClasses.Logger(base_dir, log_file_name, 'scenic_data_request')
    logger = LOGGER.start_logger()
    return logger, log_file_name

def get_params_files(base_dir):
    #Look for user parameter files in base_dir
    params_files = filter(os.path.isfile, glob.glob(base_dir + '*' + settings.PARAMS_FILE_EXTENSION))
    params_files.sort(key=lambda x: os.path.getmtime(x))
    return params_files

def set_output_file(params,base_dir, time_stamp):
    #Avoid naming conflicts of output file names--timestamp will be attached
    out_file_name = params['output_file_name']
    file_extension = WRCCData.FILE_EXTENSIONS[params['data_format']]
    if file_extension == '.html':file_extension = '.txt'
    out_file = base_dir + out_file_name + '_' + time_stamp + file_extension
    return out_file

def check_output_file(out_file):
    try:
        if os.stat(out_file).st_size > 0:
            return None
        else:
            return 'Empty file.'
    except OSError:
        return 'No file found.'

def get_display_params(params):
    keys = ['elements','units', 'start_date', 'end_date','date_format', 'data_format']
    if 'select_stations_by' in params.keys():
        #keys.insert(0, 'select_stations_by')
        for k in ['show_flags', 'show_observation_time']:
            keys.append(k)
    else:
        #keys.insert(0, 'select_grid_by')
        for k in ['grid', 'data_summary']:
            keys.append(k)

    display_params = ['' for key in keys]

    for idx, ky in enumerate(keys):
        key = ky;val = ''
        if key in params.keys():val = params[key]
        if  key == 'elements':
            elems_long = ''
            el_list = params['elements'].replace(' ', '').split(',')
            for el_idx, el in enumerate(el_list):
                elems_long+= WRCCData.DISPLAY_PARAMS[el]
                if el_idx < len(el_list):
                    elems_long+= ', '
            display_params[idx] = 'Elements: ' + elems_long
        elif key in ['date_format']:
            df = WRCCData.DATE_FORMAT[params[key]]
            d = 'yyyy' + df + 'mm' + df + 'dd'
            if 'temporal_resolution' in params.keys():
                if params['temporal_resolution'] == 'mly':d = df.join(d.split(df)[0:2])
                if params['temporal_resolution'] == 'yly':d = df.join(d.split(df)[0])
            display_params[idx] = WRCCData.DISPLAY_PARAMS[key] + ': ' + d
        elif key in ['data_format']:
            display_params[idx] = WRCCData.DISPLAY_PARAMS[key] + ': '+ WRCCData.DATA_FORMAT[params[key]]
        elif key in ['show_observation_time', 'show_flags','data_summary']:
            if key == 'data_summary' and params[key] != 'none':k = params[key] + '_summary'
            else:k=key
            display_params[idx] = WRCCData.DISPLAY_PARAMS[k] + ': ' + WRCCData.DISPLAY_PARAMS[params[k]]
        elif key == 'grid':
            display_params[idx] = WRCCData.DISPLAY_PARAMS[key] + ': '+ WRCCData.GRID_CHOICES[params[key]][0]
        else:
            display_params[idx] = WRCCData.DISPLAY_PARAMS[key] + ': ' + params[key]
    if 'select_grid_by' in params.keys():
        display_params.insert(0, WRCCData.DISPLAY_PARAMS[params['select_grid_by']] + ': ' + params[params['select_grid_by']])
        display_params.insert(0, WRCCData.DISPLAY_PARAMS['select_grid_by'])
    elif 'select_stations_by' in params.keys():
        display_params.insert(0, WRCCData.DISPLAY_PARAMS[params['select_stations_by']] + ': ' + params[params['select_stations_by']])
        display_params.insert(0, WRCCData.DISPLAY_PARAMS['select_stations_by'])
    return display_params

def get_user_info(params):
    if 'user_name' in params.keys():user_name = params['user_name']
    else : user_name = 'bdaudert'
    if 'user_email' in params.keys():user_email = params['user_email']
    else : user_email = 'bdaudert@dri.edu'
    return user_name, user_email


def compose_email(params, ftp_server, ftp_dir, out_files):
        #NOTIFY_USER
        mail_server = settings.DRI_MAIL_SERVER
        fromaddr = settings.CSC_FROM_ADDRESS
        user_name, user_email = get_user_info(params)
        subj = 'Data request %s' % params['output_file_name']
        now = datetime.datetime.now()
        date = now.strftime( '%d/%m/%Y %H:%M' )
        pick_up_latest = (now + datetime.timedelta(days=25)).strftime( '%d/%m/%Y' )
        display_params = get_display_params(params)
        dp = '';files=''
        for line in display_params:
            dp+=line +'\n' + '      '
        for f in out_files:
            files+= f + '\n' + '      '
        message_text ='''
        Date: %s
        Dear %s,
        Your data requests has been processed :-).

        The data is available here:
        %s

        The file names/file sizes are:
        %s

        You can pick up your data until: %s.

        Your parameters were:

        %s
        '''%(date, user_name,'ftp://' + ftp_server + ftp_dir, files,str(pick_up_latest), dp)
        return subj, message_text

def compose_failed_request_email(params_files_failed, log_file):
    mail_server = settings.DRI_MAIL_SERVER
    fromaddr = settings.CSC_FROM_ADDRESS
    name= 'Britta Daudert'
    email = 'bdaudert@dri.edu'
    subj = 'Failed data requests'
    now = datetime.datetime.now()
    date = now.strftime( '%d/%m/%Y %H:%M' )
    message='''
        Date: %s
        Dear Me,
        Following data requests have failed:
        %s
        Please consult logfile:
        %s
        '''%(date,','.join(params_files_failed), log_file)
    return subj, message

#############
#M A I N
###############

if __name__ == '__main__' :

    #os.remove('/tmp/data_requests/GridNVTwoYr_params.json')
    #Set statics
    base_dir = settings.DATA_REQUEST_BASE_DIR
    params_file_extension = settings.PARAMS_FILE_EXTENSION
    ftp_server = settings.DRI_FTP_SERVER
    mail_server = settings.DRI_MAIL_SERVER
    fromaddr = settings.CSC_FROM_ADDRESS
    max_file_size = settings.MAX_FILE_SIZE
    #Set timers
    cron_job_time = settings.CRON_JOB_TIME
    now = now = datetime.datetime.now()
    x_mins_ago = now - datetime.timedelta(minutes=cron_job_time)
    d = 60*24
    one_day_ago = now - datetime.timedelta(minutes=d)
    #Start Logging
    logger, log_file_name = start_logger(base_dir)

    #Get list ofparameter files
    params_files = get_params_files(base_dir)
    if not params_files:
        logger.info('No parameter files found! Exiting program.')
        sys.exit(0)
    logger.info('Found %s parameter files.' %str(len(params_files)))
    #Loop over parameter files, get data, format and write to ftp server, notify user
    params_files_failed = []
    for params_file in params_files:
        time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        params = WRCCUtils.load_json_data_from_file(params_file)
        #Extra directory for each request
        ftp_dir = settings.DRI_PUB_DIR + params['output_file_name'].replace(' ','')
        if not params:
            logger.error('Cannot read parameter file: %s! Exiting program.' %os.path.basename(params_file))
            params_files_failed.append(params_file)
            sys.exit(1)
        logger.info('Parameter file: %s' % os.path.basename(params_file))
        logger.info('Parameters: %s' % str(params))
        #Check if params file is older than
        #cron job time --> data request completed or in progress
        #Check if request in progress
        st=os.stat(params_file)
        mtime=datetime.datetime.fromtimestamp(st.st_mtime)
        if mtime <= x_mins_ago:
            logger.info('Data request for parameter file %s is in progress' %str(os.path.basename(params_file)))
            if mtime <= one_day_ago:
                os.remove(params_file)
            continue
        #Define and instantiate data request class
        LDR = WRCCClasses.LargeDataRequest(params,logger)
        #Request Data
        logger.info('Requesting data')
        LDR.get_data()
        logger.info('Data obtained')
        #check that results of data request are valid
        if 'error' in LDR.request.keys():
            logger.error('Data request error: %s! Parameter file: %s' %( LDR.request['error'],os.path.basename(params_file)))
            params_files_failed.append(params_file)
            os.remove(params_file)
            continue
        if not 'data' in LDR.request.keys() and not 'smry' in LDR.request.keys():
            logger.error('No data found! Parameter file: %s' %( os.path.basename(params_file)))
            params_files_failed.append(params_file)
            os.remove(params_file)
            continue
        #Format data and write to file
        #Avoid naming conflicts of output file names--timestamp will be attached
        out_file = set_output_file(params, base_dir, time_stamp)
        out_files = LDR.format_write_transfer(params_file,params_files_failed,out_file, ftp_server, ftp_dir,max_file_size,logger)
        logger.info('Large Data Request completed. Parameter file was: %s' %str(os.path.basename(params_file)))
        #Check that out_file exists and is non-empty
        if not out_files:
            logger.error('ERROR: No output files were generated. Parameter file: %s.' %(os.path.basename(params_file)))
            params_files_failed.append(params_file)
            os.remove(params_file)
            continue
        #Notify User
        subject, message = compose_email(params, ftp_server, ftp_dir,out_files)
        user_name, user_email = get_user_info(params)
        MAIL = WRCCClasses.Mail(mail_server,fromaddr,user_email,subject, message,logger)
        error = MAIL.write_email()
        if error:
            logger.error('ERROR notifying user %s Error: %s' %(user_email,error))
            params_files_failed.append(params_file)
            os.remove(params_file)
            continue
        #Remove parameter file
        os.remove(params_file)

    #Check for failed requests
    if params_files_failed:
        #Send emal to me
        subject, message = compose_failed_request_email(params_files_failed, log_file_name)
        EMAIL = WRCCClasses.Mail(mail_server,fromaddr,'bdaudert@dri.edu',subject, message,logger)
        error = EMAIL.write_email()
        if error:
            logger.error('ERROR notifying ME %s Error: %s' %(user_email,error))
