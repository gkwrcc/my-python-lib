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
    day_stamp = '%s%s%s' %(str(today.year), str(today.month), str(today.day))
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
    return logger

def get_params_files(base_dir):
    #Look for user parameter files in base_dir
    params_files = filter(os.path.isfile, glob.glob(base_dir + settings.PARAMS_FILE_EXTENSION))
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
    keys = ['elems_long','units', 'start_date', 'end_date','date_format', 'data_format']
    if 'select_stations_by' in params.keys():
        for k in ['show_flags', 'show_observation_time']:
            keys.append(k)
    else:
        for k in ['grid', 'data_summary']:
            keys.append(k)

    display_params = ''
    for key, val in params.iteritems():
        if key in  ['select_grid_by', 'select_stations_by']:
            display_params = WRCCData.DISPLAY_PARAMS[params[key]] + ': ' + params[params[key]] + ', '+ display_params

        if key in keys:
            if  key == 'elems_long':
                display_params+=WRCCData.DISPLAY_PARAMS[key] + ': '+  ','.join(params[key]) + ', '
            elif key == 'date_format':
                display_params+=WRCCData.DISPLAY_PARAMS[key] + ': '+ WRCCData.DATE_FORMAT[params[key]]  + ', '
            elif key == 'data_format':
                display_params+=WRCCData.DISPLAY_PARAMS[key] + ': '+ WRCCData.DATA_FORMATS[params[key]]  + ', '
            else:
                display_params+=WRCCData.DISPLAY_PARAMS[key] + ': '+  str(params[key]) + ', '
                if key == 'data_summary' and params[key] != 'none':
                    ds = params[key] + '_summary'
                    try:
                        display_params+=WRCCData.DISPLAY_PARAMS[ds] + ': ' + WRCCData.DISPLAY_PARAMS[params[ds]] + ', '
                    except:
                        pass
    return display_params

def get_user_info(params):
    if 'user_name' in params.keys():user_name = params['user_name']
    else : user_name = 'bdaudert'
    if 'email' in params.keys():user_email = params['email']
    else : user_email = 'bdaudert@dri.edu'
    return user_name, user_email


def compose_email(params, ftp_server, output_file_path):
        #NOTIFY_USER
        mail_server = settings.DRI_MAIL_SERVER
        fromaddr = settings.CSC_FROM_ADDRESS
        user_name, user_email = get_user_info(params)
        subj = 'Data request %s' % os.path.basename(output_file_path)
        now = datetime.datetime.now()
        date = now.strftime( '%d/%m/%Y %H:%M' )
        pick_up_latest = (now + datetime.timedelta(days=25)).strftime( '%d/%m/%Y' )
        display_params = get_display_params(params)
        message_text ='''
        Date: %s
        Dear %s
        Your data requests has been processed :-).
        The data is available here:
        %s
        The name of your file is:
        %s
        You can pick up your data until: %s.
        Your parameters were:
        %s
        '''%(date, user_name,'ftp://' + ftp_server + output_file_path, os.path.basename(output_file_path),str(pick_up_latest), display_params)
        return subj, message_text

def delete_params_file(params_file):
    try:
        os.remove(params_file)
    except:
        pass

if __name__ == '__main__' :

    #Set statics
    base_dir = settings.DATA_REQUEST_BASE_DIR
    params_file_extension = settings.PARAMS_FILE_EXTENSION
    ftp_server = settings.DRI_FTP_SERVER
    ftp_dir = settings.DRI_PUB_DIR
    mail_server = settings.DRI_MAIL_SERVER
    fromaddr = settings.CSC_FROM_ADDRESS

    #Set timers
    cron_job_time = settings.CRON_JOB_TIME
    now = now = datetime.datetime.now()
    x_mins_ago = now - datetime.timedelta(minutes=cron_job_time)

    #Start Logging
    logger = start_logger(base_dir)

    #Get list ofparameter files
    params_files = get_params_files(base_dir)
    if not params_files:logger.info('No parameter files found! Exiting program.');sys.exit(0)

    #Loop over parameter files, get data, format and write to ftp server, notify user
    for params_file in params_files:
        time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        params = WRCCUtils.load_json_data_from_file(params_file)
        if not params:
            logger.error('Cannot read parameter file: %s! Exiting program.' %os.path.basename(params_file))
            sys.exit(1)
        logger.info('Parameter file: %s' % os.path.basename(params_file))
        logger.info('Parameters: %s' % str(params))
        #Check if params file is older than
        #cron job time --> data request completed or in progress

        #Check if request in progress
        #st=os.stat(params_file)
        #mtime=datetime.datetime.fromtimestamp(st.st_mtime)
        #if mtime <= x_mins_ago:
        #    logger.info('Data request for parameter file %s is in progress' %str(os.path.basename(params_file)))
        #    continue

        #Avoid naming conflicts of output file names--timestamp will be attached
        out_file = set_output_file(params, base_dir, time_stamp)

        #Define and instantiate data request class
        if 'select_stations_by' in params.keys():
            LDR = WRCCClasses.LargeStationDataRequest(params,logger)
        elif 'select_grid_by' in params.keys():
            LDR = WRCCClasses.LargeGridDataRequest(params,logger)
        #Request Data
        logger.info('Requesting data')
        LDR.get_data()
        logger.info('Data obtained')
        #check that results of data request are valid
        if not 'data' in LDR.request.keys() or 'error' in LDR.request.keys():
            logger.error('No data found for parameter file: %s! Exiting program.' %os.path.basename(params_file))
            continue
        #Format data and write to file
        LDR.format_data_and_write_to_file(out_file)
        logger.info('Large Data Request completed. Parameter file was: %s' %str(os.path.basename(params_file)))
        #Check that out_file exists and is non-empty
        error = check_output_file(out_file)
        if error:
            logger.error('ERROR writing data to file. Parameter file: %s. Error %s' %(os.path.basename(params_file),error))
            continue
        #Transfer data to FTP server
        FTP = WRCCClasses.FTPClass(ftp_server, ftp_dir, out_file, logger)
        error = FTP.FTPUpload()
        if error:
            logger.error('ERROR tranferring %s to ftp server. Error %s' %(os.path.basename(params_file),error))
            continue
        #Notify User
        subject, message = compose_email(params, ftp_server, out_file)
        user_name, user_email = get_user_info(params)
        MAIL = WRCCClasses.Mail(mail_server,fromaddr,user_email,subject, message,logger)
        error = MAIL.write_email()
        if error:
            logger.error('ERROR notifying user %s Error %s' %(user_email,error))
            continue

