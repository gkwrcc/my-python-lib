#!/usr/bin/python
'''
Script to run soddyrec in background
Loops over all US COOP stations found in ACIS that have data,
computes Soddyrec statistics and writes resulting
text output to file.
Output file format dddddd.rec
where dddddd is the 6 digit coop id
Currently all files are written to /tmp
'''
import AcisWS, WRCCWrappers, WRCCUtils
import datetime
import logging
import os, glob, sys

base_dir = '/tmp/'


def get_US_station_meta():
    #params = {"bbox":"-170,30,60,-90","meta":"name,sids,valid_daterange","elems":"maxt,pcpn,mint,snow,snwd"}
    params = {
        "bbox":"-177.1,13.71,-61.48,76.63",
        "meta":"name,state,sids,valid_daterange",
        "elems":"maxt,pcpn,mint,snow,snwd"
    }
    try:
        req = AcisWS.StnMeta(params)
    except Exception, e:
        logger.error('ACIS meta request returned error: %s' %str(e))
        return {'meta':[]}
    if not 'meta' in req.keys():
        logger.error('ACIS meta request did not return metadata.')
        return {'meta':[]}
    return req

def has_data(stn_meta):
    if not 'valid_daterange' in stn_meta.keys():
        return False
    for dr in stn_meta['valid_daterange']:
        if dr:
            #We found a non empty daterange
            return True
    return False

def valid_COOP_station(stn_meta):
    '''
    Check if station is belonging
    to coop network and has data
    '''
    if not 'sids' in stn_meta.keys():
        return False
    for sid in stn_meta['sids']:
        sid_split = sid.split(' ')
        if str(sid_split[1]) == '2':
            #We found a coop station
            #Check if station has data
            if has_data(stn_meta):
                return True
    return False

def get_coop_id(stn_meta):
    stn_id = ''
    if not 'sids' in stn_meta.keys():
        return stn_id
    for sid in stn_meta['sids']:
        sid_split = sid.split(' ')
        if str(sid_split[1]) == '2':
            stn_id = str(sid_split[0])
            return stn_id
    return stn_id

def set_wrapper_params(stn_id):
    yesterday = WRCCUtils.set_back_date(1)
    w_params = [stn_id, 'all','18000101',yesterday,'txt']
    return w_params

if __name__ == "__main__":
    #Start logger
    time_stamp = datetime.datetime.now().strftime('%Y%m_%d_%H_%M_%S')
    logger = logging.getLogger('soddyrec_generator')
    logger_file = time_stamp + '_' + 'soddyrec.log'
    logger.setLevel(logging.DEBUG)
    #Delete old log files
    old_files = filter(os.path.isfile, glob.glob(base_dir + '*' + 'soddyec.log'))
    for old in old_files:
        if os.path.isfile(base_dir + old):
            try:
                os.remove(base_dir + old)
            except:
                pass
    fh = logging.FileHandler(base_dir + logger_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d in %(filename)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Retrieving metadata')
    USMeta = get_US_station_meta()
    logger.info('metadata retrieved successfully!')
    #Loop over USMeta stations
    count = 0
    if not USMeta['meta']:
        logger.error('No metadata could be retrieved.Exiting program.')
        sys.exit(1)
    for stn_meta in USMeta['meta']:
        if not valid_COOP_station(stn_meta):
            continue
        count+=1
        stn_id = get_coop_id(stn_meta)
        state = str(stn_meta['state']).lower()
        try:
            os.stat(base_dir + state)
        except:
            os.mkdir(base_dir + state)
        out_file_name = base_dir + state + '/' + str(stn_id) + '.rec'
        w_params = set_wrapper_params(stn_id)
        #Execute wrapper
        try:
            logger.info('Starting soddyrec for station %s' %str(stn_id))
            WRCCWrappers.run_soddyrec(w_params, output_file = out_file_name)
            logger.info('Writing data to file: %s' %out_file_name)
        except:
            continue
