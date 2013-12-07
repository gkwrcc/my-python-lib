#!/usr/bin/python
'''
module WRCCClasses.py

Defines classes used in my_acis project
'''

##############################################################################
# import modules required by Acis
#import  pprint, time
import time
import json
from cStringIO import StringIO
import cairo
import base64
import datetime
import csv
from xlwt import Workbook
from django.http import HttpResponse

#WRCC modules
import AcisWS, WRCCDataApps, WRCCUtils, WRCCData

MEDIA_URL = '/www/apps/csc/dj-projects/my_acis/media/'


class DownloadDataJob:
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
            labels = ['Station Name', 'Station ID', 'Station Network', 'Station State', 'Start Year', 'End Year']
            for idx, key in enumerate(['stn_name', 'stn_id', 'stn_network', 'stn_state', 'record_start', 'record_end']):
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
                row.append(key_val[0] + ': ' + key_val[1])
                if (idx + 1) % 2 == 0 or idx == len(self.header) - 1:
                    writer.writerow(row)
                    row = []
            writer.writerow(row)
            writer.writerow([])
            if self.app_name == 'Sodxtrmts':
                row = ['a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,']
                writer.writerow(row)
                row = ['z = 26 or more days missing, A = Accumulations present']
                writer.writerow(row)
                row=['Long-term means based on columns; thus, the monthly row may not']
                writer.writerow(row)
                row=['sum (or average) to the long-term annual value.']
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


class SODDataJob:
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
        self.el_type_element_dict = {
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
            'range':['maxt', 'mint'],
            'avgt':['maxt', 'mint'],
            'dtr':['maxt', 'mint'],
            'dd_raw':['maxt', 'mint'],
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

    def set_area_params(self):
        area = None; val=None
        if 'sid' in self.params.keys():area = 'sids';val = self.params['sid']
        if 'sids' in self.params.keys():area = 'sids';val = self.params['sids']
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
            'countys':[]
        }
        keys = ['state', 'll', 'elev', 'uid', 'climdiv', 'county']
        area, val = self.set_area_params()
        if area and val:
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
                #find other meta data info
                #NOTE: ACIS quirk: sometimes other meta data attributes don't show up
                for key in keys:
                    meta_dict_key = key + 's'
                    if key in stn.keys():
                        meta_dict[meta_dict_key].append(str(stn[key]))
                    else:
                        meta_dict[meta_dict_key].append(' ')
        self.station_ids = meta_dict['ids']
        return meta_dict['names'], meta_dict['states'], meta_dict['ids'], meta_dict['networks'], meta_dict['lls'], meta_dict['elevs'], meta_dict['uids'], meta_dict['climdivs'], meta_dict['countys']

    def get_dates_list(self):
        '''
        Find list of dates lying within start and end date
        Takes care of data formatting and por cases.
        '''
        dates = []
        s_date, e_date = self.set_start_end_date()
        if s_date and e_date and len(s_date) == 8 and len(e_date) == 8:
            #convert to datetimes
            if self.app_name in ['Soddyrec', 'Soddynorm', 'Soddd', 'Sodpad', 'Sodsumm', 'Sodpct', 'Sodthr', 'Sodxtrmts', 'Sodpiii']:
                #data is grouped by year so we need to change start and end_dates
                #to match whole year
                s_date = s_date[0:4] + '0101'
                e_date = e_date[0:4] + '1231'
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
                #note, these apps are grouped by year and return a 366 day year even for non-leap years
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
                    el_dict_new['smry'] = smry
                    elems.append(el_dict_new)
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
        return params


    def format_data(self, request, station_ids, elements):
        '''
        Formats output of data request dependent on
        application
        request is the output of a MultiStnData call
        '''
        #Set up data output dictonary
        error = ''
        data = [[] for i in station_ids]
        for i, stn in enumerate(station_ids):
            if self.app_name == 'Soddyrec':
                data[i] = [[['#', '#', '#', '#', '#', '#','#', '#'] for k in range(366)] for el in elements]
            elif self.app_name in ['Sodrun', 'Sodrunr']:
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

    def get_data(self):
        elements = self.get_element_list()
        station_ids, station_names = self.get_station_ids_names()
        dates = self.get_dates_list()
        #Set up resultsdict
        resultsdict = {
                    'data':[],
                    'dates':dates,
                    'elements':elements,
                    'station_ids':station_ids,
                    'station_names':station_names}

        #Make data request
        data_params = self.set_request_params()
        request = AcisWS.MultiStnData(data_params)
        resultsdict['data'], resultsdict['error'] = self.format_data(request, station_ids, elements)
        return resultsdict

class SODApplication:
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
                    'coop_station_ids': self.data['station_ids'],
                    'data':self.data['data'],
                    'elements':self.data['elements'],
                    'dates':self.data['dates'],
                    'station_names':self.data['station_names']
                    }
        if self.app_specific_params:
            app_params.update(self.app_specific_params)
        #Sanity check, make sure data has data
        #if 'error' in self.data.keys() or not self.data['data']:
        #    return {}
        print app_params.keys()
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

class SodGraphicsJob:
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

