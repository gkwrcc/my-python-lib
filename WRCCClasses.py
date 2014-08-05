#!/usr/bin/python
'''
module WRCCClasses.py
Defines classes used in the my_acis project
'''

##############################################################################
# import modules required by Acis
#import  pprint, time
import time, re, os
import json
from cStringIO import StringIO
import cairo
import base64
import datetime
import csv
from xlwt import Workbook
import logging
from ftplib import FTP
import smtplib
import gzip

#Django
from django.http import HttpResponse
#Settings
#from django.conf import settings
import my_acis.settings as settings

#WRCC modules
import AcisWS, WRCCDataApps, WRCCUtils, WRCCData



class DownloadDataJob(object):
    '''
    Download data to excel, .dat or .txt

    Keyword arguments:
    app_name         --  Application name, one of the following
                         Sodsumm, Sodsum, Sodxtrmts,Soddyrec,Sodpiii, Soddynorm,
                         Sodrun, Soddd, Sodpct, Sodpad, Sodthr
    data_fomat       --  One of dlm (.dat), clm (.txt), xl (.xls)
    delimiter        --  Delimiter separating the data values. One of:
                         space, tab, comma, colon, pipe
    json_in_file     --  Abs path to  file containing the data, json file content must be a dict
    data             --  List object containg the row data
    output_file_name --  Output file name. Default: Output. will be saved to /tmp/output_file_name_time_stamp
    request          --  html request object. If None, data will be saved to '/tmp/Output_time_stamp.file_extension'.
                         If request object is given , data will be saved in output file on the client.
    '''
    def __init__(self,app_name, data_format, delimiter, output_file_name, request=None, json_in_file=None, data=[], flags=None):
        self.app_name = app_name
        self.header = None
        self.data = data
        self.data_format = data_format
        self.delimiter = delimiter
        self.spacer = ': '
        if self.delimiter == ':':
            self.spacer = ' '
        self.request = request
        self.json_in_file = json_in_file
        self.output_file_name = output_file_name
        self.flags = flags
        self.app_data_dict = {
            'Sodxtrmts':'data',
            'Sodsumm':'table_data',
            'area_time_series':'download_data'
        }
        self.file_extension = {
            'dlm': '.dat',
            'clm': '.txt',
            'xl': '.xls'
        }
        self.delimiter_dict = {
            'space':' ',
            'tab':'\t',
            'comma':',',
            'colon':':',
            'pipe':'|'
        }
        self.column_headers = {
            'Sodxtrmts':WRCCData.COLUMN_HEADERS['Sodxtrmts'],
            'Sodsumm':None,
            'area_time_series':['Date      ']
        }


    def get_time_stamp(self):
        return datetime.datetime.now().strftime('%Y%m_%d_%H_%M_%S')

    def set_output_file_path(self):
        file_extension = self.file_extension[self.data_format]
        if self.output_file_name == 'Output':
            time_stamp = self.get_time_stamp()
            f_path = '/tmp/' + 'Output_' + time_stamp + file_extension
        else:
            f_path = '/tmp/' + self.output_file_name + file_extension
        return f_path

    def get_row_data(self):
        if self.data:
            return self.data
        try:
            with open(self.json_in_file, 'r') as json_f:
                #need unicode converter since json.loads writes unicode
                json_data = WRCCUtils.u_convert(json.loads(json_f.read()))
                #json_data = json.loads(json_f.read())
                #Find header info if in json_data
        except:
            json_data = {}
        #Set headers and column headers for the apps
        if self.app_name == 'Sodxtrmts':
            try:
                self.header = json_data['header']
            except:
                pass
        if self.app_name == 'Sodsumm':
            self.header = []
            labels = ['Station Name', 'Station ID', 'Station Network', 'Station State', 'Start Year', 'End Year', 'Climate Variables']
            for idx, key in enumerate(['stn_name', 'stn_id', 'stn_network', 'stn_state', 'record_start', 'record_end', 'table_name_long']):
                self.header.append([labels[idx], json_data[key]])
        if self.app_name == 'area_time_series':
            self.header = json_data['display_params_list']
            for el in json_data['search_params']['element_list']:
                self.column_headers['area_time_series'].append(el)
        if self.app_data_dict[self.app_name] in json_data.keys():
            data = json_data[self.app_data_dict[self.app_name]]
        else:
            data = []
        return data

    def write_to_csv(self,column_header, data):

        if self.request:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (self.output_file_name,self.file_extension[self.data_format])
            writer = csv.writer(response, delimiter=self.delimiter_dict[self.delimiter])

        else: #write to file
            try:
                output_file = self.set_output_file_path()
                csvfile = open(output_file, 'w+')
                writer = csv.writer(csvfile, delimiter=self.delimiter_dict[self.delimiter])
                response = None
            except Exception, e:
                #Can' open user given file, create emergency writer object
                writer = csv.writer(open('/tmp/csv.txt', 'w+'), delimiter=self.delimiter_dict[self.delimiter])
                response = 'Error! Cant open file' + str(e)
        #Write header if it exists
        if self.header:
            row = []
            for idx,key_val in enumerate(self.header):
                if len(key_val) != 2:
                    continue
                #three entries per row
                row.append(key_val[0] + self.spacer + key_val[1])
                if (idx + 1) % 2 == 0 or idx == len(self.header) - 1:
                    writer.writerow(row)
                    row = []
            writer.writerow(row)
            writer.writerow([])
            if self.app_name == 'Sodxtrmts':
                row = ['*a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,']
                writer.writerow(row)
                row = ['*z = 26 or more days missing, A = Accumulations present']
                writer.writerow(row)
                row=['*Long-term means based on columns; thus, the monthly row may not']
                writer.writerow(row)
                row=['*sum (or average) to the long-term annual value.']
                writer.writerow(row)

        writer.writerow([])
        row = column_header
        #row = ['%8s' %str(h) for h in column_header] #Kelly's format
        #row = ['%s' %str(h) for h in column_header]
        writer.writerow(row)
        for row_idx, row in enumerate(data):
            row_formatted = []
            for idx, r in enumerate(row):
                row_formatted.append('%s' %str(r))
                #row_formatted.append('%8s' %str(r)) #Kelly's format
            writer.writerow(row_formatted)
            #writer.writerow(row)
        try:
            csvfile.close()
        except:
            pass
        return response

    def write_to_excel(self,column_header, data):
        wb = Workbook()
        #Note row number limit is 65536 in some excel versions
        row_number = 0
        flag = 0
        sheet_counter = 0
        for date_idx, date_vals in enumerate(data): #row
            for j, val in enumerate(date_vals):#column
                if row_number == 0:
                    flag = 1
                else:
                    row_number+=1
                if row_number == 65535:flag = 1

                if flag == 1:
                    sheet_counter+=1
                    #add new workbook sheet
                    ws = wb.add_sheet('Sheet_%s' %sheet_counter)
                    #Header
                    if self.header:
                        for idx,key_val in enumerate(self.header):
                            ws.write(idx,0,key_val[0])
                            ws.write(idx,1,key_val[1])
                    #Column Header
                    for idx, head in enumerate(column_header):
                        ws.write(len(self.header), idx, head)
                        row_number = 1;flag = 0
                try:
                    row_idx = len(self.header) + 1 + date_idx
                    try:
                        ws.write(row_idx, j, float(val))
                    except:
                        ws.write(row_idx, j, str(val))#row, column, label
                except Exception, e:
                    response = 'Excel write error:' + str(e)
                    break
        if self.request:
            response = HttpResponse(content_type='application/vnd.ms-excel;charset=UTF-8')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (self.output_file_name,self.file_extension[self.data_format])
            wb.save(response)
        else: #write to file
            try:
                output_file = self.set_output_file_path()
                wb.save(output_file)
                response = None
            except Exception, e:
                response = 'Excel save error:' + str(e)
        return response

    def write_to_json(self,column_header, data):
        if request:
            response = json.dumps({'column_header':column_header,'data':data})
        else:
            output_file = self.set_output_file_path()
            with open(output_file, 'w+') as jsonf:
                json.dump(data, jsonf)
                response = None
        return response

    def write_to_file(self):
        time_stamp = self.get_time_stamp()
        column_header = self.column_headers[self.app_name]
        data = self.get_row_data()
        if self.app_name == 'Sodsumm':
            try:
                column_header = data[0]
            except:
                column_header = []
            try:
                data = data[1:]
            except:
                data = []
        #Sanity Check
        if not self.json_in_file and not self.data:
            return 'Error! Need either a data object or a json file that contains data!'
        if self.json_in_file and self.data:
            return 'Error! Only one allowed: json_file path OR data'

        #Write data to file
        if self.data_format in ['dlm', 'clm']:
            response = self.write_to_csv(column_header, data)
        elif self.data_format == 'json':
            response = self.write_to_json(column_header, data)
        elif self.data_format == 'xl':
            response = self.write_to_excel(column_header, data)

        return response


