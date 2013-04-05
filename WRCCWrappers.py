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
import WRCCUtils, AcisWS, WRCCDataApps

#########
# CLASSES
#########
class Wrapper:
    def __init__(self, app_name, data_params, app_specific_params):
        self.params = data_params
        self.app_specific_params = app_specific_params
        self.app_name = app_name
        self.data = []; self.dates = []
        self.elements  = [];self.coop_station_ids = []
        self.station_names  = []

    def get_data(self):
        (self.data, self.dates, self.elements, self.coop_station_ids, self.station_names) = \
        AcisWS.get_sod_data(self.params, self.app_name)

    def run_app(self):
        app_params = {
                    'app_name':self.app_name,
                    'coop_station_ids': self.coop_station_ids,
                    'data':self.data,
                    'elements':self.elements,
                    'dates':self.dates,
                    'station_names':self.station_names
                    }
        app_params.update(self.app_specific_params)
        Application = getattr(WRCCDataApps, self.app_name)
        if self.app_name == 'Sodxtrmts':
            results, fa_results = Application(**app_params)
            return results, fa_results
        else:
            results = Application(**app_params)
            return results
        '''
        try:
            Application = getattr(WRCCDataApps, self.app_name)
            if self.app_name == 'Sodxtrmts':
                results, fa_results = Application(**app_params)
                return results, fa_results
            else:
                results = Application(**app_params)
                return results
        except:
            if self.app_name == 'Sodxtrmts':
                return [], []
            else:
                return []
        '''
################################################
#Wrapper functions for Kelly's SOD applications
################################################
def sodxtrmts_wrapper(argv):
    '''
    NOTE: Runs without frequency analysis
    argv -- coop_station_id start_year end_year element analysis_type
            max_missing_days start_month departure_from_averages
    Explaination:
            element choices: pcpn, snow, snwd, maxt, mint, avgt, dtr, hdd, cdd, gdd
            analysis_type choices:   mmax --> Monthly Maximun
                                     mmin --> Monthly Minimum
                                     mave --> Monthly Avergage
                                     sd   --> Standard Deviation
                                     ndays--> Number of Days
                                     rmon --> Range during Month
                                     msum --> Monthly Sum
            start_month:             01 - 12
            departure from averages:   T  --> True
                                       F  --> False
    Example: python WRCCWrappers.py sodxtrmts 266779 2000 2012 pcpn msum 5 04 F
    '''
    #Sanity Check
    if len(argv) != 8:
        print 'Error: sodxtrmts  needs 8 input parameters: \
               coop_station_id start_year end_year element analysis_type max_missing_days \
               start_month departures_from_averages.'
        sys.exit(1)

    #Assign input parameters:
    coop_station_id = str(argv[0])
    start_year = str(argv[1]);end_year = str(argv[2])
    element = str(argv[3]);analysis_type = str(argv[4])
    max_missing_days = int(argv[5]); start_month = str(argv[6])
    departures_from_averages=str(argv[7])
    #Define parameters
    data_params = {
                'coop_station_id':coop_station_id,
                'start_date':start_year,
                'end_date':end_year,
                'element':element
                }
    app_params = {
                'el_type':element,
                'max_missing_days':max_missing_days,
                'start_month':start_month,
                'analysis_type': analysis_type,
                'frequency_analysis': 'F',
                'departures_from_averages':departures_from_averages
                }
    SX_wrapper = Wrapper('Sodxtrmts', data_params, app_params)
    #Get data
    SX_wrapper.get_data()
    #run app
    results, fa_results = SX_wrapper.run_app()
    print results[0]

def sodsumm_wrapper(argv):
    '''
    argv -- coop_station_id table_name start_year end_year max_missing_days

    Explaination:
            table_name choices: temp, prsn, hdd, cdd, gdd, corn
    Example: python WRCCWrappers.py sodsumm 266779 temp 2000 2012 5
    '''
    #Sanity Check
    if len(argv) != 5:
        print 'sodsumm needs 5 input parameters: \
               coop_station_id table_name start_year end_year max_missing_days.\
               You gave: %s' %str(argv)
        sys.exit(1)
    #Assign input parameters:
    coop_station_id = str(argv[0]);table_name = str(argv[1])
    start_year = str(argv[2]);end_year = str(argv[3])
    max_missing_days = int(argv[3])
    #Define parameters
    data_params = {
                'coop_station_id':coop_station_id,
                'start_date':start_year,
                'end_date':end_year,
                'element':'all'
                }
    app_params = {
                'el_type':table_name,
                'max_missing_days':max_missing_days,
                }
    SS_wrapper = Wrapper('Sodsumm', data_params, app_params)
    #Get data
    SS_wrapper.get_data()
    #run app
    results = SS_wrapper.run_app()
    print results[0][table_name]


#########
# M A I N
#########
if __name__ == "__main__":
    program = sys.argv[1]
    programs = ['sodsumm', 'sodxtrmts']
    if program not in programs:
        print 'First argument to WRCCWrappers should be valid progam name.'
        print 'Programs: ' + programs
    if program == 'sodsumm':sodsumm_wrapper(sys.argv[2:])
    if program == 'sodxtrmts':sodxtrmts_wrapper(sys.argv[2:])
