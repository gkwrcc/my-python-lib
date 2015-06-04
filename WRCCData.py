#!/usr/bin/python

'''
Module WRCCData
Contains useful dicts and lists used in my_acis
django project
CAPS names imply use in django forms
'''
from collections import defaultdict
from collections import OrderedDict
import datetime

'''
FIX ME: get web server error when
Importing WRCCUtils
#from WRCCUtils import set_back_date
#today = set_back_date(0)
'''

def set_back_date(days_back):
    '''
    Calculates today - days_back
    and returns the back date in format
    yyyymmdd
    '''
    try:
        int(days_back)
    except:
        return '99990101'
    tdy = datetime.datetime.today()
    #Choose default start_date 4 weeks back
    b = datetime.datetime.today() - datetime.timedelta(days=int(days_back))
    yr_b = str(b.year);mon_b = str(b.month);day_b = str(b.day)
    if len(mon_b) == 1:mon_b = '0%s' % mon_b
    if len(day_b) == 1:day_b = '0%s' % day_b
    back_date = '%s%s%s' % (yr_b, mon_b, day_b)
    return back_date
today = set_back_date(0)

###################################
###################################
#General
###################################
###################################
FIPS_STATE_KEYS = {'al':'01','az':'02','ca':'04','co':'05','ct':'06','hi':'51', 'id':'10','mt':'24', 'nv':'26', \
             'nm':'29','pa':'91','or':'35','tx':'41', 'ut':'42', 'wa':'45','ar':'03', 'ct':'06', \
             'de':'07','fl':'08','ga':'09','il':'11', 'in':'12', 'ia':'13','ks':'14', 'ky':'15', \
             'la':'16','me':'17','md':'18','ma':'19', 'mi':'20', 'mn':'21','ms':'22', 'mo':'23', \
             'ne':'25','nh':'27','nj':'28','ny':'30', 'nc':'31', 'nd':'32','oh':'33', 'ok':'34', \
             'pa':'36','ri':'37','sc':'38','sd':'39', 'tn':'40', 'vt':'43','va':'44', 'wv':'46', \
             'wi':'47','wy':'48','vi':'67','pr':'66','wr':'96', 'ml':'97', 'ws':'98','ak':'50'}

STATE_CHOICES = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', \
                'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', \
                'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', \
                'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', \
                'VA', 'VT', 'WA', 'WI', 'WV', 'WY','AS']

NETWORK_CODES = {
                '1': 'WBAN',
                '2':'COOP',
                '3':'FAA',
                '4':'WMO',
                '5':'ICAO',
                '6':'GHCN',
                '7':'NWSLI',
                #'8':'RCC',
                '9':'ThreadEx',
                '10':'CoCoRaHS',
                #'11':'Misc'
                }
NETWORK_ICONS = {
            '1': 'yellow-dot',
            '2': 'blue-dot',
            '3': 'green-dot',
            '4':'purple-dot',
            '5': 'ltblue-dot',
            '6': 'orange-dot',
            '7': 'pink-dot',
            '8': 'yellow',
            '9':'green',
            '10':'purple',
            #'11': 'red'
            }

KELLY_NETWORK_CODES = {
            '1': 'COOP',
            '2':'GHCN',
            '3':'ICAO',
            '4':'NWSLI',
            '5':'FAA',
            '6':'WMO',
            '7':'WBAN',
            '8':'CoCoRaHS',
            #'9':'RCC',
            '10':'Threadex',
            #'11':'Misc'
            }

KELLY_NETWORK_ICONS = {
            '1': 'blue-dot',
            '2': 'orange-dot',
            '3': 'ltblue-dot',
            '4':'pink-dot',
            '5': 'green-dot',
            '6': 'purple-dot',
            '7': 'yellow-dot',
            '8': 'purple',
            #'9':'yellow',
            '10':'green',
            #'11': 'red'
            }


ACIS_ELEMENTS = defaultdict(dict)
ACIS_ELEMENTS ={
              '1':{'name':'maxt', 'name_long': 'Maximum Daily Temperature (F/C)', 'vX':1},
              '2':{'name':'mint', 'name_long': 'Minimum Daily Temperature (F/C)', 'vX':2},
              '43': {'name':'avgt', 'name_long': 'Average Daily Temperature (F/C)', 'vX':43},
              '3':{'name':'obst', 'name_long': 'Observation Time Temperature (F/C)', 'vX':3},
              '4': {'name': 'pcpn', 'name_long':'Precipitation (in/mm)', 'vX':4},
              '10': {'name': 'snow', 'name_long':'Snowfall (in/mm)', 'vX':10},
              '11': {'name': 'snwd', 'name_long':'Snow Depth (in/mm)', 'vX':11},
              '7': {'name': 'evap', 'name_long':'Pan Evaporation (in/mm)', 'vX':7},
              '12': {'name': 'wdmv', 'name_long':'Wind Movement (mi/km)', 'vX':12},
              '45': {'name': 'dd', 'name_long':'Degree Days', 'vX':45},
              '44': {'name': 'cdd', 'name_long':'Cooling Degree Days', 'vX':44},
              '45': {'name': 'hdd', 'name_long':'Heating Degree Days', 'vX':45},
              '-44': {'name': 'gdd', 'name_long':'Growing Degree Days', 'vX':44},
              '91': {'name': 'mly_maxt', 'name_long':'Maximum Monthly Temperature (F/C)', 'vX':91},
              '92': {'name': 'mly_mint', 'name_long':'Minimum Monthly Temperature (F/C)', 'vX':92},
              '99': {'name':'mly_avgt', 'name_long': 'Average Monthly Temperature (F/C)', 'vX':99},
              '94': {'name': 'mly_pcpn', 'name_long':'Monthly Precipitation (in/mm)', 'vX':94},
              '95': {'name': 'yly_maxt', 'name_long':'Maximum Yearly Temperature (F/C)', 'vX':95},
              '96': {'name': 'yly_mint', 'name_long':'Minimum Yearly Temperature (F/C)', 'vX':96},
              '100': {'name':'yly_avgt', 'name_long': 'Average Yearly Temperature (F/C)', 'vX':100},
              '98': {'name': 'yly_pcpn', 'name_long':'Yearly Precipitation (in/mm)', 'vX':98}
              }