class SODDataJob(object):
    '''
    SOD Data class.

    Keyword arguments:
    app_name -- application name, one of the following:
    Sodsumm, Sodsum, Sodxtrmts,Soddyrec,Sodpiii, Soddynorm,
    Sodrun, Soddd, Sodpct, Sodpad, Sodthr
    data_params -- parameter dictionary for ACIS-WS call
                   keys: start_date, end_date, elements
                         and a key defining the search area, one of:
                         sid, sids,county, climdiv, cwa, basin, state, bbox
    '''
    def __init__(self, app_name, data_params, app_specific_params=None):
        self.params = data_params
        self.app_specific_params = app_specific_params
        self.app_name = app_name
        self.station_ids = None;self.station_names=None
        self.el_type_element_dict = {
            #Sodsumm
            'all_sodsumm':['maxt', 'mint', 'avgt', 'pcpn', 'snow'],
            'all':['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd'],
            'tmp':['maxt', 'mint', 'pcpn'],
            'both':['max', 'mint', 'avgt', 'pcpn', 'snow'],
            'temp':['maxt', 'mint', 'avgt'],
            'prsn':['pcpn', 'snow'],
            'wtr':['pcpn', 'snow', 'snwd'],
            'hcd':['hdd','cdd','gdd'],
            'dd':['hdd','cdd'],
            'hc':['maxt','mint'],
            'g':['maxt','mint'],
            #Sodxtrmts
            'range':['maxt', 'mint'],
            'avgt':['maxt', 'mint'],
            'dtr':['maxt', 'mint'],
            'dd_raw':['maxt', 'mint'],
            'pet':['maxt', 'mint'],
            #Sodsum
            'multi':['pcpn','snow','snwd','maxt','mint','obst'],
            #Single Element
            'pcpn':['pcpn'],
            'snow':['snow'],
            'snwd':['snwd'],
            'maxt':['maxt'],
            'mint':['mint'],
            'obst':['obst'],
            'hdd':['hdd'],
            'cdd':['cdd'],
            'gdd':['gdd'],
            'evap':['evap'],
            'wdmv':['wdmv']
        }
        self.app_elems_params = {
            'Soddyrec': {'vX':None,'groupby':'year'},
            'Soddynorm':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodsumm':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodrun':{'vX':None},
            'Sodrunr':{'vX':None},
            'Sodxtrmts':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodpct':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodthr':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodpiii':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodpad':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Soddd':{'vX':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodmonline':{'vX':None},
            'Sodsum':{'vX':None},
            'Sodmonlinemy':{'vX':None},
            'Sodlist':{'vX':None,'add':'t'},
            'Sodcnv':{'vX':None,'add':'t'}
        }
        self.soddyrec_smry_opts = [{'reduce':'mean', 'add':'date,mcnt'}, \
                        {'reduce':'max', 'add':'date,mcnt'}, \
                        {'reduce':'min', 'add':'date,mcnt'}]

    def set_element_param(self):
        if 'element' in self.params.keys():
            el = 'element'
        elif 'elements' in self.params.keys():
            el= 'elements'
        else:
            el = None
        return el

    def set_locations_list(self,params):
        '''
        Converts string of lon, lat pairs into list of lon, lat pairs
        '''
        loc_list = []
        if 'location' in params.keys():
            loc_list.append(params['location'])
        if 'locations' in params.keys():
            if isinstance(params['locations'], basestring):
                loc_list = params['locations'].split(',')
                lon_list = [loc_list[2*j] for j in range(len(loc_list) / 2)]
                lat_list = [loc_list[2*j + 1] for j in range(len(loc_list) / 2)]
                for idx,lon in enumerate(lon_list):
                    loc_list.append('%s,%s' %(lon, lat_list[idx]))
            elif isinstance(params['locations'], list):
                loc_list = params['locations']
        return loc_list

    def set_area_params(self):
        area = None; val=None
        if 'sid' in self.params.keys():area = 'sids';val = self.params['sid']
        if 'station_id' in self.params.keys():area = 'sids';val = self.params['station_id']
        if 'sids' in self.params.keys():area = 'sids';val = self.params['sids']
        if 'station_ids' in self.params.keys():area = 'sids';val = self.params['station_ids']
        if 'loc' in self.params.keys():area='loc';val=self.params['loc']
        if 'location' in self.params.keys():area='loc';val=self.params['location']
        if 'locations' in self.params.keys():area='loc';val=self.params['locations']
        if 'county' in self.params.keys():area = 'county';val = self.params['county']
        if 'climdiv' in self.params.keys():area = 'climdiv';val = self.params['climdiv']
        if 'cwa' in self.params.keys():area = 'cwa';val = self.params['cwa']
        if 'basin' in self.params.keys():area = 'basin';val = self.params['basin']
        if 'state' in self.params.keys():area = 'state';val = self.params['state']
        if 'bbox' in self.params.keys():area = 'bbox';val = self.params['bbox']
        return area, val

    def get_unique_sid(self, sids):
        '''
        sids  -- list of station ids produced by a StnMeta
                 or MultiStnData call
        Chooses coop id out of list of sids if
        station has a coop id, else
        chooses first id in list of sids
        '''
        #Take first station id listed
        if not sids:
            return None
        #If user id, find corresponding network
        stn_id = ''
        stn_network = ''
        if 'sid' in self.params.keys():
            stn_id = self.params['sid']
            for sid in sids:
                if sid.split(' ')[0] == stn_id:
                    stn_network = WRCCData.NETWORK_CODES[sid.split(' ')[1]]
                    break
            return stn_id, stn_network
        #Pick first id in list
        stn_id = sids[0].split(' ')[0]
        stn_network = WRCCData.NETWORK_CODES[sids[0].split(' ')[1]]
        if sids[0].split(' ')[1] != '2':
            #Check if station has coop id, if so, use that
            for sid in sids[1:]:
                if sid.split(' ')[1] == '2':
                    #Found coop id
                    stn_id = sid.split(' ')[0]
                    stn_network = WRCCData.NETWORK_CODES[sid.split(' ')[1]]
                    break
        return str(stn_id), stn_network

    def set_start_end_date(self):
        s_date = None; e_date = None
        if 'station_id' in self.params.keys():
            if not self.station_ids:
                return s_date, e_date
        #Format yyyy, yyyymm data into yyyymmdd
        if len(self.params['start_date']) == 4:
            s_date = self.params['start_date'] + '0101'
        elif len(self.params['start_date']) == 6:
            s_date = self.params['start_date'] + '01'
        elif len(self.params['start_date']) == 8:
            s_date = self.params['start_date']

        if len(self.params['end_date']) == 4:
            e_date = self.params['end_date'] + '1231'
        elif len(self.params['end_date']) == 6:
            mon_len = WRCCUtils.find_mon_len(self.params['end_date'][0:4], self.params['end_date'][4:6])
            e_date = self.params['end_date'] + str(mon_len)
        elif len(self.params['end_date']) == 8:
            e_date = self.params['end_date']
        #deal with por input
        element_list = self.get_element_list()
        if self.params['start_date'].lower() == 'por' or self.params['end_date'].lower() == 'por':
            if self.params['start_date'].lower() == 'por' and self.params['end_date'].lower() == 'por':
                vd = WRCCUtils.find_valid_daterange(self.station_ids[0],el_list=element_list,max_or_min='min')
            elif self.params['start_date'].lower() == 'por' and self.params['end_date'].lower() != 'por':
                vd = WRCCUtils.find_valid_daterange(self.station_ids[0],el_list=element_list,max_or_min='min', end_date=e_date)
            elif self.params['start_date'].lower() != 'por' and self.params['end_date'].lower() == 'por':
                vd = WRCCUtils.find_valid_daterange(self.station_ids[0],el_list=element_list,max_or_min='min', start_date=s_date)
            if vd:
                s_date = vd[0];e_date=vd[1]
        return s_date, e_date

    def get_station_ids_names(self):
        '''
        Finds type of search area
        and makes a call to Acis meta data to
        find all station IDs lying within the search area
        '''
        stn_ids =[]
        stn_names = []
        area, val = self.set_area_params()
        if area and val:
            request =  AcisWS.get_meta_data(area, val)
        else:
            request = {}
        if request:
            for i, stn in enumerate(request['meta']):
                #remove appostrophes from name, gives trouble in json file
                stn_names.append(str(stn['name']).replace("\'"," "))
                sids = stn['sids']
                stn_id,stn_network = self.get_unique_sid(sids)
                #Take first station id listed
                if not stn_id:
                    continue
                stn_ids.append(stn_id)
        self.station_ids = stn_ids
        return stn_ids, stn_names

    def get_grid_meta(self):
        meta_dict = {
            'ids':[''],
            'names':[''],
            'states':[''],
            'lls':[],
            'elevs': [],
            'uids':[''],
            'networks':[''],
            'climdivs':[''],
            'countys':[''],
            'valid_daterange':[['00000000','00000000']]
        }
        meta_dict['location_list'] = self.set_locations_list(self.params)
        meta_dict['ids'] = [[str(l[0]) + '_' + str(l[1])] for l in meta_dict['location_list']]
        meta_dict['lls'] = [[l] for l in meta_dict['location_list']]
        return meta_dict

    def get_station_meta(self):
        '''
        Finds type of search area
        and makes a call to Acis meta data to
        find all station IDs lying within the search area
        '''
        meta_dict = {
            'ids':[],
            'names':[],
            'states':[],
            'lls':[],
            'elevs':[],
            'uids':[],
            'networks':[],
            'climdivs':[],
            'countys':[],
            'valid_daterange':[]
        }
        area, val = self.set_area_params()
        if area and val:
            if self.app_name == 'Sodsum':
                request = AcisWS.get_meta_data(area, val,vX_list=[1,4,7,10,12])
            else:
                request =  AcisWS.get_meta_data(area, val)
        else:
            request = {}
        if request:
            for i, stn in enumerate(request['meta']):
                sids = stn['sids']
                #Find stationID and network
                stn_id, stn_network = self.get_unique_sid(sids)
                if not stn_id:
                    continue
                meta_dict['ids'].append(stn_id)
                meta_dict['networks'].append(stn_network)
                meta_dict['names'].append(str(stn['name']).replace("\'"," "))
                if stn['ll'] and len(stn['ll']) == 2:
                    meta_dict['lls'].append(stn['ll'])
                else:
                    meta_dict['lls'].append([-999.99,99.99])
                if 'valid_daterange' in stn.keys():
                    meta_dict['valid_dateranges'] = stn['valid_daterange']
                #Find other meta data info
                #NOTE: ACIS quirk: sometimes other meta data attributes don't show up
                keys = ['state', 'elev', 'uid', 'climdiv', 'county']
                for key in keys:
                    meta_dict_key = key + 's'
                    if key in stn.keys():
                        meta_dict[meta_dict_key].append(str(stn[key]))
                    else:
                        meta_dict[meta_dict_key].append(' ')
        self.station_ids = meta_dict['ids']
        return meta_dict

    def get_dates_list(self):
        '''
        Find list of dates lying within start and end date
        Takes care of data formatting and por cases.
        '''
        dates = []
        s_date, e_date = self.set_start_end_date()
        if s_date and e_date and len(s_date) == 8 and len(e_date) == 8:
            #Some apps need date changes
            l = ['Soddyrec', 'Soddynorm', 'Soddd', 'Sodpad', 'Sodsumm', 'Sodpct', 'Sodthr', 'Sodxtrmts', 'Sodpiii']
            if self.app_name in l:
                #Data is grouped by year so we need to change start and end_dates
                #To match whole year
                s_date = s_date[0:4] + '0101'
                e_date = e_date[0:4] + '1231'
            #Convert to datetimes
            start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6]), int(s_date[6:8]))
            end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6]), int(e_date[6:8]))
            for n in range(int ((end_date - start_date).days +1)):
                next_date = start_date + datetime.timedelta(n)
                n_year = str(next_date.year)
                n_month = str(next_date.month)
                n_day = str(next_date.day)
                if len(n_month) == 1:n_month='0%s' % n_month
                if len(n_day) == 1:n_day='0%s' % n_day
                acis_next_date = '%s%s%s' %(n_year,n_month,n_day)
                dates.append(acis_next_date)
                #Note, these apps are grouped by year and return a 366 day year even for non-leap years
                if self.app_name in ['Sodpad', 'Sodsumm', 'Soddyrec', 'Soddynorm', 'Soddd']:
                    if dates[-1][4:8] == '0228' and not WRCCUtils.is_leap_year(int(dates[-1][0:4])):
                        dates.append(dates[-1][0:4]+'0229')
        return dates

    def get_element_list(self):
        '''
        Get element list for data request
        Element list depends on self.app_name to be run
        '''
        el_type = self.set_element_param()
        if self.app_name == 'Sodsumm' and self.params[el_type] == 'all':
            el_list = self.el_type_element_dict['all_sodsumm']
        elif self.app_name == 'Soddynorm':
             el_list = self.el_type_element_dict['tmp']
        elif self.app_name == 'Sodxtrmts' and self.params[el_type] in ['hdd','cdd', 'gdd','dtr']:
            el_list = self.el_type_element_dict['dd_raw']
        else:
            el_list = self.el_type_element_dict[self.params[el_type]]
        return el_list


    def set_request_elements(self):
        '''
        Function to set elems value needed in ACIS data call
        '''
        elements = self.get_element_list()
        elems = []
        el_dict = self.app_elems_params[self.app_name]
        for el in elements:
            el_dict_new = {}
            for key, val in el_dict.iteritems():
                if key == 'vX':
                    el_dict_new[key] = WRCCData.ACIS_ELEMENTS_DICT[el]['vX']
                else:
                    el_dict_new[key] = val
            #We have to add three types of summaries for each element of Soddyrec
            if self.app_name == 'Soddyrec':
                for smry in self.soddyrec_smry_opts:
                    e_d = {}
                    for key, val in el_dict_new.iteritems():
                        e_d[key] = val
                    e_d['smry'] = smry
                    elems.append(e_d)
            else:
                elems.append(el_dict_new)
        #FIX ME: should need to treat Sodsumm separately
        #but somehow the above code jumbles up the elements
        if self.app_name == 'Sodsumm':
            elems  = [{'name':el,'interval':'dly','duration':'dly','groupby':'year'} for el in elements]
        return elems

    def set_request_params(self):
        area, val = self.set_area_params()
        sdate, edate = self.set_start_end_date()
        elems = self.set_request_elements()
        params = {area:val, 'sdate':sdate, 'edate':edate,'elems':elems}
        if 'grid' in self.params.keys():
            params['grid'] = self.params['grid']
            params['meta'] = 'll, elev'
        return params

    def find_leap_yr_indices(self):
        '''
        Finds indices of leap years given start/end_year
        Needed to fomat grid data most efficiently
        '''
        leap_indices =[]
        s_yr = int(self.params['start_date'][0:4])
        e_yr = int(self.params['end_date'][0:4])
        yrs = range(s_yr, e_yr + 1)
        num_years = e_yr - s_yr + 1
        max_num_leap = num_years / 4
        idx = 0
        #Find first leap year
        for yr in range(s_yr, e_yr + 1):
            if WRCCUtils.is_leap_year(yr):break
            idx+=1
        leap_indices.append(idx)
        while idx < len(yrs):
            idx+=4
            leap_indices.append(idx)
        return leap_indices, yrs

    def format_data_grid(self, request, locations,elements):
        '''
        Formats output of data request dependent on
        application
        For each location i
        request[i]['meta'] = {'lat', 'lon','elev'}
        request[i]['data'] = [[date_1, el1, el2,...], ['date_2', el_1, el_2,..]...]
        We need to convert to staton data request format that is grouped by year
        '''
        leap_indices,year_list =self.find_leap_yr_indices()
        #Set up data output dictonary
        error = ''
        if self.app_name == 'Sodsum':
            data = {}
        else:
            data = [[] for i in locations]
        for i, loc in enumerate(locations):
            if self.app_name == 'Soddyrec':
                data[i] = [[['#', '#', '#', '#', '#', '#','#', '#'] for k in range(366)] for el in elements]
            elif self.app_name in ['Sodrun', 'Sodrunr', 'Sodsum']:
                data[i] = []
            else:
                #data[i] = [[] for el in elements]
                data[i] = [[] for yr in  year_list]
        #Sanity checks on request object
        if not request:
            error = 'Bad request, check params: %s'  % str(self.params)
            return data, error
        for loc_idx, loc in enumerate(locations):
            loc_request = request[loc_idx]
            if 'error' in loc_request.keys():
                error = loc_request['error']
                continue
            if not 'data' in loc_request.keys():
                error = 'No data found for parameters: %s' % str(self.params)
                continue
            '''
            for el_idx, element in enumerate(elements):
                start_idx = 0
                yr_data = []
                for yr_idx, yr in enumerate(year_list):
                    length = 365
                    #Feb 29 not recorded as M for non-leap years.
                    # Need to insert for gouping by year
                    if yr_idx in leap_indices:length =  366
                    else:length=365
                    d = loc_request['data'][start_idx:start_idx + length]
                    start_idx = start_idx + length
                    #Only pick relevant element data
                    d = [d[el_idx + 1] for d in d]
                    #Add missing leap year value if not leap year
                    if length == 365:d.insert(59,'M')
                    yr_data.append(d)
                    data[loc_idx][el_idx].append(yr_data)
            '''
            start_idx = 0
            for yr_idx, yr in enumerate(year_list):
                yr_data = [[] for el in elements]
                length = 365
                #Feb 29 not recorded as M for non-leap years.
                # Need to insert for gouping by year
                if yr_idx in leap_indices:length =  366
                else:length=365
                d = loc_request['data'][start_idx:start_idx + length]
                start_idx = start_idx + length
                for el_idx, element in enumerate(elements):
                    #Only pick relevant element data
                    el_data = [day_data[el_idx + 1] for day_data in d]
                    #Add missing leap year value if not leap year
                    if length == 365:el_data.insert(59,'M')
                    yr_data[el_idx] = el_data
                data[loc_idx][yr_idx] = yr_data
        return data, error

    def format_data_station(self, request, station_ids, elements):
        '''
        Formats output of data request dependent on
        application
        request is the output of a MultiStnData call
        '''
        #Set up data output dictonary
        error = ''
        if self.app_name == 'Sodsum':
            data = {}
        else:
            data = [[] for i in station_ids]
        for i, stn in enumerate(station_ids):
            if self.app_name == 'Soddyrec':
                data[i] = [[['#', '#', '#', '#', '#', '#','#', '#'] for k in range(366)] for el in elements]
            elif self.app_name in ['Sodrun', 'Sodrunr', 'Sodsum']:
                data[i] = []
            else:
                data[i] = [[] for el in elements]

        #Sanity checks on request object
        if not request:
            error = 'Bad request, check params: %s'  % str(self.params)
            return data, error
        if 'error' in request.keys():
            error = request['error']
            return data, error
        if not 'data' in request.keys():
            error = 'No data found for parameters: %s' % str(self.params)
            return data, error

        for stn, stn_data in enumerate(request['data']):
            if not 'data' in stn_data.keys():
                continue

            #find station_id, Note: MultiStnData call may not return the stations in order
            sids = stn_data['meta']['sids']
            stn_id,stn_network = self.get_unique_sid(sids)
            try:
                index = station_ids.index(stn_id)
            except:
                continue

            if self.app_name == 'Soddyrec':
                if 'smry' not in stn_data.keys():
                    continue
                data[index] = stn_data['smry']
            else:
                if 'data' not in stn_data.keys():
                    continue
                if self.app_name in ['Soddynorm', 'Soddd', 'Sodpct']:
                    for yr, el_data in enumerate(stn_data['data']):
                        for el_idx, dat in enumerate(el_data):
                            data[index][el_idx].append(dat)
                else:
                    data[index] = stn_data['data']
        return data, error

    def get_data_station(self):
        '''
        Request SOD data from ACIS data for a station
        '''
        elements = self.get_element_list()
        station_ids, station_names = self.get_station_ids_names()
        dates = self.get_dates_list()
        meta_dict = self.get_station_meta()
        #Set up resultsdict
        resultsdict = {
                    'data':[],
                    'dates':dates,
                    'elements':elements,
                    'station_ids':station_ids,
                    'station_names':station_names,
                    'lls':meta_dict['lls']
        }
        #Make data request
        data_params = self.set_request_params()
        request = AcisWS.MultiStnData(data_params)
        resultsdict['data'], resultsdict['error'] = self.format_data_station(request, station_ids, elements)
        return resultsdict

    def get_data_grid(self):
        '''
        Request SOD data from ACIS for a gridpoint
        '''
        elements = self.get_element_list()
        locations_list = self.set_locations_list(self.params)
        dates = self.get_dates_list()
        meta_dict = self.get_grid_meta()
        #Set up resultsdict
        resultsdict = {
                    'data':[],
                    'dates':dates,
                    'elements':elements,
                    'location_list':locations_list,
                    'lls':meta_dict['lls']
        }
        #Make data request
        #Each location requires separate request
        #request = {'meta':{'lat':'', 'lon':'','elev':''},'data':[]}
        data = [{} for loc in locations_list]
        for i,loc in enumerate(locations_list):
            data_params = self.set_request_params()
            data_params['loc'] = loc
            req = AcisWS.GridData(data_params)

            '''
            try:
                req = AcisWS.GridData(data_params)
                req['meta'];req['data']
            except Exception, e:
                data[i]['error'] = str(e)
                continue
            '''
            data[i]['meta'] = req['meta']
            data[i]['data']= req['data']
        resultsdict['data'], resultsdict['error'] = self.format_data_grid(data, locations_list, elements)
        return resultsdict

