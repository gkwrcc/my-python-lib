#!/usr/bin/python
'''
module WRCCWrappers.py

Contains wrapper scripts for Kelly's SOD applications.
The wrappers will be called from within the perl scripts
that interact with the WRCC webpages.
The wrapper script accepts an odered list
of input parameters.
It converts these inputs into a dictionary of key, value pairs
to be passed along to the corresponding python script
in WRCCDataAppps.
The wrapper will then format the output of the WRCCData app
to a list and pass this list pack to the perl script
'''
import sys
import WRCCUtils, AcisWS, WRCCDataApps, WRCCClasses, WRCCData

today = WRCCUtils.set_back_date(0)

#########
# CLASSES
#########
class Wrapper:
    def __init__(self, app_name, data_params, app_specific_params=None):
        self.params = data_params
        self.app_specific_params = app_specific_params
        self.app_name = app_name
        self.data = []; self.dates = []
        self.elements  = [];self.coop_station_ids = []
        self.station_names  = []
        self.station_states = []

    def get_data(self):
        #(self.data, self.dates, self.elements, self.coop_station_ids, self.station_names) = \
        #AcisWS.get_sod_data(self.params, self.app_name)
        DJ = WRCCClasses.SODDataJob(self.app_name,self.params)
        #self.station_ids, self.station_names = DJ.get_station_ids_names()
        data = DJ.get_data()
        self.station_names, self.station_states, self.station_ids, self.station_networks, self.station_lls, self.station_elevs,self.station_uids, self.station_climdivs, self.station_countys = DJ.get_station_meta()
        return data

    def run_app(self, data):
        SSApp = WRCCClasses.SODApplication(self.app_name,data,app_specific_params=self.app_specific_params)
        results = SSApp.run_app()
        return results

################################################
#Wrapper functions for Kelly's SOD applications
################################################
def sodxtrmts_wrapper(argv):
    '''
    NOTES: Runs without frequency analysis,
           ndays analysis not implemented here
    argv -- stn_id start_year end_year element monthly_statistic
            max_missing_days start_month departure_from_averages
    Explaination:
            element choices:
                pcpn, snow, snwd, maxt, mint, avgt, dtr, hdd, cdd, gdd
            monthly_statistic choices:
                mmax --> Monthly Maximum
                mmin --> Monthly Minimum
                mave --> Monthly Avergage
                sd   --> Standard Deviation
                rmon --> Range during Month
                msum --> Monthly Sum
            start_month: 01 - 12
            departure from averages:
                T  --> True
                F  --> False
    Example (web): http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodxtrmts+266779+2000+2012+avgt+mave+5+01+F
    '''
    #Sanity Check
    if len(argv) != 8:
        format_sodxtrmts_results_web([], [], {'error':'Invalid Request'}, {}, {}, '0000', '0000')
    #Assign input parameters:
    stn_id = str(argv[0])
    start_year = str(argv[1]);end_year = str(argv[2])
    #Sanity check on start/end year
    if start_year.upper() != 'POR':
        try:
            int(start_year)
            if len(start_year) != 4:
                format_sodxtrmts_results_web([], [], {'error':'Invalid Start Year: %s' %start_year}, {}, {}, '0000', '0000')
        except:
            format_sodxtrmts_results_web([], [], {'error':'Invalid Start Year: %s' %start_year}, {}, {}, '0000', '0000')
    if end_year.upper() != 'POR':
        try:
            int(end_year)
            if len(end_year) !=4:
                format_sodxtrmts_results_web([], [], {'error':'Invalid End Year: %s' %end_year}, {}, {}, '0000', '0000')
        except:
            format_sodxtrmts_results_web([], [], {'error':'Invalid End Year: %s' %endt_year}, {}, {}, '0000', '0000')
    user_start_year = str(argv[1]);user_end_year = str(argv[2])
    element = str(argv[3]);monthly_statistic = str(argv[4])
    try:
        max_missing_days = int(argv[5])
    except:
        format_sodxtrmts_results_web([], [], {'error':'Invalid Max Missing Days: %s' %argv[5] }, {}, {}, '0000', '0000')
    start_month = str(argv[6])
    if len(start_month) == 1:
        start_montrh = '0' +start_month
    departures_from_averages=str(argv[7])
    #Change POR start/end year to 8 digit start/end dates
    if start_year.upper() == 'POR' or end_year.upper() == 'POR':
        valid_daterange = por_to_valid_daterange(stn_id)
        if start_year.upper() == 'POR':
            start_year = valid_daterange[0][0:4]
        if end_year.upper() == 'POR':
            end_year = valid_daterange[1][0:4]
    #more sanity check
    if monthly_statistic not in ['mmax','mmin','mave','sd','rmon','msum']:
        format_sodxtrmts_results_web([], [], {'error':'Invalid Analysis: %s' % monthly_statistic}, {}, {}, '0000', '0000')
    if element not in ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'avgt', 'dtr', 'hdd', 'cdd', 'gdd']:
        format_sodxtrmts_results_web([], [], {'error':'Invalid Element: %s' %element }, {}, {}, '0000', '0000')
    if start_month not in ['01','02','03','04','05','06','07','08','09','10','11','12']:
        format_sodxtrmts_results_web([], [], {'error':'Invalid Start Month: %s' %start_month }, {}, {}, '0000', '0000')
    #Define parameters
    data_params = {
                'sid':stn_id,
                'start_date':start_year,
                'end_date':end_year,
                'element':element
                }
    app_params = {
                'el_type':element,
                'max_missing_days':max_missing_days,
                'start_month':start_month,
                'monthly_statistic': monthly_statistic,
                'frequency_analysis': 'F',
                'departures_from_averages':departures_from_averages
                }
    try:
        SX_wrapper = Wrapper('Sodxtrmts',data_params, app_specific_params=app_params)
        #Get data
        data = SX_wrapper.get_data()
        #run app
        results, fa_results = SX_wrapper.run_app(data)
    except:
        results = []
        fa_results = []
        data = []
    format_sodxtrmts_results_web(results, data, data_params, app_params, SX_wrapper, user_start_year, user_end_year)

