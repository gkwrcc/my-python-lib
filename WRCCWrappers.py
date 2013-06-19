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

    def get_data(self):
        #(self.data, self.dates, self.elements, self.coop_station_ids, self.station_names) = \
        #AcisWS.get_sod_data(self.params, self.app_name)
        DJ = WRCCClasses.SODDataJob(self.app_name,self.params)
        self.station_ids, self.station_names = DJ.get_station_ids_names()
        data = DJ.get_data()
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
    NOTE: Runs without frequency analysis
    argv -- stn_id start_year end_year element monthly_statistic
            max_missing_days start_month departure_from_averages output_format
    Explaination:
            element choices:
                pcpn, snow, snwd, maxt, mint, avgt, dtr, hdd, cdd, gdd
            monthly_statistic choices:
                mmax --> Monthly Maximum
                mmin --> Monthly Minimum
                mave --> Monthly Avergage
                sd   --> Standard Deviation
                ndays--> Number of Days
                rmon --> Range during Month
                msum --> Monthly Sum
            start_month: 01 - 12
            departure from averages:
                T  --> True
                F  --> False
            output format choices:
                list --> python list of list
                txt_list --> output looks like Kelly's commandline output
    Example: python WRCCWrappers.py sodxtrmts 266779 2000 2012 pcpn msum 5 04 F txt_list
    '''
    #Sanity Check
    if len(argv) != 9:
        print 'Error: sodxtrmts  needs 9 input parameters: \
               stn_id start_year end_year element monthly_statistic max_missing_days \
               start_month departures_from_averages output_format.'
        sys.exit(1)

    #Assign input parameters:
    statistics_dict = {
        'mmax':'Monthly Maximum',
        'mmin':'Monthly Miniimum',
        'mave':'Monthly Average',
        'sd': 'Standard Deviation',
        'ndays':'Number of Days',
        'rmon':'Range during Month',
        'msum':'Monthly Sum'
    }
    stn_id = str(argv[0])
    start_year = str(argv[1]);end_year = str(argv[2])
    element = str(argv[3]);monthly_statistic = str(argv[4])
    max_missing_days = int(argv[5]); start_month = str(argv[6])
    departures_from_averages=str(argv[7])
    output_format = str(argv[8])
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
    SX_wrapper = Wrapper('Sodxtrmts',data_params, app_specific_params=app_params)
    #Get data
    data = SX_wrapper.get_data()
    #run app
    results, fa_results = SX_wrapper.run_app(data)
    #format resulst if needed
    if output_format =='txt_list':
        #Header
        print 'STATION NUMBER %s  ELEMENT : %s           QUANTITY :        %s' %(stn_id, WRCCData.acis_elements_dict[element]['name_long'],statistics_dict[monthly_statistic])
        print ' STATION : %s' %SX_wrapper.station_names[0]
        print ' a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,'
        print ' z = 26 or more days missing, A = Accumulations present '
        print ' Long-term means based on columns; thus, the monthly row may not '
        print '  sum (or average) to the long-term annual value.'
        print ''
        print ' MAXIMUM ALLOWABLE NUMBER OF MISSING DAYS :  %s' %max_missing_days
        print ''
        #Data
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
    else:
        print results[0]

def sodsumm_wrapper(argv):
    '''
    argv -- stn_id table_name start_year end_year max_missing_days output_format

    Explaination:
            table_name choices:
                temp, prsn, hdd, cdd, gdd, corn
            output format choices:
                list --> python list of list
                txt_list --> output looks like Kelly's commandline output
    Example: python WRCCWrappers.py sodsumm 266779 temp 2000 2012 5 txt_list
    '''
    def print_header(table_name, start_year, end_year, station_id, station_name):
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

    #Sanity Check
    if len(argv) != 6:
        print 'sodsumm needs 6 input parameters: \
               coop_station_id table_name start_year end_year max_missing_days output_format.\
               You gave: %s' %str(argv)
        sys.exit(1)
    #Assign input parameters:
    stn_id = str(argv[0]);table_name = str(argv[1])
    start_year = str(argv[2]);end_year = str(argv[3])
    max_missing_days = int(argv[4])
    output_format = str(argv[5])
    #Define parameters
    data_params = {
                'sid':stn_id,
                'start_date':start_year,
                'end_date':end_year,
                'element':'all'
                }
    app_params = {
                'el_type':table_name,
                'max_missing_days':max_missing_days,
                }
    SS_wrapper = Wrapper('Sodsumm', data_params, app_specific_params=app_params)
    #Get data
    data = SS_wrapper.get_data()
    #Run app
    results = SS_wrapper.run_app(data)
    if output_format == 'txt_list':
        print_header(table_name, start_year, end_year, SS_wrapper.station_ids[0], SS_wrapper.station_names[0])
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
    else:
        print results[0][table_name]

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
    Example: python WRCCWrappers.py soddyrec 266779 all 20000101 20101231 txt_list
    '''
    def print_header(element, start_date, end_date, station_id, station_name):
        print ' Daily Records for station %s %s' %(station_id, station_name)
        print ''
        if element in ['all', 'tmp','wtr', 'pcpn','maxt', 'mint']:
            print ' For temperature and precipitation, multi-day accumulations'
            print '   are not considered either for records or averages.'
            print ' The year given is the year of latest occurrence.'
        s = start_date[4:6] + '/' + start_date[6:8] + '/' + start_date[0:4]
        e = end_date[4:6] + '/' + end_date[6:8] + '/' + end_date[0:4]
        print ' Period requested -- Begin :  %s -- End :  %s' %(s, e)
        print 'AVG   Multi-year unsmoothed average of the indicated quantity'
        print 'HI    Highest value of indicated quantity for this day of year'
        print 'LO    Lowest  value of indicated quantity for this day of year'
        print 'YR    Latest year of occurrence of the extreme value'
        print 'NO    Number of years with data for this day of year.'
        print ''

    #Sanity Check
    if len(argv) != 5:
        print 'soddyrec needs 5 input parameters: \
               stn_id element_type start_date end_date output_format.\
               You gave: %s' %str(argv)
        sys.exit(1)
    #Assign input parameters:
    stn_id = str(argv[0]);element = str(argv[1])
    start_date = str(argv[2]);end_date = str(argv[3])
    output_format = str(argv[4])
    #Define parameters
    data_params = {
                'sid':stn_id,
                'start_date':start_date,
                'end_date':end_date,
                'element':element
                }
    SS_wrapper = Wrapper('Soddyrec', data_params)
    #Get data
    data = SS_wrapper.get_data()
    #run app
    results = SS_wrapper.run_app(data)
    if output_format == 'txt_list':
        #Headers
        print_header(element, start_date, end_date, SS_wrapper.station_ids[0], SS_wrapper.station_names[0])
        header_row = '    '
        if element == 'all':
            el_list = ['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd']
        elif element == 'tmp':
            el_list = ['maxt', 'mint', 'pcpn']
        elif element == 'wtr':
            el_list = ['pcpn', 'snow', 'snwd']
        else:
            el_list =[element]
        table_header = '      '
        table_header_2 = ' MO DY'
        for el_idx, el in enumerate(el_list):
            el_name = WRCCData.acis_elements_dict[el]['name_long']
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
    else:
        print results


#########
# M A I N
#########
if __name__ == "__main__":
    program = sys.argv[1]
    programs = ['sodsumm', 'sodxtrmts','soddyrec']
    if program not in programs:
        print 'First argument to WRCCWrappers should be valid progam name.'
        print 'Programs: ' + str(programs)
    if program == 'sodsumm':sodsumm_wrapper(sys.argv[2:])
    if program == 'sodxtrmts':sodxtrmts_wrapper(sys.argv[2:])
    if program == 'soddyrec':soddyrec_wrapper(sys.argv[2:])
