#!/usr/bin/python

'''
Module WRCCData

Contains useful dicts and lists
CAPS names imply use in django forms
'''
from collections import defaultdict

#################################
#General
#################################
fips_state_keys = {'al':'01','az':'02','ca':'04','co':'05', 'hi':'51', 'id':'10','mt':'24', 'nv':'26', \
             'nm':'29','pi':'91','or':'35','tx':'41', 'ut':'42', 'wa':'45','ar':'03', 'ct':'06', \
             'de':'07','fl':'08','ga':'09','il':'11', 'in':'12', 'ia':'13','ks':'14', 'ky':'15', \
             'la':'16','me':'17','md':'18','ma':'19', 'mi':'20', 'mn':'21','ms':'22', 'mo':'23', \
             'ne':'25','nh':'27','nj':'28','ny':'30', 'nc':'31', 'nd':'32','oh':'33', 'ok':'34', \
             'pa':'36','ri':'37','sc':'38','sd':'39', 'tn':'40', 'ct':'43','va':'44', 'wv':'46', \
             'wi':'47','vi':'67','pr':'66','wr':'96', 'ml':'97', 'ws':'98','ak':'50'}
fips_key_state = {}
state_choices = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', \
                'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', \
                'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', \
                'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', \
                'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

network_codes = {'1': 'WBAN', '2':'COOP', '3':'FAA', '4':'WMO', '5':'ICAO', '6':'GHCN', '7':'NWSLI', \
'8':'RCC', '9':'ThreadEx', '10':'CoCoRaHS', '11':'Misc'}
network_icons = {'1': 'yellow-dot', '2': 'blue-dot', '3': 'green-dot','4':'purple-dot', '5': 'ltblue-dot', \
'6': 'orange-dot', '7': 'pink-dot', '8': 'yellow', '9':'green', '10':'purple', '11': 'red'}
#1YELLOW, 2BLUE, 3BROWN, 4OLIVE, 5GREEN, 6GRAY, 7TURQOIS, 8BLACK, 9TEAL, 10WHITE Multi:Red, Misc:Fuchsia
kelly_network_codes = {'1': 'COOP', '2':'GHCN', '3':'ICAO', '4':'NWSLI', '5':'FAA', '6':'WMO', '7':'WBAN', \
'8':'CoCoRaHS', '9':'RCC', '10':'Threadex', '11':'Misc'}
kelly_network_icons = {'1': 'blue-dot', '2': 'orange-dot', '3': 'ltblue-dot','4':'pink-dot', '5': 'green-dot', \
'6': 'purple-dot', '7': 'yellow-dot', '8': 'purple', '9':'yellow', '10':'green', '11': 'red'}


acis_elements = defaultdict(dict)
acis_elements ={'1':{'name':'maxt', 'name_long': 'Maximum Daily Temperature (F)', 'vX':'1'},
              '2':{'name':'mint', 'name_long': 'Minimum Daily Temperature (F)', 'vX':'2'},
              '43': {'name':'avgt', 'name_long': 'Average Daily Temperature (F)', 'vX':'43'},
              '3':{'name':'obst', 'name_long': 'Observation Time Temperature (F)', 'vX':'3'},
              '4': {'name': 'pcpn', 'name_long':'Precipitation (In)', 'vX':'4'},
              '10': {'name': 'snow', 'name_long':'Snowfall (In)', 'vX':'10'},
              '11': {'name': 'snwd', 'name_long':'Snow Depth (In)', 'vX':'11'},
              '7': {'name': 'evap', 'name_long':'Pan Evaporation (In)', 'vX':'7'},
              '45': {'name': 'dd', 'name_long':'Degree Days (Days)', 'vX':'45'},
              '44': {'name': 'cdd', 'name_long':'Cooling Degree Days (Days)', 'vX':'44'},
              '-45': {'name': 'hdd', 'name_long':'Heating Degree Days (Days)', 'vX':'45'},
              '-46': {'name': 'gdd', 'name_long':'Growing Degree Days (Days)', 'vX':'45'}}
              #bug fix needed for cdd = 44