def sodsum_wrapper(argv):
    '''
    argv -- stn_id start_date end_date element

    Explaination:
            element choices:
                One of:
                pcpn, snow, snwd, maxt, mint, obst, multi (all 6)
            output format choices:
                html --> html output for display on WRCC pages
    Example (web): http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodsum+266779+por+por+multi
    '''
    #Sanity Check
    if len(argv) != 4:
        format_sodsum_results_web({}, {}, {'error':'Invalid Request'},{})
    #Define parameters
    stn_id = str(argv[0])
    start_date = format_date(str(argv[1]));end_date = format_date(str(argv[2]))
    #Sanity Check on dates
    if start_date.upper() != 'POR':
        if len(start_date)!=8:
            format_sodsum_results_web({}, {}, {'error':'Invalid Start Date: %s' %start_date}, {})
        else:
            try:
                int(start_date)
            except:
                format_sodsum_results_web({}, {}, {'error':'Invalid Start Date: %s' %start_date}, {})
    if end_date.upper() != 'POR':
        if len(end_date)!=8:
            format_sodsum_results_web({}, {}, {'error':'Invalid End Date: %s' %end_date}, {})
        else:
            try:
                int(end_date)
            except:
                format_sodsum_results_web({}, {}, {'error':'Invalid End Date: %s' %end_date}, {})
    element = str(argv[3])
    #Sanity Check on element
    if element not in ['snow','snwd','maxt','mint', 'obst','pcpn','multi']:
        format_sodsum_results_web({}, {}, {'error':'Invalid Element: %s' %element}, {})
    data_params = {
                'sid':stn_id,
                'start_date':start_date,
                'end_date':end_date,
                'element':element
                }
    app_params = {}
    try:
        SS_wrapper = Wrapper('Sodsum', data_params, app_specific_params=app_params)
        #Get data
        data = SS_wrapper.get_data()
        #Run app
        results = SS_wrapper.run_app(data)
    except:
        SS_wrapper = {}
        data = {}
        results = {}
    #Format resumts
    format_sodsum_results_web(results, data, data_params,SS_wrapper)

def sodsumm_wrapper(argv):
    '''
    argv -- stn_id table_name start_year end_year max_missing_days

    Explaination:
            table_name choices:
                temp, prsn, hdd, cdd, gdd, corn
    Example (commandline): python WRCCWrappers.py sodsumm 266779 temp 2000 2012 5
    Example (web): http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodsumm+266779+temp+por+por+5
    '''
    #Sanity Check on input parameter number
    if len(argv) != 5:
        format_sodsumm_results_web([],'',{'error':'Invalid Request'}, '0000', '0000', '', '','')
    #Assign input parameters:
    stn_id = str(argv[0]);table_name = str(argv[1])
    if table_name in ['hdd','cdd']:
        tbls = 'hc'
    elif table_name == 'gdd':
        tbls = 'g'
    else:
        tbls =  table_name
    start_year = str(argv[2]);end_year = str(argv[3])
    #Sanity check on start/end year
    if start_year.upper() != 'POR':
        try:
            int(start_year)
            if len(start_year)!=4:
                format_sodsumm_results_web([],'',{'error':'Invalid Start Year: %s' %start_year }, '0000', '0000', '','','')
        except:
            format_sodsumm_results_web([],'',{'error':'Invalid Start Year: %s' %start_year }, '0000', '0000', '','','')
    if end_year.upper() != 'POR':
        try:
            int(end_year)
            if len(end_year)!=4:
                format_sodsumm_results_web([],'',{'error':'Invalid End Year: %s' %end_year }, '0000', '0000', '', '','')
        except:
            format_sodsumm_results_web([],'',{'error':'Invalid End Year: %s' %end_year }, '0000', '0000', '', '','')
    #Change POR start/end year to 8 digit start/end dates
    if start_year.upper() == 'POR' or end_year.upper() == 'POR':
        valid_daterange = por_to_valid_daterange(stn_id)
        if start_year.upper() == 'POR':
            start_year = valid_daterange[0][0:4]
        if end_year.upper() == 'POR':
            end_year = valid_daterange[1][0:4]
    try:
        max_missing_days = int(argv[4])
    except:
        format_sodsumm_results_web([],'',{'error':'Invalid Max Missing Days: %s' %argv[4] }, '0000', '0000', '', '','')
    #More Sanity checks
    if table_name not in ['temp', 'prsn', 'hdd', 'cdd', 'gdd', 'corn']:
        format_sodsumm_results_web([],'',{'error':'Invalid Table Name: %s' %table_name }, '0000', '0000','','','')
    #Define parameters
    data_params = {
                'sid':stn_id,
                'start_date':start_year,
                'end_date':end_year,
                'element':'all'
                }
    app_params = {
                'el_type':tbls,
                'max_missing_days':max_missing_days,
                }
    try:
        SS_wrapper = Wrapper('Sodsumm', data_params, app_specific_params=app_params)
        #Get data
        data = SS_wrapper.get_data()
        #Run app
        results = SS_wrapper.run_app(data)
    except:
        SS_wrapper = {
            'station_ids':[stn_id],
            'station_names':['No Data'],
            'station_states':['No State']
        }
        results = []
        data = {}
    #Format results
    if not data or ('error' in data.keys() and data['error']) or not results:
        format_sodsumm_results_web([],table_name, {'error': 'No Data found!'}, start_year, end_year, stn_id, 'No Data found for Station ID: ' + stn_id,'')
        #results = []
    else:
        format_sodsumm_results_web(results,table_name, data_params,start_year, end_year, SS_wrapper.station_ids[0], SS_wrapper.station_names[0],SS_wrapper.station_states[0])
    print_sodsumm_footer_web(app_params)


