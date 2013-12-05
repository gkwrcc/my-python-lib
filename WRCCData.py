#!/usr/bin/python

'''
Module WRCCData

Contains useful dicts and lists
CAPS names imply use in django forms
'''
from collections import defaultdict
from collections import OrderedDict

###################################
###################################
#General
###################################
###################################

FIPS_STATE_KEYS = {'al':'01','az':'02','ca':'04','co':'05', 'hi':'51', 'id':'10','mt':'24', 'nv':'26', \
             'nm':'29','pi':'91','or':'35','tx':'41', 'ut':'42', 'wa':'45','ar':'03', 'ct':'06', \
             'de':'07','fl':'08','ga':'09','il':'11', 'in':'12', 'ia':'13','ks':'14', 'ky':'15', \
             'la':'16','me':'17','md':'18','ma':'19', 'mi':'20', 'mn':'21','ms':'22', 'mo':'23', \
             'ne':'25','nh':'27','nj':'28','ny':'30', 'nc':'31', 'nd':'32','oh':'33', 'ok':'34', \
             'pa':'36','ri':'37','sc':'38','sd':'39', 'tn':'40', 'ct':'43','va':'44', 'wv':'46', \
             'wi':'47','vi':'67','pr':'66','wr':'96', 'ml':'97', 'ws':'98','ak':'50'}

STATE_CHOICES = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', \
                'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', \
                'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', \
                'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', \
                'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

NETWORK_CODES = {'1': 'WBAN', '2':'COOP', '3':'FAA', '4':'WMO', '5':'ICAO', '6':'GHCN', '7':'NWSLI', \
'8':'RCC', '9':'ThreadEx', '10':'CoCoRaHS', '11':'Misc'}
NETWORK_ICONS = {'1': 'yellow-dot', '2': 'blue-dot', '3': 'green-dot','4':'purple-dot', '5': 'ltblue-dot', \
'6': 'orange-dot', '7': 'pink-dot', '8': 'yellow', '9':'green', '10':'purple', '11': 'red'}
#1YELLOW, 2BLUE, 3BROWN, 4OLIVE, 5GREEN, 6GRAY, 7TURQOIS, 8BLACK, 9TEAL, 10WHITE Multi:Red, Misc:Fuchsia
KELLY_NETWORK_CODES = {'1': 'COOP', '2':'GHCN', '3':'ICAO', '4':'NWSLI', '5':'FAA', '6':'WMO', '7':'WBAN', \
'8':'CoCoRaHS', '9':'RCC', '10':'Threadex', '11':'Misc'}
KELLY_NETWORK_ICONS = {'1': 'blue-dot', '2': 'orange-dot', '3': 'ltblue-dot','4':'pink-dot', '5': 'green-dot', \
'6': 'purple-dot', '7': 'yellow-dot', '8': 'purple', '9':'yellow', '10':'green', '11': 'red'}


ACIS_ELEMENTS = defaultdict(dict)
ACIS_ELEMENTS ={'1':{'name':'maxt', 'name_long': 'Maximum Daily Temperature (F)', 'vX':1},
              '2':{'name':'mint', 'name_long': 'Minimum Daily Temperature (F)', 'vX':2},
              '43': {'name':'avgt', 'name_long': 'Average Daily Temperature (F)', 'vX':43},
              '3':{'name':'obst', 'name_long': 'Observation Time Temperature (F)', 'vX':3},
              '4': {'name': 'pcpn', 'name_long':'Precipitation (in)', 'vX':4},
              '10': {'name': 'snow', 'name_long':'Snowfall (in)', 'vX':10},
              '11': {'name': 'snwd', 'name_long':'Snow Depth (in)', 'vX':11},
              '7': {'name': 'evap', 'name_long':'Pan Evaporation (in)', 'vX':7},
              '12': {'name': 'wdmv', 'name_long':'Wind Movement (Mi)', 'vX':12},
              '45': {'name': 'dd', 'name_long':'Degree Days', 'vX':45},
              '44': {'name': 'cdd', 'name_long':'Cooling Degree Days', 'vX':45},
              '-45': {'name': 'hdd', 'name_long':'Heating Degree Days', 'vX':45},
              '-44': {'name': 'gdd', 'name_long':'Growing Degree Days', 'vX':45}}
              #bug fix needed for cdd = 44

