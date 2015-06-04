#!/usr/bin/python
'''
module WRCCClasses.py
Defines classes used in the my_acis project
'''

##############################################################################
# import modules required by Acis
#import  pprint, time
import time, datetime, re, os
import numpy as np
import scipy
import json
from cStringIO import StringIO
try:
    import cairo
except:
    import cairocffi as cairo
import base64
import csv
from xlwt import Workbook
import logging
from ftplib import FTP
import smtplib
import gzip

try:
    #Settings
    #from django.conf import settings
    import my_acis.settings as settings
except:
    try:
        import my_acis_settings as settings
    except:
        pass

#WRCC modules
import AcisWS, WRCCDataApps, WRCCUtils, WRCCData

class GraphDictWriter(object):
    '''
    Writes dictionary for plotting
    with generateHighartsFigure.js
    Args:
        form: user input dictionary
        data: element data formatted for highcarts plotting
    Returns:
        Dictionary with keys:
            data
            chartType
            title, subtitle, legendTitle
            start_date, end_date
            yLabel, xLabel
            axis_min
            elUnits
    '''
    def __init__(self, form, data,element = None, name = None):
        self.form = form
        self.data = data
        self.element = element
        self.name = name
        if self.element is None:
            self.element = form['element']
        if 'start_year' in self.form.keys() and not 'start_date' in self.form.keys():
            self.form['start_date'] = self.form['start_year']
        if 'end_year' in self.form.keys() and not 'end_date' in self.form.keys():
            self.form['end_date'] = self.form['end_year']


    def set_chartType(self):
        el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element)
        if el_strip in ['pcpn','snow', 'snwd', 'hdd','cdd','gdd']:
            chartType = 'column'
        else:
            chartType = 'spline'
        return chartType

    def set_elUnits(self):
        el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element)
        if 'units' in self.form.keys() and self.form['units'] == 'metric':
            elUnits = WRCCData.UNITS_METRIC[el_strip]
        else:
            elUnits = WRCCData.UNITS_ENGLISH[el_strip]
        return elUnits

    def set_date(self,date):
        if len(date) == 8:
            return date[0:4] + '-' + date[4:6] + '-' + date[6:8]
        else:
            return date

    def set_title(self):
        #NOTE: element comes from form_cleaned as english
        el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element)
        '''
        if self.form['units'] == 'metric':
            base_temp = WRCCUtils.convert_to_metric('base_temp',base_temp)
        '''
        unit = self.set_elUnits()
        title = ''
        if 'spatial_summary' in self.form.keys():
            title = WRCCData.DISPLAY_PARAMS[self.form['spatial_summary']]
            title += ' of ' + WRCCData.DISPLAY_PARAMS[el_strip]
        elif 'temporal_summary' in self.form.keys() and not 'start_month' in self.form.keys():
            title = WRCCData.DISPLAY_PARAMS[self.form['temporal_summary']]
            title += ' of ' + WRCCData.DISPLAY_PARAMS[el_strip]
        elif 'monthly_statistic' in self.form.keys():
            if self.form['monthly_statistic'] == 'ndays':
                title = 'Number of days where ' +  WRCCData.DISPLAY_PARAMS[el_strip]
                if self.form['less_greater_or_between'] == 'l':
                    title+= ' less than ' + str(self.form['threshold_for_less_than']) + ' '  + unit
                if self.form['less_greater_or_between'] == 'g':
                    title+= ' greater than ' + str(self.form['threshold_for_greater_than']) + ' '  + unit
                if self.form['less_greater_or_between'] == 'b':
                    title+= ' between ' + self.form['threshold_low_for_between'] + ' '  + unit +\
                    ' and ' +  self.form['threshold_high_for_between'] + ' '  + unit
            else:
                title = WRCCData.DISPLAY_PARAMS[self.form['monthly_statistic']]
                title += ' of ' + WRCCData.DISPLAY_PARAMS[el_strip]
        elif 'station_id' in self.form.keys() or 'location' in self.form.keys():
            if 'user_area_id' in self.form.keys():
                title = self.form['user_area_id']
            elif 'station_id' in self.form.keys():
                title = 'Station ID: ' + self.form['station_id']
            elif 'location' in self.form.keys():
                 title = 'Location: ' + self.form['location']
            title += ', '
            if 'temporal_summary' in self.form.keys():
                title += WRCCData.DISPLAY_PARAMS[self.form['temporal_summary']] + ' of '
            elif 'spatial_summary' in self.form.keys():
                title += WRCCData.DISPLAY_PARAMS[self.form['spatial_summary']] + ' of '
            title += WRCCData.DISPLAY_PARAMS[el_strip]
            if self.name is None:
                self.name = title.split(', ')[-1]
        if base_temp:
            title+= ' Base: ' + str(base_temp)
        return title
        title += ' (' + unit + ')'
        return title

    def set_subTitle(self):
        subTitle = ''
        if 'spatial_summary' in self.form.keys():
            subTitle = WRCCData.DISPLAY_PARAMS[self.form['area_type']]
            subTitle+= ': ' + self.form[self.form['area_type']]
        if 'monthly_statistic' in self.form.keys():
            if 'station_id' in self.form.keys():
                try:
                    subTitle = 'Station: ' + self.form['user_area_id']
                except:
                    subTitle = 'Station: ' + self.form['station_id']
            if 'location' in self.form.keys():
                subTitle = 'Location: ' + self.form['location']
        if 'start_month' in self.form.keys() and 'start_day' in self.form.keys():
            if 'end_month' in self.form.keys() and 'end_day' in self.form.keys():
                subTitle = 'From ' + WRCCData.NUMBER_TO_MONTH_NAME[self.form['start_month']]
                subTitle+= ', ' + self.form['start_day'] + ' To '
                subTitle+= WRCCData.NUMBER_TO_MONTH_NAME[self.form['end_month']]
                subTitle+= ', ' + self.form['end_day']
        return subTitle


    def set_xLabel(self):
        xLabel = ''
        if 'start_date' in self.form.keys() and 'end_date' in self.form.keys():
            xLabel = 'Start Date: '
            xLabel+= WRCCUtils.format_date_string(self.form['start_date'],'dash')
            xLabel+= ' End Date: '
            xLabel+= WRCCUtils.format_date_string(self.form['end_date'],'dash')
        if 'start_year' in self.form.keys() and 'end_year' in self.form.keys():
            xLabel = 'Start Year: '
            xLabel+= self.form['start_year']
            xLabel+= ' End Year: '
            xLabel+= self.form['end_year']
        return xLabel

    def set_yLabel(self):
        yLabel = self.set_elUnits()
        return yLabel

    def set_legendTitle(self):
        legendTitle = ''
        return legendTitle

    def set_axisMin(self):
        el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element)
        if el_strip in ['snow', 'snwd', 'hdd','cdd','gdd']:
            axisMin = 0
        else:
            axisMin = None
        return axisMin

    def set_plotColor(self):
        if 'monthly_statistic' in self.form.keys():
            pl_color  = WRCCData.PLOT_COLOR_MONTH[self.name.upper()][0]
        else:
            el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element)
            pl_color = WRCCData.PLOT_COLOR[el_strip]
        return pl_color

    def set_runningMeanColor(self):
         if 'monthly_statistic' in self.form.keys():
            rm_color  = WRCCData.PLOT_COLOR_MONTH[self.name.upper()][1]
         else:
            el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element)
            rm_color =  WRCCData.RM_COLOR[el_strip]
         return rm_color

    def set_seriesName(self):
        sname = self.name
        if 'spatial_summary' in self.form.keys():
            el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element)
            if self.form['units'] == 'metric':
                base_temp = WRCCUtils.convert_to_metric('base_temp',base_temp)
            sname = WRCCData.DISPLAY_PARAMS[el_strip]
            if base_temp:
                sname+=' ' + str(base_temp)
        if 'monthly_statistic' in self.form.keys():
            if self.name != None:
                sname = self.name
        return sname

    def write_dict(self):
        datadict = {
            'chartType':self.set_chartType(),
            'data':self.data,
            'element':self.element,
            'elUnits':self.set_elUnits(),
            'startDate':self.set_date(self.form['start_date']),
            'endDate': self.set_date(self.form['end_date']),
            'title':self.set_title(),
            'subTitle':self.set_subTitle(),
            'legendTitle':self.set_legendTitle(),
            'xLabel':self.set_xLabel(),
            'yLabel':self.set_yLabel(),
            'axisMin':self.set_axisMin(),
            'series_color':self.set_plotColor(),
            'running_mean_color':self.set_runningMeanColor(),
            'seriesName':self.set_seriesName(),
        }
        return datadict

