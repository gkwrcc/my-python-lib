#!/usr/bin/python
'''
module AcisWS.py

This module handles all Acis-WS calls for data needed to run WRCC data apps.
WRCC programs included so far:
sodlist, sodsum
'''

LIB_PREFIX = '/www-devel/apps/csc/my-python-lib/'
MEDIA_URL = '/www-devel/apps/csc/dj-projects/my_acis/media/'

#############################################################################
#python modules
import numpy
import datetime
import sys
from collections import defaultdict
#############################################################################
#WRCC specific modules
import WRCCUtils, WRCCClasses
##############################################################################
# import modules required by Acis
import urllib2
import json
##############################################################################
# set Acis data server
base_url = 'http://data.rcc-acis.org/'
##############################################################################

#Acis WebServices functions
###########################
def make_request(url,params) :
    req = urllib2.Request(url,
    json.dumps(params),
    {'Content-Type':'application/json'})
    try:
        response = urllib2.urlopen(req)
        return json.loads(response.read())
    except urllib2.HTTPError as error:
        if error.code == 400 : print error.msg

def MultiStnData(params):
    return make_request(base_url+'MultiStnData',params)

def StnData(params):
    return make_request(base_url+'StnData',params)

def StnMeta(params):
    return make_request(base_url+'StnMeta',params)

def GridData(params):
    return make_request(base_url+'GridData',params)

def GridCalc(params):
    return make_request(base_url+'GridCalc',params)

def General(params):
    return make_request(base_url+'General',params)


###############################
#Southwest CSC DATA PORTAL modules
#Used in Station Finder pages of SW CSC Data Portal