ACIS_ELEMENTS_DICT = {
              'maxt':{'name':'maxt', 'name_long': 'Maximum Daily Temperature (F)', 'vX':1},
              'mint':{'name':'mint', 'name_long': 'Mininimum Daily Temperature (F)', 'vX':2},
              'avgt': {'name':'avgt', 'name_long': 'Mean Daily Temperature (F)', 'vX':43},
              'dtr': {'name':'dtr', 'name_long': 'Daily Temperature Range (F)', 'vX':None},
              'obst':{'name':'obst', 'name_long': 'Observation Time Temperature (F)', 'vX':3},
              'pcpn': {'name': 'pcpn', 'name_long':'Precipitation (in)', 'vX':4},
              'snow': {'name': 'snow', 'name_long':'Snowfall (in)', 'vX':10},
              'snwd': {'name': 'snwd', 'name_long':'Snow Depth (in)', 'vX':11},
              'cdd': {'name': 'cdd', 'name_long':'Cooling Degree Days', 'vX':45},
              'hdd': {'name': 'hdd', 'name_long':'Heating Degree Days', 'vX':45},
              'gdd': {'name': 'gdd', 'name_long':'Growing Degree Days', 'vX':45},
              'evap': {'name': 'evap', 'name_long':'Evaporation (in)', 'vX':7},
              'wdmv': {'name': 'wdmv', 'name_long':'Wind Movement (Mi)', 'vX':12}
              #bug fix needed for cdd = 44 (WAITING FOR BILL, ALSO IN PLACES BELOW, eg in station_locator_app, also in AcisWS.py)
}

ACIS_ELEMENTS_LIST = [['maxt','Maximum Daily Temperature (F)'], ['mint','Minimum Daily Temperature (F)'],
                      ['avgt','Average Daily Temperature (F)'], ['obst', 'Observation Time Temperature (F)'], \
                      ['pcpn', 'Precipitation (in)'], ['snow', 'Snowfall (in)'], \
                      ['snwd', 'Snow Depth (in)'], ['cdd', 'Cooling Degree Days'], \
                      ['hdd','Heating Degree Days'], ['gdd', 'Growing Degree Days'], \
                      ['evap', 'Pan Evaporation (in)'], ['gdd', 'Wind Movement (Mi)']]

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
    'Jul':'07',
    'Aug':'08',
    'Sep':'09',
    'Oct':'10',
    'Nov':'11',
    'Dec':'12',
}

NUMBER_TO_MONTH_NAME = {
    '01':'Jan',
    '02':'Feb',
    '03':'Mar',
    '04':'Apr',
    '05':'May',
    '06':'Jun',
    '07':'Jul',
    '08':'Aug',
    '09':'Sep',
    '10':'Oct',
    '11':'Nov',
    '12':'Dec'
}

MONTH_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

DELIMITERS = {
    'comma':',',
    'tab':chr(9),
    'colon': ':',
    'space': ' ',
    'pipe':'|'
}

###################################
###################################
#FORM CHOICES/FORM related stuff
###################################
###################################
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

ACIS_TO_SEARCH_AREA = {
    'climdiv':'climate_division',
    'cwa':'county_warning_area',
    'bbox':'bounding_box',
    'stnid':'station_id',
    'stn_id': 'station_id',
    'stnids':'station_ids',
    'basin':'basin',
    'county':'county',
    'shape':'shape',
    'point':'location',
    'loc':'location',
    'state':'state',
    'states':'states',
    'sw_states':'states'
}

AREA_DEFAULTS = {
    'stnid': '266779',
    'station_id':'266779',
    'station_ids':'266779,050848',
    'stn_id':'266779',
    'stnids':'266779,050848',
    'climdiv':'NV01',
    'climate_division':'NV01',
    'cwa':'PUB',
    'county_warning_area':'PUB',
    'bbox':'-115,34,-114,35',
    'bounding_box':'-115,34,-114,35',
    'state':'NV',
    'states':'states',
    'sw_states':'states',
    'county':'08051',
    'basin':'10180002',
    'shape':'-115,34, -115, 35,-114,35, -114, 34',
    'point': '-111,40',
    'location':'-111,40'
}