class CsvWriter(object):
    '''
    Writes data to csv
    Keyword arguments:
        req data requestdictionary with keys
            data,meta, smry,form,errors
        f file, if given, data will be written to file
        response HTTPResponse object, if given, output file will appear in browser
    '''
    def __init__(self, req, f=None, response=None):
        self.req = req
        self.form =  self.req['form']
        self.response = response
        self.f = f
        self.delim = WRCCData.DELIMITERS[self.form['delimiter']]

    def set_data_type(self):
        self.data_type = WRCCUtils.get_data_type(self.form)

    def set_data(self):
        if 'smry' in self.req.keys() and self.req['smry']:
            self.data = self.req['smry']
            self.smry = True
        else:
            self.data = self.req['data']
            self.smry = False

    def set_meta_keys(self):
        self.meta_keys = WRCCUtils.get_meta_keys(self.form)

    def set_writer(self):
        import csv
        if self.f is not None:
            #self.csvfile = open(self.f, 'w+')
            self.csvfile = gzip.open(self.f, 'wb')
            self.writer = csv.writer(self.csvfile, delimiter=self.delim )
        if self.response is not None:
            self.writer = csv.writer(self.response, delimiter=self.delim)

    def write_header(self):
        #Search params header:
        if self.smry and self.form['data_summary'] != 'None':
            header_keys = [self.form['area_type'],'data_summary','start_date', 'end_date']
        else:
            header_keys = [self.form['area_type'],'start_date', 'end_date']
        if 'data_type' in self.form.keys():
            header_keys.insert(0,'data_type')
        if 'user_area_id' in self.form.keys():
            header_keys.insert(0,'user_area_id')
        header = WRCCUtils.form_to_display_list(header_keys, self.form)
        for key_val in header:
            row = ['*' + key_val[0].replace(' ',''),key_val[1]]
            self.writer.writerow(row)

        if self.data_type == 'station' and not self.smry:
            row = ['*DataFlags','M=Missing', 'T=Trace', 'S=Subsequent', 'A=Accumulated']
            self.writer.writerow(row)

    def write_data(self):
        #Loop over data points
        for p_idx, p_data in enumerate(self.data):
            self.writer.writerow(['*'])
            #Write meta
            meta_display_params = WRCCUtils.metadict_to_display_list(self.req['meta'][p_idx], self.meta_keys, self.form)
            for key_val in meta_display_params:
                row = ['*' + key_val[0].replace(' ',''),' '.join(key_val[1])]
                self.writer.writerow(row)
            #Write data
            self.writer.writerow(['*'])
            for d_idx, date_data in enumerate(p_data):
                if d_idx == 0:
                    #Data Header
                    h = ['*' + date_data[0]]
                else:
                    h = [date_data[0]]
                d = date_data[1:]
                self.writer.writerow(h + d)


    def write_summary(self):
        for s_idx, s_data in enumerate(self.data):
            if s_idx == 0:
                #Data Header
                s_data[0] = '*' + s_data[0]
            row = s_data
            self.writer.writerow(row)

    def close_writer(self):
        try:
            self.csvfile.close()
        except:
            pass

    def write_to_file(self):
        self.set_data_type()
        self.set_data()
        self.set_meta_keys()
        self.set_writer()
        self.write_header()
        if self.smry:
            self.write_summary()
        else:
            self.write_data()
        self.close_writer()