def station_meta_to_json(by_type, val):
    stn_list = []
    network_codes = {'1': 'WBAN', '2':'COOP', '3':'FAA', '4':'WMO', '5':'ICAO', '6':'GHCN', '7':'NWSLI', '8':'RCC', '9':'ThreadEx', '10':'CoCoRaHS'}
    network_icons = {'1': 'yellow-dot', '2': 'blue-dot', '3': 'green-dot','4':'yellow-dot', '5': 'ltblue-dot', \
                    '6': 'orange-dot', '7': 'yellow-dot', '8': 'purple-dot', '9':'green', '10':'pink-dot', 'Multi': 'red', 'Misc':'red-dot'}
                     #1YELLOW, 2BLUE, 3BROWN, 4OLIVE, 5GREEN, 6GRAY, 7TURQOIS, 8BLACK, 9TEAL, 10WHITE Multi:Red, Misc:Fuchsia
    stn_json={'network_codes': network_codes, 'network_icons': network_icons}
    if by_type == 'county':
        params = dict(county=val)
    elif by_type == 'climate_division':
        params = dict(climdiv=val)
    elif by_type == 'county_warning_area':
        params = dict(cwa=val)
    elif by_type == 'basin':
        params = dict(basin=val)
    elif by_type == 'state':
        params = dict(state=val)
    elif by_type == 'bounding_box':
        params = dict(bbox=val)
    elif by_type == 'id':
        params = dict(sids=val)
    else:
        pass

    if by_type == 'states':
        request = WRCCClasses.DataJob('StnMeta', {"state":"az,ca,co,nm,nv,ut"}).make_data_call()
        #request = StnMeta({"state":"az,ca,co,nm,nv,ut"})
    else:
        #request = WRCCClasses.DataJob('StnMeta', params).make_data_call()
        request = StnMeta(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    stn_meta_list = []
    if 'meta' in request.keys():
        for i, stn in enumerate(request['meta']):
            stn_sids = []
            stn_network_codes = []
            sids = stn['sids'] if 'sids' in stn.keys() else []
            if not sids:
                pass
            elif len(sids) == 1:
                net_id = str(sids[0].split(' ')[1])
                if int(net_id) >10:
                    marker_icon = network_icons['Misc']
                else:
                    marker_icon = network_icons[str(sids[0].split(' ')[1])]
            else:
                marker_icon = network_icons['Multi']
            for sid in sids:
                sid_split = sid.split(' ')
                #put coop id up front (for cscs application metagraph  and possibly others)
                if str(sid_split[1]) == '2':
                    stn_sids.insert(0,str(sid_split[0]).replace("\'"," "))
                    stn_network_codes.insert(0, str(sid_split[1]))
                else:
                    stn_sids.append(str(sid_split[0]).replace("\'"," "))
                    stn_network_codes.append(str(sid_split[1]))
            #Sanity check : Some Acis records are incomplete, leading to key error
            if 'll' in stn.keys():
                lat = str(stn['ll'][1])
                lon = str(stn['ll'][0])
            else:
                continue
            name = str(stn['name']).replace("\'"," ") if 'name' in stn.keys() else 'Name not listed'
            uid = str(stn['uid']) if 'uid' in stn.keys() else 'Uid not listed'
            elev = str(stn['elev']) if 'elev' in stn.keys() else 'Elevation not listed'
            state_key = str(stn['state']).lower() if 'state' in stn.keys() else 'State not listed'

            stn_dict = {"name":name,"uid":uid,"sids":stn_sids,"elevation":elev,"lat":lat,"lon":lon,\
            "state":state_key, 'marker_icon': marker_icon, 'stn_network_codes': stn_network_codes}
            stn_meta_list.append(stn_dict)
    else:
        if 'error' in request.keys():
            stn_json['error'] = request['error']
        else:
            stn_json['error'] = ['No meta data found']

    stn_json["stations"] = stn_meta_list
    #double quotes needed for jquery json.load
    stn_json_str = str(stn_json).replace("\'", "\"")
    time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_')
    if by_type == 'states':
        f_name = 'SW_stn.json'
        f = open('/tmp/' + f_name,'w+')
    else:
        f_name = time_stamp + 'stn.json'
        f = open('/tmp/' +  f_name,'w+')
    f.write(stn_json_str)
    f.close()
    return stn_json, f_name

#Rountine computes mean precip and temp for month given in end_date
#for each year starting 1900 ending end_date[year] - 1
#def mean_temp_pcpn(state, month, elements):
def state_aves(state, month, elements):
    mon = int(month)
    if mon not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        print "Not a valid month: %s. Enter a number 1-12" % str(mon)
        sys.exit(0)

    mon_lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    today = datetime.date.today()
    year = today.year
    start_year = 1900
    year_list = []
    if WRCCUtils.is_leap_year(year) and mon == 2:
        start_date = "%s%s%s" %(str(start_year), str(mon), str(29))
        end_date = "%s%s%s" % (str(year), str(mon), str(29))
    else:
        end_date = "%s%s%s" % (str(year), str(mon), str(mon_lens[mon - 1]))
        start_date = "%s%s%s" %(str(start_year), str(mon), str(mon_lens[mon - 1]))

    el_list = [{"name":el, "interval":[1,0,0],"duration":30,"reduce":"mean","smry":"mean"} for el in elements]
    params = {"state":state,"sdate":start_date,"edate":end_date, "elems":el_list}
    request = MultiStnData(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    state_aves = defaultdict(dict)
    if 'error' in request:
        state_ave_temp = []
        state_ave_pcpn = []
    try:
        for k, el in enumerate(elements):
            state_aves[k] = {'element': el, 'state_ave': [999 for yr in range(len(request['data'][0]['data']))]}
        state_ave_temp = [999 for yr in range(len(request['data'][0]['data']))]
        state_ave_pcpn = [999 for yr in range(len(request['data'][0]['data']))]
    except:
        state_ave_temp = []
        state_ave_pcpn = []

    for yr in range(len(request['data'][0]['data'])):
        year_list.append("%s" % str(start_year + yr))
        for k,el in enumerate(elements):
            ave_list = []
            for stn in request['data']:
                try:
                    ave_list.append(float(stn['data'][yr][k]))
                except:
                    pass
            state_aves[k]['state_ave'][yr] = numpy.mean(ave_list)
    return year_list, state_aves

def get_point_data(form_input, program):
    def get_stn_list(by_type, val):
        stn_list = []
        if by_type == 'county':
            params = dict(county=val)
        elif by_type == 'climate_division':
            params = dict(climdiv=val)
        elif by_type == 'county_warning_area':
            params = dict(cwa=val)
        elif by_type == 'basin':
            params = dict(basin=val)
        elif by_type == 'state':
            params = dict(state=val)
        elif by_type == 'bounding_box':
            params = dict(bbox=val)
        else:
            pass
        request=StnMeta(params)
        try:
            request['meta']
            for k, stn in enumerate(request['meta']):
                try:
                    stn_list.append(str(stn['sids'][0].split(' ')[0]))
                except:
                    continue
        except:
            pass
        return stn_list

    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    elements = WRCCUtils.get_element_list(form_input, program)
    if 'station_id' in form_input.keys():
        station_ids =[form_input['station_id']]
    elif 'station_ids' in form_input.keys():
        station_ids = form_input['station_ids']
    elif 'county' in form_input.keys():
        station_ids = get_stn_list('county', form_input['county'])
    elif 'climate_division' in form_input.keys():
        station_ids = get_stn_list('climate_division', form_input['climate_division'])
    elif 'county_warning_area' in form_input.keys():
        station_ids = get_stn_list('county_warning_area', form_input['county_warning_area'])
    elif 'basin' in form_input.keys():
        station_ids = get_stn_list('basin', form_input['basin'])
    elif 'state' in form_input.keys():
        station_ids = get_stn_list('state', form_input['state'])
    elif 'bounding_box' in form_input.keys():
        station_ids = get_stn_list('bounding_box', form_input['bounding_box'])
    else:
        station_ids =[]

    datadict = defaultdict(list)
    station_names = ['No Name found' for stn in station_ids]

    for i, stn in enumerate(station_ids):
        datadict[i] = [[] for el in elements]
    if len(station_ids) == 1:
        params = dict(sid=station_ids[0], sdate=s_date, edate=e_date, \
        elems=[dict(name=el)for el in elements])
        request = StnData(params)
    else:
        params = dict(sids=station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el)for el in elements])
        #request = MultiStnData(params)
        request = WRCCClasses.DataJob('MultiStnData', params).make_data_call()

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    try:
        request['meta']
    except:
        request['meta'] = {}

    try:
        request['data']
    except:
        request['data'] = []

    if len(station_ids) == 1:
        #make look like MultiStn call request and take care of por start/end dates
        request = {'data':[{'meta':request['meta'],'data':request['data']}]}
        if s_date == 'por':
            s_date = ''.join(request['data'][0]['data'][0][0].split('-'))
        if e_date == 'por':
            e_date = ''.join(request['data'][0]['data'][-1][0].split('-'))
    dates = WRCCUtils.get_dates(s_date, e_date, program)
    for stn, stn_data in enumerate(request['data']):
        try:
            stn_data['meta']
            index = None
            sids = stn_data['meta']['sids']
            for k,sid_tuple in enumerate(sids):
                sid= sid_tuple.split(' ')[0]
                if sid in station_ids:
                    index = station_ids.index(sid)
                    break
                else:
                    continue

            if index is None:
                continue
            else:
                station_names[index] = str(stn_data['meta']['name'])
                try:
                    stn_data['data']
                    datadict[index] = stn_data['data']
                except:
                    datadict[index] = []
        except:
            pass
    stn_ids_dict = {}
    stn_names_dict = {}
    dates_dict = {}
    #convert to dict for easier handling in html
    for k, name in enumerate(station_names):
        stn_ids_dict[k] = station_ids[k]
        stn_names_dict[k] = station_names[k]
    for k, date in enumerate(dates):
        dates_dict[k] = date

    return dict(datadict), dates_dict, elements, stn_ids_dict, stn_names_dict