def soddyrec_wrapper(argv):
    '''
    argv -- stn_id_id element_type start_date end_date

    Explaination:
            start/end date are 8 digits long, e.g 20100102
            element_type choices:
                all  -- generates tables for  maxt, mint, pcpn, snow, snwd, hdd, cdd,
                tmp  -- generates tables for maxt, mint, pcpn,
                wtr  -- generates tables for pcpn, snow, snwd,
                pcpn -- generates tables for Precipitation,
                snow -- generates tables for Sowfall,
                snwd -- generates tables for Snowdepth,
                maxt -- generates tables for Maximum Temperature,
                mint -- generates tables for Minimum Temperature,
                hdd  -- generates tables for Heating Degree Days,
                cdd  -- generates tables for Cooling Degree Days
            output format choices:
                list     --> python list of list
                txt_list --> output looks like Kelly's commandline output
    Example(command line): python WRCCWrappers.py soddyrec 266779 all 20000101 20101231
    Example (web): http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?soddyrec+266779+all+20000101+20101231
    '''
    #Sanity Check
    if len(argv) != 4:
        format_soddyrec_results_web([],{'error':'Invalid Request'},{})
    #Assign input parameters:
    stn_id = str(argv[0]);element = str(argv[1])
    start_date = format_date(str(argv[2]));end_date = format_date(str(argv[3]))
    #Sanity checks
    #Change POR start/end year to 8 digit start/end dates
    if start_date.upper() == 'POR' or end_date.upper() == 'POR':
        valid_daterange = por_to_valid_daterange(stn_id)
        if start_date.upper() == 'POR':
            start_date = valid_daterange[0]
        if end_date.upper() == 'POR':
            end_date = valid_daterange[1]
    if element not in ['all','tmp','wtr','pcpn','snow','snwd','maxt','mint','hdd','cdd']:
        format_soddyrec_results_web([],{'error':'Invalid element: %s' %element},{})
    if len(start_date) != 8:
        format_soddyrec_results_web([],{'error':'Invalid start_date: %s' %start_date},{})
    if len(end_date) != 8:
        format_soddyrec_results_web([],{'error':'Invalid end_date: %s' %end_date},{})

    #Define parameters
    data_params = {
                'sid':stn_id,
                'start_date':start_date,
                'end_date':end_date,
                'element':element
                }
    SR_wrapper = Wrapper('Soddyrec', data_params)
    #Get data
    data = SR_wrapper.get_data()
    #run app
    results = SR_wrapper.run_app(data)
    format_soddyrec_results_web(results,data_params,SR_wrapper)
########
#Utils
#######
def format_soddyrec_results_web(results, data_params, wrapper):
    '''
    Generates Soddyrec web content
    '''
    print_html_header()
    if 'error' in data_params.keys() or not wrapper or not results:
        print '<BODY BGCOLOR="#FFFFFF"><CENTER>'
        if 'error' in data_params.keys():
            print '<H1><FONT COLOR="RED">' + data_params['error'] + '</FONT></H1>'
        else:
            print '<H1>No data found!</H1>'
        print '</BODY>'
        print '</HTML>'

    else:
        print '<TITLE>' +  wrapper.station_names[0] + ', ' + wrapper.station_states[0] + ' Period of Record Daily Climate Summary </TITLE>'
        print '<BODY BGCOLOR="#FFFFFF">'
        print '<H1>' +  wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '</H1>'
        print '<H3>Period of Record Daily Climate Summary </H3>'
        print '<PRE>'
        format_soddyrec_results_txt(results, wrapper,data_params)
        print '</PRE>'
        print '<HR>'
        print '<address>Western Regional Climate Center, <A HREF="mailto:wrcc@dri.edu">wrcc@dri.edu </A> </address>'
        print '</BODY>'
        print '</HTML>'