ACIS_ELEMENTS_DICT = {
              'maxt':{'name':'maxt', 'name_long': 'Maximum Daily Temperature', 'vX':1},
              'mint':{'name':'mint', 'name_long': 'Minimum Daily Temperature', 'vX':2},
              'avgt': {'name':'avgt', 'name_long': 'Mean Daily Temperature', 'vX':43},
              'dtr': {'name':'dtr', 'name_long': 'Daily Temperature Range', 'vX':None},
              'obst':{'name':'obst', 'name_long': 'Observation Time Temperature', 'vX':3},
              'pcpn': {'name': 'pcpn', 'name_long':'Precipitation', 'vX':4},
              'snow': {'name': 'snow', 'name_long':'Snowfall', 'vX':10},
              'snwd': {'name': 'snwd', 'name_long':'Snow Depth', 'vX':11},
              'cdd': {'name': 'cdd', 'name_long':'Cooling Degree Days', 'vX':44},
              'hdd': {'name': 'hdd', 'name_long':'Heating Degree Days', 'vX':45},
              'gdd': {'name': 'gdd', 'name_long':'Growing Degree Days', 'vX':44},
              'evap': {'name': 'evap', 'name_long':'Evaporation', 'vX':7},
              'wdmv': {'name': 'wdmv', 'name_long':'Wind Movement', 'vX':12},
              'mly_maxt':{'name':'mly_maxt', 'name_long': 'Maximum Monthly Temperature', 'vX':91},
              'mly_mint':{'name':'mly_mint', 'name_long': 'Minimum Monthly Temperature', 'vX':92},
              'mly_avgt': {'name':'mly_avgt', 'name_long': 'Mean Monthly Temperature', 'vX':99},
              'mly_pcpn': {'name': 'mly_pcpn', 'name_long':'Monthly Precipitation', 'vX':94},
              'yly_maxt':{'name':'yly_maxt', 'name_long': 'Maximum Yearly Temperature', 'vX':91},
              'yly_mint':{'name':'yly_mint', 'name_long': 'Minimum Yearly Temperature', 'vX':92},
              'yly_avgt': {'name':'yly_avgt', 'name_long': 'Mean Yearly Temperature', 'vX':99},
              'yly_pcpn': {'name': 'yly_pcpn', 'name_long':'Yearly Precipitation', 'vX':98}
}

#Soddyrec el list
ACIS_ELEMENTS_DICT_SR = {
              'maxt':{'name':'maxt', 'name_long': 'Maximum Temperature', 'vX':1},
              'mint':{'name':'mint', 'name_long': 'Minimum Temperature', 'vX':2},
              'avgt': {'name':'avgt', 'name_long': 'Mean Temperature', 'vX':43},
              'dtr': {'name':'dtr', 'name_long': 'Temperature Range', 'vX':None},
              'obst':{'name':'obst', 'name_long': 'Observation Time Temperature', 'vX':3},
              'pcpn': {'name': 'pcpn', 'name_long':'Precipitation', 'vX':4},
              'snow': {'name': 'snow', 'name_long':'Snowfall', 'vX':10},
              'snwd': {'name': 'snwd', 'name_long':'Snow Depth', 'vX':11},
              'cdd': {'name': 'cdd', 'name_long':'Cooling Degree Days', 'vX':44},
              'hdd': {'name': 'hdd', 'name_long':'Heating Degree Days', 'vX':45},
              'gdd': {'name': 'gdd', 'name_long':'Growing Degree Days', 'vX':44},
              'evap': {'name': 'evap', 'name_long':'Evaporation', 'vX':7},
              'wdmv': {'name': 'wdmv', 'name_long':'Wind Movement', 'vX':12},
              'mly_maxt':{'name':'mly_maxt', 'name_long': 'Maximum Monthly Temperature', 'vX':91},
              'mly_mint':{'name':'mly_mint', 'name_long': 'Minimum Monthly Temperature', 'vX':92},
              'mly_avgt': {'name':'mly_avgt', 'name_long': 'Mean Monthly Temperature', 'vX':99},
              'mly_pcpn': {'name': 'mly_pcpn', 'name_long':'Monthly Precipitation', 'vX':94},
              'yly_maxt':{'name':'yly_maxt', 'name_long': 'Maximum Yearly Temperature', 'vX':91},
              'yly_mint':{'name':'yly_mint', 'name_long': 'Minimum Yearly Temperature', 'vX':92},
              'yly_avgt': {'name':'yly_avgt', 'name_long': 'Mean Yearly Temperature', 'vX':99},
              'yly_pcpn': {'name': 'yly_pcpn', 'name_long':'Yearly Precipitation', 'vX':98}
}

ACIS_ELEMENTS_LIST = [['maxt','Maximum Daily Temperature (F)'], ['mint','Minimum Daily Temperature (F)'],
                      ['avgt','Average Daily Temperature (F)'], ['obst', 'Observation Time Temperature (F)'], \
                      ['pcpn', 'Precipitation (in)'], ['snow', 'Snowfall (in)'], \
                      ['snwd', 'Snow Depth (in)'], ['cdd', 'Cooling Degree Days'], \
                      ['hdd','Heating Degree Days'], ['gdd', 'Growing Degree Days'], \
                      ['evap', 'Pan Evaporation (in)'], ['gdd', 'Wind Movement (Mi)'],\
                      ['pet', 'Potential Evapotranspiration'], ['dtr', 'Daily Temperature Range (F)']]