class SODApplication(object):
    '''
    SOD Application Class.


    Keyword arguments:
    app_name    -- application name, on of the following
                    Sodsumm, Sodsum, Sodxtrmts,Soddyrec,Sodpiii,
                    Sodrun, Soddd, Sodpct, Sodpad, Sodthr, Soddynorm
    datadict    --  dictionary containing results of SODDataJob
                    keys: data, dates, elements, station_ids, station_names
    app_specific_params -- application specific parameters
    '''
    def __init__(self, app_name, data, app_specific_params=None):
        self.app_name = app_name
        self.data = data
        self.app_specific_params = app_specific_params

    def run_app(self):
        app_params = {
                    'app_name':self.app_name,
                    'data':self.data['data'],
                    'elements':self.data['elements'],
                    'dates':self.data['dates'],
                    'lls':self.data['lls']
                    }
        if 'station_ids' in self.data.keys():
            app_params['coop_station_ids'] = self.data['station_ids']
            app_params['station_names'] = self.data['station_names'],
        if 'location_list' in self.data.keys():
            app_params['location_list'] = self.data['location_list']
            app_params['station_names'] = self.data['location_list'],
        if self.app_specific_params:
            app_params.update(self.app_specific_params)
        #Sanity check, make sure data has data
        #if 'error' in self.data.keys() or not self.data['data']:
        #    return {}
        Application = getattr(WRCCDataApps, self.app_name)
        if self.app_name == 'Sodxtrmts':
            results, fa_results = Application(**app_params)
            return results, fa_results
        elif self.app_name == 'Soddyrec':
            results = Application(app_params['data'],app_params['dates'], app_params['elements'], app_params['coop_station_ids'], app_params['station_names'])
            return results
        else:
            results = Application(**app_params)
            return results