def format_soddyrec_results_txt(results, wrapper,data_params):
    '''
    Generates soddyrec text output that matches Kelly's commandline output
    '''
    print ' Daily Records for station %s %s           state: %s' %(data_params['sid'], wrapper.station_names[0], wrapper.station_states[0])
    print ''
    if data_params['element'] in ['all', 'tmp','wtr', 'pcpn','maxt', 'mint']:
        print ' For temperature and precipitation, multi-day accumulations'
        print ' are not considered either for records or averages.'
        print ' The year given is the year of latest occurrence.'
    s = data_params['start_date'][4:6] + '/' + data_params['start_date'][6:8] + '/' + data_params['start_date'][0:4]
    e = data_params['end_date'][4:6] + '/' + data_params['end_date'][6:8] + '/' + data_params['end_date'][0:4]
    print ' Period requested -- Begin :  %s -- End :  %s' %(s, e)
    print ''
    print 'Cooling degree threshold =   65.00  Heating degree threshold =   65.00'
    print ''
    print 'AVG   Multi-year unsmoothed average of the indicated quantity'
    print 'HI    Highest value of indicated quantity for this day of year'
    print 'LO    Lowest  value of indicated quantity for this day of year'
    print 'YR    Latest year of occurrence of the extreme value'
    print 'NO    Number of years with data for this day of year.'
    print ''
    header_row = '    '
    if data_params['element'] == 'all':
        el_list = ['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd']
    elif data_params['element'] == 'tmp':
        el_list = ['maxt', 'mint', 'pcpn']
    elif data_params['element'] == 'wtr':
        el_list = ['pcpn', 'snow', 'snwd']
    else:
        el_list =[data_params['element']]
    table_header = '      '
    table_header_2 = ' MO DY'
    for el_idx, el in enumerate(el_list):
        el_name = WRCCData.ACIS_ELEMENTS_DICT[el]['name_long']
        start ='|';end=''
        if len(el_name)<=27:
            left = 27 - len(el_name)
            if left%2 == 0:
                for k in range(left/2):
                    start+='-';end+='-'

            else:
                for k in range((left-1)/2):
                    start+='-';end+='-'
                end+='-'
        table_header+=start
        table_header+=el_name
        table_header+=end
        table_header_2+='    AVG     NO   HIGH     YR'
    print table_header
    print table_header_2
    #Data
    for doy in range(366):
        row =''
        mon,day = WRCCUtils.compute_mon_day(doy+1)
        row+='%3s%3s' %(mon, day)
        for el_idx, el in enumerate(el_list):
            for k in range(2,6):
                row+='%7s' %results[0][el_idx][doy][k]
        print row

def format_sodumm_results_txt(table_name, results, start_year, end_year, station_id, station_name, station_state):
    '''
    Generates sodsumm text output that matches Kelly's commandline output
    '''
    if table_name == 'temp':
        print 'Station:(%s) %s ' %(station_id, station_name)
        print 'From Year=%s To Year=%s                                   #Day-Max #Day-Min' %(str(start_year), str(end_year))
        print '       Averages         Daily Extremes         Mean Extremes   >=   =<   =<  =<'
        print '-------------------------------------------------------------------------------'
    elif table_name == 'prsn':
        print 'Station:(%s) %s         From Year=%s To Year=%s' %(station_id, station_name,str(start_year), str(end_year))
        print 'Missing data not yet determined'
        print '       Total Precipitation       Precipitation  Total Snowfall  #Days Precip >='
        print '-------------------------------------------------------------------------------'
    elif table_name == 'hdd':
        print ' For degree day calculations:'
        print ' Output is rounded, unlike NCDC values, which round input.'
        print ''
        print 'Station:(%s) %s         Missing data not yet determined' %(station_id, station_name)
        print ''
        print '                Degree Days to Selected Base Temperatures (F)'
        print '                          Heating Degree Days'
    elif table_name == 'cdd':
        print ' For degree day calculations:'
        print ' Output is rounded, unlike NCDC values, which round input.'
        print ''
        print 'Station:(%s) %s         Missing data not yet determined' %(station_id, station_name)
        print ''
        print '                Degree Days to Selected Base Temperatures (F)'
        print '                          Cooling Degree Days'
    elif table_name == 'gdd':
        print ' For degree day calculations:'
        print ' Output is rounded, unlike NCDC values, which round input.'
        print ''
        print 'Station:(%s) %s         Missing data not yet determined' %(station_id, station_name)
        print ''
        print '                Degree Days to Selected Base Temperatures (F)'
        print '                          Growing Degree Days'
    elif table_name == 'corn':
        print '                    Corn Growing Degree Days'
    if results and results[0]:
        for mon_idx, mon_vals in enumerate(results[0][table_name]):
            if table_name in ['temp', 'prsn'] and mon_idx == len(results[0][table_name])-5:
                print ''
            row = ''
            row_end = ''
            for v_idx, val in enumerate(mon_vals):
                if v_idx in [5,7] and table_name == 'temp':
                    row+='%9s' %str(val)
                elif v_idx in [6,7] and table_name == 'prsn':
                    row+='%8s' %str(val)
                elif v_idx in [8,9,10,11] and table_name == 'prsn':
                    row_end+='%6s' %str(val)
                else:
                    row+='%6s' %str(val)
            print row + row_end