ELEMENT_THRESHOLDS = {
    'english':{
        'maxt':['60','80'],
        'mint':['30','50'],
        'avgt':['40','60'],
        'dtr': ['10','40'],
        'obst':['30','50'],
        'pcpn': ['0','1'],
        'snow': ['0','1'],
        'snwd': ['0','1'],
        'cdd': ['10','20'],
        'hdd': ['10','20'],
        'gdd':['10','20'],
        'evap': ['0','1'],
        'wdmv': ['0','50'],
        'pet':['0','1']
        },
    'metric':{
        'maxt':['20','30'],
        'mint':['0','10'],
        'avgt':['15','25'],
        'dtr': ['10','40'],
        'obst':['10','20'],
        'pcpn': ['0','3'],
        'snow': ['0','3'],
        'snwd': ['0','10'],
        'cdd': ['10','20'],
        'hdd': ['10','20'],
        'gdd':['10','20'],
        'evap': ['0','3'],
        'wdmv': ['0','65'],
        'pet':['0','3']
        },
}

UNITS_METRIC = {
    'maxt':'C',
    'mint':'C',
    'avgt':'C',
    'dtr': 'C',
    'obst':'C',
    'pcpn': 'mm',
    'snow': 'mm',
    'snwd': 'mm',
    'cdd': '',
    'hdd': '',
    'gdd':'',
    'evap': 'mm',
    'wdmv': 'km',
    'elev':'m',
    'pet':'mm/day'
}

UNITS_ENGLISH = {
    'maxt':'F',
    'mint':'F',
    'avgt':'F',
    'dtr': 'F',
    'obst':'F',
    'pcpn': 'in',
    'snow': 'in',
    'snwd': 'in',
    'cdd': '',
    'hdd': '',
    'gdd':'',
    'evap': 'in',
    'wdmv': 'Mi',
    'elev':'ft',
    'pet':'in/day'
}

UNITS_LONG={
    'C':'Degrees Celsius',
    'F':'Degrees Fahrenheit',
    'in':'Inches',
    'mm':'Millimiter',
    'Mi':'Miles',
    'km':'Kilometer',
    'ft':'Feet',
    'm':'Meter',
    #Degree days are unit less
    '':''
}

PLOT_COLOR = {
    'maxt':'#660066',
    'mint':'#0000FF',
    'avgt':'#FF00FF',
    'dtr': '#FF00FF',
    'obst':'#FF00FF',
    'pcpn': '#008000',
    'snow': '#008000',
    'snwd': '#008000',
    'cdd': '#00FFFF',
    'hdd': '#00FFFF',
    'gdd': '#00FFFF',
    'evap': '#008000',
    'wdmv': '#008000',
    'pet':'#008000',
}
RM_COLOR = {
    'maxt':'#FF0000',
    'mint':'#8B0000',
    'avgt':'#FF1493',
    'dtr': '#B22222',
    'obst':'#FF00FF',
    'pcpn': '#FF69B4',
    'snow': '#CD5C5C',
    'snwd': '#F08080',
    'cdd': '#BA55A3',
    'hdd': '#9370BD',
    'gdd': '#C71585',
    'evap': '#FF0066',
    'wdmv': '#FF99CC',
    'pet':'#9900FF',
}
#Plot and running mean colors
PLOT_COLOR_MONTH = {
    'JAN':['#0000FF','#FF0000'],
    'FEB':['#00FFFF','#8B0000'],
    'MAR':['#8A2BE2','#FF1493'],
    'APR':['#6495ED','#B22222'],
    'MAY':['#8B008B','#FF00FF'],
    'JUN':['#00008B','#FF69B4'],
    'JUL':['#483D8B','#CD5C5C'],
    'AUG':['#00CED1','#F08080'],
    'SEP':['#00BFFF','#BA55D3'],
    'OCT':['#696969','#9370BD'],
    'NOV':['#4B0082','#C71585'],
    'DEC':['#008B8B','#DB7093']
}

#Blues
SERIES_COLOR_LIST = ['#0000FF','#00FFFF','#8A2BE2','#6495ED','  #8B008B',\
    '#00008B','008B8B','#483D8B ','#00CED1','#00BFFF','#696969','#4B0082']
#Reds
RUNNING_MEAN_COLOR_LIST = ['#FF0000','#8B0000','#FF1493','#B22222', '#FF00FF',\
    '#FF69B4','#CD5C5C','#F08080','#BA55D3','#9370BD','#C71585','#DB7093']

MONTH_NAMES_LONG = ['January', 'February', 'March', 'April', 'May', 'June',\
               'July', 'August', 'September', 'October', 'November', 'December']

MONTH_NAMES_SHORT_CAP = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

MONTH_NAME_TO_NUMBER= {
    'Jan':'01',
    'Feb':'02',
    'Mar':'03',
    'Apr':'04',
    'May':'05',
    'Jun':'06',
    'Jul':'i07',
    'Aug':'08',
    'Sep':'09',
    'Oct':'10',
    'Nov':'11',
    'Dec':'12',
    'January':'01',
    'February':'02',
    'March':'03',
    'April':'04',
    'May':'05',
    'June':'06',
    'July':'07',
    'August':'08',
    'September':'09',
    'October':'10',
    'November':'11',
    'December':'12',
}