class SodGraphicsJob(object):
    '''
    SOD Graphics Class.


    Keyword arguments:
    app_name    -- application name, one of the following
                    Sodsumm, Sodsum, Sodxtrmts,Soddyrec,Sodpiii,
                    Sodrun, Soddd, Sodpct, Sodpad, Sodthr, Soddynorm
    datadict    --  dictionary containing results of SODDataJob
                    keys: data, dates, elements, station_ids, station_names
    app_specific_params -- application specific parameters
    '''
    def __init__(self, app_name, data, app_specific_params=None):
        self.app_name = app_name
        self.data = data
        self.app_specific_params = app_specific_params

class StnDataJob(object):
    '''
    Class to retrieve data via Acis Webservice
    acis_data_call is one of StnMeta, StnData, MultiStnData, GridData, General
    given as a string argument,
    params is the parameter dictionary for the acis_data_call
    '''
    def __init__(self, acis_data_call, params):
        self.params = params
        self.acis_data_call = acis_data_call
        self.request = {}

    def format_stn_meta(self, meta_dict):
        '''
        deal with meta data issues:
        1)jQuery does not like ' in station names
        2) unicode output can cause trouble
        '''
        Meta = {}
        for key, val in meta_dict.items():
            if key == 'sids':
                Val = []
                for sid in val:
                    Val.append(str(sid).replace("\'"," "))
            elif key == 'valid_daterange':
                Val = []
                for el_idx, rnge in enumerate(val):
                    start = str(rnge[0])
                    end = str(rnge[1])
                    dr = [start, end]
                    Val.append(dr)
            else:
                Val = str(val)
            Meta[key] = Val
        return Meta

    def format_stn_dict(self, stn_dict):
        new_dict = {}
        for res_key, res in stn_dict.items():
            if res_key == 'meta':
                res_dict = self.format_stn_meta(res)
            else:
                res_dict = res
            new_dict[str(res_key)] = res
        return new_dict


    def make_data_call(self):
        get_data = getattr(AcisWS, self.acis_data_call)
        self.request = get_data(self.params)
        result = {}
        if not self.request:
            result['error'] = 'bad request, check params: %s'  % self.params
        elif 'error'in self.request.keys():
            result['error'] = self.request['error']
        else:
            if self.acis_data_call == 'StnData':
                result = iself.format_stn_dict(self.request)

            else:
                result = self.request
        return result