class StnDataJob:
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
    image_padding = 20,80
    title = 'Acis GridData map'
    def __init__(self, params, img_offset=10, text_offset=(50, 50)) :
        if 'state' in params.keys():
            self.region = 'state'
        elif 'bbox' in params.keys():
            self.region = 'bbox'
        if self.region == 'bbox':
            self.bbox = params['bbox']
        elif self.region == 'state':
            self.state = params['state']
        self.params = params
        if 'date' in params.keys():
            self.date = params['date']
        elif 'this' in params.keys():
            self.date = params['this']['date']
        else:
            self.date = date = time.strftime('%Y%m%d')
        if 'data' in params.keys():
            self.data = params['data']
        else:
            self.data = None
        self.image_offset = img_offset
        self.text_offset = text_offset


    def get_grid(self) :
        try:
            if not self.data:
                result = AcisWS.GridData(self.params)
            else:
                result = self.data
            if not result or 'error' in result.keys() or not 'data' in result.keys():
                with open('%simg/empty.png' %MEDIA_URL, 'rb') as image_file:
                    encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
                self.results = {'data':encoded_string, 'range':[0.0, 0.0], \
                'cmap': [u'#000000', u'#4300a1', u'#0077dd', u'#00aa99', u'#00ba00', \
                u'#5dff00', u'#ffcc00', u'#ee0000', u'#cccccc'], 'levels':[40,50,60], \
                'error':'bad request, check parameters %s' %str(self.params)}
            else:
                self.results = result
        except ValueError:
            with open('%simg/empty.png' %MEDIA_URL, 'rb') as image_file:
                encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
            self.results = {'data':encoded_string, 'range':[0.0, 0.0], \
            'cmap': [u'#000000', u'#4300a1', u'#0077dd', u'#00aa99', u'#00ba00', \
            u'#5dff00', u'#ffcc00', u'#ee0000', u'#cccccc'], 'levels':[40,50,60], \
            'error':'bad request, check parameters %s' %str(self.params)}

        return self.results

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
        ctx.set_source_rgb(1.,1.,1.)
        ctx.paint()
        # place image
        ctx.set_source_surface(in_img,pad_w/2,self.image_offset)
        ctx.paint()
        # frame image
        ctx.set_line_width(1.0)
        ctx.set_source_rgb(0,0,0)
        ctx.rectangle(pad_w/2,self.image_offset,width,height)
        ctx.stroke()

        #self.add_title()
        ctx.set_matrix(cairo.Matrix(y0=self.image_offset+height+5))
        #self.add_footer()
        ctx.set_matrix(cairo.Matrix(x0=15+25,
            y0=self.image_offset+height+30))
        self.add_legend(image_info)

        out_buf = open(out_name,'w')
        out_img.write_to_png(out_buf)

    def add_title(self) :
        ctx = self.ctx
        date_str = '%s to %s' % (self.params['sdate'], self.params['edate'])
        ctx.set_font_size(16.)
        #if self.region == 'eny' : just = 'c'
        #else :
        just = 'l'
        ctx.move_to(*self.text_offset)
        self.place_text(self.title,j=just)
        ctx.move_to(*self.text_offset)
        ctx.rel_move_to(0,20)
        self.place_text(date_str,j=just)
        ctx.move_to(*self.text_offset)
        ctx.rel_move_to(0,25)
        ctx.set_font_size(16.)
        ctx.set_source_rgb(.8,.1,.1)
        if 'bbox' in self.params.keys():
            fig_title = 'Element: %s Bounding Box: %s' %( self.params['elems'][0]['name'], self.params['bbox'])
        elif 'state' in self.params.keys():
            fig_title = 'Element: %s State: %s' %( self.params['elems'][0]['name'], self.params['state'])
        #self.place_text(fig_title,j=just,v='t')
        self.place_text(fig_title,j=just,v='t')

    def add_legend(self, image_info) :
        ctx = self.ctx
        #ctx.set_matrix(cairo.Matrix(yy=-1,y0=height))
        ctx.set_font_size(12.)
        w = 450./len(image_info['cmap'])
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
    title = 'Difference from Last Year'
    def get_grid(self):
        try:
            result = AcisWS.GridCalc(self.params)
            if not result or 'error' in result.keys():
                with open('%simg/empty.png' %MEDIA_URL, 'rb') as image_file:
                    encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
                self.results = {'data':encoded_string, 'range':[0.0, 0.0], \
                'cmap': [u'#000000', u'#4300a1', u'#0077dd', u'#00aa99', u'#00ba00', \
                u'#5dff00', u'#ffcc00', u'#ee0000', u'#cccccc'], 'levels':[40,50,60], \
                'error':'bad request, check parameters %s' %str(self.params)}
            else:
                self.results = results
        except ValueError:
            with open('%simg/empty.png' %MEDIA_URL, 'rb') as image_file:
                encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
            self.results = {'data':encoded_string, 'range':[0.0, 0.0], \
            'cmap': [u'#000000', u'#4300a1', u'#0077dd', u'#00aa99', u'#00ba00', \
            u'#5dff00', u'#ffcc00', u'#ee0000', u'#cccccc'], 'levels':[40,50,60], \
            'error':'bad request, check parameters %s' %str(self.params)}

        return self.results