def format_sodsumm_results_web(results, table_name, data_params, start_year, end_year, station_id, station_name, station_state):
    print_html_header()
    if 'error' in data_params.keys():
        print '<BODY BGCOLOR="#FFFFFF"><CENTER>'
        print '<H1><FONT COLOR="RED">' + data_params['error'] + '</FONT></H1>'
        print '</BODY>'
        print '</HTML>'
    else:
        print '<TITLE> ' + station_name + ', ' + station_id + ' Period of Record General Climate Summary - ' + WRCCData.SODSUMM_TABLE_NAMES[table_name] + '</TITLE>'
        print '<BODY BGCOLOR="#FFFFFF"><CENTER>'
        print '<H1> ' + station_name + ', ' + station_state + ' </H1>'
        print '<H3>Period of Record General Climate Summary - ' + WRCCData.SODSUMM_TABLE_NAMES[table_name] + '</H3>'
        print '<TABLE BORDER>'
        print '<TR>'
        print '<TH COLSPAN=16> Station:(' + station_id + ') ' + station_name + '</TH>'
        print '</TR>'
        print '<TR>'
        print '<TD COLSPAN=16 ALIGN=CENTER> From Year=' + start_year + ' To Year=' + end_year + '</TD>'
        print '</TR>'
        print '<TR ALIGN=CENTER>'
        if table_name == 'temp':
            print '<TD></TD>'
            print '<TD COLSPAN=3> Monthly Averages </TD>'
            print '<TD COLSPAN=4> Daily Extremes </TD>'
            print '<TD COLSPAN=4> Monthly Extremes </TD>'
            print '<TD COLSPAN=2> Max. Temp.</TD>'
            print '<TD COLSPAN=2> Min. Temp.</TD>'
            print '</TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD>Max.</TD>'
            print '<TD>Min.</TD>'
            print '<TD>Mean</TD>'
            print '<TD>High</TD>'
            print '<TD>Date</TD>'
            print '<TD>Low</TD>'
            print '<TD>Date</TD>'
            print '<TD>Highest<BR> Mean</TD>'
            print '<TD>Year</TD>'
            print '<TD>Lowest<BR> Mean</TD>'
            print '<TD>Year</TD>'
            print '<TD>>= <BR> 90 F</TD>'
            print '<TD><= <BR> 32 F</TD>'
            print '<TD><= <BR> 32 F</TD>'
            print '<TD><= <BR> 0 F</TD>'
            print '<TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD> F  </TD>'
            print '<TD> F  </TD>'
            print '<TD> F  </TD>'
            print '<TD> F  </TD>'
            print '<TD>dd/yyyy<BR>or<BR>yyyymmdd</TD>'
            print '<TD> F </TD>'
            print '<TD>dd/yyyy<BR>or<BR>yyyymmdd</TD>'
            print '<TD> F  </TD>'
            print '<TD> -  </TD>'
            print '<TD> F </TD>'
            print '<TD> -  </TD>'
            print '<TD># Days</TD>'
            print '<TD># Days</TD>'
            print '<TD># Days</TD>'
            print '<TD># Days</TD>'
            print '</TR>'
        elif table_name == 'prsn':
            print '<TD></TD>'
            print '<TD COLSPAN=11> Precipitation </TD>'
            print '<TD COLSPAN=3> Total Snowfall </TD>'
            print '</TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD>Mean</TD>'
            print '<TD>High</TD>'
            print '<TD>Year</TD>'
            print '<TD>Low</TD>'
            print '<TD>Year</TD>'
            print '<TD COLSPAN=2> 1 Day Max.</TD>'
            print '<TD> >= <BR> 0.01 in.</TD>'
            print '<TD> >= <BR> 0.10 in.</TD>'
            print '<TD> >= <BR> 0.50 in.</TD>'
            print '<TD> >= <BR> 1.00 in.</TD>'
            print '<TD>Mean</TD>'
            print '<TD>High</TD>'
            print '<TD>Year</TD>'
            print '<TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD> in.</TD>'
            print '<TD> in.</TD>'
            print '<TD> -  </TD>'
            print '<TD> in.</TD>'
            print '<TD> - </TD>'
            print '<TD> in.</TD>'
            print '<TD>dd/yyyy<BR>or<BR>yyyymmdd</TD>'
            print '<TD> # Days</TD>'
            print '<TD> # Days</TD>'
            print '<TD> # Days</TD>'
            print '<TD> # Days</TD>'
            print '<TD> in. </TD>'
            print '<TD> in. </TD>'
            print '<TD> - </TD>'
            print '</TR>'
        elif table_name in  ['hdd','cdd','gdd']:
            if table_name == 'hdd':
                print '<TD COLSPAN=14> Heating Degree Days for Selected Base Temperature (F)</TD>'
            elif table_name == 'cdd':
                print '<TD COLSPAN=14> Cooling Degree Days for Selected Base Temperature (F)</TD>'
            elif table_name == 'gdd':
                print '<TD COLSPAN=14> Growing Degree Days for Selected Base Temperature (F)</TD>'
            print '</TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD>Base</TD>'
            if table_name == 'gdd':
                print '<TD>M/S</TD>'
            print '<TD>Jan.</TD>'
            print '<TD>Feb.</TD>'
            print '<TD>Mar.</TD>'
            print '<TD>Apr.</TD>'
            print '<TD>May </TD>'
            print '<TD>Jun.</TD>'
            print '<TD>Jul.</TD>'
            print '<TD>Aug.</TD>'
            print '<TD>Sep.</TD>'
            print '<TD>Oct.</TD>'
            print '<TD>Nov.</TD>'
            print '<TD>Dec.</TD>'
            print '<TD>Annual</TD>'
            print '</TR>'
        else:
            pass
        if results and results[0]:
            for mon_idx, mon_vals in enumerate(results[0][table_name][1:]):
                print '<TR ALIGN=RIGHT>'
                for v_idx, val in enumerate(mon_vals):
                    print '<TD>' + str(val) + '</TD>'
                print '</TR>'
        print '</TABLE>'