NUMBER_TO_MONTH_NAME = {
    '01':'Jan',
    '1':'Jan',
    '02':'Feb',
    '2':'Feb',
    '03':'Mar',
    '3':'Mar',
    '04':'Apr',
    '4':'Apr',
    '05':'May',
    '5':'May',
    '06':'Jun',
    '6':'Jun',
    '07':'Jul',
    '7':'Jul',
    '08':'Aug',
    '8':'Aug',
    '09':'Sep',
    '9':'Sep',
    '10':'Oct',
    '11':'Nov',
    '12':'Dec'
}

MONTH_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

DELIMITERS = {
    'comma':',',
    ',':',',
    'tab':chr(9),
    '   ':chr(9),
    '\t':chr(9),
    'colon': ':',
    ':': ':',
    'space':' ',
    ' ': ' ',
    'pipe':'|',
    '|':'|'
}

CMAPS = [ 'Accent','Blues','BrBG','BuGn','BuPu','CMRmap','Dark2','GnBu','Greens',\
    'Greys','OrRd','Oranges','PRGn','Paired','Pastel1','Pastel2','PiYG','PuBu',\
    'PuBuGn','PuOr','PuRd','Purples','RdBu','RdGy','RdPu','RdYlBu','RdYlGn','Reds',\
    'Set1','Set2','Set3','Spectral','YIGn','YlGnBu','YlOrBr','YlOrRd','afmhot','autumn',\
    'binary','bone','brg','bwr','cool','coolwarm','copper','cubehelix','flag','gist_earth',\
    'gist_gray','gist_rainbow','gist_heat','gits_ncar','gist_stern','gist_yarg','gnuplot',\
    'gnuplot2','gray','hot','hsv','jet','ocean','pink','prism','rainbow','seismic','spectral',\
    'spring','summer','terrain','winter']

###########################
#Thresholds
############################
#CLIM_SUM_MAPS element, min, max
CLIM_SUM_MAPS_DAILY_THRESHES = {
    'maxt':[-10,140],
    'mint':[-50,80],
    'avgt':[-50,100],
    'dtr': [10,60],
    'obst':[-70,150],
    'pcpn': [0,3],
    'snow': [0,10],
    'snwd': [0,50],
    'cdd': [0,50],
    'hdd': [0,50],
    'gdd': [0,50],
    'evap': [0,10],
    'wdmv': [0,100]
}

###################################
###################################
#LARGE DATA REQUEST
###################################
###################################

###################################
###################################
#FORM CHOICES/FORM related stuff
###################################
###################################
#DELETE?
SEARCH_AREA_FORM_TO_ACIS = {
    'station_id':'stnid',
    'station_ids':'stnids',
    'climate_division':'climdiv',
    'climdiv':'climdiv',
    'county_warning_area':'cwa',
    'cwa':'cwa',
    'bounding_box':'bbox',
    'bbox':'bbox',
    'state':'state',
    'county':'county',
    'basin':'basin',
    'shape':None,
    'location':'loc',
    'point':'loc',
}

#DELETE??
STN_AREA_FORM_TO_PARAM = {
    'station_id':'sids',
    'station_ids':'sids',
    'sid':'sids',
    'sids':'sids',
    'climate_division':'climdiv',
    'climdiv':'climdiv',
    'county_warning_area':'cwa',
    'cwa':'cwa',
    'bounding_box':'bbox',
    'bbox':'bbox',
    'state':'state',
    'sw_states':'state',
    'states':'state',
    'county':'county',
    'basin':'basin',
    'shape':'bbox',
    'location':'loc',
    'point':'loc'
}

#NEW
FORM_TO_META_PARAMS = {
    'station_id':'sids',
    'station_ids':'sids',
    'station':'sids',
    'grid':'sids',
    'climate_division':'climdiv',
    'climdiv':'climdiv',
    'county_warning_area':'cwa',
    'cwa':'cwa',
    'bounding_box':'bbox',
    'bbox':'bbox',
    'state':'state',
    'states':'state',
    'county':'county',
    'basin':'basin',
    'shape':'bbox',
    'location':'loc',
    'point':'loc'
}

#NEW
FORM_TO_PARAMS = {
    'station_id':'sid',
    'station_ids':'sids',
    'sid':'sid',
    'sids':'sids',
    'climate_division':'climdiv',
    'climdiv':'climdiv',
    'county_warning_area':'cwa',
    'cwa':'cwa',
    'bounding_box':'bbox',
    'bbox':'bbox',
    'state':'state',
    'states':'state',
    'county':'county',
    'basin':'basin',
    'shape':'bbox',
    'location':'loc',
    'point':'loc'
}
#NEW
PARAMS_TO_FORM= {
    'climdiv':'climate_division',
    'climate_division':'climate_division',
    'cwa':'county_warning_area',
    'county_warning_area':'county_warning_area',
    'bbox':'bounding_box',
    'bounding_box':'bounding_box',
    'stnid':'station_id',
    'station_id':'sid',
    'stn_id': 'sid',
    'stnids':'sids',
    'station_ids':'sids',
    'basin':'basin',
    'county':'county',
    'shape':'shape',
    'point':'location',
    'location':'location',
    'loc':'location',
    'state':'state',
    'states':'states',
}


GRID_AREA_FORM_TO_PARAM = {
    #Note: gridACIS calls currently don't support cwa, climdiv, basin, county
    'climate_division':'bbox',
    'climdiv':'bbox',
    'county_warning_area':'bbox',
    'cwa':'bbox',
    'bounding_box':'bbox',
    'bbox':'bbox',
    'state':'state',
    'sw_states':'state',
    'states':'state',
    'county':'bbox',
    'basin':'bbox',
    'shape':'bbox',
    'location':'loc',
    'point':'loc'
}

