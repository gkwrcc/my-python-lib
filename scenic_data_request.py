#!/usr/bin/python

import sys, os, datetime, glob
import my_acis.settings as settings

import WRCCClasses, WRCCUtils

'''
scenic_data_request.py
required input argument:
base_dir -- directory on server that contains user parameter files
'''

if __name__ == '__main__' :

    base_dir = settings.DATA_REQUEST_BASE_DIR
    params_file_extension = settings.PARAMS_FILE_EXTENSION
    #Set timers
    cron_job_time = settings.CRON_JOB_TIME
    now = now = datetime.datetime.now()
    x_mins_ago = now - datetime.timedelta(minutes=cron_job_time)
    #Set up logger
    #start new log file for each day:
    today = datetime.datetime.today()
    day_stamp = '%s%s%s' %(str(today.year), str(today.month), str(today.day))
    log_file_test  = 'scenic_data_requests_' + day_stamp + '.log'
    #Check if we need to create a new log file
    #look at most recent log file
    log_files = logfiles = sorted([ f for f in os.listdir(base_dir) if f.endswith('.log')])
    if not log_files:log_file_name = ''
    else:log_file_name = log_files[-1]
    if log_file_test != log_file_name:log_file_name = log_file_test

    #Start Logging
    Logger = WRCCClasses.Logger(base_dir, log_file_name, 'scenic_data_request')
    logger = Logger.start_logger()

    #Look for user parameter files in base_dir
    params_files = filter(os.path.isfile, glob.glob(base_dir + settings.PARAMS_FILE_EXTENSION))
    params_files.sort(key=lambda x: os.path.getmtime(x))
    if not params_files:logger.info('No parameter files found! Exiting program.');sys.exit(0)
    #Loop over parameter files and get data
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
        '''
        #Check if request in progress
        st=os.stat(params_file)
        mtime=datetime.datetime.fromtimestamp(st.st_mtime)
        if mtime <= x_mins_ago:
            logger.info('Data request for parameter file %s is in progress' %str(os.path.basename(params_file)))
            continue
        '''

        #Avoid naming conflicts of output file names--timestamp will be attached
        out_file_name = params['output_file_name']
        temp_out_file = base_dir + out_file_name + '_' + time_stamp
        if 'select_stations_by' in params.keys():
            LDR = WRCCClasses.LargeStationDataRequest(params,logger)
        elif 'select_grid_by' in params.keys():
            LDR = WRCCClasses.LargeGridDataRequest(params,logger)
        #params_list = LDR.split_data_request()
        logger.info('Requesting data')
        LDR.get_data()
        logger.info('Data obtained')
        LDR.format_data_and_write_to_file(temp_out_file)
        logger.info('Large Data Request completed. Parameter file was: %s' %str(os.path.basename(params_file)))

        #Transfer data to FTP server
        #Notify User