class GridFigure(object) :
    '''
    ACIS Grid figure. Used in clim_sum_map
    '''
    image_padding = 0,150
    def __init__(self, params, img_offset=0, text_offset=(80,50)) :
        self.params= params
        self.region =params['select_grid_by']
        if 'date' in params.keys():
            self.date = params['date']
        elif 'this' in params.keys():
            self.date = params['this']['date']
        else:
            self.date = time.strftime('%Y%m%d')
        if 'data' in params.keys():
            self.data = params['data']
        else:
            self.data = None
        self.image_offset = img_offset

    def set_levels(self):
        levels = []
        level_number = self.params['level_number']
        #data_min = WRCCData.CLIM_SUM_MAPS_DAILY_THRESHES[self.params['elems'][0]['name']][0]
        #data_max = WRCCData.CLIM_SUM_MAPS_DAILY_THRESHES[self.params['elems'][0]['name']][1]
        data_min = self.data['range'][0]
        data_max = self.data['range'][1]
        step = abs(data_max - data_min) / float(level_number)
        x = data_min
        while x <= data_max:
            levels.append(x)
            x+=step
        return levels

    def get_grid(self) :
        with open('%simg/empty.png' %settings.MEDIA_DIR, 'rb') as image_file:
            encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
        empty_img = {'data':encoded_string, 'range':[0.0, 0.0], 'levels':[0,1,2,3,4,5,6,7,8],\
        'cmap': [u'#000000', u'#4300a1', u'#0077dd', u'#00aa99', u'#00ba00', \
        u'#5dff00', u'#ffcc00', u'#ee0000', u'#cccccc'], 'size':[self.params['image']['width'],300],\
        'error':'bad request, check parameters %s' %str(self.params)}
        try:
            self.data = AcisWS.GridData(self.params)
            #levels = self.set_levels()
            #self.params['image']['levels'] = levels
            if not 'data' in self.data.keys():
                self.data = empty_img
        except:
            self.data = empty_img
        #Overwrite levels according to data range
        if not self.data or 'error' in self.data.keys() or not 'data' in self.data.keys():
            self.data = empty_img
        return self.data

    @staticmethod
    def get_color(rgb) :
        return (int(rgb[1:3],16)/255.,int(rgb[3:5],16)/255.,int(rgb[5:7],16)/255.)

    def place_text(self,txt,j='l',v='b') :
        ctx = self.ctx
        _,_,w,h,_,_ = ctx.text_extents(txt)
        if   v == 'b' : h = 0
        elif v == 'm' : h = h/2
        elif v == 't' : h = h
        if   j == 'l' : w = 0
        elif j == 'c' : w = -w/2
        elif j == 'r' : w = -w
        ctx.rel_move_to(w,h)
        ctx.show_text(txt)


    def build_figure(self, image_info, out_name) :
        img_buf = StringIO(image_info['data'][21:].decode('base64'))
        img_buf.seek(0)
        # create input image
        in_img = cairo.ImageSurface.create_from_png(img_buf)
        self.size = height,width = in_img.get_height(),in_img.get_width()
        pad_w,pad_h = self.image_padding
        # create output image
        out_img = cairo.ImageSurface(cairo.FORMAT_ARGB32,
            width+pad_w, height+pad_h+self.image_offset)
        self.ctx = ctx = cairo.Context(out_img)
        # set background color
        ctx.set_source_rgb(255,239,213)
        ctx.paint()
        # place image
        ctx.set_source_surface(in_img,pad_w/2,self.image_offset)
        ctx.paint()
        # frame image
        ctx.set_line_width(1.0)
        ctx.set_source_rgb(0,0,0)
        ctx.rectangle(pad_w/2,self.image_offset,width,height)
        ctx.stroke()

        ctx.set_matrix(cairo.Matrix(x0=15+25,y0=self.image_offset+height+80))
        #ctx.move_to(35,self.image_offset+self.params['image']['height']+30)
        self.add_title()
        #ctx.set_matrix(cairo.Matrix(y0=self.image_offset+height+5))
        #self.add_footer()
        ctx.set_matrix(cairo.Matrix(x0=15+25,
            y0=self.image_offset+height+30))
        self.add_legend(image_info)

        out_buf = open(out_name,'w')
        out_img.write_to_png(out_buf)

    def add_title(self) :
        ctx = self.ctx
        title = WRCCData.DISPLAY_PARAMS[self.params['temporal_summary']]
        el_strip = re.sub(r'(\d+)(\d+)', '', self.params['elems'][0]['name'])
        try:
            base_temp = int(self.params['elems'][0]['name'][-2:])
        except:
            base_temp = None
        title+=' ' + WRCCData.DISPLAY_PARAMS[el_strip] + ' (' + WRCCData.UNITS_ENGLISH[el_strip] + ')'
        if base_temp:
            title+= ' Base Temperature: ' + str(base_temp)
        area_description = WRCCData.DISPLAY_PARAMS[self.params['select_grid_by']]
        area_description+= ': ' + self.params[self.params['select_grid_by']].upper()
        date_str = '%s to %s' % (self.params['sdate'], self.params['edate'])
        if self.params['image']['width']<301:
            ctx.set_font_size(8.)
            h = 10
        elif self.params['image']['width']>300 and self.params['image']['width']<501:
            ctx.set_font_size(10.)
            h=20
        else:
            ctx.set_font_size(12.)
            h=30
        #ctx.set_source_rgb(.8,.1,.1)
        ctx.move_to(0,0)
        self.place_text(title,j='l', v='t')
        ctx.move_to(0,0)
        ctx.rel_move_to(0,h)
        self.place_text(area_description,j='l',v='t')
        ctx.move_to(0,0)
        ctx.rel_move_to(0,2*h)
        self.place_text(date_str,j='l',v='t')

    def add_legend(self, image_info) :
        ctx = self.ctx
        #ctx.set_matrix(cairo.Matrix(yy=-1,y0=height))
        if image_info['size'][0]<301:
            ctx.set_font_size(8.)
            w = image_info['size'][0]/(len(image_info['cmap']) + 3)
        elif image_info['size'][0]>300 and image_info['size'][0]<501:
            ctx.set_font_size(10.)
            w = image_info['size'][0]/(len(image_info['cmap'])+2)
        else:
            ctx.set_font_size(12.)
            w = image_info['size'][0]/(len(image_info['cmap'])+2)
        for idx,color in enumerate(image_info['cmap']) :
            ctx.rectangle(idx*w,0,w,10)
            ctx.set_source_rgb(*self.get_color(color))
            ctx.fill_preserve()
            ctx.set_source_rgb(0,0,0)
            ctx.stroke()
        for idx,value in enumerate(image_info['levels']) :
            ctx.move_to((idx+1)*w,10)
            ctx.rel_line_to(0,5)
            ctx.rel_move_to(-2,3)
            if value >0.0 and value < 1.0:
                self.place_text('%.2f'%(value),j='c',v='t')
            else:
                self.place_text('%d'%(value),j='c',v='t')
        ctx.stroke()

    def draw_thumbnail(self, image_info, out_name) :
        img_buf = StringIO(image_info['data'][21:].decode('base64'))
        img_buf.seek(0)
        # create input image
        in_img = cairo.ImageSurface.create_from_png(img_buf)
        height,width = in_img.get_height(),in_img.get_width()

        thm_img = cairo.SurfacePattern(in_img)
        scale = width/180.
        scale_ctm = cairo.Matrix()
        scale_ctm.scale(scale,scale)
        thm_img.set_matrix(scale_ctm)
        thm_img.set_filter(cairo.FILTER_BEST)

        # create output image
        out_img = cairo.ImageSurface(cairo.FORMAT_ARGB32,180,int(height/scale))
        ctx = cairo.Context(out_img)
        ctx.set_source_rgb(1,1,1)
        ctx.paint()
        ctx.set_source(thm_img)
        ctx.paint()
        out_img.write_to_png(out_name)