ACIS_TO_SEARCH_AREA = {
    'climdiv':'climate_division',
    'climate_division':'climate_division',
    'cwa':'county_warning_area',
    'county_warning_area':'county_warning_area',
    'bbox':'bounding_box',
    'bounding_box':'bounding_box',
    'stnid':'station_id',
    'station_id':'station_id',
    'stn_id': 'station_id',
    'stnids':'station_ids',
    'station_ids':'station_ids',
    'basin':'basin',
    'county':'county',
    'shape':'shape',
    'point':'location',
    'location':'location',
    'loc':'location',
    'state':'state',
    'states':'states',
    'sw_states':'states'
}

AREA_DEFAULTS = {
    'stnid': 'RENO TAHOE INTL AP, 266779',
    'station_id':'RENO TAHOE INTL AP, 266779',
    'station_ids':'266779,050848',
    'stn_id':'RENO TAHOE INTL AP, 266779',
    'stnids':'266779,050848',
    'climdiv':'Northwestern, NV01',
    'climate_division':'Northwestern, NV01',
    'cwa':'Las Vegas NV, VEF',
    'county_warning_area':'Las Vegas NV, VEF',
    'bbox':'-115,34,-114,35',
    'bounding_box':'-115,34,-114,35',
    'state':'nv',
    'states':'states',
    'sw_states':'states',
    'county':'Churchill, 32001',
    'basin':'Hot Creek-Railroad Valleys,16060012',
    'shape':'-115,34, -115, 35,-114,35, -114, 34',
    'point': '-111,40',
    'location':'-111,40'
}

DISPLAY_PARAMS = {
    #data types
    'data_type':'Data Type',
    'station': 'Station',
    'grid':'Grid',
    #metadata
    'uid':'Unique Station Identifier',
    'coop_id': 'COOP Identifier',
    'sids': 'Station ID/Network List',
    'll':'Longitude, Latitude',
    'elev':'Elevation',
    'name':'Station Name',
    'state':'State',
    'valid_daterange': 'Valid Date Range (by Element)',
    'select_grid_by':'Grid Data Request',
    'select_stations_by': 'Station Data Request',
    #search areas
    'user_area_id': 'Point/Area',
    'stnid': 'Station ID',
    'stnids': 'Station IDs',
    'station_id': 'Station ID',
    'station_ID': 'Station ID',
    'station_ids': 'Station IDs',
    'station_IDs':'Station IDs',
    'location': 'Location (lon,lat)',
    'loc': 'Location(lon,lat)',
    'point': 'Location (lon,lat)',
    'lat': 'Latitude',
    'lon': 'Longitude',
    'shape': 'Custom Shape',
    'polygon': 'Polygon',
    'circle':'Circle',
    'climate_division': 'Climate Division',
    'climdiv': 'Climate Division',
    'county_warning_area': 'County Warning Area',
    'cwa': 'County Warning Area',
    'county': 'County',
    'basin': 'Drainage Basin',
    'state': 'State',
    'states':'States',
    'bounding_box': 'Bounding Box',
    'bbox': 'Bounding Box',
    'custom_shape': 'Custom Shape',
    'shape': 'Custom Shape',
    #dates and elements
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'start_window': 'Start Window',
    'end_window': 'End Window',
    'window':'Window',
    'start_month': 'Start Month',
    'end_month': 'End Month',
    'start_day':'Start Day',
    'end_day': 'End Day',
    'time_period': 'Time Period',
    'X': 'X',
    'start_year': 'Start Year',
    'end_year': 'End Year',
    'graph_start_year': 'Graph Start Year',
    'graph_end_year': 'Graph End Year',
    'dates_constraints': 'Date Constraints',
    'element':'Element',
    'elements':'Elements',
    'elems_long':'Elements',
    'elements_string': 'Elements String',
    'degree_days':'Degree Days',
    'element_selection': 'Element Selection',
    'el_type':'Climate Element Type',
    'units': 'Units',
    'metric': 'Metric',
    'english': 'English',
    'elements_constraints':'Element Constraints',
    'base_temperature': 'Base Temperature',
    'maxt': 'Maximum Daily Temperature',
    'mly_maxt':'Maximum Monthly Temperature',
    'yly_maxt':'Maximum Yearly Temperature',
    'mint': 'Minimum Daily Temperature',
    'mly_mint': 'Minimum Monthly Temperature',
    'yly_mint': 'Minimum Yearly Temperature',
    'avgt': 'Average Daily Temperature',
    'mly_avgt': 'Average Monthly Temperature',
    'yly_avgt': 'Average Yearly Temperature',
    'obst': 'Observation Time Temperature',
    'pcpn': 'Precipitation',
    'mly_pcpn': 'Monthly Precipitation',
    'yly_pcpn': 'Yearly Precipitation',
    'snow': 'Snowfall',
    'snwd': 'Snow Depth',
    'dtr': 'Daily Temperature Range',
    'gdd': 'Growing Degree Days',
    'hdd': 'Heating Degree Days',
    'cdd': 'Cooling Degree Days',
    'hddxx': 'Heating Degree Days Base xx',
    'cddxx': 'Cooling Degree Days Base xx',
    'gddxx': 'Growing Degree Days Base xx',
    'wdmv': 'Wind Movement',
    'evap': 'Pan Evaporation',
    'pet': 'Potential ET',
    #Other
    'temporal_resolution': 'Temporal Resolution',
    'temporal': 'Temporal Summary',
    'spatial':'Spatial Summary',
    'dly':'Daily',
    'mly':'Monthly',
    'yly':'Yearly',
    'summary': 'Summary',
    'data_summary': 'Data Summary',
    'summary_type': 'Summary Type',
    'temporal_summary':'Temporal Summary',
    'spatial_summary':'Spatial Summary',
    'windowed_data': 'Windowed Data',
    'mean': 'Mean',
    'median':'Median',
    'sum': 'Sum of',
    'max': 'Maximum',
    'min': 'Minimum',
    'none': 'Raw Data',
    'constraints': 'Constraints',
    'all_all': 'All Elements, All Dates',
    'all_any': 'All Elements, Any Dates',
    'any_any': 'Any Elements, Any Dates',
    'any_all': 'Any Elements, All Dates',
    'grid': 'Grid',
    'show_running_mean': 'Show Running Mean',
    'running_mean_years': 'Years used in Running Mean Computation',
    'running_mean_days': 'Days used in Running Mean Computation',
    'delimiter': 'Delimiter',
    'data_format': 'Data Format',
    'date_format': 'Date Format',
    'show_flags': 'Show Flags',
    'show_observation_time': 'Show Observation Time',
    'temporal_resolution': 'Temporal Resolution',
    'monthly_statistic': 'Monthly Statistic',
    'mmax':'Monthly Maximum',
    'mmin':'Monthly Minimum',
    'msum':'Monthly Sum',
    'mave':'Monthly Average',
    'sd':'Standard Deviation',
    'ndays':'Number of Days',
    'rmon':'Range during Month',
    'max_missing_days': 'Maximum Number of Missing Days',
    'departures_from_averages': 'Show results as departures from averages',
    'frequency_analysis': 'Frequency Analysis',
    'frequency_analysis_type': 'Frequency Analysis Type',
    'pearson': 'Pearson III',
    'gev': 'Generalized Extreme Value',
    'less_greater_or_between': '',
    'threshold': 'Threshold',
    'l':'Below',
    'g':'Above',
    'b':'Between',
    'threshold_low_for_between':'Lower Threshold',
    'threshold_high_for_between':'Upper Threshold',
    'threshold_for_less_or_greater':'Threshold',
    'less':'Threshold',
    'greater':'Threshold',
    'above': 'Above',
    'below': 'Below',
    'T': 'Yes',
    'F': 'No',
    #Plot Options
    'graph_title': 'Graph Title',
    'image_size': 'Image Size',
    'show_major_grid': 'Show Major Grid',
    'show_minor_grid': 'Show Minor Grid',
    'connector_line': 'Connect Data Points',
    'connector_line_width': 'Connector Line Width',
    'markers': 'Show Markers',
    'marker_type': 'Marker Type',
    'axis_min':'Y-Axis minimum',
    'axis_max':'Y-Axis maximum',
    'vertical_axis_min':'Vertical Axis Minimum',
    'vertical_axis_max':'Vertical Axis Maximum',
    'level_number': 'Number of Levels',
    'projection':'Projection',
    'map_ol': 'Map Overlay',
    'interpolation':'Interpolation Method',
    'cmap': 'Color Map',
    'user_name': 'User Name',
    'user_email': 'User Email'
}
#id, name, time range, resolution (km), valid daterange