class ExcelWriter(object):
    '''
    Writes data to excel
    Keyword arguments:
        req data requestdictionary with keys
            data, meta, smry, form, errors
            f file, if given, data will be written to file
        response HTTPResponse object, if given, output file will appear in browser
    '''
    def __init__(self, req, f = None, response = None):
        self.req = req
        self.form =  self.req['form']
        self.f = f
        self.response = response
        self.delim = WRCCData.DELIMITERS[self.form['delimiter']]

    def set_data_type(self):
        self.data_type = WRCCUtils.get_data_type(self.form)

    def set_data(self):
        if 'smry' in self.req.keys() and self.req['smry']:
            self.data = self.req['smry']
            self.smry = True
        else:
            self.data = self.req['data']
            self.smry = False

    def set_meta_keys(self):
        self.meta_keys = WRCCUtils.get_meta_keys(self.form)

    def set_workbook(self):
        from xlwt import Workbook
        self.wb = Workbook()

    def write_header(self,ws):
        '''
        if self.smry:
            header_keys = [self.form['area_type'],'data_summary','start_date', 'end_date']
            header = WRCCUtils.form_to_display_list(header_keys, self.form)
        else:
            header = []
        for k_idx, key_val in enumerate(header):
            ws.write(0,k_idx,key_val[0].replace(' ',''))
            ws.write(1,k_idx,key_val[1])
        '''
        #Search params header:
        if self.smry and self.form['data_summary'] != 'None':
            header_keys = [self.form['area_type'],'data_summary','start_date', 'end_date']
        else:
            header_keys = [self.form['area_type'],'start_date', 'end_date']
        if 'data_type' in self.form.keys():
            header_keys.insert(0,'data_type')
        if 'user_area_id' in self.form.keys():
            header_keys.insert(0,'user_area_id')
        header = WRCCUtils.form_to_display_list(header_keys, self.form)
        for k_idx, key_val in enumerate(header):
            ws.write(0,k_idx,key_val[0].replace(' ',''))
            ws.write(1,k_idx,key_val[1])

    def write_data(self):
        #Loop over data points
        for p_idx, p_data in enumerate(self.data):
            #Write meta
            meta_display_params = WRCCUtils.metadict_to_display_list(self.req['meta'][p_idx], self.meta_keys, self.form)
            #New sheet for each point
            ws = self.wb.add_sheet('Point' + str(p_idx))
            self.write_header(ws)
            #Write header
            for m_idx,key_val in enumerate(meta_display_params):
                ws.write(3,m_idx,meta_display_params[m_idx][0])
                ws.write(4,m_idx,' '.join(meta_display_params[m_idx][1]))
            if self.data_type =='station':
                ws.write(6,0,'DataFlags')
                ws.write(6,1,'M=Missing')
                ws.write(6,2,'T=Trace')
                ws.write(6,3,'S=Subsequent')
                ws.write(6,4,'A=Accumulated')
            #Write data
            for date_idx in range(len(p_data)):
                for data_idx in range(len(p_data[date_idx])):
                    try:
                        ws.write(date_idx + 8, data_idx, float(p_data[date_idx][data_idx]))
                    except:
                        ws.write(date_idx + 8, data_idx, p_data[date_idx][data_idx])
        #Save workbook
        if self.f is not None:
            self.wb.save(self.f)
        if self.response is not None:
            self.wb.save(self.response)

    def write_summary(self):
        ws = self.wb.add_sheet('1')
        self.write_header(ws)
        #Write data
        for row_idx in range(len(self.data)):
            for val_idx in range(len(self.data[row_idx])):
                try:
                    val =  round(float(self.data[row_idx][val_idx]),4)
                except:
                    val = self.data[row_idx][val_idx]
                ws.write(row_idx + 4 ,val_idx,val)
        #Save workbook
        if self.f is not None:
            self.wb.save(self.f)
        if self.response is not None:
            self.wb.save(self.response)

    def write_to_file(self):
        self.set_data_type()
        self.set_data()
        self.set_meta_keys()
        self.set_workbook()
        #self.write_header()
        if self.smry:
            self.write_summary()
        else:
            self.write_data()