class GridDiffFigure(GridFigure) :
    '''
    ACIS Grid anomaly map
    '''
    title = 'Difference from Last Year'
    def get_grid(self):
        try:
            result = AcisWS.GridCalc(self.params)
            if not result or 'error' in result.keys():
                with open('%simg/empty.png' %settings.MEDIA_DIR, 'rb') as image_file:
                    encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
                self.results = {'data':encoded_string, 'range':[0.0, 0.0], \
                'cmap': [u'#000000', u'#4300a1', u'#0077dd', u'#00aa99', u'#00ba00', \
                u'#5dff00', u'#ffcc00', u'#ee0000', u'#cccccc'], 'levels':[40,50,60], \
                'error':'bad request, check parameters %s' %str(self.params)}
            else:
                self.results = results
        except ValueError:
            with open('%simg/empty.png' %settings.MEDIA_DIR, 'rb') as image_file:
                encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
            self.results = {'data':encoded_string, 'range':[0.0, 0.0], \
            'cmap': [u'#000000', u'#4300a1', u'#0077dd', u'#00aa99', u'#00ba00', \
            u'#5dff00', u'#ffcc00', u'#ee0000', u'#cccccc'], 'levels':[40,50,60], \
            'error':'bad request, check parameters %s' %str(self.params)}

        return self.results