def print_sodsumm_footer_web(app_params):
    '''
    Sodsumm footer web content
    '''
    print 'Table updated on ' + today + '<BR>'
    print 'For monthly and annual means, thresholds, and sums:'
    print '<BR>'
    print 'Months with ' + str(app_params['max_missing_days']) + ' or more missing   days are not considered'
    print '<BR>'
    print 'Years  with 1 or more missing months are not considered'
    print '<BR>'
    print 'Seasons are climatological not calendar seasons<BR>'
    print '<TABLE> <TR>'
    print '<TD>Winter = Dec., Jan., and Feb. </TD><TD> </TD><TD>  Spring = Mar., Apr., and May</TD>'
    print '</TR><TR>'
    print '<TD>Summer = Jun., Jul., and Aug. </TD><TD> </TD><TD>  Fall = Sep., Oct., and Nov.</TD>'
    print '</TR> </TABLE>'
    print '<PRE>'
    print '</PRE>'
    print '</CENTER>'
    print '<HR>'
    print '<address>Western Regional Climate Center, <A HREF="mailto:wrcc@dri.edu">wrcc@dri.edu </A> </address>'

def format_sodxtrmts_results_txt(results, data, data_params, app_params, wrapper, user_start_year, user_end_year):
    '''
    Generates sodxtrmts text output that matches Kelly's commandline output
    '''
    #Header
    print 'STATION NUMBER %s  ELEMENT : %s           QUANTITY :        %s' %(data_params['sid'], WRCCData.ACIS_ELEMENTS_DICT[element]['name_long'],WRCCData.SXTR_ANALYSIS_CHOICES[app_params['monthly_statistic']])
    try:
        print ' STATION : %s' %wrapper.station_names[0]
    except:
        print ' STATION : No station name found'
    print ' a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,'
    print ' z = 26 or more days missing, A = Accumulations present '
    print ' Long-term means based on columns; thus, the monthly row may not '
    print '  sum (or average) to the long-term annual value.'
    print ''
    print ' MAXIMUM ALLOWABLE NUMBER OF MISSING DAYS :  %s' %app_params['max_missing_days']
    print ''
    #Data
    if not results:
        print 'NO DATA FOUND!'
    elif not results[0]:
        print 'NO DATA FOUND!'
    else:
        for yr_idx,yr_data in enumerate(results[0]):
            if yr_idx == len(results[0]) - 6:
                print ''
            row = ''
            for idx,val in enumerate(yr_data):
                if str(val) == '-9999.00':
                    v = '-9999'
                elif  str(val) == '9999.00':
                    v = '9999'
                else:
                    v = val
                if idx == 0:
                    row+='%7s ' %str(v)
                elif idx != 0 and idx%2 ==0:
                    row+='%s' %str(v)
                else:
                    row+='%6s' %str(v)
            print row