class DataComparer(object):
    '''
    Compare historic station data with gridded data at a lat/lon coordinate.
    The closest gridpoint to lat/lon and the closest
    station to lat/lo are found
    Data is obtained for both.

    Keywork arguments:
        form: Dictionary containing request parameters:
            location: lon, lat
            grid: grid ID
            start_date/end_date of request
            elements: comma seperated list of element abbreviations
            degree_days: comma separated list of degree days with irregular base temperatures
            units: metric or english
    '''
    def __init__(self, form):
        self.form = form
        self.location = form['location']
        self.grid = form['grid']
        self.start_date = form['start_date']
        self.end_date = form['end_date']
        self.element = form['element']
        if isinstance(self.element, list):
            self.elements = [form['element']]
            self.element = form['element'][0]
        else:
            self.elements = [form['element']]
        if isinstance(self.elements,list):
            self.elements  = ','.join(self.elements)
        self.degree_days = None
        if 'degree_days' in form.keys():
            self.degree_days = form['degree_days']
        self.units = form['units']

    def hms_to_seconds(self,date_string):
        #Convert python date string to javascript milliseconds
        t = date_string.replace('-','').replace(':','').replace('/','')
        y = int(t[0:4]);m = int(t[4:6]);d = int(t[6:8])
        dt = datetime.datetime(y,m,d)
        #Python does seconds so we need to multiply by 1000
        s = int(time.mktime(dt.timetuple())) *1000
        return s

    def get_bbox(self,length):
        '''
        Returns bounding box around location
        Bounding box = (lon-length, lat - length,lon+length, lat+length)
        '''
        lat = self.location.split(',')[1]
        lon = self.location.split(',')[0]
        lower_left = str(float(lon) - float(length)) + ',' + str(float(lat) - float(length))
        upper_right = str(float(lon) + float(length)) + ',' + str(float(lat) + float(length))
        bbox = lower_left + ',' + upper_right
        return bbox

    def combine_elements(self):
        if not self.degree_days:
            return self.elements
        if self.units == 'english':
            return self.elements + ',' + self.degree_days
        dd_els = ''
        for dd_idx, dd in enumerate(self.degree_days.split(',')):
            el = dd[0:3]
            val = dd[3:]
            new_val = int(round(WRCCUtils.convert_to_english(el,val)))
            dd_els+=el+str(new_val)
            if dd_idx < len(self.degree_days.split(',')) - 1:
                dd_els+=','
        return self.elements + ',' + dd_els

    def check_valid_daterange(self,vd):
        '''
        Checks if valid daterange of station for an element
        lies between start and end date of request
        '''
        sd = self.start_date.replace('-','').replace('/','').replace(':','')
        ed = self.end_date.replace('-','').replace('/','').replace(':','')
        vds = vd[0].replace('-','')
        vde = vd[1].replace('-','')
        sd_dt = datetime.datetime(int(sd[0:4]),int(sd[4:6]),int(sd[6:8]))
        ed_dt = datetime.datetime(int(ed[0:4]),int(ed[4:6]),int(ed[6:8]))
        vds_dt = datetime.datetime(int(vds[0:4]),int(vds[4:6]),int(vds[6:8]))
        vde_dt = datetime.datetime(int(vde[0:4]),int(vde[4:6]),int(vde[6:8]))
        if vde_dt< sd_dt:
            return False
        if vds_dt >=ed_dt:
            return False
        if vds_dt <= sd_dt and sd_dt < vde_dt:
            return True
        if sd_dt <= vds_dt and vde_dt <= ed_dt:
            return True
        if vds_dt <= ed_dt and vds_dt>=sd_dt:
            return True
        if sd_dt <= vde_dt and vde_dt <= ed_dt:
            return True
        return False

    def find_closest_station(self):
        '''
        Finds closest station to lon/lat grid coordinate
        such that each element's valid daterange is overlapping
        with start/end date period of request
        '''
        length = 0.01
        stn_meta = {}
        #els = self.combine_elements()
        while not stn_meta:
            bbox = self.get_bbox(length)
            meta_params = {
                'bbox':bbox,
                "meta":"name,state,sids,ll,elev,uid,valid_daterange",
            }
            meta_params['elems'] = self.element
            try:
                req = AcisWS.StnMeta(meta_params)
                req['meta']
            except:
                req = {'meta':[]}
            if not req['meta']:
                length = 2.0*length
                if length >2:
                    return {}
                else:
                    continue
            '''
            if len(req['meta']) == 1:
                stn_meta = req['meta'][0]
                continue
            '''
            lat = float(self.location.split(',')[1])
            lon = float(self.location.split(',')[0])
            stn_lat = None
            stn_lon = None
            dist = 999999999.0;idx = None
            for stn_idx, stn in enumerate(req['meta']):
                try:
                    stn_lat = req['meta'][stn_idx]['ll'][1]
                    stn_lon = req['meta'][stn_idx]['ll'][0]
                except:
                    continue
                #Checkvalid_dateranges
                #If one exists, ok to proceed
                if not 'valid_daterange' in req['meta'][stn_idx]:
                    continue
                for vd in req['meta'][stn_idx]['valid_daterange']:
                    vd_found = False
                    if vd:
                        valid_dr = self.check_valid_daterange(vd)
                        if valid_dr:
                            vd_found = True
                            #stn_meta = req['meta'][stn_idx]
                            continue
                        else:
                            break
                    else:
                        break
                if not vd_found:
                    continue
                else:
                    return req['meta'][stn_idx]
                try:
                    dist_temp = abs(stn_lat - lat) + abs(stn_lon - lon)
                except:
                    continue

                if dist_temp < dist:
                    dist = dist_temp;idx = stn_idx
                    stn_meta = req['meta'][idx]
            if not idx:
                length = 2*length
                continue
        return stn_meta

    def get_data(self):
        #Grid Data
        #els =  self.combine_elements()
        data_params = {
            'loc': self.location,
            'grid':self.grid,
            'elems': self.element,
            'sdate': self.start_date,
            'edate': self.end_date,
            'meta':'ll,elev'
        }
        try:
            gdata = AcisWS.GridData(data_params)
        except Exception, e:
            gdata = {'data':[], 'meta': [],'error': str(e)}
        stn_meta = self.find_closest_station()
        if not stn_meta or 'sids' not in stn_meta.keys():
            err = 'No station could be found near given lon,lat: %s' %str(self.location)
            sdata = {'data':[], 'meta': [], 'error': err}
        else:
            del data_params['loc']
            del data_params['grid']
            data_params['sid'] = str(stn_meta['sids'][0].split(' ')[0])
            data_params['meta'] = 'name,state,sids,ll,elev,uid,valid_daterange'
            try:
                sdata = AcisWS.StnData(data_params)
            except Exception, e:
                sdata = {'data':[], 'meta': [],'error': str(e)}
        return gdata, sdata

    def get_graph_data(self,gdata,sdata):
        '''
        For each element return series data [date, val] for both grid and station data.
        Returns dict {el1:[[Date1, el_val1],[Date,el_val2],...], 'el2':...}
        '''
        graph_data = []
        #els = self.combine_elements()
        gloc = str(round(gdata['meta']['lon'],2)) + ', ' + str(round(gdata['meta']['lat'],2))
        sloc = ','.join([str(round(s,2)) for s in sdata['meta']['ll']])
        sname = str(sdata['meta']['name'])
        sids = ''
        for idx, sid in enumerate(sdata['meta']['sids']):
            sids+= sid.split(' ')[0]
            if idx != len(sdata['meta']['sids']) - 1:
                sids+=', '
        s_graph_title = 'Station' + sname + ', IDs: (' + sids + ')'
        g_graph_title =  'Location: ' +  gloc
        sid = str(sdata['meta']['sids'][0].split(' ')[0])
        el_strip, base_temp = WRCCUtils.get_el_and_base_temp(self.element, units=self.units)
        grid_data = [];station_data = [];
        for date_idx, data in enumerate(gdata['data']):
            try:
                if self.units == 'english':
                    gd = float(data[1])
                else:
                    gd = WRCCUtils.convert_to_metric(el_strip,float(data[1]))
            except:
                gd = None
            try:
                if self.units == 'english':
                    sd = float(sdata['data'][date_idx][1])
                else:
                    sd = WRCCUtils.convert_to_metric(el_strip,float(sdata['data'][date_idx][1]))
            except:
                sd = None
            int_time = self.hms_to_seconds(str(data[0]))
            grid_data.append([int(int_time),gd])
            station_data.append([int(int_time),sd])
            SGDWriter = GraphDictWriter(self.form, station_data, self.element, name = sname)
            s_graph_dict = SGDWriter.write_dict()
            GGDWriter =  GraphDictWriter(self.form, grid_data, self.element, name = g_graph_title)
            g_graph_dict = GGDWriter.write_dict()
            graph_data = [s_graph_dict,g_graph_dict]
        return graph_data

    def get_statistics(self,s_graph_dict, g_graph_dict):
        stats = {
            'max':[None, None],
            'min':[None, None],
            'mean':[None, None],
            'median':[None, None],
            'std':[None, None],
            'skew':[None, None],
            'pearsonc':None,
            'pearsonp': None,
            'ksc':None,
            'ksp':None,
        }
        sdata = s_graph_dict['data']
        gdata = g_graph_dict['data']
        svals =[];gvals = []
        #need separate data arrays to compute correlations
        #data arrays need to be of same size even when data is missing
        scorrvals = [];gcorrvals = []
        for idx, date_val in enumerate(sdata):
            try:
                svals.append(float(date_val[1]))
            except:
                svals.append(None)
            try:
                gvals.append(float(gdata[idx][1]))
            except:
                gvals.append(None)
            try:
                scorrvals.append(float(date_val[1]))
                gcorrvals.append(float(gdata[idx][1]))
            except:
                pass
        compute_stat = getattr(WRCCUtils,'compute_statistic')
        stats['max'] = [compute_stat(svals,'max'),compute_stat(gvals,'max')]
        stats['min'] = [compute_stat(svals,'min'),compute_stat(gvals,'min')]
        stats['mean'] = [compute_stat(svals,'mean'),compute_stat(gvals,'mean')]
        stats['median'] = [compute_stat(svals,'median'),compute_stat(gvals,'median')]
        stats['std'] = [compute_stat(svals,'std'),compute_stat(gvals,'std')]
        stats['skew'] = [compute_stat(svals,'skew'),compute_stat(gvals,'skew')]
        #Single value stats
        snp = np.array(scorrvals, dtype = np.float)
        gnp = np.array(gcorrvals, dtype = np.float)
        pearson_stats = scipy.stats.pearsonr(snp, gnp)
        stats['pearsonc'] = round(pearson_stats[0],4)
        stats['pearsonp'] =  round(pearson_stats[1],4)
        ks_stats = scipy.stats.ks_2samp(snp, gnp)
        stats['ksc'] = round(ks_stats[0],4)
        stats['ksp'] =  round(ks_stats[1],4)
        return stats

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
            'both':['maxt', 'mint', 'avgt', 'pcpn', 'snow'],
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
        for key in ['locations', 'location','loc']:
            if key in params.keys():
                if isinstance(params[key], basestring):
                    ll_list = params[key].split(',')
                    lon_list = [ll_list[2*j] for j in range(len(ll_list) / 2)]
                    lat_list = [ll_list[2*j + 1] for j in range(len(ll_list) / 2)]
                    for idx,lon in enumerate(lon_list):
                        loc_list.append('%s,%s' %(lon, lat_list[idx]))
                elif isinstance(params[key], list):
                    loc_list = params[key]
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
        if 'sid' in self.params.keys() and not self.station_ids:
             self.station_ids = [self.params['sid']]
        if 'sids' in self.params.keys() and self.station_ids is None:
            if isinstance(self.params['sids'], basestring):
                self.station_ids = self.params['sids'].replace(' ','').split(',')
            else:
                self.station_ids = self.params['sids']
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
            'ids':['Lon, Lat'],
            'names':[''],
            'states':[''],
            'lls':[],
            'elevs': [],
            'uids':[''],
            'networks':[''],
            'valid_daterange':[['00000000','00000000']]
        }
        meta_dict['location_list'] = self.set_locations_list(self.params)
        meta_dict['names'] = meta_dict['location_list']
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
                keys = ['state', 'elev', 'uid']
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
            #Grid data dows not have snow
            if 'location' in self.params.keys() or 'loc' in self.params.keys():
                el_list = self.el_type_element_dict[self.params['element']]
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
        if 'station_id' not in self.params.keys() and 'sid' not in self.params.keys() and 'sids' not in self.params.keys():
            params['grid'] = self.params['grid']
            params['meta'] = 'll, elev'
        else:
            params['meta'] = 'name,state,sids,ll,elev,uid'
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
        #Find first leap year
        for idx, yr in enumerate(yrs):
            if WRCCUtils.is_leap_year(yr):
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
        leap_indices,year_list = self.find_leap_yr_indices()
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
            start_idx = 0
            for yr_idx, yr in enumerate(year_list):
                yr_data = [[] for el in elements]
                length = 365
                #Grid 1, 3 and 21 record Feb 29
                if yr_idx in leap_indices and self.params['grid'] in ['1','3','21']:
                    length =  366
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
            try:
                req = AcisWS.GridData(data_params)
                req['meta'];req['data']
            except Exception, e:
                data[i]['error'] = str(e)
                continue
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
            #Delete eventually
            app_params['coop_station_ids'] = self.data['station_ids']
            app_params['station_names'] = self.data['station_names']
            #Use ids and names oin WRCCDataApps
            app_params['ids'] = self.data['station_ids']
            app_params['names'] = self.data['station_names']
        if 'location_list' in self.data.keys():
            app_params['location_list'] = self.data['location_list']
            app_params['station_names'] = self.data['location_list']
            app_params['ids'] = self.data['location_list']
            app_params['names'] = self.data['location_list']
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
        try:
            self.region = params['select_grid_by']
        except:
            self.region = params['area_type']
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
        ctx.fill()
        #ctx.paint()
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
        try:
            area_description = WRCCData.DISPLAY_PARAMS[self.params['select_grid_by']]
            area_description+= ': ' + self.params[self.params['select_grid_by']].upper()
        except:
            area_description = WRCCData.DISPLAY_PARAMS[self.params['area_type']]
            area_description+= ': ' + self.params[self.params['area_type']].upper()
        date_str = 'Start Date: %s End Date: %s' % (self.params['sdate'], self.params['edate'])
        if self.params['image']['width']<301:
            ctx.set_font_size(8.)
            h = 10
        elif self.params['image']['width']>300 and self.params['image']['width']<501:
            ctx.set_font_size(14.)
            h=20
        else:
            ctx.set_font_size(16.)
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
        #sh = logging.StreamHandler()
        fh.setLevel(logging.DEBUG)
        #sh.setLevel(logging.DEBUG)
        #create formatter and add it to handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d in %(filename)s - %(message)s')
        fh.setFormatter(formatter)
        #sh.setFormatter(formatter)
        logger.addHandler(fh)
        #logger.addHandler(sh)
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
    Args:
        form:  dictionary of user input
        logger -- logger object
    '''
    def __init__(self, form, logger, local_base_dir, ftp_server, ftp_dir, max_lines_per_file):
        self.form = form
        self.logger =  logger
        self.base_dir = local_base_dir
        self.ftp_server = ftp_server
        self.ftp_dir = ftp_dir
        self.max_lines_per_file = max_lines_per_file

    def get_data(self):
        '''
        Requests and format data
        resultsdict has keys:
            errors, meta, data, smry, form
        '''
        resultsdict = WRCCUtils.request_and_format_data(self.form)
        if 'errors' in resultsdict.keys():
            self.logger.error('ERROR in get_data: ' + str(resultsdict['errors']))
        self.logger.info('Data request  %s completed successfully!' %str(self.form['output_file_name']))
        if not resultsdict['data'] and not resultsdict['smry']:
            self.logger.error('ERROR in get_data: empty data lists')
            return {}
        return resultsdict

    def split_data(self,resultsdict,max_lines):
        '''
        Splits results of get_data into
        smaller chunks if needed
        '''

        if resultsdict['data']:
            data = resultsdict['data']
            key_data = 'data';key_empty = 'smry'
        elif resultsdict['smry']:
            data = resultsdict['smry']
            key_data = 'smry';key_empty = 'data'
        else:
            self.logger.error('ERROR in split_data: empty data lists')
            return []
        chunks =[]
        c_idx = 0
        start_idx = 0
        if len(data) <= max_lines:
            end_idx = len(data)
        else:
            end_idx = max_lines
        while end_idx <= len(data):
            c_idx+=1
            chunk = {
                key_data:data[start_idx:end_idx],
                key_empty:[],
                'meta':resultsdict['meta'][start_idx:end_idx],
                'form':resultsdict['form']
            }
            chunks.append(chunk)
            #Check if we at end of data
            if end_idx == len(data):
                break
            #Set start/end for next chunk
            start_idx = end_idx
            end_idx = end_idx + max_lines
            #Check if new chunk covers rest of data
            if end_idx > len(data):
                end_idx = len(data)
        self.logger.info('Split data into %s chunks.' %str(c_idx))
        return chunks

    def set_out_file_path(self):
        time_stamp = datetime.datetime.now().strftime('%Y%m_%d_%H_%M_%S.%f')
        fe = WRCCData.FILE_EXTENSIONS[self.form['data_format']]
        path_to_file = self.base_dir + self.form['output_file_name']
        #FIX ME: save excel wb to file as .gz.
        if self.form['data_format'] == 'xl':
            path_to_file +='_' + time_stamp + fe
        else:
            path_to_file +='_' + time_stamp + fe + '.gz'
        self.logger.info('Output file path: %s.' %str(path_to_file))
        return path_to_file

    def write_to_file(self,data_chunk,path_to_file):
        error = None
        if self.form['data_format'] in ['clm','dlm']:
            try:
                Writer = CsvWriter(data_chunk, f = path_to_file)
            except Exception, e:
                self.logger.error('ERROR in write_to_file. Cannot initialize writer: ' + str(e))
                return str(e)
        if self.form['data_format'] == 'xl':
            try:
                Writer = ExcelWriter(data_chunk,f = path_to_file)
            except Exception, e:
                self.logger.error('ERROR in write_to_file. Cannot initialize writer: ' + str(e))
                return str(e)
        self.logger.info('Writing data to file.')
        Writer.write_to_file()
        '''
        try:
            Writer.write_to_file()
        except Exception, e:
            self.logger.error('ERROR in write_to_file. Cannot write to file: ' + str(e))
            return str(e)
        return error
        '''
    def load_file(self,f_name, ftp_server, ftp_dir):
        error = None
        FTP = FTPClass(ftp_server, ftp_dir, f_name, self.logger)
        error = FTP.FTPUpload()
        if error:
            self.logger.error('ERROR in load_file: %s' %str(error))
            os.remove(f_name)
            return error
        self.logger.info('File loaded to ftp server.')
        os.remove(f_name)
        self.logger.info('File deleted from local server server.')
        return None

    def process_request(self):
        error = None
        out_files =[]
        resultsdict = self.get_data()
        if not resultsdict:
            error = 'ERROR: Data Request failed!'
            return error, out_files
        chunks = self.split_data(resultsdict,self.max_lines_per_file)
        if not chunks:
            error = 'ERROR: Data request could not be slpit into chunks.'
            return error, out_files
        for c_idx,data_chunk in enumerate(chunks):
            path_to_file = self.set_out_file_path()
            f_name = path_to_file
            self.logger.info('Processing chunk %s' %str(c_idx))
            error = self.write_to_file(data_chunk,path_to_file)
            if error is not None:
                return error, []
            #Compress file
            '''
            try:
                f = gzip.open(f_name, 'wb')
            except:
                error = 'ERROR: Cannot open file %s' %f_name
                return error, []
            try:
                with open(path_to_file, 'r') as temp:
                    f.write(temp.read())
                f.close()
            except:
                error = 'ERROR: Cannot read file %s' %path_to_file
                return error, out_files
            self.logger.info('Output file compressed.')
            '''
            error = self.load_file(f_name, self.ftp_server, self.ftp_dir)
            if error is not None:
                return error,[]
            self.logger.info('File %s successfully loaded to FTP server' %f_name)
            out_files.append(f_name)
        self.logger.info('All files successfully loaded to FTP server')
        return error, out_files