class Logger(object):
    def __init__(self, base_dir, log_file_name, logger_name=None):
        self.base_dir = base_dir
        self.log_file_name =  log_file_name
        self.logger_name = 'logger'
        if logger_name:self.logger_name = logger_name
        import logging

    def start_logger(self):
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        #Create file and shell handlers
        fh = logging.FileHandler(self.base_dir + self.log_file_name)
        sh = logging.StreamHandler()
        fh.setLevel(logging.DEBUG)
        sh.setLevel(logging.DEBUG)
        #create formatter and add it to handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d in %(filename)s - %(message)s')
        fh.setFormatter(formatter)
        sh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(sh)
        return logger

class FTPClass(object):
    '''
    Uploads file f to ftp_server
    in directory pub_dir
    '''
    def __init__(self, ftp_server, pub_dir, f=None, logger = None):
        self.ftp_server = ftp_server
        self.pub_dir = pub_dir
        self.f = f
        self.logger = logger

    def login(self):
        '''
        ftp server login
        '''
        try:
            self.ftp = FTP(self.ftp_server)
            self.ftp.login()
            self.ftp.set_debuglevel(0)
            if self.logger:
                self.logger.info('Successfully Connected to ftp server %s' %str(self.ftp_server))
            return None
        except Exception, e:
            return 'Error connecting to FTP server: %s' %str(e)

    def cwd(self, directory):
        try:
            self.ftp.cwd(directory)
            if self.logger:
                self.logger.info('Successfully changed to directory: %s' %str(directory))
            return None
        except:
            #Need to create sub_directories one by one
            dir_list = directory.strip('/').split('/')
            sub_dir = ''
            for d in dir_list:
                sub_dir = sub_dir +  '/' + d
                try:
                    self.ftp.cwd(sub_dir)
                    if self.logger:
                        self.logger.info('Successfully changed to directory: %s' %str(sub_dir))
                except:
                    if self.logger:
                        self.logger.info('Creating Directory: %s on %s' %(sub_dir, self.ftp_server))
                    try:
                        self.ftp.mkd(sub_dir)
                    except Exception, e:
                        return 'Error creating sub dircetory %s . Error: %s' %(str(sub_dir), str(e))
        try:
            self.ftp.cwd(self.pub_dir)
            return None
        except:
            error = 'Can not change to directory: %s on %s.' %(self.pub_dir, self.ftp_server)
            if self.logger:
                error = 'Can not change to directory: %s on %s.' %(self.pub_dir, self.ftp_server)
                self.logger.error(error)
            return error

    def delete_dir(self, base_dir, dir_name):
        error = self.ftp.cwd(base_dir)
        if error:
            if self.logger:
                self.logger.error(error)
            return error
        try:
            self.ftp.rmd(dir_name)
            return None
        except:
            error = 'Can not remove directory: %s on %s.' %(base_dir + dir_name, self.ftp_server)
            if self.logger:
                self.logger.error(error)
            return error
    '''
    def delete_file(self, base_dir, file_name):
        self.ftp.cwd(base_dir)
        try:
            self.ftp.delete(file_name)
            return None
        except:
            error = 'Can not remove directory: %s on %s.' %(base_dir + dir_name, self.ftp_server)
            if self.logger:
                error = 'Can not remove file: %s on %s.' %(base_dir + file_name, self.ftp_server)
                self.logger.error(error)
            return error

    '''
    def upload_file(self):
        fname = os.path.basename(self.f)
        ext = os.path.splitext(self.f)[1]
        #Check if file already exists
        if fname in self.ftp.nlst():
            if self.logger:
                self.logger.info('File %s already exists on server!' %str(fname))
            return None
        if ext in (".txt", ".htm", ".html", ".json"):
            try:
                if self.logger:
                    self.logger.info('Uploading file: %s' %str(fname))
                self.ftp.storlines('STOR %s' % fname, open(self.f))
                if self.logger:
                    self.logger.info('Successfully uploaded file: %s' %str(fname))
                return None
            except Exception, e:
                return 'Upload error: %s' %str(e)
        else:
            try:
                if self.logger:
                    self.logger.info('Uploading file: %s' %str(fname))
                self.ftp.storbinary('STOR %s' % fname, open(self.f, 'rb'), 1024)
                if self.logger:
                    self.logger.info('Successfully uploaded file: %s' %str(fname))
                return None
            except Exception, e:
                return 'Upload error: %s' %str(e)

    def close_ftp(self):
        self.ftp.quit()

    def FTPUpload(self):
        error = self.login()
        if not error:error = self.cwd(self.pub_dir)
        else:return 'ERROR'
        if not error:
            self.upload_file()
            return None
        self.close_ftp()

class Mail(object):
    def __init__(self, mail_server,fromaddr,toaddr,subject, message, logger=None):
        self.mail_server = mail_server
        self.fromaddr = fromaddr
        self.toaddr = toaddr
        self.subject = subject
        self.message = message
        self.logger = logger

    def write_email(self):
        '''
        Write e-mail via python's  smtp module
        '''
        msg = "From: %s\nTo: %s\nSubject:%s\n\n%s" % ( self.fromaddr, self.toaddr, self.subject, self.message )
        try:
            server = smtplib.SMTP(self.mail_server)
            if self.logger:
                self.logger.info('Connected to mail server %s' %str(self.mail_server))
        except Exception, e:
            if self.logger:
                self.logger.info('Connecting to mail server %s failed with error: %s' %(str(self.mail_server),str(e)))
            return str(e)

        server.set_debuglevel(1)
        try:
            server.sendmail(self.fromaddr, self.toaddr, msg)
            server.quit()
            if self.logger:
                self.logger.info('Email message sent to %s' %str(self.toaddr))
            return None
        except Exception, e:
            return 'Email attempt to recipient %s failed with error %s' %(str(self.toaddr), str(e))