#yesterday = WRCCUtils.set_back_date(1)
GRID_CHOICES = {
    '1': ['NRCC Interpolated (US)','',5,[['19500101',today]]],
    '2': ['NRCC Hi-Res (East of Rockies)','',5,[['20070101',today]]],
    '3': ['NARCCAP (US)','',50,[['19700101','19991231'],['20400101','20691231']]],
    '4': ['CRCM + NCEP (Historical only)','',50,[['19700101','19991231']]],
    '5': ['CRCM + CCSM','',50,[['19700101','19991231'],['20400101','20691231']]],
    '6': ['CRCM + CCSM3','',50,[['19700101','19991231'],['20400101','20691231']]],
    '7': ['HRM3 + NCEP  (Historical only)','',50,[['19700101','19991231']]],
    '8': ['HRM3 HadCM3','',50,[['19700101','19991231'],['20400101','20691231']]],
    '9': ['MM5I + NCEP (Historical only)','',50,[['19700101','19991231']]],
    '10': ['MM5I + CCSM','',50,[['19700101','19991231'],['20400101','20691231']]],
    '11': ['RCM3 + NCEP (Historical only)','',50,[['19700101','19991231']]],
    '12': ['RCM3 + CGCM3','',50,[['19700101','19991231'],['20400101','20691231']]],
    '13': ['RCM3 + GFDL','',50,[['19700101','19991231'],['20400101','20691231']]],
    '14': ['WRFG + NCEP (Historical only)','',50,[['19700101','19991231']]],
    '15': ['WRFG + CCSM','',50,[['19700101','19991231'],['20400101','20691231']]],
    '16': ['WRFG + CGCM3','',50,[['19700101','19991231'],['20400101','20691231']]],
    '21': ['PRISM','',50,[['18950101',today],['19810101',today]]]
}