def format_sodxtrmts_results_web(results, data, data_params, app_params, wrapper, user_start_year, user_end_year):
    '''
    Generates Sodxtrmts web content
    '''
    if 'error' in data_params.keys():
        print_html_header()
        print '<HEAD><TITLE><FONT COLOR="RED">' + data_params['error'] + '</FONT></TITLE></HEAD>'
        print '<BODY BGCOLOR="#FFFFFF">'
        print '<CENTER>'
        print '<H1><FONT COLOR="RED">' + data_params['error'] + '</FONT></H1>'
        print '</CENTER>'
        print '<PRE>'
        print '</PRE>'
        print '</BODY>'
        print '</HTML>'
    else:
        print_html_header()
        print '<HEAD><TITLE>' + WRCCData.SXTR_ANALYSIS_CHOICES_DICT[app_params['monthly_statistic']] + ' of ' + \
        WRCCData.DISPLAY_PARAMS[data_params['element']] +', Station id: ' + data_params['sid'] +'</TITLE></HEAD>'
        print '<BODY BGCOLOR="#FFFFFF">'
        print '<CENTER>'
        if  wrapper.station_names and wrapper.station_states:
            print '<H1>' + wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '</H1>'
        else:
            print '<H1> No Station Name</H1>'
        print '<H2>' + WRCCData.SXTR_ANALYSIS_CHOICES_DICT[app_params['monthly_statistic']] +  ' of '+ WRCCData.DISPLAY_PARAMS[data_params['element']] + ' ('+ WRCCData.UNITS_LONG[WRCCData.UNITS_ENGLISH[data_params['element']]] +') </H2>'
        print '<H3> (<B>' + data_params['sid'] + '</B>) </H3>'
        if not data or not results or not results[0]:
            print '<H1>No Data found!</H1>'
            print '<H3>Start Year: ' + user_start_year + ', End Year:' + user_end_year +'</H3>'
            print '</CENTER>'
            print '<PRE>'
            print '</PRE>'
            print '</BODY>'
            print '</HTML>'
        else:
            print '</CENTER>'
            print '<CENTER>'
            print '<CAPTION ALIGN=LEFT><CENTER>'
            print 'File last updated on '+ WRCCData.NUMBER_TO_MONTH_NAME[today[4:6]] + ' ' + today[6:8] + ', ' + today[0:4]
            print '<BR>'
            print 'a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,'
            print '<BR>'
            print 'z = 26 or more days missing, A = Accumulations present'
            print '<BR>'
            print 'Long-term means based on columns; thus, the monthly row may not'
            print '<BR>'
            print 'sum (or average) to the long-term annual value.'
            print '<BR>'
            print 'MAXIMUM ALLOWABLE NUMBER OF MISSING DAYS : ' +  str(app_params['max_missing_days'])
            print '<BR>'
            print 'Individual Months not used for annual or monthly statistics if more than 5 days are missing. <BR>'
            print 'Individual Years not used for annual statistics if any month in that year has more than 5 days missing.</CENTER>'
            print '<BR>'
            if not data or not results or not results[0]:
                print 'NO DATA FOUND!'
                print '</CENTER>'
                print '<PRE></PRE>'
            else:
                print '<TABLE BORDER=0 CELLSPACING=2 CELLPADDING=0>'
                header = '<TR><TD>YEAR(S)</TD>'
                s_month = int(app_params['start_month'])
                month_names_list = []
                for mon in range(s_month,13):
                    month_names_list.append(WRCCData.NUMBER_TO_MONTH_NAME[str(mon)].upper())
                if s_month!=1:
                    for mon in range(1,s_month):
                        month_names_list.append(WRCCData.NUMBER_TO_MONTH_NAME[str(mon)].upper())
                for mon in month_names_list:
                    header+='<TD ALIGN=CENTER COLSPAN=2>' + mon + '</TD>'
                header+='<TD ALIGN=CENTER COLSPAN=2>ANN</TD></TR>'
                print header
                for yr_idx,yr_data in enumerate(results[0]):
                    if yr_idx == len(results[0]) - 6:
                        print '<TR> <TD ALIGN=CENTER COLSPAN=26> Period of Record Statistics  </TD> </TR>'
                    row = '<TR>'
                    for idx,val in enumerate(yr_data):
                        if str(val) == '-9999.00':
                            v = '-9999'
                        elif  str(val) == '9999.00':
                            v = '9999'
                        else:
                            v = val
                        if idx == 0:
                            row+='<TD ALIGN=CENTER WIDTH=8%>'
                        elif idx % 2 == 0:
                            row+='<TD ALIGN=LEFT WIDTH=1%>'
                        else:
                            row+='<TD ALIGN=RIGHT WIDTH=6%>'

                        row+=v + '</TD>'
                    row+='</TR>'
                    print row
                print '</TABLE>'
                print '</CENTER>'
                print '<PRE>'
                print '</PRE>'
                print '</BODY>'
                print '</HTML>'