DISPLAY_PARAMS = {
    #metadata
    'uid':'Unique Station Identifier',
    'coop_id': 'COOP Identifier',
    'sids': 'Station ID/Network List',
    'll':'Longitude, Latitude',
    'elev':'Elevation',
    'name':'Station Name',
    'state':'State',
    'valid_daterange': 'Valid Date Range (by element)',
    'select_grid_by':'Grid Selection By',
    'select_stations_by': 'Station Selection By',
    #search areas
    'stnid': 'Station ID',
    'stnids': 'Station IDs',
    'station_id': 'Station ID',
    'station_ID': 'Station ID',
    'station_ids': 'Station IDs',
    'station_IDs':'Station IDs',
    'location': 'Location (lon, lat)',
    'loc': 'Location (lon, lat)',
    'point': 'Location (lon, lat)',
    'lat': 'Latitude',
    'lon': 'Longitude',
    'shape': 'Custom Shape',
    'polygon': 'Polygon',
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
    'start_month': 'Start Month',
    'end_month': 'End Month',
    'time_period': 'Time Period',
    'X': 'X',
    'start_year': 'Start Year',
    'end_year': 'End Year',
    'graph_start_year': 'Graph Start Year',
    'graph_end_year': 'Graph End Year',
    'element':'Element',
    'elements':'Elements',
    'element_selection': 'Element Selection',
    'el_type':'Climate Element Type',
    'base_temperature': 'Base Temperature',
    'maxt': 'Maximum Daily Temperature (F)',
    'mint': 'Minimum Daily Temperature (F)',
    'avgt': 'Average Daily Temperature (F)',
    'obst': 'Observation Time Temperature (F)',
    'pcpn': 'Precipitation (in)',
    'snow': 'Snowfall (in)',
    'snwd': 'Snow Depth (in)',
    'gdd': 'Growing Degree Days',
    'hdd': 'Heating Degree Days',
    'cdd': 'Cooling Degree Days',
    'hddxx': 'Heating Degree Days Base xx',
    'cddxx': 'Cooling Degree Days Base xx',
    'gddxx': 'Growing Degree Days Base xx',
    'wdmv': 'Wind Movement (Mi)',
    'evap': 'Pan Evaporation (in)',
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
    'mean': 'Mean',
    'sum': 'Sum',
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
    'vertical_axis_max':'Vertical Axis Maximum'
}

GRID_CHOICES = {
    '1': 'NRCC Interpolated (US)',
    '2': 'NRCC Hi-Res (East of Rockies)',
    '3': 'NARCCAP (US)',
    '4': 'CRCM + NCEP (Historical only)',
    '5': 'CRCM + CCSM',
    '6': 'CRCM + CCSM3',
    '7': 'HRM3 + NCEP  (Historical only)',
    '8': 'HRM3 HadCM3',
    '9': 'MM5I + NCEP (Historical only)',
    '10': 'MM5I + CCSM',
    '11': 'RCM3 + NCEP (Historical only)',
    '12': 'RCM3 + CGCM3',
    '13': 'RCM3 + GFDL',
    '14': 'WRFG + NCEP (Historical only)',
    '15': 'WRFG + CCSM',
    '16': 'WRFG + CGCM3',
    '21': 'PRISM'
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
    ('dtr', 'Daily Temperature Range'),
    ('hdd', 'Daily Heating Degree Days'),
    ('cdd', 'Daily Cooling Degree Days'),
    ('gdd', 'DailyGrowing degree days'),
    ('evap', 'Daily Evaporation'),
    ('wdmv', 'Daily Wind Movement'),
)

SXTR_ELEMENT_LIST = ['pcpn','snow','snwd','maxt','mint','avgt','dtr','hdd', 'cdd','gdd','evap','wdmv']

SXTR_ANALYSIS_CHOICES = (
    ('mmax', 'Monthly Maximum'),
    ('mmin', 'Monthly Minimum'),
    ('mave', 'Monthly Average'),
    ('sd', 'Standard Deviation'),
    ('ndays', 'Number of Days'),
    ('rmon', 'Range during Month'),
    ('msum', 'Monthly Sum'),
)



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
