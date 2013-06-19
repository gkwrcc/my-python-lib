#!/usr/bin/python
'''
module WRCCClasses.py

Defines classes used in my_acis project
'''

##############################################################################
# import modules required by Acis
#import  pprint, time
import time
from cStringIO import StringIO
import cairo
import base64
import datetime
#WRCC modules
import AcisWS, WRCCDataApps, WRCCUtils, WRCCData

MEDIA_URL = '/www/apps/csc/dj-projects/my_acis/media/'

class SODDataJob:
    '''
    SOD Data class.

    Keyword arguments:
    app_name -- application name, on of the following
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
            'evap':['7.1'],
            'wind':['12.1']
        }
        self.app_elems_params = {
            'Soddyrec': {'name':None,'groupby':'year'},
            'Soddynorm':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodsumm':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodrun':{'name':None},
            'Sodrunr':{'name':None},
            'Sodxtrmts':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodpct':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodthr':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodpiii':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodpad':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Soddd':{'name':None,'interval':'dly','duration':'dly','groupby':'year'},
            'Sodmonline':{'name':None},
            'Sodsum':{'name':None},
            'Sodmonlinemy':{'name':None},
            'Sodlist':{'name':None,'add':'t'},
            'Sodcnv':{'name':None,'add':'t'}
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
        #Pick first id in list
        stn_id = sids[0].split(' ')[0]
        if sids[0].split(' ')[1] != '2':
            #Check if station has coop id, if so, use that
            for sid in sids[1:]:
                if sid.split(' ')[1] == '2':
                    #Found coop id
                    stn_id = sid.split(' ')[0]
                    break
        return str(stn_id)

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
        if self.params['start_date'] == 'por' or self.params['end_date'] == 'por':
            if self.params['start_date'] == 'por' and self.params['end_date'] == 'por':
                vd = WRCCUtils.find_valid_daterange(self.station_ids[0],max_or_min='max')
            elif self.params['start_date'] == 'por' and self.params['end_date'] != 'por':
                vd = WRCCUtils.find_valid_daterange(self.station_ids[0],max_or_min='max', end_date=e_date)
            elif self.params['start_date'] != 'por' and self.params['end_date'] == 'por':
                vd = WRCCUtils.find_valid_daterange(self.station_ids[0],max_or_min='max', start_date=s_date)
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
                stn_id = self.get_unique_sid(sids)
                #Take first station id listed
                if not stn_id:
                    continue
                stn_ids.append(stn_id)
        self.station_ids = stn_ids
        return stn_ids, stn_names


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
        elif self.app_name == 'Sodxtrmts' and self.params[el_type] in ['hdd','cdd', 'gdd']:
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
        for el in elements:
            el_dict = self.app_elems_params[self.app_name]
            el_dict['name'] = el
            #We have to add three types of summaries for each element of Soddyrec
            if self.app_name == 'Soddyrec':
                for smry in self.soddyrec_smry_opts:
                    el_dict['smry'] = smry
                    elems.append(el_dict)
            else:
                elems.append(el_dict)
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
            stn_id = self.get_unique_sid(sids)
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