def format_sodsum_results_web(results, data, data_params,wrapper):
    '''
    Generates sodsum text output that matches Kelly's commandline output
    '''
    print_html_header()
    print '<TITLE>  POR - Station Metadata </TITLE>'
    print '<BODY BGCOLOR="#FFFFFF">'
    print '<CENTER>'
    if 'error' in data_params.keys():
        print '<H1><FONT COLOR="RED">' + data_params['error'] + '</FONT></H1>'
        print '</CENTER>'
        print '</BODY>'
        print '</HTML>'
    else:
        if not results or not data or not wrapper:
            print '<H2>   Station Metadata </H2>'
            print '<H2>No Data found!</H2>'
        else:
            print '<H1>  '+ wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '</H1>'
            print '<H2>   Station Metadata </H2>'
            print '<BR>'
            print '<TABLE>'
            print '<TR><TH>Count</TH><TH> Number</TH><TH>   Station Name   </TH><TH>Lat</TH><TH> Long</TH><TH>  Elev</TH><TH>  Start</TH><TH COLSPAN=6> ObsTyp</TH><TH>  End</TH></TR>'
            print '<TR><TD> </TD><TD> (Coop) </TD><TD>  (From ACIS listing) </TD><TD>    ddmm</TD><TD> dddmm</TD><TD> ft</TD><TD> yy mm</TD><TD> t</TD><TD>p</TD><TD>w</TD><TD>s</TD><TD>e</TD><TD>h</TD><TD> yy mm</TD></TR>'
            print '<TR><TD>=====</TD><TD> ======</TD><TD>   =======================</TD><TD> ====</TD><TD> =====</TD><TD> ====</TD><TD>  =====</TD><TD> =</TD><TD>=</TD><TD>=</TD><TD>=</TD><TD>=</TD><TD>=</TD><TD> =====</TD></TR>'
            print '<TR><TD>' + wrapper.station_countys[0] + '</TD><TD>' + wrapper.station_ids[0] + '</TD><TD>' + wrapper.station_names[0] + '</TD><TD>' + str(int(100*round(float(wrapper.station_lls[0].rstrip(']').split(',')[1]),2))) + '</TD><TD>' + str(int(100*round(float(wrapper.station_lls[0].lstrip('[').split(',')[0][1:]),2))) + '</TD><TD>' + str(int(round(float(wrapper.station_elevs[0])))) + '</TD><TD>' + '99 01' + '</TD><TD>U</TD><TD>U</TD><TD>  </TD><TD>  </TD><TD>  </TD><TD> U</TD><TD> 99 99</TD></TR>'
            print '</TABLE></CENTER>'
            print '<HR>'
            print '<CENTER>'
            print '<H1> Statistics by element </H1>'
            print '(From ACIS data archives)<BR>'
            print 'Last updated ' + today
            print '. Dates are format of YYYYMMDD. Numbers are total Number of observations<BR>'
            print '<TABLE>'
            el_header = '<TR><TH>STATION </TH><TH>START </TH><TH> END </TH>'
            h_lines = '<TR><TH>======= </TH><TH>======== </TH><TH> ======== </TH>'
            el_data = '<TR><TD>' + wrapper.station_ids[0] + '</TD><TD>' + results[0]['start'] + '</TD><TD>' + results[0]['end'] + '</TD>'
            for el in data['elements']:
                el_header+= '<TH>' + el.upper() + '</TH>'
                h_lines+='<TH> ===== </TH>'
                el_data+='<TD>' + str(results[0][el]) + '</TD>'
            el_header+='</TR>'
            h_lines+='</TR>'
            el_data+='</TR>'
            print el_header
            print h_lines
            print el_data
            print '</TABLE><BR>'
            print '</CENTER><BR>'
            print ' STATION - ACIS COOP Station number<BR>'
            print 'START - First Date in record<BR>'
            print 'END - Last Date in record (when last compiled)<BR>'
            print 'PCPN - Precipitation<BR>'
            print 'SNOW - Snowfall<BR>'
            print 'SNWD - Snow depth<BR>'
            print 'MAXT - Daily Max. Temperature<BR>'
            print 'MINT - Daily Min. Temperature<BR>'
            print 'TOBS - Temperature at Observation time<BR>'
            print 'EVAP - Evaporation<BR>'
            print 'WDMV - Wind Movement<BR>'
            print '<HR>'
            print '<CENTER>'
            print '<H1> Statistics by observation </H1>'
            print '(From ACIS data archives) <BR>'
            print 'Last updated ' + today
            print '. Dates are format of YYYYMMDD. Numbers are total Number of observations<BR>'
            print '<TABLE>'
            print '<TR><TH> STATION </TH>'
            print '<TH> NAME </TH>'
            print '<TH> START </TH>'
            print '<TH> END </TH>'
            print '<TH> POSBL </TH>'
            print '<TH> PRSNT </TH>'
            print '<TH> LNGPR </TH>'
            print '<TH> MISSG </TH>'
            print '<TH> LNGMS </TH></TR>'
            print '<TR><TD> ====== </TD><TD> ======================== </TD><TD> ======== </TD><TD> ======== </TD><TD> ===== </TD><TD> ===== </TD><TD> ===== </TD><TD> ===== </TD><TD> ===== </TD></TD>'
            data = '<TR><TD>' + wrapper.station_ids[0] + '</TD><TD>'+ wrapper.station_names[0] + '</TD><TD>' + results[0]['start'] + '</TD><TD>' + results[0]['end'] + '</TD>'
            for key in ['PSBL', 'PRSNT','LNGPR','MISSG','LNGMS']:
                data+='<TD>' + str(results[0][key]) + '</TD>'
            data+='</TR>'
            print data
            print '</TABLE>'
            print '<BR>'
            print '</CENTER>'
            print 'STATION - NCDC COOP Station number<BR>'
            print 'NAME - Most recent name in NCDC history file<BR>'
            print 'START - First Date in record<BR>'
            print 'END - Last Date in record (when last compiled)<BR>'
            print 'POSBL - Possible number of observations between START and END date<BR>'
            print 'PRSNT - Number of days present in record<BR>'
            print 'LNGPR - Largest number of consecutive observations<BR>'
            print 'MISSG - Total number of missing days (no observation)<BR>'
            print 'LNGMS - Largest number of consecutive missing observations<BR>'
            print '<BR>'

def print_html_header():
    print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml" lang="en-US">'
    print 'Content-type: text/html \r\n\r\n'
    print '<HTML>'

def por_to_valid_daterange(stn_id):
    valid_daterange = WRCCUtils.find_valid_daterange(stn_id)
    if not valid_daterange or valid_daterange == ['','']:
        valid_daterange = ['00000000','00000000']
    return valid_daterange

def format_date(date):
    d = date.replace('-','').replace(':','').replace('/','').replace(' ','')
    return d

#########
# M A I N
#########
if __name__ == "__main__":
    program = sys.argv[1]
    programs = ['sodsumm', 'sodxtrmts','soddyrec', 'sodsum']
    if program not in programs:
        print 'First argument to WRCCWrappers should be valid progam name.'
        print 'Programs: ' + str(programs)
    #execute wrapper
    globals()[program + '_wrapper'](sys.argv[2:])