MONTH_CHOICES = (
    ('01', 'January'),
    ('02', 'February'),
    ('03', 'March'),
    ('04', 'April'),
    ('05', 'May'),
    ('06', 'June'),
    ('07', 'July'),
    ('08', 'August'),
    ('09', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
)

#Data Formats
FILE_EXTENSIONS = {
    'json':'.json',
    'clm':'.txt',
    'dlm':'.dat',
    'xl':'.xls',
    'html':'.html'
}

DATA_FORMAT_CHOICES_LTD = (
    #('json', 'JSON, .json'),
    ('dlm', 'Delimited, .dat'),
    ('clm', 'Columnar, .txt'),
    ('xl', 'Excel, .xls'),

)

DATA_FORMAT = {
    'dlm':'Delimited .dat',
    'clm':'Columnar .txt',
    'xl':'Excel .xls',
    'html':'HTML'
}


DATE_FORMAT = {
    'none':'',
    'dash':'-',
    'colon':':',
    'slash': '/'
}

#width, height in pixels
IMAGE_SIZES = {
    'small':[510, 290],
    'medium':[650, 370],
    'large':[850, 480],
    'larger':[1150, 610],
    'extra_large':[1450, 820],
    'wide':[1850, 610],
    'wider':[2450, 610],
    'widest':[3450, 610],
}

IMAGE_SIZES_MAP = {
    'small':300,
    'medium':500,
    'large':700
}

###################################
###################################
#GRIDDED APPS
###################################
###################################
CLIM_RISK_SUMMARY_CHOICES = (
    ('max', 'Maximum over polygon'),
    ('min', 'Minimium over polygon'),
    ('sum', 'Sum over polygon'),
    ('mean', 'Avererage over polygon'),
)

SHAPE_NAMES = {
    'bounding_box': 'Bounding Box ',
    'state': 'State ',
    'shape': 'Custom Shape ',
    'circle': 'Circle (lat, lon, radius (meter)) ',
    'county': 'County ',
    'climate_division':'Climate Division ',
    'county_warning_area':'County Warning Area ',
    'basin':'Drainage Basin ',
    'location':'Point Location '
}

###################################
###################################
#SODS
###################################
###################################
MICHELES_ELEMENT_NAMES = {
    'pcpn':'Pcpn',
    'snow':'Snfl',
    'snwd':'Sndp',
    'maxt':'TMax',
    'mint':'TMin',
    'avgt':'TMean',
    'obst':'TObs',
    'dtr':'TRange',
    'range':'TRange',
    'cdd':'Cdd',
    'hdd':'Hdd',
    'gdd':'Gdd',
    'corn':'Corn',
    'evap':'Evap',
    'wdmv':'Wdmv',
    'pet':'Potential ET'
}

SOD_ELEMENT_LIST_BY_APP = {
    'Soddyrec': {
                'all':['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd'],
                'tmp':['maxt', 'mint', 'pcpn'],
                'wtr':['pcpn', 'snow', 'snwd'],
                'pcpn':['pcpn'],
                'snow':['snow'],
                'snwd':['snwd'],
                'maxt':['maxt'],
                'mint':['mint'],
                'cdd':['cdd'],
                'hdd':['hdd']
                },
    'Soddynorm': {
                'all':['maxt', 'mint', 'pcpn']
                },
    'Sodsumm': {
                'all':['maxt', 'mint', 'avgt', 'pcpn', 'snow'],
                'temp':['maxt', 'mint', 'avgt'],
                'prsn':['pcpn', 'snow'],
                'both':['maxt', 'mint', 'avgt', 'pcpn', 'snow'],
                'hc':['maxt', 'mint'],
                'g':['maxt', 'mint']
               },
    'Sodsum': {
                'multi':['pcpn','snow','snwd','maxt','mint'],
                'pcpn':['pcpn'],
                'snow':['snow'],
                'snwd':['snwd'],
                'maxt':['maxt'],
                'mint':['mint']
               },
    'Sodrun':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'range':['maxt','mint'],
            },
    'Sodrunr':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'range':['maxt', 'mint'],
            },
    'Sodlist':{
              'all':['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst']
              },
    'sodlist_web':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'avgt':['avgt'],
              'cdd':['cdd'],
              'hdd':['hdd'],
              'gdd':['gdd'],
              'evap':['evap'],
              'wdmv':['wdmb']
                },

    'Sodcnv':{
            'all':['pcpn', 'snow', 'snwd', 'maxt', 'mint']
            },
    'Soddd':{
            'all':['maxt', 'mint']
            },
    'Sodpad':{
            'all':['pcpn']
            },
    'Sodmonline':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'avgt':['avgt'],
              'dtr':['maxt','mint'],
              'range':['maxt','mint'],
              'cdd':['cdd'],
              'hdd':['hdd'],
              'gdd':['gdd'],
              'evap':['evap'],
              'wdmv':['wdmv']
                },
    'Sodmonlinemy':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'avgt':['avgt'],
              'dtr':['maxt','mint'],
              'range':['maxt','mint'],
              'cdd':['cdd'],
              'hdd':['hdd'],
              'gdd':['gdd'],
              'evap':['evap'],
              'wdmv':['wdmv']
                },
    'Sodpct':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'avgt':['maxt','mint'],
              'dtr':['maxt','mint'],
              'range':['maxt','mint'],
              'cdd':['maxt','mint'],
              'hdd':['maxt','mint'],
              'gdd':['maxt','mint'],
              'evap':['evap'],
              'wdmv':['wdmv']
                },
    'Sodthr':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'avgt':['maxt','mint'],
              'dtr':['maxt','mint'],
              'range':['maxt','mint'],
              'cdd':['maxt','mint'],
              'hdd':['maxt','mint'],
              'gdd':['maxt','mint'],
              'evap':['evap'],
              'wdmv':['wdmv']
                },
    'Sodpiii':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'avgt':['maxt','mint'],
              'dtr':['maxt','mint'],
              'range':['maxt','mint'],
              'cdd':['maxt','mint'],
              'hdd':['maxt','mint'],
              'gdd':['maxt','mint'],
              'evap':['evap'],
              'wdmv':['wdmv']
                },

    'Sodxtrmts':{
              'pcpn':['pcpn'],
              'snow':['snow'],
              'snwd':['snwd'],
              'maxt':['maxt'],
              'mint':['mint'],
              'avgt':['maxt','mint'],
              'dtr':['maxt','mint'],
              'range':['maxt','mint'],
              'cdd':['maxt','mint'],
              'hdd':['maxt','mint'],
              'gdd':['maxt','mint'],
              'evap':['evap'],
              'wdmv':['wdmv'],
              'pet':['maxt','mint']
                }
}


FORM_IMAGE_SIZES = (
    ('small', 'Small (510x290)'),
    ('medium', 'Medium (650x370)'),
    ('large', 'Large (850x480)'),
    ('larger', 'Larger (1150x610)'),
    ('extra_large', 'Extra Large (1450x820)'),
    ('wide', 'Wide (1850x610)'),
    ('wider', 'Wider (2450x610)'),
    ('widest', 'Widest (3450x610)'),
)