acis_elements_dict = {
              'maxt':{'name':'maxt', 'name_long': 'Max Daily Temperature (F)', 'vX':'1'},
              'mint':{'name':'mint', 'name_long': 'Min Daily Temperature (F)', 'vX':'2'},
              'avgt': {'name':'avgt', 'name_long': 'Mean Daily Temperature (F)', 'vX':'43'},
              'dtr': {'name':'dtr', 'name_long': 'Daily Temperature Range (F)', 'vX':None},
              'obst':{'name':'obst', 'name_long': 'Observation Time Temperature (F)', 'vX':'3'},
              'pcpn': {'name': 'pcpn', 'name_long':'Precipitation (In)', 'vX':'4'},
              'snow': {'name': 'snow', 'name_long':'Snowfall (In)', 'vX':'10'},
              'snwd': {'name': 'snwd', 'name_long':'Snow Depth (In)', 'vX':'11'},
              'cdd': {'name': 'cdd', 'name_long':'Cooling Degree Days (F)', 'vX':'45'},
              'hdd': {'name': 'hdd', 'name_long':'Heating Degree Days (F)', 'vX':'45'},
              'gdd': {'name': 'gdd', 'name_long':'Growing Degree Days (F)', 'vX':'45'},
              'evap': {'name': 'evap', 'name_long':'Evaporation (In)', 'vX':'7'},
              'wdmv': {'name': 'wdmv', 'name_long':'Wind Movement (Mi)', 'vX':'12'}
              #bug fix needed for cdd = 44 (WAITING FOR BILL, ALSO IN PLACES BELOW, eg in station_locator_app, also in AcisWS.py)
}

acis_elements_list = [['maxt','Maximum Daily Temperature (F)'], ['mint','Minimum Daily Temperature (F)'],
                      ['avgt','Average Daily Temperature (F)'], ['obst', 'Observation Time Temperature (F)'], \
                      ['pcpn', 'Precipitation (In)'], ['snow', 'Snowfall (In)'], \
                      ['snwd', 'Snow Depth (In)'], ['cdd', 'Cooling Degree Days (F)'], \
                      ['hdd','Heating Degree Days (F)'], ['gdd', 'Growing Degree Days (F)']]

month_names_long = ['January', 'February', 'March', 'April', 'May', 'June',\
               'July', 'August', 'September', 'October', 'November', 'December']
month_names_short_cap = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

month_lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

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

delimiters = {
    'comma':',',
    'tab':' ',
    'colon': ':',
    'space': ' ',
    'pipe':'|'
}

###################################
#SODS
###################################
###########
#SODXTRMTS
###########
SXTR_ELEMENT_CHOICES = (
    ('pcpn', 'Precipitation'),
    ('snow', 'Snowfall'),
    ('snwd', 'Snowdepth'),
    ('maxt', 'Maximum Temperature '),
    ('mint', 'Minimum Temperature'),
    ('avgt', 'Mean Temperature'),
    ('dtr', 'Daily Temperature Range'),
    ('hdd', 'Heating Degree Days'),
    ('cdd', 'Cooling Degree Days'),
    ('gdd', 'Growing degree days'),
    ('evap', 'Evaporation'),
    ('wind', 'Wind Movement'),
)

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
    ('individual', 'Plot months separately')
)

sodxtrmts_params = {
    'station_ID':'Station Identifier',
    'start_year':'Start Year',
    'end_year':'End Year',
    'el_type':'Climate Element Type',
    'element':'Climate Element',
    'base_temperature':'Base Temperature',
    'monthly_statistic':'Monthly Statistic',
    'mmax':'Monthly Maximum',
    'mmin':'Monthly Minimum',
    'msum':'Monthly Sum',
    'mave':'Monthly Avererage',
    'sd':'Standard Deviation',
    'ndays':'Number of Days',
    'rmon':'Range during Month',
    'individual':'Plot months separately',
    'max_missing_days':'Maximum number of missing days allowed',
    'start_month':'Start Month',
    'departures_from_averages':'Departures from Averages',
    'frequency_analysis': 'Frequency Analysis',
    'T':True,
    'F':False,
    'less_greater_or_between': 'Less Than, Greater or Between?',
    'l':'Less Than',
    'g':'Greater Than',
    'b':'Between',
    'threshold_low_for_between':'Lower Threshold',
    'threshold_high_for_between':'Upper Threshold',
    'threshold_for_less_or_greater':'Threshold'
}

sodxtrmts_visualize_params = {
    'months': 'Months analized',
    'summary': 'Analysis Type',
    'max':'Maximum over months',
    'min':'Minimium over months',
    'sum':'Sum over months',
    'mean':'Avererage over months',
    'individual':'Plot months separately'
}