class LargeDataRequest(object):
    '''
    This class handles large station data request freom SCENIC.
    Components:
    Keyword arguments:
        params -- data request parameters, keys:
                  select_station_by/select_grid_by: specifies type of data request (station data/gridded data)
                  start_date/end_date, temporal resolution (daily/monthly/yearly)
                  elements, units (metric/english), flags (station data only)
                  grid (gridded data only)
                  data_summary (temporal/spatial)
                        temporal_summary/spatial_summary (max, min, mean, sum)
                  date_format (yyyy-mm-dd/yyyymmdd/yyyy:mm:dd/yyyy/mm/dd)/data_format (html, csv, excel)
        logger -- logger object
    '''
    def __init__(self, params, logger):
        self.params = params
        self.logger =  logger
        #Limit of days per data request
        self.day_limit = settings.GRID_REQUEST_DAY_LIMIT
        #Limit of lats, lons for file writing
        self.max_lats = settings.MAX_LATS
        self.max_lons = settings.MAX_LONS
        #Limit of stations for file writing
        self.max_stations = settings.MAX_STATIONS
        #Set data request and formatting scripts
        if 'select_grid_by' in self.params.keys():
            self.request_data = getattr(AcisWS, 'get_grid_data')
            self.format_data = getattr(WRCCUtils, 'format_grid_data')
            self.write_to_file = getattr(WRCCUtils, 'write_griddata_to_file')
        else:
            self.request_data = getattr(AcisWS, 'get_station_data')
            self.format_data = getattr(WRCCUtils, 'format_station_data')
            self.write_to_file = getattr(WRCCUtils, 'write_station_data_to_file')

    def get_data(self):
        '''
        ACIS data request
        request_type -- grid or station
        params       -- parameter file
        '''
        self.request = {'data':[]}
        try:
            self.request = self.request_data(self.params,'sodlist-web')
        except:
            self.request['error'] = 'Invalid data request.'

    def split_data_station(self):
        '''
        Splits grid data request into smaller chunks
        for writing to file
        request     -- results of a large station data request
                       (MultiStnData call)
        max_stations -- max number of stations allowed
                       for writing to file
        return a list of stn  indices
        '''
        #Sanity check
        if 'error' in self.request.keys():return []
        if not 'data' in self.request.keys():return []
        if not self.request['data']:return []
        idx_list = [0]
        num_stations = len(self.request['data'])
        if num_stations < int(self.max_stations):
            div = 1
            rem = 0
        else:
            div = num_stations / int(self.max_stations)
            rem = num_stations % int(self.max_stations)
        for idx in range(1, div + 1):
            idx_list.append(idx * self.max_stations)
        if rem != 0:
            idx_list.append(idx_list[-1] + rem)
        if self.logger:
            self.logger.info('Splitting data request into %s chunks' % str(len(idx_list)))
        return idx_list


    def split_data_grid(self):
        '''
        Splits grid data request into smaller chunks
        by looking at lats, lons and number of days
        for writing to file
        request        -- results of a large gridde data request
                          (GridData call)
        returns list of data indices
        '''
        #Sanity check
        if 'error' in self.request.keys():return []
        if not 'meta' in self.request.keys():return []
        if not 'lat' in self.request['meta'].keys(): return []
        if not 'lat' in self.request['meta'].keys(): return []
        if not 'data' in self.request.keys() and not 'smry' in self.request.keys():return []
        idx_list = [0]
        #find number of grid points in request
        num_lats =0;num_lons=0
        try:
            num_lats = len(self.request['meta']['lat'])
        except:
            if type(self.request['meta']['lat']) == float:
                num_lats = 1
        try:
            num_lons = len(self.request['meta']['lon'][0])
        except:
            if type(self.request['meta']['lon']) == float:
                num_lons = 1
        if 'smry' in self.request.keys():days = 1
        else:days =  len(self.request['data'])
        num_loop_points = num_lats * num_lons * days
        max_loop_points = self.day_limit * self.max_lats * self.max_lons
        max_days = 0
        while (max_days + 1) * num_lats * num_lons < max_loop_points:
            max_days+=1
        div = days / max_days
        rem = days % max_days
        if div == 0:
            if 'smry' in self.request.keys():idx_list = [0, len(self.request['smry'])]
            else:idx_list = [0, len(self.request['data'])]
            return idx_list
        for idx in range(1, div + 1):
            idx_list.append(idx * max_days)
        if rem != 0:
            idx_list.append(idx_list[-1] + rem)
        return idx_list

    def split_data(self):
        idx_list = []
        if 'select_grid_by' in self.params.keys():
            idx_list = self.split_data_grid()
        elif 'select_stations_by' in self.params.keys():
            idx_list = self.split_data_station()
        return idx_list

    def load_file(self,f_name, ftp_server, ftp_dir, logger=None):
        error = None
        if logger:FTP = FTPClass(ftp_server, ftp_dir, f_name, logger)
        else: FTP = FTPClass(ftp_server, ftp_dir, f_name)
        error = FTP.FTPUpload()
        if error:
            if self.logger:
                self.logger.error('ERROR tranferring %s to ftp server. Error %s'%(os.path.basename(f_name),error))
            os.remove(f_name)
        return error


    def format_write_transfer(self,params_file, params_files_failed,out_file, ftp_server, ftp_dir,max_file_size,logger=None):
        '''
        Formats data for file output.
        Writes data to files of max size max_file_size in chunks.
        Transfers data files to ftp server.
        Returns list of output files of max size max_file_size
        '''
        f_ext = os.path.splitext(out_file)[1]
        f_base = os.path.splitext(out_file)[0]
        file_idx = 1
        f_name = f_base + '_' + str(file_idx) + f_ext + '.gz'
        out_files = []
        f = gzip.open(f_name, 'wb')
        if self.logger:
            self.logger.info('Splitting data into smaller chunks for formatting')
        idx_list = self.split_data()
        if 'smry' in self.request.keys():
            generator = (self.request['smry'][idx_list[idx]:idx_list[idx+1]] for idx in range(len(idx_list) - 1) )
        else:
            generator = (self.request['data'][idx_list[idx]:idx_list[idx+1]] for idx in range(len(idx_list) - 1) )
        if self.logger:
            self.logger.info('Formatting data')
        idx = 0
        for data in generator:
            idx+=1
            req_small={}
            for key, val in self.request.iteritems():
                if key != 'data':
                    req_small[key] = val
            req_small['data'] = data
            temp_file = settings.DATA_REQUEST_BASE_DIR + 'temp_out'
            if self.logger:
                self.logger.info('Formatting data chunk %s' %str(idx))
            results_small = self.format_data(req_small, self.params)
            if self.logger:
                self.logger.info('Finished formatting data chunk %s' %str(idx))
                self.logger.info('Writing data chunk %s to file' %str(idx))
            self.write_to_file(results_small,self.params,f=temp_file)
            if self.logger:
                self.logger.info('Finished writing data chunk %s to file' %str(idx))
                self.logger.info('Appending data chunk  %s to output file %s' %(str(idx), os.path.basename(f_name)))
            with open(temp_file, 'r') as temp:
                f.write(temp.read())
            #Check file size and open new file if needed
            fs = str(round(os.stat(f_name).st_size / 1048576.0,2)) + 'MB'
            ms = str(round(settings.MAX_FILE_SIZE / 1048576.0,2))+ 'MB'
            self.logger.info('FILE SIZE %s , MAX FILE SIZE %s' %(fs, ms))
            if os.stat(f_name).st_size < max_file_size:
                continue
            try:f.close()
            except:pass
            if self.logger:
                self.logger.info('FILE SIZE %s' %fs)
            out_files.append(os.path.basename(f_name) + ' '  + fs)
            logger.info('Files: %s' %str(out_files))
            #transfer to FTP and delete file
            error = self.load_file(f_name, ftp_server, ftp_dir, logger)
            if error:params_files_failed.append(params_file)
            os.remove(f_name)
            file_idx+=1
            #new file
            f_name = f_base +  '_' + str(file_idx) + f_ext +'.gz'
            f = gzip.open(f_name, 'wb')
        if self.logger:
            self.logger.info('Data request completed')
        #Transfer last file
        try:f.close()
        except:pass
        if not os.stat(f_name).st_size > 0:
            return out_files
        out_files.append(os.path.basename(f_name) + ' '  + str(round(os.stat(f_name).st_size / 1048576.0, 2)) + 'MB')
        f.close()
        error = self.load_file(f_name, ftp_server, ftp_dir, logger)
        if error:params_files_failed.append(params_file)
        os.remove(f_name)
        return out_files