COLUMN_HEADERS = {
    'Sodxtrmts': ['YEAR', 'JAN', 'FLAG', 'FEB', 'FLAG', 'MAR', 'FLAG', 'APR', 'FLAG', 'MAY', 'FLAG', \
                  'JUN', 'FLAG', 'JUL', 'FLAG', 'AUG', 'FLAG', 'SEP', 'FLAG', 'OCT', 'FLAG', 'NOV', \
                  'FLAG', 'DEC', 'FLAG', 'ANN', 'FLAG'],
    'Sodsumm':None
}


##########
#SODXTRMTS
##########
SXTR_ELEMENT_CHOICES = (
    ('pcpn', 'Daily Precipitation'),
    ('snow', 'Daily Snowfall'),
    ('snwd', 'Daily Snowdepth'),
    ('maxt', 'Daily Maximum Temperature '),
    ('mint', 'Daily Minimum Temperature'),
    ('avgt', 'Daily Mean Temperature'),
    ('obst', 'Observation Time Temperature'),
    ('dtr', 'Daily Temperature Range'),
    ('hdd', 'Daily Heating Degree Days'),
    ('cdd', 'Daily Cooling Degree Days'),
    ('gdd', 'DailyGrowing degree days'),
    ('evap', 'Daily Evaporation'),
    ('wdmv', 'Daily Wind Movement'),
    ('pet', 'Potential ET'),
)

SXTR_ELEMENT_LIST = ['pcpn','snow','snwd','maxt','mint','avgt','dtr','hdd', 'cdd','gdd','evap','wdmv','pet']

SXTR_ANALYSIS_CHOICES = (
    ('mmax', 'Monthly Maximum'),
    ('mmin', 'Monthly Minimum'),
    ('mave', 'Monthly Average'),
    ('sd', 'Standard Deviation'),
    ('ndays', 'Number of Days'),
    ('rmon', 'Range during Month'),
    ('msum', 'Monthly Sum'),
)
SXTR_ANALYSIS_CHOICES_DICT = {
    'mmax': 'Monthly Maximum',
    'mmin': 'Monthly Minimum',
    'mave': 'Monthly Average',
    'sd': 'Standard Deviation',
    'ndays': 'Number of Days',
    'rmon': 'Range during Month',
    'msum': 'Monthly Sum',
}



F_ANALYSIS_CHOICES = (
    ('p', 'Pearson Type III'),
    ('g', 'Generalized Extreme Value'),
    #('b', 'Beta-P'),
    #('c', 'Censored Gamma'),
)

SXTR_SUMMARY_CHOICES = (
    ('max', 'Maximum over months'),
    ('min', 'Minimium over months'),
    ('sum', 'Sum over months'),
    ('mean', 'Avererage over months'),
    ('individual', 'Plot months separately'),
)

MARKER_CHOICES = (
    ('diamond', 'Diamond'),
    ('circle', 'Circle'),
    ('square', 'Square'),
    ('triangle', 'Upward Triangle'),
    ('triangle-down', 'Downward Triangle'),
)


########
#SODSUMM
########
SODSUMM_TABLE_NAMES = {
    'temp':'Temperature',
    'prsn':'Precipitation',
    'hdd':'Heating Degree Days',
    'cdd':'Cooling Degree Days',
    'gdd':'Growing Degree Days',
    'corn':'Corn Growiing Degree Days',
}

TAB_NAMES_WITH_GRAPHICS = {
'all': ['Temp', 'Precip', 'Snow', 'Hdd', 'Cdd', 'Gdd', 'Corn'],
'both':['Temperature', 'Precip', 'Snow'],
'temp':['Temperature'],
'prsn':['Precip', 'Snow'],
'hc':['Hdd', 'Cdd'],
'g':['Gdd', 'Corn']
}

TAB_NAMES_NO_GRAPHICS= {
'all':['Temp', 'Precip/Snow', 'Hdd', 'Cdd', 'Gdd', 'Corn'],
'both':['Temp', 'Precip/Snow'],
'temp':['Temperature'],
'prsn':['Precip/Snow'],
'hc':['Hdd', 'Cdd'],
'g':['Gdd', 'Corn']
}


TAB_LIST_WITH_GRAPHICS = {
'all': ['temp', 'pcpn', 'snow', 'hdd', 'cdd', 'gdd', 'corn'],
'both':['temp', 'pcpn', 'snow'],
'temp':['temp'],
'prsn':['pcpn', 'snow'],
'hc':['hdd', 'cdd'],
'g':['gdd', 'corn']
}

TAB_LIST_NO_GRAPHICS = {
'all':['temp', 'prsn', 'hdd', 'cdd', 'gdd', 'corn'],
'both':['temp', 'prsn'],
'temp':['temp'],
'prsn':['prsn'],
'hc':['hdd', 'cdd'],
'g':['gdd', 'corn']
}

TABLE_LIST_WITH_GRAPHICS = {
'all':['temp', 'prsn', 'prsn', 'hdd', 'cdd', 'gdd', 'corn'],
'both':['temp', 'prsn', 'prsn'],
'temp':['temp'],
'prsn':['prsn', 'prsn'],
'hc':['hdd', 'cdd'],
'g':['gdd', 'corn']
}

TABLE_LIST_NO_GRAPHICS = {
'all':['temp','prsn', 'hdd', 'cdd', 'gdd', 'corn'],
'both':['temp''prsn'],
'temp':['temp'],
'prsn':['prsn'],
'hc':['hdd', 'cdd'],
'g':['gdd', 'corn']
}