def get_grid_data(form_input, program):
    #datalist[date_idx] = [[date1,lat1, lon1, elev1, el1_val1, el2_val1, ...],
    #[date2, lat2, ...], ...]
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    #grid data calls do not except list of elements, need to be string of comma separated values
    el_list = WRCCUtils.get_element_list(form_input, program)
    elements = ','.join(el_list)
    params = {'sdate': s_date, 'edate': e_date, 'grid': form_input['grid'], 'elems': elements, 'meta': 'll,elev'}
    if 'location' in form_input.keys():params['loc'] = form_input['location']
    if 'state' in form_input.keys():params['state'] = form_input['state']
    if 'bounding_box' in form_input.keys():params['bbox'] = form_input['bounding_box']
    request = GridData(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    return request

#######################################
#APPLICATION modules
#######################################
def get_station_list(by_type, val):
    stn_list = []
    if by_type == 'county':
        params = dict(county=val)
    elif by_type == 'climate_division':
        params = dict(climdiv=val)
    elif by_type == 'county_warning_area':
        params = dict(cwa=val)
    elif by_type == 'basin':
        params = dict(basin=val)
    elif by_type == 'state':
        params = dict(state=val)
    elif by_type == 'bounding_box':
        params = dict(bbox=val)
    elif type == 'id':
        params = dict(sids=val)
    else:
        pass
    request=StnMeta(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    try:
        request['meta']
        for i, stn in enumerate(request['meta']):
            sids = stn['sids']
            for sid in sids:
                sid_split = sid.split(' ')
                if sid_split[1] == '2':
                    stn_list.append(str(sid_split[0]))
    except:
        pass

    return stn_list


def get_us_meta():
    #states=['DE']
    states = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME'\
    ,'MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC'\
    ,'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
    params = {"state":["%s" % state for state in states]}
    request = StnMeta(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    return request

#data acquisition for Soddyrec, Soddynorm, Soddd, Sodpad, Sodsumm
def get_sod_data(form_input, program):
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    '''
    if program in ['Sodpiii']:
        #get an extra year of data previos and after s_date, e_date
        s_date = str(int(s_date[0:4]) - 1) + s_date[4:]
        e_date = str(int(e_date[0:4]) + 1) + e_date[4:]
    '''
    dates = WRCCUtils.get_dates(s_date, e_date, program)
    elements = WRCCUtils.get_element_list(form_input, program)
    els = [dict(name='%s' % el) for el in elements]
    if 'coop_station_id' in form_input.keys():
        coop_station_ids =[form_input['coop_station_id']]
    elif 'coop_station_ids' in form_input.keys():
        coop_station_ids = form_input['coop_station_ids']
    elif 'county' in form_input.keys():
        coop_station_ids = get_station_list('county', form_input['county'])
    elif 'climate_division' in form_input.keys():
        coop_station_ids = get_station_list('climate_division', form_input['climate_division'])
    elif 'county_warning_area' in form_input.keys():
        coop_station_ids = get_station_list('county_warning_area', form_input['county_warning_area'])
    elif 'basin' in form_input.keys():
        coop_station_ids = get_station_list('basin', form_input['basin'])
    elif 'state' in form_input.keys():
        coop_station_ids = get_station_list('state', form_input['state'])
    elif 'bounding_box' in form_input.keys():
        coop_station_ids = get_station_list('bounding_box', form_input['bounding_box'])
    else:
        coop_station_ids =[]
    #sort station id in ascending order
    coop_station_ids = WRCCUtils.strip_n_sort(coop_station_ids)
    station_names=['No Name found' for i in range(len(coop_station_ids))]
    #Since Acis may not return results for some stations, we need to initialize output dictionary
    datadict = defaultdict(list)
    for i, stn in enumerate(coop_station_ids):
        if program == 'Soddyrec':
            yr_list = [[['#', '#', '#', '#', '#'] for k in range(366)] for el in elements]
            datadict[i] = yr_list
        elif program in ['Sodrun', 'Sodrunr']:
            datadict[i] = []
        else:
            datadict[i] = [[] for el in elements]

    if program == 'Soddyrec':
        smry_opts = {'reduce':'max', 'add':'date,mcnt'}
        if len(elements) >1 and 'mint'in elements:
            mint_indx = elements.index('mint')
            elements.remove('mint')
            elts = [dict(name='%s' % el, interval='dly', duration='dly', smry=smry_opts\
            , groupby="year") for el in elements]
            elts.insert(mint_indx,dict(name='mint', interval='dly', duration='dly', \
            smry={'reduce':'min', 'add':'date,mcnt'}, groupby="year"))
            elements.insert(mint_indx, 'mint')
        elif len(elements) == 1 and elements[0] == 'mint':
            elts = [dict(name='mint', interval='dly', duration='dly',\
            smry={'reduce':'min', 'add':'date,mcnt'}, groupby="year")]
        else:
            elts = [dict(name='%s' % el, interval='dly', duration='dly', smry=smry_opts, \
            groupby="year") for el in elements]

        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=elts)
    elif program in ['Soddynorm', 'Soddd', 'Sodpad', 'Sodsumm', 'Sodpct', 'Sodthr', 'Sodxtrmts', 'Sodpiii']:
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el,interval='dly',duration='dly',groupby='year')for el in elements])
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el,interval='dly',duration='dly',groupby='year')for el in elements])
    elif program in ['Sodlist', 'Sodcnv']:
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el,add='t')for el in elements])
    else:
        params = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, \
        elems=[dict(name=el)for el in elements])
    request = MultiStnData(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    try:
        request['data']#list of data for the stations
    except:
        if request['error']:
            print '%s' % str(request['error'])
            sys.exit(1)
        else:
            'Unknown error ocurred when getting data'
            sys.exit(1)

    for stn, stn_data in enumerate(request['data']):
        try:
            stn_data['meta']
            #find station_id, Note: MultiStnData call may not return the stations in order
            sids = stn_data['meta']['sids']
            for sid in sids:
                sid_split = sid.split(' ')
                if sid_split[1] == '2':
                    #station_id = str(stn_data['meta']['sids'][1].split()[0])
                    station_id = str(sid_split[0])
                    break
            try:
                index = coop_station_ids.index(station_id)
                station_names[index] = str(stn_data['meta']['name'])
                if program == 'Soddyrec':
                    try:
                        stn_data['smry']
                        datadict[index] = stn_data['smry']
                    except:
                        datadict[index] = []
                #sort data by element
                elif program in ['Soddynorm', 'Soddd', 'Sodpct']:
                    try:
                        stn_data['data']
                        for yr, el_data in enumerate(stn_data['data']):
                            for el_idx, dat in enumerate(el_data):
                                datadict[index][el_idx].append(dat)
                    except:
                        pass
                else:
                    try:
                        stn_data['data']
                        datadict[index] = stn_data['data']
                    except:
                        datadict[index] = []

            except ValueError:
                continue

        except:
            pass

    if program == 'Soddyrec':
        #need to get averages separately add: date, mcnt fails if we ask for mean, max together
        elts_x = [dict(name='%s' % el, interval='dly', duration='dly', smry={'reduce':'mean'}, \
        groupby="year") for el in elements]
        params_x = dict(sids=coop_station_ids, sdate=s_date, edate=e_date, elems=elts_x)
        request_x = MultiStnData(params_x)
        if not request_x:
            request_x = {'error':'bad request, check params: %s'  % str(params_x)}

        try:
            request_x['data']#list of data for the stations
            #order results by stn id

            for stn, stn_data in enumerate(request_x['data']):
                sids = stn_data['meta']['sids']
                station_id = ' '
                for sid in sids:
                    sid_split = sid.split(' ')
                    if sid_split[1] == '2':
                        #station_id = str(stn_data['meta']['sids'][1].split()[0])
                        station_id = str(sid_split[0])
                        break
                if station_id == ' ':
                    continue

                try:
                    indx_x = coop_station_ids.index(station_id)
                    try:
                        stn_data['smry']
                        for el_id, ave_list in enumerate(stn_data['smry']): #k : element id
                            for date_id,ave in enumerate(ave_list):
                                datadict[indx_x][el_id][date_id].insert(0,ave)
                                #figure out the number of years that are in the record
                                val_list = [stn_data['data'][l][0][date_id] for l in range(len(stn_data['data']))]
                                yrs_in_record = len(filter(lambda a: a != 'M', val_list))
                                datadict[indx_x][el_id][date_id].append(yrs_in_record)
                    except:
                        pass
                except ValueError:
                    continue
        except:
            if 'error' in request_x.keys():
                print '%s' % str(request_x['error'])
                sys.exit(1)
            else:
                'Unknown error ocurred when getting data'
                sys.exit(1)
    return datadict, dates, elements, coop_station_ids, station_names

def get_sodsum_data(form_input):
    if 'element' not in form_input.keys() or 'coop_station_ids' not in form_input.keys():
        print 'element and coop_station_id options required!'
        sys.exit(0)
    if not form_input['element'] or not form_input['coop_station_ids']:
        print 'element and coop_station_id options required!'
        sys.exit(0)
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    coop_station_ids = form_input['coop_station_ids'] #list of stn ids (converted to list in form)
    #sort coop ids in ascending order, strip left zeros first, sort and reattach zeros
    coop_station_ids = WRCCUtils.strip_n_sort(coop_station_ids)
    datadict = defaultdict(list)
    station_names=[' ' for i in range(len(coop_station_ids))]
    if form_input['element']!= 'multi':
        elements = [form_input['element']]
        #evap, wdmv, wesf not fully implemented into Acis_WS yet
        if form_input['element'] in ['evap', 'wdmv', 'wesf']:
            print 'Evaporation, wind and water equivalent not implemented yet. Please chose another element!'
            sys.exit(0)
    else:
        elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst']
    #request data on a station by station basis
    for i, stn_id in enumerate(coop_station_ids):
        if form_input['element']!= 'multi':
            params = dict(sid=stn_id, sdate=s_date, edate=e_date, elems=[dict(name='%s' % form_input['element'])])
        else:
            params = dict(sid=stn_id, sdate=s_date, edate=e_date, elems=[dict(name='pcpn'), \
            dict(name='snow'), dict(name='snwd'), dict(name='maxt'), dict(name='mint'), dict(name='obst')])

        request = StnData(params)

        if not request:
            request = {'error':'bad request, check params: %s'  % str(params)}

        try:
            request['meta']
            station_names[i] = request['meta']['name']
        except:
            station_names[i] = ' '

        try:
            request['data']
            datadict[i] = request['data']
        except:
            datadict[i]=[]

    return datadict, elements, coop_station_ids, station_names


#Routine to return data for programs sodlist, sodmonline(my), sodcnv
def get_sodlist_data(form_input, program):
    s_date, e_date = WRCCUtils.find_start_end_dates(form_input)
    coop_station_id = form_input['coop_station_id']
    if program in ['sodlist', 'sodcnv']:
        if 'include_tobs_evap' in form_input.keys():
            params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, \
            elems=[dict(name='pcpn', add='f,t'), dict(name='snow', add='f,t'), dict(name='snwd', add='f,t'),
            dict(name='maxt', add='f,t'), dict(name='mint', add='f,t'), dict(name='obst', add='f,t')])

            params_e = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(vX=7,add='f,t', prec=2)])
        else:
            if not program == 'sodcnv':
                params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, \
                elems=[dict(name='pcpn', add='f,t'), dict(name='snow', add='f,t'), dict(name='snwd', add='f,t'),
                dict(name='maxt', add='f,t'), dict(name='mint', add='f,t')])
            else:
                params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, \
                elems=[dict(name='pcpn', add='f,t'), dict(name='snow', add='f,t'), dict(name='snwd', add='f,t'),
                dict(name='maxt', add='f,t'), dict(name='mint', add='f,t'), dict(name='obst', add='f,t')])
    elif program in ['sodmonline', 'sodmonlinemy']:
        #sodmonline(my) only available for full years
        s_date = '%s%s' % (s_date[0:4], '0101')
        e_date = '%s%s' % (e_date[0:4], '1231')
        if form_input['element'] == 'evap':
            vXvN = 7
        elif form_input['element'] == 'wdmv':
            vXvN = 12
        elif form_input['element'] in ['wesf']:
            vXvN = 13

        if form_input['element'] in ['evap','wdmv', 'wesf' ]: #need to work with var major (vX) and var minor (vN)
            params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[vXvN])
        elif form_input['element'] in ['dtr', 'mmt']:
            params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(name='maxt'), dict(name='mint')])
        else:
            params = dict(sid='%s' % coop_station_id, sdate=s_date, edate=e_date, elems=[dict(name='%s' % form_input['element'])])
    else:
        print 'Program %s not supported in get_sodlist_data. Program should be one out of [sodlist, sodcnv, sodmonline, sodmonlinemy]!' % program
        sys.exit(0)

    #Request evap, wind and water equivalent data
    #NOTE: these data need to be obtained via var major:
    if program == 'sodlist' and 'include_tobs_evap' in form_input.keys():
        request_evap = StnData(params_e)

        if not request_evap:
            request_evap = {'error':'bad request, check params: %s'  % str(params_e)}

        try:
            request_evap['meta']
        except:
            if request_evap['error']:
                print '%s' % str(request_evap['error'])
            else:
                print 'Unknown error ocurred when getting evap data'
        try:
            request_evap['data']
            evap_data = request_evap['data']
        except:
            evap_data = None
    else:
        evap_data = None

    #retrieve data via Acis webservices
    request = StnData(params)

    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    #Test for successful data retrieval and get metadata information
    try:
        request['meta']
        stn_name = request['meta']['name']
    except:
        if request['error']:
            print '%s' % str(request['error'])
            stn_name = ' '
        else:
            print 'Unknown error ocurred. Check input values!'

    try:
        request['data']
        req_data = request['data']
    except:
        print 'No data found!'
        req_data = None

    #get windowed data is program is sodlist
    if program == 'sodlist':
        if 'start_window' not in form_input.keys():
            s_window = '0101'
        else:
            s_window = form_input['start_window']
        if 'end_window' not in form_input.keys():
            e_window = '1231'
        else:
            e_window = form_input['end_window']


        if s_window!= '0101' or e_window != '1231':
            if req_data:
                data = WRCCUtils.get_windowed_data(req_data, s_date, e_date, s_window, e_window)
            else:
                data = None
        else:
            if req_data:
                data = req_data
            else:
                data = None
    else:
        if req_data:
            data = req_data
        else:
            data = None

    #Join evap_data if present
    if evap_data:
        for i, val in enumerate(evap_data):
            data[i].append(val[1])

    return data, stn_name
