#!/usr/bin/python

'''
Module WRCCDataApps
'''
from collections import defaultdict
import WRCCUtils, AcisWS, WRCCData
import numpy
import sys, os, datetime
import fileinput
from scipy import stats
from math import ceil
import sets
#from django.conf import settings
#import my_acis.settings as settings
#LIB_PREFIX = settings.LIB_PREFIX

LIB_PREFIX = "/www/apps/csc/my-python-lib/"

#############################
#CSC DATA PORTAL APPLICATIONS
#############################

def state_aves_stn(state, month, elements):
    '''
    Routine computes monthly averages of stn data in a state
    for a given month over date range (default 1900 - present)
    element, start end date and state are chosen by user
    '''
    mon = int(month)
    if mon not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        print "Not a valid month: %s. Enter a number 1-12" % str(mon)
        sys.exit(0)

    mon_lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    today = datetime.date.today()
    year = today.year
    start_year = 1900
    year_list = []
    if len(str(mon)) == 1:
        mon = '0%s' % mon
    if WRCCUtils.is_leap_year(year) and mon == 2:
        start_date = "%s%s%s" %(str(start_year), str(mon), str(29))
        end_date = "%s%s%s" % (str(year), str(mon), str(29))
    else:
        end_date = "%s%s%s" % (str(year), str(mon), str(mon_lens[int(mon) - 1]))
        start_date = "%s%s%s" %(str(start_year), str(mon), str(mon_lens[int(mon) - 1]))

    dur = mon_lens[int(mon) - 1]
    el_list = [{"name":el, "interval":[1,0,0],"duration":dur,"reduce":"mean","smry":"mean"} for el in elements]
    params = {"state":state,"sdate":start_date,"edate":end_date, "elems":el_list}
    request = AcisWS.MultiStnData(params)

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

def state_aves_grid(state, month, elements):
    '''
    Routine computes monthly averages of Acis gridded data in a state
    for a given month over date range (default 1900 - present)
    element, start end date and state are chosen by user
    '''
    state_aves = defaultdict(dict)
    mon = int(month)
    if mon not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        print "Not a valid month: %s. Enter a number 1-12" % str(mon)
        sys.exit(0)

    mon_lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    today = datetime.date.today()
    year = today.year - 1
    start_year = 1950
    year_list = []
    if len(str(mon)) == 1:
        mon = '0%s' % mon
    if WRCCUtils.is_leap_year(year) and mon == 2:
        start_date = "%s%s%s" %(str(start_year), str(mon), str(29))
        end_date = "%s%s%s" % (str(year), str(mon), str(29))
    else:
        end_date = "%s%s%s" % (str(year), str(mon), str(mon_lens[int(mon) - 1]))
        start_date = "%s%s%s" %(str(start_year), str(mon), str(mon_lens[int(mon) - 1]))

    dur = mon_lens[int(mon) - 1]
    el_list = [{"name":el, "interval":[1,0,0],"duration":dur,"reduce":"mean","smry":"mean"} for el in elements]
    params = {"state":state,"sdate":start_date,"edate":end_date, "meta":"elev,ll", "elems":el_list, "grid":"1"}
    request = AcisWS.GridData(params)
    if not request:
        request = {'error':'bad request, check params: %s'  % str(params)}

    try:
        for k, el in enumerate(elements):
            state_aves[k] = {'element': el, 'state_ave': [999.0 for yr in range(len(request['data']))], \
            'moving_ave': [999.0 for yr in range(len(request['data']))]}
    except:
        state_aves = {}

    if 'error' in request:
        year_list = []
        state_aves = {'error': request['error']}
    else:
        for yr in range(len(request['data'])):
            year_list.append("%s" % str(start_year + yr))
            for k,el in enumerate(elements):
                ave_list = []
                for grid_idx, lat_grid in enumerate(request['meta']['lat']):
                    for lat_idx, lat in enumerate(lat_grid):
                        #Averages
                        try:
                            float(request['data'][yr][k+1][grid_idx][lat_idx])
                        except:
                            continue

                        if abs(float(request['data'][yr][k+1][grid_idx][lat_idx]) + 999.0) < 0.01:
                            continue
                        elif abs(float(request['data'][yr][k+1][grid_idx][lat_idx]) - 999.0) < 0.01:
                            continue
                        else:
                            ave_list.append(float(request['data'][yr][k+1][grid_idx][lat_idx]))
                if ave_list:
                    state_aves[k]['state_ave'][yr] = numpy.mean(ave_list)
                #9yr Moving Averages
                mov_ave_list = []
                if yr >= 4 and yr <= len(request['data']) - 5:
                    for l in range(yr - 4, yr + 5):
                        if abs(state_aves[k]['state_ave'][l] - 999.0) > 0.01:
                            mov_ave_list.append(state_aves[k]['state_ave'][l])
                else:
                    mov_ave_list.append(state_aves[k]['state_ave'][yr])
                if mov_ave_list:
                    state_aves[k]['moving_ave'][yr] = numpy.mean(mov_ave_list)
    return year_list, state_aves


def monthly_aves(request, el_list):
    '''
    CSC hsitoric station data app
    computes monthly aves over multiple years for multiple elements chosen by user

    Keyword arguments:
    request  -- data request object containing data
    el_list  -- List of climate elements
    '''
    #request['data'] = [[year1, [el1(366entries)], [el2(366entries)], ...],
    #                   [year2, [el1(366entries)], [el2(366entries)], ...],...
    #                   [lastyear, [el1(366entries)], [el2(366entries)], ...]]
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    results = defaultdict(list)
    #Loop over elements
    for el in el_list:
        results[el] = []

    #Loop over months and compute monthly stats
    for mon_idx, mon in enumerate(months):
        #Find indices for each time category
        if mon_idx == 0:
            idx_start = 0
            idx_end = 31
        else:
            idx_start = sum(mon_lens[idx] for idx in range(mon_idx))
            idx_end = idx_start + mon_lens[mon_idx]
        #Loop over years and elements
        for el_idx, el in enumerate(el_list):
            yr_aves = []
            for yr in range(len(request['data'])):
                data = request['data'][yr][el_idx+1][idx_start:idx_end]
                #Sanity check for missing data
                if len(sets.Set(data)) == 1 and str(data[0]) == 'M':
                #if all(str(val) == 'M' for val in data):
                    continue
                #deal with flags
                new_data = ['M' for k in range(len(data))]
                s_count = 0
                for idx, dat in enumerate(data):
                    val, flag = WRCCUtils.strip_data(str(dat))
                    if flag == 'M':
                        pass
                    elif flag == 'S':
                        new_data[idx] = 0.00
                        s_count+=1
                    elif flag == 'A':
                        s_count+=1
                        new_val = float(val) / s_count
                        for k in range (idx,idx-s_count,-1):
                            new_data[k] = new_val
                        s_count = 0

                    elif flag == 'T':
                        new_data[idx] = 0.0
                    else:
                        try:
                            new_data[idx] = float(val)
                        except:
                            pass

                #Sanity check for missing data
                #if all(str(val) == 'M' for val in new_data):
                if len(sets.Set(new_data)) == 1 and str(new_data[0]) == 'M':
                    continue
                if el in ['pcpn', 'snow']: #want total monthly values
                    summ = 0.0
                    #count number of data values
                    count = 0
                    for dat in new_data:
                        try:
                            summ+=float(dat)
                        except:
                            count+=1
                    if count == len(new_data):
                        yr_aves = []
                    else:
                        yr_aves.append(summ)
                else: #want averages of averages
                    aves = []
                    for dat in new_data:
                        try:
                            aves.append(float(dat))
                        except:
                            pass
                    if aves:
                        yr_aves.append(numpy.mean(aves))
                    else:
                        pass
            if yr_aves:
                #results[el].append(numpy.mean(yr_aves))
                results[el].append(round(numpy.mean(yr_aves),2))
            else:
                results[el].append(9999.9)
    return dict(results)

#####################################################
#KELLY's DATA APPLICATION
#Mostly copied straight from Kelly's Fortran programs
#####################################################

def Sodpiii(**kwargs):
    '''
    THIS PROGRAM CALCULATES ANNUAL TIME SERIES OF EXTREME VALUES OF A CLIMATE
    VARIABLE
    '''
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    results_0 = defaultdict(dict)
    results = defaultdict(dict)
    averages = {}
    skews= {}
    stdevs = {}
    dates = kwargs['dates']
    start_year = int(dates[0][0:4])
    end_year = int(dates[-1][0:4])
    start_month = int(dates[0][5:7])
    end_month = int(dates[-1][5:7])
    #Initialize fixed data arrays
    lisdur = [99, 99, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,15, 20, 25, 30]
    mxmis = [0 for k in range(len(lisdur))]
    rtnlis = [.0001, .0002, .0003, .0004, .0005, .0010, .0020,\
            .0025, .0033, .0040, .0050, .0100, .0200, .0250,\
            .0333, .0400, .0500, .1000, .2000, .2500, .3000,\
            .3333, .4000, .5000, .6000, .7000, .7500, .8000,\
            .8333, .8750, .9000, .9500, .9600, .9666, .9750,\
            .9800, .9900, .9950, .9960, .9966, .9975, .9980,\
            .9990, .9995, .9996, .9998, .9999]

    ppiii = [.0001, .0005, .0010, .0050, .0100, .0200, .0250,\
            .0400, .0500, .1000, .2000, .3000, .4000, .5000, \
            .6000, .7000, .8000, .9000, .9500, .9600, .9750,\
            .9800, .9900, .9950, .9990, .9995, .9999,]
    #Areal Statistics, taken from climate.dri.edu:/wrcc2/krwrcc/sep11/arealstats.dat
    amean = [1.00, 1.50, 2.00, 3.00, 4.00, 5.00, 6.00, 7.00, \
             9.00, 10.00, 11.00, 12.00, 14.00, 16.00, 18.00, 20.00]
    apctan = [.024, .032, .040, .064, .077, .087, .098, .107, \
             .116, .125, .131, .138, .171, .199, .226, .253]
    #ask = [1.20, 1.10, .92, .92, .95, 1.07, .94, .85, \
          #.80, .75, .70, .64, .46, .45, .43, .32]
    #acv = [.26, .26, .26, .27, .27, .26, .25, .24, \
          #.24, .24, .23, .23, .23, .23, .22, .21]
    ask = [2.00, 1.50, 1.00, .90, .85, .80, .75, .70, \
          .65, .60, .55, .50, .45, .40, .35, .30]
    acv = [.25, .25, .25, .25, .25, .25, .25, .25, \
          .25, .25, .25, .25, .25, .25, .25, .25]
    #Read in piii table:
    piii = {}
    count = 0
    for line in fileinput.input([LIB_PREFIX + 'piii.dat.2']):
        count+=1
        if count > 11 and count < 193:
            skew = line[1:4].lstrip()
            if skew[0] == '-':
                if skew[1] == '0' and skew[2] != '0':
                    skew = '-%s' % skew[2]
                elif skew[1] == '0' and skew[2] == '0':
                    skew = 0
            else:
                if skew == '00':
                    skew = 0
                else:
                    skew.lstrip('0')
            skew = int(skew)
            piii[skew] = []
            for k in range(1,15):
                piii[skew].append(int(line[5*k:5*k+5]))
        if count > 194:
            skew = line[1:4].lstrip()
            if skew[0] == '-':
                if skew[1] == '0':
                    skew = '-%s' % skew[2]
            else:
                skew.lstrip('0')
            skew = int(skew)
            for k in range(1,14):
                piii[skew].append(int(line[5*k:5*k+5]))
    #Loop over stations
    for i, stn in enumerate(kwargs['coop_station_ids']):
        elements = kwargs['elements']
        el_type = kwargs['el_type'] # maxt, mint, avgt, dtr (daily temp range)
        el_data = kwargs['data'][i]
        num_yrs = len(el_data)
        #el_data[el_idx][yr] ;
        #if element_type is hdd, cdd, dtr or gdd: el_data[0] = maxt, el_data[1]=mint

        #Check for empty data and initialize results directory
        if not any(el_data[j] for j in range(len(el_data))):
            results_0[i] = []
            results[i] = []
            continue
        if kwargs['days'] == 'i':
            num_tables = 1
        elif kwargs['days'] == '5':
            num_tables = 5
        else:
            num_tables = 16

        for tbl_idx in range(num_tables):
            results_0[i][tbl_idx] = [[] for row in range(num_yrs + 7)] # each row has length 4
            results_0[i][tbl_idx][num_yrs] = ['MEAN']
            results_0[i][tbl_idx][num_yrs+1] = ['S.D.']
            results_0[i][tbl_idx][num_yrs+2] = ['C.V.']
            results_0[i][tbl_idx][num_yrs+3] = ['SKEW']
            results_0[i][tbl_idx][num_yrs+4] = ['MIN']
            results_0[i][tbl_idx][num_yrs+5] = ['MAX']
            results_0[i][tbl_idx][num_yrs+6] = ['YEARS']

            results[i][tbl_idx] = [[] for row in range(47)] #each row has length 4
            averages[tbl_idx] = 0.0
            stdevs[tbl_idx] = 0.0
            skews[tbl_idx] = 0.0
        #Initialize data array
        ndata = [[[kwargs['value_missing'] for day in range(31)] for mon in range(12)] for yr in range(num_yrs)]
        stats = [[0.0 for numdur in range(len(lisdur))] for k in range(7)]
        rtndur = [[0.0 for k in range(len(lisdur))] for l in range(len(rtnlis))]
        #Populate data array ndata
        for yr in range(num_yrs):
            for mon in range(12):
            #for mon in range(start_month, end_month +1):
                if yr == 0 and mon + 1 < start_month:
                    continue
                if yr == num_yrs - 1 and mon +1 > end_month:
                    continue

                if mon == 1  and not WRCCUtils.is_leap_year(start_year + yr):
                    mon_len = 28
                else:
                    mon_len = mon_lens[mon]

                for day in range(mon_len):
                    #find the right data
                    doy = WRCCUtils.compute_doy(str(mon + 1), str(day + 1))
                    if kwargs['el_type'] == 'avgt':
                        dat_x = el_data[yr][0][doy -1]
                        dat_n = el_data[yr][1][doy -1]
                        val_x, flag_x = WRCCUtils.strip_data(dat_x)
                        val_n, flag_n = WRCCUtils.strip_data(dat_n)
                        if flag_x == 'M' or flag_n == 'M':
                            pass
                        else:
                            try:
                                value = (int(dat_x) + int(dat_n)) / 2.0
                                ndata[yr][mon][day] = value
                            except:
                                pass
                    else:
                        dat = el_data[yr][0][doy-1]
                        val, flag = WRCCUtils.strip_data(dat)
                        if flag == 'M' or flag == 'A':
                            pass
                        elif flag == 'T':
                            ndata[yr][mon][day] = 0.0
                        elif flag == 'S':
                            ndata[yr][mon][day] = kwargs['value_subsequent']
                        else:
                            try:
                                value = float(val)
                                ndata[yr][mon][day] = value
                            except:
                                pass
        numdur = 0
        annser = [[[0.0 for j in range(16)] for k in range(3)] for yr in range(num_yrs)]
        for yr in range(num_yrs):
            for j in range(len(lisdur)):
                annser[yr][0][j] = -9999.0
        #BIG numdur loop
        #Loop over all durations
        while numdur < len(lisdur) - 1: #16 = len(lisdur)
            numdur+=1
            ndur = lisdur[numdur -1] #number of days
            if 'days' in kwargs.keys():
                if kwargs['days'] == 'i':
                    numdu1 = numdur - 1
                    if ndur < kwargs['number_of_days']:
                        continue
                    elif ndur > kwargs['number_of_days'] and ndur != 99:
                        break
                    elif ndur == 99:
                        continue
                elif kwargs['days'] == '5':
                    if numdur < 3:continue
                    if numdur >=8:break
                    #if ndur < 2:continue
                    #if ndur >= 7:break
            maxmis = mxmis[numdur -1]
            #Year loop
            n732 = [kwargs['value_missing'] for k in range(733)]
            #Year loop
            for iyear in range(num_yrs):
                mont = start_month - 1
                iyeart = iyear
                mcount = 0
                idycnt = 0
                #Special consideration to last day of previous year
                #Need to later check for accumulations beginning previous day
                iyearl = iyear
                monl = start_month - 1
                if monl == 0 and iyear > 0:
                    monl = 12
                    iyearl = iyear - 1
                ndayl = mon_lens[monl -1]
                n732[0] = ndata[iyearl][monl-1][ndayl-1]
                while mont < 12:
                    if iyeart > num_yrs -1:
                        break
                    elif iyeart == num_yrs -1:
                        if mont > end_month:break
                    mont+=1
                    if mont == 13:mont = 1
                    mcount+=1
                    if mcount == 25:break
                    if mont == 1 and mcount != 1:
                        iyeart+=1
                    if mont == 2 and not WRCCUtils.is_leap_year(start_year + iyeart):
                        length = 28
                    else:
                        length = mon_lens[mont -1]
                    for iday in range(length):
                        idycnt+=1
                        n732[idycnt] = ndata[iyeart][mont-1][iday]
                #End while loop
                #Find yearly stats
                xmax = -9999.0
                xmin = 9999.0
                xdate = 0
                ndate = 0
                nummis = 0
                #Day loop:
                break_flag = False
                for idoy in range(366):
                    summ = 0
                    sumobs = 0
                    naccum = 0
                    numacc = 0
                    #ndur loop
                    for iplus in range(ndur): #NOTE: Kellys also goes from 0  to ndur -1
                        if iplus == 0:
                            #Skip periods that begin with previous accumulation
                            if abs(n732[idoy] - kwargs['value_subsequent']) < 0.001:
                                nummis+=1
                                break_flag = True
                                break
                            #ntrip is set to 0 when iplus is 0
                            #when nummis is added to, ntrip is tripped to 1, after which
                            #nummis cannot be incremented for that day
                            ntrip = 0
                        iday = idoy + iplus
                        val = n732[iday]
                        if abs(val - kwargs['value_missing']) < 0.001:
                            if idoy <= 364 and ntrip == 0:
                                nummis+=1
                                #Trip the switch
                                ntrip = 1
                            if nummis > maxmis:
                                break
                        elif abs(val - kwargs['value_subsequent']) < 0.001:
                            naccum = 1
                            numacc+=1
                        else:
                            sumobs+=1
                            summ+=val
                            if naccum ==1:naccum=0
                    #End ndur loop
                    if break_flag:break
                    if sumobs > 0.5:
                        if el_type in ['snwd', 'maxt', 'mint', 'avgt']:
                            summ = summ / float(sumobs)
                    #Do not use averages if all days are not there
                    if el_type in ['snwd', 'maxt', 'mint', 'avgt']:
                        if sumobs < ndur:
                            if el_type == 'avgt':
                                if kwargs['mean_temperatures'] == 'b':
                                    summ = 9999.0
                                else:
                                    summ = -9999.0
                            elif el_type in ['snwd', 'maxt']:
                                summ = -9999.0
                            else:
                                summ = 9999.0
                    if naccum == 1:
                        nummis+=numacc
                        numacc = 0
                    if el_type in ['pcpn', 'snow', 'snwd', 'maxt']:
                        if summ > xmax:
                            xmax = summ
                            mon, day = WRCCUtils.compute_mon_day(idoy + 1)
                    elif el_type == 'mint':
                        if summ < xmin:
                            xmin = summ
                            mon, day = WRCCUtils.compute_mon_day(idoy + 1)
                    elif el_type == 'avgt':
                        if (kwargs['mean_temperatures'] == 'a' and summ > xmax) or (kwargs['mean_temperatures'] == 'b' and summ < xmin):
                            xmax = summ
                            xmin = summ
                            mon, day = WRCCUtils.compute_mon_day(idoy + 1)

                #End of day loop
                if not mon:mon = '-1'
                if not day:day = '-1'
                mon = str(mon)
                day = str(day)
                if len(mon) == 1:
                    mon = '0%s' %mon
                if len(day) == 1:
                    day = '0%s' %day
                idate = WRCCUtils.Doymd(idoy, start_month, iyear)
                xdate = float(idate)

                xmismo = float(nummis)
                if el_type == 'mint':
                    x = xmin
                else:
                    x = xmax
                annser[iyear][0][numdur - 1] = x
                annser[iyear][1][numdur - 1] = xdate
                annser[iyear][2][numdur - 1] = nummis # In Kellys this is set to mysterios "xmisno"
                if kwargs['days'] == 'i':
                    tbl_idx = 0
                elif kwargs['days'] == '5':
                    tbl_idx = numdur - 3
                else:
                    tbl_idx = numdur - 1
                results_0[i][tbl_idx][iyear].append('%i' %(start_year + iyear))
                results_0[i][tbl_idx][iyear].append('%.3f' %x)
                results_0[i][tbl_idx][iyear].append('%s%s' %(mon,day))
                results_0[i][tbl_idx][iyear].append('%i' %nummis)
            #End of year loop!
            #Find Statistics
            xmaxx = -9999.0
            xminn = 9999.0
            summ = 0.0
            summ2 = 0.0
            summ3 = 0.0
            count = 0.0
            #Year loop
            for nyear in range(num_yrs):
                value = annser[nyear][0][numdur - 1]
                if value >= -9998.0:
                    summ+=value
                    summ2+=value*value
                    summ3+=value*value*value
                    count+=1
                    if value > xmaxx:xmaxx = value
                    if value < xminn:xminn = value
            if count > 0.5:
                average = summ / count
            else:
                average = 0.0

            if count > 1.5:
                try:
                    stdev = numpy.sqrt((summ2 - summ*summ/ count) /  (count - 1.0))
                except:
                    stdev = 0.0
            else:
                stdev = 0.0

            if abs(average) >= 0.00001:
                cv = stdev / average
            else:
                cv = 0.0
            if count > 1.5:
                h1 = summ / count
                h2 = summ2 / count
                h3 = summ3 / count
                xm2 = h2 - h1*h1
                xm3 = h3 - 3.0*h1*h2 + 2.0*h1*h1*h1
                if abs(xm2) > 0.000001:
                    try:
                        sk = xm3 / (xm2*numpy.sqrt(xm2))
                    except:
                        sk = 0.0
                else:
                    sk = 0.0
            else:
                sk = 0.0
            stats[0][numdur-1] = average
            stats[1][numdur-1] = stdev
            stats[2][numdur-1] = cv
            stats[3][numdur-1] = sk
            stats[4][numdur-1] = xminn
            stats[5][numdur-1] = xmaxx
            stats[6][numdur-1] = count
            if kwargs['days'] == 'i':
                tbl_idx = 0
            elif kwargs['days'] == '5':
                tbl_idx = numdur - 3
            else:
                tbl_idx = numdur - 1

            averages[tbl_idx] = '%.2f' %average
            stdevs[tbl_idx] = '%.2f' %stdev
            skews[tbl_idx] = '%.2f' %sk
            results_0[i][tbl_idx][num_yrs].append('%.2f' % average)
            results_0[i][tbl_idx][num_yrs+1].append('%.2f' % stdev)
            results_0[i][tbl_idx][num_yrs+2].append('%.2f' % cv)
            results_0[i][tbl_idx][num_yrs+3].append('%.2f' % sk)
            results_0[i][tbl_idx][num_yrs+4].append('%.2f' % xminn)
            results_0[i][tbl_idx][num_yrs+5].append('%.2f' % xmaxx)
            results_0[i][tbl_idx][num_yrs+6].append('%i' % int(count))
        #End numdur while loop... Phew...
        if kwargs['mean'] == 'am':stats[0] = amean
        annpcp = 50.0 #from LIB_PREFIX + arealstats.dat
        if kwargs['pct_average'] == 'apct':
            for idur in range(16):stats[1][idur] = apctan[idur]*annpcp

        if kwargs['skew'] == 'as':
            for idur in range(16):stats[3][idur] = ask[idur]

        if kwargs['cv'] == 'acv':
            for idur in range(16):stats[1][idur] = acv[idur] * stats[0][idur]
        #Ration of 6 and 12 hr to one day (from LIB_PREFIX + arealstats.dat)
        r6to1 = 0.5
        r12to1 = 0.75

        for idur in range(len(lisdur)):
            if kwargs['days'] == 'i':
                if idur != numdu1 - 1:continue
            elif kwargs['days'] == '5':
                if idur <2: #idur 0,1 are 6hr, 12 hr
                    continue
                if idur >= 7:break
            ave = stats[0][idur]
            sd = stats[1][idur]
            sk = stats[3][idur]
            for iretrn in range(len(rtnlis)):
                pnoexc = rtnlis[iretrn]
                psd = WRCCUtils.Pintp3(pnoexc, piii, ppiii,len(ppiii),sk)
                rtndur[iretrn][idur] = psd
            #End iretrn loop
        #End idur loop
        for idur in range(len(lisdur)):
            if kwargs['days'] == 'i':
                if idur != numdu1 - 1:continue
                tbl_idx = 0
            elif kwargs['days'] == '5':
                if idur < 2:continue
                if idur >=7:break
                #if idur >= 5:break
                #tbl_idx = idur
                tbl_idx = idur - 2
            else:
                tbl_idx = idur
            for iretrn in range(len(rtnlis)):
                pnonex = rtnlis[iretrn]
                pexc = 1.0 - pnonex
                period = 1.0 / (pexc)
                psd = rtndur[iretrn][idur]
                if idur >=2:
                    value = stats[0][idur] + stats[1][idur] * psd
                elif idur == 0:
                    value = r6to1 * (stats[0][0] + stats[1][0] * rtndur[iretrn][0])
                elif idur == 1:
                    value = r12to1 * (stats[0][0] + stats[1][0] * rtndur[iretrn][0])
                results[i][tbl_idx][iretrn].append('PN = %.4f ' % pnonex)
                results[i][tbl_idx][iretrn].append('P = %.4f ' % pexc)
                results[i][tbl_idx][iretrn].append('T = %.4f ' % period)
                results[i][tbl_idx][iretrn].append('PSD = %.4f ' % psd)
                results[i][tbl_idx][iretrn].append('VALUE = %.4f ' % value)
    return results_0, results, averages, stdevs, skews

def Sodxtrmts(**kwargs):
    '''
    THIS PROGRAM PRODUCES MONTHLY AND ANNUAL TIME SERIES FOR A
    LARGE NUMBER OF PROPERTIES DERIVED FROM THE SOD DAILY DATA SET.
    '''
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    results = defaultdict(list)
    fa_results = defaultdict(list)
    dates = kwargs['dates']
    if not dates:
        return results, fa_results
    start_year = int(dates[0][0:4])
    end_year = int(dates[-1][0:4])
    #Initialize analysis parameters
    mischr = [' ','a','b','c','d','e','f','g','h','i','j',\
            'k','l','m','n','o','p','q','r','s','t','u','v',\
            'w','x','y','z','=','*']
    #pnlist contains the list of numpn nonexceedance probabilities
    pnlist = [.0001, .0002, .0003, .0004, .0005, .0010, .0020,\
            .0025, .0033, .0040, .0050, .0100, .0200, .0250,\
            .0333, .0400, .0500, .1000, .2000, .2500, .3000,\
            .3333, .4000, .5000, .6000, .7000, .7500, .8000,\
            .8333, .8750, .9000, .9500, .9600, .9666, .9750,\
            .9800, .9900, .9950, .9960, .9966, .9975, .9980,\
            .9990, .9995, .9996, .9998, .9999]
    #ppiii contains the list of nonexceedance probabilities read in from
    #the file containing the values
    piiili = [.0001, .0005, .0010, .0050, .0100, .0200, .0250,\
            .0400, .0500, .1000, .2000, .3000, .4000, .5000,\
            .6000, .7000, .8000, .9000, .9500, .9600, .9750,\
            .9800, .9900, .9950, .9990, .9995, .9999]
    probs = [0.001, 0.002, 0.005, 0.01, 0.02, 0.04, 0.050, 0.1, \
            0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.96, 0.9666, \
            0.975, 0.98, 0.99, 0.995, 0.996, 0.998, 0.999]
    probss = probs
    #Read in piii table:
    piii = {}
    count = 0
    for line in fileinput.input([LIB_PREFIX + 'piii.dat.2']):
        count+=1
        if count > 11 and count < 193:
            skew = line[1:4].lstrip()
            if skew[0] == '-':
                if skew[1] == '0' and skew[2] != '0':
                    skew = '-%s' % skew[2]
                elif skew[1] == '0' and skew[2] == '0':
                    skew = 0
            else:
                if skew == '00':
                    skew = 0
                else:
                    skew.lstrip('0')
            skew = int(skew)
            piii[skew] = []
            for k in range(1,15):
                piii[skew].append(int(line[5*k:5*k+5]))
        if count > 194:
            skew = line[1:4].lstrip()
            if skew[0] == '-':
                if skew[1] == '0':
                    skew = '-%s' % skew[2]
            else:
                skew.lstrip('0')
            skew = int(skew)
            for k in range(1,14):
                piii[skew].append(int(line[5*k:5*k+5]))
    #Loop over stations
    for i, stn in enumerate(kwargs['coop_station_ids']):
        elements = kwargs['elements']
        el_type = kwargs['el_type'] # maxt, mint, avgt, dtr (daily temp range)
        el_data = kwargs['data'][i]
        num_yrs = len(el_data)
        #el_data[el_idx][yr] ;
        #if element_type is hdd, cdd, dtr or gdd: el_data[0] = maxt, el_data[1]=mint

        #Check for empty data and initialize results directory
        if not any(el_data[j] for j in range(len(el_data))):
            results[i] = []
            fa_results[i] = []
            continue
        results[i] = [[] for k in range(num_yrs + 6)]
        #Initialize frequency analysis result arrays:
        proutp = [[0 for k in range(13)] for l in range(len(probs))]
        proutg = [[0 for k in range(13)] for l in range(len(probs))]
        proutb = [[0 for k in range(13)] for l in range(len(probs))]
        proutc = [[0 for k in range(13)] for l in range(len(probs))]
        if 'frequency_analysis_type' in kwargs.keys():
            fa_results[i] = [['%s %s' % (str(kwargs['frequency_analysis_type']), probss[k])] for k in range(len(probss))]
        for yr in range(num_yrs):
            year = start_year + yr
            if kwargs['start_month'] != '01':
                results[i][yr] = [str(year)+ '-'+str(year+1)[2:4]]
            else:
                results[i][yr] = [str(year)]
        results[i][num_yrs] = ['MEAN'];results[i][num_yrs+1]=['S.D.']
        results[i][num_yrs+2] = ['SKEW'];results[i][num_yrs+3]=['MAX']
        results[i][num_yrs+4] = ['MIN'];results[i][num_yrs+5]=['YEARS']
        #Read in Pearson III lookup tables/to be done
        #PIII = []
        table_1 = [[-9999.0 for mon in range(13)] for yr in range(num_yrs)]
        table_2 = [[31 for mon in range(13)] for yr in range(num_yrs)]
        annsav = [[' ' for mon in range(13)] for yr in range(num_yrs)]
        #out = [[0.0 for k in range(13)] for l in range(7)]
        mean_out = [0.0 for k in range(13)]
        outchr = [0 for k in range(13)]
        xmiss = -9999.0
        #Year loop
        for yr in range(num_yrs):
            annmin =  9999.0
            annmax = -9999.0
            annflg = [' ' for k in range(13)]
            icount = 0
            #Month loop
            for monind in range(12):
                nyeart = yr
                mon =  monind + int(kwargs['start_month'].lstrip('0')) - 1
                if mon > 11:
                    mon-=12
                    nyeart+=1
                if nyeart == num_yrs:
                    continue
                #Check for leap year
                if mon == 1 and not WRCCUtils.is_leap_year(start_year + nyeart):
                    mon_len = 28
                else:
                    mon_len = mon_lens[mon]
                flag = ' '
                sumda = 0
                summ = 0
                summ2 = 0
                xmin = 9999.0
                xmax = -9999.0
                #Day loop
                for nda in range(mon_len):
                    #Find day of year
                    doy = WRCCUtils.compute_doy_leap(str(mon + 1),str(nda + 1))
                    if el_type in ['maxt', 'mint', 'wdmv']:
                        dat = el_data[nyeart][0][doy-1]
                        val, flag = WRCCUtils.strip_data(dat)
                        if flag == 'M':
                            value = xmiss
                        else:
                            try:
                                value = float(val)
                            except:
                                value = xmiss
                    elif el_type in ['pcpn', 'snow', 'snwd', 'evap']:
                        dat = el_data[nyeart][0][doy-1]
                        val, flag = WRCCUtils.strip_data(dat)
                        if flag == 'M':
                            value = xmiss
                        elif flag == 'T':
                            value = 0.001
                        elif flag == 'S':
                            value = 245.0
                        elif flag == 'A':
                            try:
                                value = float(val)
                                value = value +100
                            except:
                                value = xmiss
                        else:
                            try:
                                value = float(val)
                            except:
                                value = xmiss
                    else:
                        #We have to compute values from maxt, mint
                        dat_x = el_data[nyeart][0][doy-1]
                        dat_n = el_data[nyeart][1][doy-1]
                        val_x, flag_x = WRCCUtils.strip_data(dat_x)
                        val_n, flag_n = WRCCUtils.strip_data(dat_n)
                        if flag_x == 'M' or flag_n == 'M':
                            value = xmiss
                        else:
                            try:
                                nval_x = int(val_x)
                                nval_n = int(val_n)
                                if el_type == 'dtr':
                                    value = nval_x - nval_n
                                    print value
                                elif el_type == 'avgt':
                                    value = (nval_x + nval_n)/2.0
                                elif el_type in ['hdd','cdd', 'gdd']:
                                    ave = (nval_x + nval_n)/2.0
                                    if el_type == 'hdd':
                                        value = float(kwargs['base_temperature']) - ave
                                    else:
                                        value = ave - float(kwargs['base_temperature'])
                                    if value < 0:
                                        value = 0
                            except:
                                value = xmiss
                    if kwargs['monthly_statistic'] in ['mmax', 'mmin']:
                        if value > -9998.0:
                            sumda+=1
                            if el_type in ['snow', 'pcpn', 'evap'] and abs(value - 245.0) < 0.01: #S flag
                                value = 0.0
                            elif el_type in ['snow', 'pcpn', 'evap'] and value > 99.99 and value < 240.0: #A flag
                                value -=100.0
                            if kwargs['monthly_statistic'] == 'mmax' and value > xmax:
                                xmax = value
                                #annflg[mon] = 'A'
                            if kwargs['monthly_statistic'] == 'mmin' and value < xmin:
                                xmin = value
                        #if kwargs['monthly_statistic'] == 'mmax' and value > xmax:xmax = value
                        #if kwargs['monthly_statistic'] == 'mmin' and value < xmin:xmin = value

                        if nda  == mon_len -1:
                            if kwargs['monthly_statistic'] == 'mmax':table_1[yr][mon] = xmax
                            if kwargs['monthly_statistic'] == 'mmin':table_1[yr][mon] = xmin
                            table_2[yr][mon] = mon_len - sumda

                    elif kwargs['monthly_statistic'] == 'mave':
                        if el_type in ['snow', 'pcpn', 'evap'] and abs(value - 245.0) < 0.01: #S flag
                            value = 0.0
                        elif el_type in ['snow', 'pcpn', 'evap'] and value > 99.99 and value < 240.0: #A flag
                            value-=100.0

                        if value > -9998.0:
                            summ+=value
                            sumda+=1
                        if nda  == mon_len -1:
                            if sumda >= 0.5:
                                table_1[yr][mon] =summ/sumda
                                table_2[yr][mon] = mon_len - sumda

                    elif kwargs['monthly_statistic'] == 'sd':
                        if el_type in ['snow', 'pcpn', 'evap'] and abs(value - 245.0) < 0.01: #S flag
                            value = 0
                        elif el_type in ['snow', 'pcpn','evap'] and value > 99.99 and value < 240.0: #A flag
                            value-=100.0
                            annfl[mon] = 'A'

                        if value > -9998.0:
                            summ+=value
                            summ2+=value * value
                            sumda+=1

                        if nda  == mon_len -1:
                            if sumda >1.5:
                                try:
                                    table_1[yr][mon] = numpy.sqrt((summ2 - summ*summ/sumda)/(sumda -1.0))
                                except:
                                    pass
                                table_2[yr][mon] = mon_len - sumda

                    elif kwargs['monthly_statistic'] == 'ndays':
                        flag = ' '
                        if el_type in ['snow', 'pcpn', 'evap'] and abs(value - 245.0) < 0.01: #S flag
                            value = 0
                        elif el_type in ['snow', 'pcpn', 'evap'] and value > 99.99 and value < 240.0: #A flag
                            value-=100
                            flag = 'A'

                        if value > -9998.0:
                            sumda+=1
                            if kwargs['less_greater_or_between'] == 'l' and value < float(kwargs['threshold_for_less_or_greater']):
                                summ+=1
                            elif kwargs['less_greater_or_between'] == 'g' and value > float(kwargs['threshold_for_less_or_greater']):
                                summ+=1
                                if flag != ' ':annflg[mon] = flag
                            elif kwargs['less_greater_or_between'] == 'b' and value > float(kwargs['threshold_low_for_between']) and value < float(kwargs['threshold_high_for_between']):
                                summ+=1
                                if flag != ' ':annflg[mon] = flag

                        if nda  == mon_len -1:
                            table_1[yr][mon] = summ
                            table_2[yr][mon] = mon_len - sumda

                    elif kwargs['monthly_statistic'] == 'rmon':
                        if el_type in ['snow', 'pcpn', 'evap'] and abs(value - 245.0) < 0.01: #S flag
                            value = 0
                        elif el_type in ['snow', 'pcpn', 'evap'] and value > 99.99 and value < 240.0: #A flag
                            value-=100
                            flag = 'A'

                        if value > -9998.0:
                            sumda+=1
                            if value > xmax:xmax = value
                            if value < xmin:xmin = value
                            if value > annmax:annmax = value
                            if value < annmin:annmin = value

                        if nda  == mon_len - 1:
                            table_1[yr][mon] = xmax - xmin
                            table_2[yr][mon] = mon_len - sumda
                            annran = annmax - annmin

                    elif kwargs['monthly_statistic'] == 'msum':
                        flag = ' '
                        if el_type in ['snow', 'pcpn', 'evap'] and abs(value - 245.0) < 0.01: #S flag
                            value = 0.0
                            if nda == mon_len -1:flag = 'S'
                        elif el_type in ['snow', 'pcpn', 'evap'] and value > 99.99 and value < 240.0: #A flag
                            value-=100

                        if value > -9998.0:
                            summ+=round(value,2)
                            sumda+=1
                        #Estimate missing sum for degree days, using the mean of the other days
                        nummsg = mon_len - sumda
                        if nda  == mon_len -1:
                            if el_type in ['hdd', 'cdd', 'gdd']:
                                if nummsg != 0 and nummsg <= kwargs['max_missing_days'] and sumda > 0.5:
                                    summ = summ/sumda * float(mon_len -1)

                        if nda  == mon_len -1:
                            table_1[yr][mon] = summ
                            table_2[yr][mon] = mon_len - sumda
                            if flag != ' ':annflg[mon] = flag
                    #End of day loop

                #Need annual values later on
                annsav[yr][mon] = annflg[mon]
                #End of monind loop
            #Compute annual values
            count = 0
            annmax = -9999.0
            annmin = 9999.0
            annminh = 9999.001
            sumann = 0.0
            for mon in range(12):
                if el_type in ['snow', 'pcpn', 'snwd', 'evap']:
                    valmon = round(table_1[yr][mon],2)
                else:
                    valmon = table_1[yr][mon]
                #valmon = table_1[yr][mon]
                summon = table_2[yr][mon]
                if kwargs['monthly_statistic'] == 'mmax':
                    if el_type in ['snow', 'pcpn', 'evap']:
                        if valmon > 99.99 and valmon <= 240.0:
                            continue
                        else:
                            if valmon > annmax and annflg[mon] != 'A':annmax = valmon
                    else:
                        if valmon > annmax:annmax = valmon
                    sumann+=summon

                elif kwargs['monthly_statistic'] == 'mmin':
                    if valmon < annmin:annmin= valmon
                    sumann+=summon

                elif kwargs['monthly_statistic'] in ['mave', 'ndays', 'msum']:
                    if int(summon) <= int(kwargs['max_missing_days']):
                        sumann+=valmon
                        count+=1

                elif kwargs['monthly_statistic'] == 'sd':
                    sumann = 0

                elif kwargs['monthly_statistic'] == 'rmon':
                    if valmon > annmax:annmax = valmon
                    if valmon < annmin:annmin= valmon
                    sumann+=summon
            #End mon loop
            #Populate table 1 and 2 with annual values
            if kwargs['monthly_statistic'] in ['mmax', 'mmin']:
                if kwargs['monthly_statistic'] == 'mmax':table_1[yr][12] = annmax
                if kwargs['monthly_statistic'] == 'mmin':table_1[yr][12] = annmin
                table_2[yr][12] = sumann
            elif kwargs['monthly_statistic'] == 'mave':
                if count > 0.5:
                    table_1[yr][12] = float(sumann)/float(count)
                    table_2[yr][12] = 12.0 - count
            elif kwargs['monthly_statistic'] == 'sd':
                table_1[yr][12] = 0.0
                table_2[yr][12] = 12.0
            elif kwargs['monthly_statistic'] in ['ndays', 'msum']:
                table_1[yr][12] = float(sumann)
                table_2[yr][12] = 12.0 - count
            elif kwargs['monthly_statistic'] == 'rmon':
                if el_type != 'dtr':
                    table_1[yr][12] = annmax - annmin
                table_2[yr][12] = sumann
        #End of Year loop! Phew...
        for monind in range(13):
            if monind <= 11:
                mon = monind + int(kwargs['start_month'].lstrip('0')) - 1
                if mon > 11:mon-=12
            else:
                mon = monind

            xmax = -9999.0
            xmin = 9999.0
            summ = 0.0
            summ2 = 0.0
            summ3 = 0.0
            count = 0.0

            for yr in range(num_yrs):
                if el_type in ['snow', 'pcpn', 'snwd', 'evap']:
                    value = round(table_1[yr][mon],2)
                else:
                    value = table_1[yr][mon]
                #value = table_1[yr][mon]
                missng = table_2[yr][mon]

                #Treat monthly totals and annual totals differently
                #For annual totals, ignore years with at least one
                #Month that does not meet the missing day criterium
                if mon <= 11:
                    if missng <= int(kwargs['max_missing_days']):
                        summ+=value
                        summ2+= value**2
                        summ3+=value**3
                        count+=1
                        if value > xmax:xmax=value
                        if value < xmin:xmin=value
                else:
                    ncheck = int(kwargs['max_missing_days'])-1
                    #For annual: for ave, thresholds, sums, include only full years
                    if kwargs['monthly_statistic']  in ['mave', 'ndays', 'msum']:
                        ncheck = 0
                    if missng <= ncheck:
                        summ+=value
                        summ2+= value**2
                        summ3+=value**3
                        count+=1
                        if value > xmax:xmax=value
                        if value < xmin:xmin=value
            #End year loop
            if count > 0.5:
                mean_out[monind] = round(summ/count,2)
                results[i][num_yrs].append('%.2f' % mean_out[monind])
                #New
                results[i][num_yrs].append(' ')
            sk = 0.0
            if count > 1.5:
                try:
                    results[i][num_yrs+1].append('%.2f' % numpy.sqrt((summ2 - summ**2/count)/(count -1)))
                    #New
                    results[i][num_yrs+1].append(' ')
                except:
                    pass
                h1 = summ/count
                h2 = summ2/count
                h3 = summ3/count
                xm2 = h2 - h1**2
                xm3 = h3 - 3.0*h1*h2 + 2.0*h1**3
                if abs(xm2) > 0.00001:
                    try:
                        sk = xm3 / (xm2*numpy.sqrt(xm2))
                    except:
                        sk = 0.0

            results[i][num_yrs+2].append('%.2f' % sk)
            #New
            results[i][num_yrs+2].append(' ')
            results[i][num_yrs+3].append('%.2f' % xmax)
            #New
            results[i][num_yrs+3].append(' ')
            results[i][num_yrs+4].append('%.2f' % xmin)
            #New
            results[i][num_yrs+4].append(' ')
            results[i][num_yrs+5].append('%.2f' % count)
            #New
            results[i][num_yrs+5].append(' ')
        #End month loop
        #Record results for each year
        for yr in range(num_yrs):
            for monind in range(13):
                if monind < 12:
                    mon = monind + int(kwargs['start_month'].lstrip('0')) - 1
                    if mon > 11:
                        mon-=12
                else:
                    mon = monind

                intgr = int(table_2[yr][mon])
                if intgr > 26:intgr = 26
                #Special for accumulations or subsequents
                outchr[monind] = mischr[intgr]
                if annsav[yr][mon] != ' ':
                    outchr[monind] = annsav[yr][mon]

                if (table_1[yr][mon]> 9998.5 or table_1[yr][mon] < -9998.0 or outchr[monind] =='z'):
                    if kwargs['monthly_statistic'] == 'msum' and el_type == 'hdd' and table_1[yr][mon]> 9998.5:
                        continue
                    else:
                        results[i][yr].append('-----')
                        results[i][yr].append('z')
                        continue

                if kwargs['departures_from_averages']  == 'F':
                    #results[i][yr].append('%.2f%s' % (table_1[yr][mon], outchr[monind]))
                    results[i][yr].append('%.2f' % table_1[yr][mon])
                    results[i][yr].append('%s' % outchr[monind])
                else:
                    #results[i][yr].append('%.2f%s' % ((table_1[yr][mon] - mean_out[monind]), outchr[monind]))
                    results[i][yr].append('%.2f' % (table_1[yr][mon] - mean_out[monind]))
                    results[i][yr].append('%s' % outchr[monind])
            #End month loop
        #End of year loop
        #Start for frequency analysis
        xdata = {}
        xx = {}
        if kwargs['frequency_analysis'] == 'T':
            fa_type = kwargs['frequency_analysis_type']
            #fa types: p = PearsonIII, g = Generalized Extreme values
            #b =  Beta-P, c = Cnesored Gamma
        else:
            fa_type = None

        for monind in range(13):
            if monind <= 11:
                nmo = monind + int(kwargs['start_month'].lstrip('0')) - 1
                if nmo > 11:
                    nmo-=12
            else:
                nmo =monind

            numdat = 0
            numnz = 0
            last_year = num_yrs
            if int(kwargs['start_month'].lstrip('0')) !=1:
                last_year-=1
            for nyear in range(last_year):
                dat = table_1[nyear][nmo]
                misng = table_2[nyear][nmo]
                if abs(dat) < 9998.5:
                    if int(misng) <= kwargs['max_missing_days']:
                        numdat+=1
                        xdata[numdat-1] = dat
                        if dat > 0.005:numnz+=1
                        xx[numdat-1] = dat
                        #Note that xmax, xmin were re-determinde in capiii
                #End year loop
            if numdat < 5:
                fa_results[i].append('Not enough data to perfom frequency analysis')
                break

            #Set some bouns for certain types of analyses to avoid obvious
            #problems like negative precip or threshold excedances.
            #Also don't perform certain analyses for some element/analysis combinations.
            if el_type in ['maxt', 'mint', 'avgt']:
                vmin = -999.9
                vmax = 999.0
            elif el_type == 'dtr':
                vmin = 0.0
                vmax = 999.0
            else:
                vmin = 0.0
                vmax = 99999.0

            if kwargs['monthly_statistic'] == 'ndays':
                vmin = 0.0
                if nmo <= 11:
                    vmax = float(mon_lens[nmo])
                else:
                    vmax = 365.24

            xdata_list = [val for key, val in xdata.iteritems()]
            xx_list = [val for key, val in xx.iteritems()]
            #Frequency Analysis routines
            if fa_type == 'p': #Pearson III
                #(psd, ave, stdev, sk, cv, xmax, xmin) = WRCCUtils.Capiii(xdata, numdat, piii, piiili,len(piiili), pnlist,len(pnlist))
                shape, loc, scale = stats.gamma.fit(xdata_list)
                for k in range(len(probss)): #len(probss) = 24
                    proutp[k][monind] = stats.gamma.ppf(probs[k],shape,loc=loc,scale=scale)
                    if proutp[k][monind] < vmin:proutp[k][monind] = vmin
                    if proutp[k][monind] > vmax:proutp[k][monind] = vmax
                    '''
                    for j in range(len(pnlist)):  #len(pnlist) = 47
                        if (pnlist[j] - probss[k]) < 0.00001:
                            proutp[k][monind] = ave + stdev*psd[j]
                            if proutp[k][monind] < vmin:proutp[k][monind] = vmin
                            if proutp[k][monind] > vmax:proutp[k][monind] = vmax
                    '''
                    fa_results[i][k].append('%.2f' % proutp[k][monind])

            elif fa_type == 'g':
                #para = WRCCUtils.Gev(xx, numdat)
                shape, loc, scale = stats.genextreme.fit(xx_list)
                #Compute Quantiles:
                #rsultsg = WRCCUtils.Quantgev(para, probs, len(probs))
                for k in range(len(probs)):
                    proutg[k][monind] = stats.genextreme.ppf(probs[k],shape,loc=loc,scale=scale)
                    #proutg[k][monind] = rsultsg[k]
                    if proutg[k][monind] < vmin:proutg[k][monind] = vmin
                    if proutg[k][monind] > vmax:proutg[k][monind] = vmax
                    fa_results[i][k].append('%.2f' % proutg[k][monind])
            elif fa_type == 'b':
                #rsultb = WRCCUtils.Cabetap(xdata, numdat, probss,len(probss))
                shape_a, shape_b, loc, scale = stats.beta.fit(xdata_list)
                for k in range(len(probss)):
                    #proutb[k][monind] = rsultb[k]
                    proutb[k][monind] = stats.beta.ppf(probs[k],shape_a, shape_b, loc=loc, scale=scale )
                    if proutb[k][monind] < vmin:proutb[k][monind] = vmin
                    if proutb[k][monind] > vmax:proutb[k][monind] = vmax
                    fa_results[i][k].append('%.2f' % proutg[k][monind])
            elif fa_type == 'c':
                if numnz >= 1:
                    rsultc = WRCCUtils.Cagamma(xdata, numdat, probss, len(probss))
                    for k in range(len(probss)):
                        proutc[k][monind] = rsultsc[k]
                        if proutc[k][monind] < vmin:proutc[k][monind] = vmin
                        if proutc[k][monind] > vmax:proutc[k][monind] = vmax
                        fa_results[i][k].append('%.2f' % proutc[k][monind])
                else:
                    for k in range(len(probbs)):
                        proutc[k][monind] = 0.0
                        fa_results[i][k].append('%.2f' % proutc[k][monind])
            #End monind loop

    return results, fa_results

def Sodthr(**kwargs):
    '''
    This program can be used to find the latest spring and
    earliest fall frost (or other temperature(s)) each year.
    However, it is written much more generally to allow
    finding the latest or earliest occurrence above or below
    a threshold value, for a period up to 12-months long,
    which may extend from one year into the next (for example,
    the winter season from July thru June), for up to 10 sets
    of values.  Furthermore, the midpoint of the period can
    be set anywhere between the starting and ending dates.
    For example, July 31 can be used as mid-year, rather than
    June 30 (is a frost on July 2 the "last frost" of  spring
    or the "first frost" of autumn??)  A time series of the
    values for each half of the interval is formed, and the
    probability of exceedance is calculated, using only those
    years with less missing data than the user specifies as a
    minimum.
    '''
    results = defaultdict(dict)
    dates = kwargs['dates']
    start_year = int(dates[0][0:4])
    end_year = int(dates[-1][0:4])
    #Loop over stations
    for i, stn in enumerate(kwargs['coop_station_ids']):
        elements = kwargs['elements']
        el_type = kwargs['el_type'] # maxt, mint, avgt, dtr (daily temp range)
        el_data = kwargs['data'][i]
        num_yrs = len(el_data)
        #el_data[el_idx][yr] ;
        #if element_type is hdd, cdd, dtr or gdd: el_data[0] = maxt, el_data[1]=mint

        #Check for empty data
        if not any(el_data[j] for j in range(len(el_data))):
            results[i][0] = []
            results[i][1] = []
            results[i][2] = []
            continue
        #Set analysis parameters
        if kwargs['custom_tables'] == True:
            most = str(kwargs['interval_start'])[0:2]; ndyst = str(kwargs['interval_start'])[2:4]
            moen = str(kwargs['interval_end'][0:2]); ndyen = str(kwargs['interval_end'])[2:4]
            momid = str(kwargs['midpoint'][0:2]); ndymid = str(kwargs['midpoint'][2:4])
            thresholds = kwargs['thresholds']
            time_series = kwargs['time_series']
            ab = str(kwargs['ab'])
            le_1 = str(kwargs['le_1']); le_2 = str(kwargs['le_2'])
            misdat = int(kwargs['miss_days_1']); misdif = int(kwargs['miss_days_2'])
        else:
            most = '01'; ndyst='01'
            moen = '12'; ndyen = '31'
            momid = '07'; ndymid = '31'
            if kwargs['el_type'] == 'mint':thresholds = [36.5, 32.5, 28.5, 24.5, 20.5]; ab = 'b'
            if kwargs['el_type'] == 'maxt':thresholds = [70.5, 74.5, 78.5, 82.5, 86.5]; ab = 'a'
            if kwargs['el_type'] == 'avgt':thresholds = [45.5, 49.5, 53.5, 57.5, 61.5]; ab = 'a'
            if kwargs['el_type'] == 'dtr':thresholds = [20.0, 30.0, 40.0, 50.0, 60.0]; ab = 'a'
            time_series = [False, False, False, False, False]
            le_1 = 'l';le_2 = 'e'
            misdat = 10; misdif = 10
        numthr = len(thresholds)
        #Initialize result array
        for table in range(3):
            results[i][table] = [[999.9 for k in range(12)] for thresh in range(numthr)]
        #Initialize data arrays
        yr_doy_data = [[999.9 for doy in range(366)] for yr in range(num_yrs)]
        ndiff = [[999 for j in range(2)] for yr in range(num_yrs)]
        nts =[[[999 for k in range(3)]for j in range(2)]for yr in range(num_yrs)]
        thrpct = [[[999.9 for k in range(11)] for thresh in range(numthr)] for period in range(3)]
        #Populate yr_doy_data dealing with flags on original data
        for yr in range(num_yrs):
            for doy in range(366):
                if el_type in ['dtr','avgt']:
                    dat_x = el_data[yr][0][doy]
                    dat_n = el_data[yr][1][doy]
                    val_x, flag_x = WRCCUtils.strip_data(dat_x)
                    val_n, flag_n = WRCCUtils.strip_data(dat_n)
                    if flag_x == 'M' or flag_n == 'M':
                        continue
                    try:
                        nval_x = int(val_x)
                        nval_n = int(val_n)
                    except:
                        continue

                    if el_type == 'dtr':
                        val = nval_x - nval_n
                    elif el_type == 'avgt':
                        val = (nval_x + nval_n)/2.0
                else:
                    dat = el_data[yr][0][doy]
                    val, flag = WRCCUtils.strip_data(dat)
                    if flag == 'M':
                        continue
                    try:
                        float(val)
                    except:
                        continue
                yr_doy_data[yr][doy] = float(val)

        #Get day of year of start, mid and endpoint
        ndoyst = WRCCUtils.Catoju(most, ndyst)
        ndoyen = WRCCUtils.Catoju(moen, ndyen)
        ndoymd = WRCCUtils.Catoju(momid, ndymid)

        midm1 = ndoymd - 1
        if midm1 == 0: midm1 = 366

        if le_1 == 'e': nel1 = 1
        if le_1 == 'l': nel1 = 2
        if le_2 == 'e': nel2 = 1
        if le_2 == 'l': nel2 = 2
        if ab == 'a': nab = 1
        if ab == 'b': nab = 2

        #Loop over thresholds
        for ithr in range(1, numthr +1):
            if time_series[ithr - 1]:
                pass
                #Kelly's out put messages here?? --> new mssg out or headers in results
            #Loop over years
            for yr in range(num_yrs):
                nyear = yr + 1 #double check this, should be yr +1??
                nyeart = nyear

                #Loop over period 1 and 2
                for period in range(1,3):
                    last  = 0 #= 1 if last day of period
                    miss1 = 0 #Missing days for midpoint
                    miss2 = 0 #Missing days away from midpoint
                    metthr = 0 #= 1 if threshold has been met already

                    if period == 1:
                        if le_1 == 'e': ndoyt = ndoyst - 1
                        if le_1 == 'l': ndoyt = ndoymd
                    else:
                        if le_2 == 'e': ndoyt = ndoymd - 1
                        if le_2 == 'l': ndoyt = ndoyen + 1

                    while last != 1:
                        #Set start day and year
                        #See whether earliest or latest is required
                        if period == 1:
                            le = le_1; end = midm1; start = ndoyst
                        if period == 2:
                            le  = le_2; end = ndoyen; start = ndoymd

                        if le == 'e':
                            ndoyt+=1
                            if ndoyt > 366:
                                ndoyt = 1
                                nyeart = nyear + 1
                            if ndoyt == end: last = 1
                        elif le == 'l':
                            ndoyt-=1
                            if ndoyt == 0:
                                ndoyt = 366
                                nyeart = nyear -1
                            if ndoyt == start: last = 1

                        #skip non-leap day
                        if ndoyt == 60 and not WRCCUtils.is_leap_year(start_year + nyeart):
                            continue
                        #Get appropriate dataob
                        value = yr_doy_data[nyeart-1][ndoyt-1]
                        #Check whether threshold is exceeded. If missing, add to proper counter.
                        #miss1 and miss2 will depend on whether earliest or latest is desired
                        if ab == 'a':
                            if value > thresholds[ithr -1]:
                                if abs(value - 999.9) < 0.1:
                                    if metthr == 1:
                                        if le == 'e':
                                            miss1+=1
                                        else:
                                            miss2+=1
                                    else:
                                        if le == 'e':
                                            miss2+=1
                                        else:
                                            miss1+=1
                                else:
                                    if metthr != 1:
                                        nts[nyear - 1][period - 1][0] = ndoyt
                                        metthr = 1
                        elif ab == 'b':
                            if value < thresholds[ithr - 1]:
                                if metthr != 1:
                                    nts[nyear - 1][period - 1][0] = ndoyt
                                    metthr = 1
                            if abs(value - 999.9) < 0.1:
                                if metthr == 1:
                                    if le == 'e':
                                        if period ==1:
                                            miss1+=1
                                        else:
                                            miss2+=1
                                    else:
                                        if period ==1:
                                            miss2+=1
                                        else:
                                            miss1+=1
                                else:
                                    if le == 'e':
                                        if period ==1:
                                            miss2+=1
                                        else:
                                            miss1+=1
                                    else:
                                        if period ==1:
                                            miss1==1
                                        else:
                                            miss2+=1
                        if last != 1: continue
                        #Done assigning values
                        if metthr == 0:
                            if le == 'e':
                                nts[nyear -1][period -1][0] = 367
                            else:
                                nts[nyear - 1][period - 1][0] = -1
                        #end of while loop
                    nts[nyear -1 ][period - 1][1] = miss1
                    nts[nyear - 1][period - 1][2] = miss1
                    #End of period loop

                #Now do differences in dates
                ndoy1 = nts[nyear - 1][0][0]
                ndoy2 = nts[nyear -1][1][0]
                mo1, ndy1 = WRCCUtils.Jutoca(ndoy1)
                mo2, ndy2 = WRCCUtils.Jutoca(ndoy2)

                ndif = ndoy2 - ndoy1
                if ndif < 0:ndif+=366

                #If th event did not occur, set value to 367
                if ndoy1 == -1 or ndoy1 == 367 or ndoy2 == -1 or ndoy2 == 367:
                    ndif = 367
                else:
                    #Leap year check loop
                    #Reset Counters
                    #The following code is merely to find whether the period selected contains a leap year
                    #Possibilities:
                    #1)Period starts before or after Feb 29
                    #2)Midpoint is before or after Feb 29
                    #3)Date of occurrence is before or after Feb 29
                    leap = 0
                    includ = 0
                    nyyearl = nyear
                    moda1 = 100 * mo1 + ndy1
                    moda2 = 100 * mo2 + ndy2
                    if ndoyst <= 60:
                        if ndoymd < 60:
                            if ndoy2 >= 60:
                                includ =1
                                nyearl = nyear
                        else:
                            if ndoy1 <= 60:
                                includ = 1
                                nyearl = nyear
                    else: #Period starts after Feb 29
                        if ndoymd <= 60:
                            if ndoy2 >= 60:
                                includ =1
                                nyearl = nyear +1
                        else:
                            if ndoy1 < 60:
                                includ =1
                                nyearl = nyear +1

                    if includ ==1:
                        if WRCCUtils.is_leap_year(start_year + nyearl):
                            leap = 1
                        if leap == 0:
                            ndif-=1 # end of check year loop

                if ndoy1 == -1 or ndoy1 == 367:mo1 = -1;ndy1 = -1
                if ndoy2 == -1 or ndoy2 == 367:mo2 = -1;ndy2 = -1
                ndiff[nyear - 1 ][0] = ndif

                #Find total number of missing dys for period 1 and 2
                missyr = nts[nyear - 1][0][1] + nts[nyear - 1][0][2] + nts[nyear - 1][1][1] + nts[nyear - 1][1][2]
                ndiff[nyear - 1][1] = missyr
                #End of year loop
            modast  = 100 * most + ndyst
            modaen = 100 * moen + ndyen

            #Now find percentiles for this threshold
            #Find the lowest, highest and 10th through 90th percentile
            #For 5 - 9 years, find 20th percentile and extremes

            #Do 2 periods, first and secon table
            for period in range(3):
                icount = 0
                array = {}
                for yr in range(num_yrs):
                    if period == 2: #differences
                        if ndiff[yr][1] < misdif:
                            icount+=1
                        array[icount -1] = ndiff[yr][0]
                    else:
                        if nts[yr][period][1] + nts[yr][period][2] < misdat:
                            icount+=1
                            array[icount -1] = nts[yr][period][0]
                    #End year loop
                if icount >= 5:
                    pctile, sort, xmed = WRCCUtils.pctil('Sodthr', array, icount, 5)
                    thrpct[period][ithr - 1][5] = xmed
                    thrpct[period][ithr - 1][2] = pctile[0]
                    thrpct[period][ithr - 1][4] = pctile[1]
                    thrpct[period][ithr - 1][6] = pctile[2]
                    thrpct[period][ithr - 1][8] = pctile[3]
                    thrpct[period][ithr - 1][0] = sort[0]
                    thrpct[period][ithr - 1][10] = sort[icount - 1]

                if icount >= 10:
                    pctile, sort, xmed = WRCCUtils.pctil('Sodthr', array, icount, 10)
                    thrpct[period][ithr - 1][1] = pctile[0]
                    thrpct[period][ithr - 1][3] = pctile[2]
                    thrpct[period][ithr - 1][7] = pctile[6]
                    thrpct[period][ithr - 1][9] = pctile[8]
                    #End of period loop
            #End threshold loop
        #Populate results
        for period in range(3):
            for thresh in range(len(thrpct[period])):
                results[i][period][thresh][0] = thresholds[thresh]
                if period < 2:
                    icount = 0
                    for k in range(1,12):
                        ndoypc = int(round(thrpct[period][thresh][k-1]))
                        if ndoypc > 0:
                            nmopc, ndypc = WRCCUtils.Jutoca(ndoypc)
                        else:
                            nmopc = -1; ndypc = -1
                        results[i][period][thresh][k] = '%s %s' % (str(nmopc), str(ndypc))
                else:
                    for k in range(1,12):
                        results[i][period][thresh][k] = '%.1f' % thrpct[period][thresh][k -1]

    return results

def Sodpct(**kwargs):
    '''
    This program determines percentiles of distributions of
    climate elements.  These elements include max, min and
    mean temperature, degree days, daily temperature range
    precipitation, snowfall and snowdepth.  The user selects
    the starting and ending year.  Distributions are
    empirical rather than fitted to theoretical distributions.
    Separate values are calculated for each day of the year.
    The values for any given day are determined from the next
    1 to 30 days, starting on that day (a user-selectable
    quantity).  (The use of additional days increases the
    sample size, and smooths the day-to-day variations.)
    Furthermore, these values can be based on individual
    daily values, or on averages (or sums, for some elements)
    for the next (n) days.
    '''
    results = defaultdict(list)
    dates = kwargs['dates']
    start_year = int(dates[0][0:4])
    end_year = int(dates[-1][0:4])
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    el_type = kwargs['el_type'] # maxt, mint, avgt, dtr (daily temp range), hdd, cdd, gdd, pcpn, snow or snwd
    if kwargs['number_days_ahead']== 1:
        ia = 'I'
    else:
        ia = kwargs['ia']
    if kwargs['accumulate_over_season'] is not None:
        ncom = 1
    else:
        ncom = kwargs['number_days_ahead']
    #Loop over stations
    for i, stn in enumerate(kwargs['coop_station_ids']):
        elements = kwargs['elements']
        if el_type in ['dtr', 'hdd', 'cdd', 'gdd', 'avgt']:
            el_data = kwargs['data'][i]
            num_yrs = len(el_data[0])
        else:
            el_data = kwargs['data'][i][0]
            num_yrs = len(el_data)
        #el_data[el_idx][yr] ; if element_type is hdd, cdd, dtr or gdd: el_data[0] = maxt, el_data[1]=mint
        #Check for empty data
        if not any(el_data[j] for j in range(len(el_data))):
            results[i] = {}
            continue
        #for each yr in record and each dy of year find values for percentile caculation
        yr_doy_data = [[9999.0 for doy in range(366)] for yr in range(num_yrs)]
        accum = [9999.0 for yr in range(num_yrs)]
        results[i] = [[] for doy in range(366)] #results[i][doy] will have 21 entries: 15 thresholds and some html info
        for yr in range(num_yrs):
            for doy in range(366):
                val = None
                #check if we have to compute values from maxt, mint
                if el_type in ['dtr', 'hdd', 'cdd', 'gdd', 'avgt']:
                    dat_x = el_data[0][yr][doy]
                    dat_n = el_data[1][yr][doy]
                    val_x, flag_x = WRCCUtils.strip_data(dat_x)
                    val_n, flag_n = WRCCUtils.strip_data(dat_n)
                    if flag_x == 'M' or flag_n == 'M':
                        continue
                    try:
                        nval_x = int(val_x)
                        nval_n = int(val_n)
                    except:
                        continue

                    if el_type == 'dtr':
                        val = nval_x - nval_n
                    elif el_type == 'avgt':
                        val = (nval_x + nval_n)/2.0
                    elif el_type in ['hdd','cdd']:
                        ave = val = (nval_x + nval_n)/2.0
                        if el_type == 'hdd':
                            val = float(kwargs['base_temperature']) - ave
                        else:
                            val = ave - float(kwargs['base_temperature'])
                        if val < 0:
                            val = 0
                    elif el_type == 'gdd':
                        high = nval_x
                        low = nval_n
                        if high > kwargs['max_temperature']:
                            high = kwargs['max_temperature']
                        if low < kwargs['min_temperature']:
                            low = kwargs['min_temperature']
                        val = (high + low)/2.0 - float(kwargs['base_temperature'])
                elif el_type in ['snow', 'snwd', 'pcpn']: #Deal with T,S,A flags
                    dat = el_data[yr][doy]
                    val, flag = WRCCUtils.strip_data(dat)
                    if flag == 'T':
                        val = 0.001
                    if ia == 'a': #if kwargs['ia'] == 'i', S,A flags are treated as missing
                        if flag == 'S':
                            val+=2000.0
                        elif flag == 'A':
                            val+=3000.0
                    try:
                        float(val)
                    except:
                        continue
                else:
                    dat = el_data[yr][doy]
                    val, flag = WRCCUtils.strip_data(dat)
                    if flag == 'M':
                        continue
                    try:
                        float(val)
                    except:
                        continue
                yr_doy_data[yr][doy] = float(val)
        #Prepare method of looping, if seasoal accumulations are required
        monlo = 1
        monhi = 12
        if kwargs['accumulate_over_season'] is not None:
            end_yr = end_year - 1
            if el_type == 'hdd':
                monlo = 7
                nonhi = 18
            elif el_type in ['cdd', 'gdd']:
                monlo = 1
                monhi = 12
            else:
                monlo = kwargs['begin_month']
                monhi = monlo + 11
        #Loop over months and days
        for mondum in range(monlo,monhi + 1):
            mon = mondum
            if mon > 12: mon-=12
            #python indices start with 0 not 1!
            mon_idx = mon - 1
            for day_idx in range(mon_lens[mon_idx]):
                nda = day_idx +1
                nfrst = 0
                if kwargs['accumulate_over_season'] is not None and day_idx == 0 and mon == monlo:
                    nfrst = 1
                #Get day of typical year
                doy = WRCCUtils.compute_doy_leap(str(mon),str(day_idx+1)) - 1
                number = 0
                array={}
                #Loop over individual years
                for yr_idx in range(num_yrs):
                    nyeart = yr_idx
                    ndoyt = doy - 1 #will be added back shortly
                    leap = 0
                    valsum = 0
                    valcnt = 0
                    ndoym1 = doy - 1 # used to check for 'S' flags
                    nyearm = yr_idx
                    if ndoym1 == 60 and not WRCCUtils.is_leap_year(start_year+yr_idx):
                        ndoym1-=1
                    if ndoym1 < 0:
                        ndoym1+=366
                        nyearm-=1
                    nyrm = nyearm

                    #Loop over number of days to look ahead for each year
                    breaker = False
                    for icom in range(ncom):
                        ndoyt+=1
                        if ndoyt > 365:
                            ndoyt-=365
                            nyeart+=1
                        if nyeart > num_yrs -1: #finished with year loop
                            breaker = True
                            break

                        #Check to see if really a leap year if on Feb29
                        if ndoyt == 60:
                            if WRCCUtils.is_leap_year(start_year + nyeart):
                                leap =1
                            else:
                                #if start date (ndoy) id Feb 29, use only Feb 29's
                                if doy != 60:ndoyt+=1
                        nyrt = nyeart
                        val = yr_doy_data[nyrt][ndoyt]

                        if val > 9998.0: #skip this year
                            breaker = True
                            break

                        if ia == 'I':
                            if el_type in ['pcpn', 'snow', 'snwd', 'hdd', 'cdd', 'gdd']:
                                if val > 1999.0: #skip this year
                                    breaker = True
                                    break
                            number+=1
                            array[number - 1] = val
                        #number+=1
                        #array[number - 1] = val
                        if ia == 'A':
                            if el_type in ['pcpn', 'snow', 'snwd']:
                                if icom == 0:
                                    if yr_idx == 0 and doy == 1:
                                        if val > 1999.0: #skip this year if flag 'S' or 'A'
                                            breaker = True
                                            break
                                    else: #Check to see if prior was 'S', if so skip that year
                                        valm = yr_doy_data[nyrm][ndoym1]
                                        if valm > 1999.0 and valm < 2999.0:
                                            breaker = True
                                            break
                                if icom == ncom - 1: #end of days_ahead loop
                                    #Check if last day is 'S', if so skip that year
                                    if val > 1999.0 and val < 2999.0:
                                        breaker = True
                                        break
                                if val > 2999.0:val-=3000.0
                                if val > 1999.0:val-=2000.0

                            if kwargs['threshold'] is not None:
                                if kwargs['threshold_ab'] == 'a':
                                    if val > kwargs['threshold']:
                                        val = 1
                                    else:
                                        val = 0
                                else:
                                    if val < kwargs['threshold']:
                                        val = 1
                                    else:
                                        val = 0
                            valsum+=val
                            valcnt+=1
                    #End of icom loop
                    #Check if we chould skip this year
                    if breaker:
                        continue

                    if ia == 'A':
                        if el_type in ['maxt', 'mint', 'dtr', 'avgt'] and valcnt >0:
                            valsum = valsum/valcnt
                        number+=1
                        array[number-1] =  valsum

                    if kwargs['accumulate_over_season'] is not None:
                        if nfrst == 1: accum[yr_idx] = 0.0
                        if accum[yr_idx] > 9998.0:continue
                        accum[yr_idx]+=val
                #End of year loop
                if kwargs['accumulate_over_season'] is not None:
                    number = 0
                    for acc_idx in range(len(accum)):
                        if accum[acc_idx] > 9998.0:
                            continue
                        number+=1
                        array[number]=accum[acc_idx]
                out = [9999.0 for k in range(17)] # low, high and 15 percentages
                if number >= 10:
                    pctile, sort = WRCCUtils.pctil('Sodpct', array, number, 10)
                    out[2] = pctile[0]
                    out[3] = pctile[1]
                    out[5] = pctile[2]
                    out[7] = pctile[3]
                    out[8] = pctile[4]
                    out[9] = pctile[5]
                    out[11] = pctile[6]
                    out[13] = pctile[7]
                    out[14] = pctile[8]
                if number >= 20:
                    pctile, sort = WRCCUtils.pctil('Sodpct', array, number, 20)
                    out[1] = pctile[0]
                    out[15] = pctile[18]
                if number >= 4:
                    pctile, sort = WRCCUtils.pctil('Sodpct', array, number, 4)
                    out[4] = pctile[0]
                    out[8] = pctile[1]
                    out[12] = pctile[2]
                if number >= 3:
                    pctile, sort = WRCCUtils.pctil('Sodpct', array, number, 3)
                    out[6] = pctile[0]
                    out[10] =  pctile[1]
                    out[0] = sort[0]
                    out[16] = sort[number-1]

                results[i][doy] = [str(mon), str(day_idx + 1), str(ncom), str(ia), str(number)]
                for pct_idx,pct in enumerate(out):
                    if pct >= 9998.0:
                        results[i][doy].append('*')
                        continue

                    if el_type == 'pcpn':
                        if pct > 0.0 and pct < 0.00499:
                            results[i][doy].append('T')
                        else:
                            results[i][doy].append('%.2f' % pct)
                    else:
                        results[i][doy].append('%.1f' % pct)
        #Resort data if monlo !=1
        if monlo != 1:
            doy_start = WRCCUtils.compute_doy_leap(str(monlo), '01')
            doy_start-=1
            results_temp = results[i][doy_start:]
            for doy in range(doy_start):
                results_temp.append(results[i][doy])
            results[i] = results_temp
    return results

def Sodrun(**kwargs):
    '''
    Sodrun and Sodrunr
    THESE PROGRAMS FIND ALL RUNS OF CONSECUTIVE DAYS WHERE REQUESTED THRESHOLD
    CONDITIONS ARE MET. SODRUNR CONSIDERS 2 DAYS A TIME. OTHERWISE, THE TWO
    PROGRAMS ARE IDENTICAL.
    '''
    def write_str_missing(days, nxt):
        print_str = '%5s DAYS MISSING.  NEXT DATE %s' % (str(days), str(nxt))
        return print_str
    def write_str_data(start, end, days, el, op, thresh):
        print_str = ' %s %2s %5s START : %s END : %s %7s DAYS' % (el, op, str(thresh), str(start), str(end), str(days))
        return print_str
    def write_str_thresh(days, nxt):
        print_str = '%5s DAYS WHERE THRESHOLD NOT MET.  NEXT DATE %s' % (str(days), str(nxt))
        return print_str
    def write_str_range(l):
        print_str1 = '%s %s %s mx/mn day 1 = %6s %6s mx/min day 2 = %6s %6s' %(l[0],l[1],l[2], l[3], l[4], l[5], l[6])
        print_str2 = 'max2 - min1 = %6s min2 - max1 = %6s ======> max change = %6s' %(l[7], l[8], l[9])
        return '\n'.join([print_str1, print_str2])
    def convert_date(date):
        str_date = ''.join(date.split('-'))
        return str_date
    def update_run_cnt(run_cnt, day_cnt):
        if day_cnt in run_cnt:
            run_cnt[day_cnt]+=1
        else:
            run_cnt[day_cnt]=1

    results = defaultdict(list)
    coop_station_ids = kwargs['coop_station_ids']
    elements = kwargs['elements']
    dates = kwargs['dates']
    jd_start = WRCCUtils.JulDay(int(dates[0][0:4]), int(dates[0][4:6]), int(dates[0][6:8]))#Julian day of start date
    jd_end = WRCCUtils.JulDay(int(dates[-1][0:4]), int(dates[-1][4:6]), int(dates[-1][6:8]))#Julian day of end date
    app_name = kwargs['app_name']
    op = kwargs['op']
    if elements == ['maxt', 'mint']:
        el = 'range'
    else:
        el = elements[0]
    thresh = kwargs['thresh']
    min_run = kwargs['minimum_run']
    verbose = kwargs['verbose']
    #Loop over stations
    for i, stn in enumerate(coop_station_ids):
        print "STATION:" + coop_station_ids[i]
        results[i] = []
        stn_data = kwargs['data'][i]
        #first format data to include dates
        if not stn_data:
            continue
        for k, date in enumerate(dates):
            stn_data[k].insert(0,date)
        #If el is 'range', comput range
        if el == 'range':
            stn_data_new = []
            stn_data_range = []
            for idx, val_pair in enumerate(stn_data):
                if app_name == 'Sodrunr':
                    idif1 = ' '
                    idif2 = ' '
                    imax2 = str(val_pair[1])
                    imin2 = str(val_pair[2])
                    if idx == 0:
                        imax1 = imax2
                        imin1 = imin2
                    else:
                        imax1 = str(stn_data[idx -1][1])
                        imin1 = str(stn_data[idx -1][2])
                    try:
                        idif1 = abs(int(imax2) - int(imin1))
                        try:
                            idif2 = abs(int(imax1) - int(imin2))
                            mmax = max(idif1, idif2)
                            if idif2 > idif1:
                                mmax = -mmax
                        except:
                            mmax = idif1
                    except:
                        try:
                            idif2 = abs(int(imax2) - int(imin2))
                            mmax = -idif2
                        except:
                            mmax = '**'
                    if mmax == '**':
                        stn_data_new.append([stn_data[idx][0], 'M'])
                    else:
                        stn_data_new.append([stn_data[idx][0], str(mmax)])

                    stn_data_range.append([val_pair[0][0:4], val_pair[0][5:7], val_pair[0][8:10], imax2, \
                    imin2,imax1, imin1, str(idif1), str(idif2), str(mmax)])
                else:#Sodrun
                    flag_x = val_pair[1][-1]
                    flag_n = val_pair[2][-1]
                    if flag_x in ['M', '', ' '] or flag_n in ['M', '', ' ']:
                        stn_data_new.append([stn_data[idx][0], 'M'])
                    else:
                        try:
                            rg = int(val_pair[1]) - int(val_pair[2])
                        except:
                            rg = 'M'
                        stn_data_new.append([stn_data[idx][0], str(rg)])
            stn_data = stn_data_new
        #Initialize parameters
        day_cnt = 0
        run_cnt = {} #run_cnt[#days] = #runs of #days length
        flag = 0  #flag are 'M', 'S', 'A', 'T' (Acis flags) or 'D', '0'(internal flag)
        run_start = 0 # start date of run
        run_end = 0   #end date of run
        days_missing = 0
        days_not_thresh = 0
        gap = False
        #Loop over [date, value] pairs of input data
        ############################################
        for idx, date_val in enumerate(stn_data):
            #Compute Julian day for current data and check for gap with previous data
            #########################################################################
            if idx == 0:
                jd_old = jd_start
            else:
                jd_old = jd
            jd = WRCCUtils.JulDay(int(date_val[0][0:4]), int(date_val[0][4:6]), int(date_val[0][6:8]))
            gap_days = jd - jd_old
            if idx == 0 and gap_days >0: #found gap between user given start data and  first data point
                print_str =  write_str_missing(str(gap_days), convert_date(date_val[0]))
                results[i].append(print_str)
            elif gap_days >1: #gap between two successive data entries
                days_missing += gap_days
                gap = True
            else:
                gap = False
            #Take care of gaps in data
            ######################################################
            if gap and day_cnt !=0: # we are in middle of run and need to stop it
                run_end = stn_data[idx-1][0]
                if day_cnt >= min_run:
                    update_run_cnt(run_cnt, day_cnt)
                    if el == 'range':
                        print_str = write_str_range(stn_data_range[idx-1])
                        results[i].append(print_str)
                    print_str = write_str_data(convert_date(run_start), convert_date(run_end), str(day_cnt), el, op, thresh)
                    results[i].append(print_str)
                    if days_missing !=0:
                        print_str = write_str_missing(str(days_missing), convert_date(date_val[0]))
                        results[i].append(print_str)
                day_cnt = 0
                flag = 0
                days_missing = 0
            elif gap and days_missing !=0:
                days_missing+=gap
            elif gap and days_not_thresh !=0:
                if verbose:
                    print_str = write_str_thresh(str(days_not_thresh), convert_date(date_val[0]))
                    results[i].append(print_str)
            #Check internal flags
            #####################
            if flag == 0 and day_cnt == 0: #Beginning of a run
                run_start = date_val[0]
                run_start_idx = idx
                #check for missing days
                if days_missing != 0:
                    flag = date_val[1][-1]
                    if not flag in ['M', 'S', 'A', 'T', ' ']:
                        print_str = write_str_missing(str(days_missing), convert_date(date_val[0]))
                        results[i].append(print_str)
                        days_missing = 0
            elif flag == 0 and day_cnt != 0: #Middle of run
                day_cnt+=1
                continue
            elif flag == 'D' and day_cnt != 0: #End of run
                if day_cnt >= min_run:
                    update_run_cnt(run_cnt, day_cnt)
                    print_str = write_str_data(convert_date(run_start), convert_date(run_end), str(day_cnt), el, op, thresh)
                    results[i].append(print_str)
                day_cnt = 0
                flag = 0

            #Check data flags
            ##############################
            flag = date_val[1][-1]
            if flag in ['T', 'A', 'S', 'M', ' ']:
                if flag in ['M', ' ']:
                    days_missing+=1
                if day_cnt != 0 and day_cnt >= min_run: #Run ends here
                    run_end = date_val[0]
                    update_run_cnt(run_cnt, day_cnt)
                    print_str = write_str_data(convert_date(run_start), convert_date(run_end), str(day_cnt), el, op, thresh)
                    results[i].append(print_str)
                if days_not_thresh != 0:
                    if verbose:
                        print_str = write_str_thresh(str(days_not_thresh), convert_date(date_val[0]))
                        results[i].append(print_str)
                    days_not_thresh = 0
                if flag in ['T', 'A', 'S']:
                    days_not_thresh+=1
                day_cnt = 0
                continue

            #Check for invalid flag
            #######################
            if not flag.isdigit():
                print 'found invalid flag %s' % str(flag)
                sys.exit(1)

            #Make sure data can be converted to float
            #########################################
            try:
                float(date_val[1])
            except ValueError:
                print '%s cannot be converted to float' % str(date_val[1])
                sys.exit(1)
            #Data is sound and we can check threshold condition
            ###################################################
            if el in ['maxt', 'mint', 'snwd', 'range']:
                data = int(float(date_val[1]))
            elif el == 'snow':
                data = int(float(date_val[1]) * 10)
            elif el == 'pcpn':
                data = int(float(date_val[1]) * 100)

            if (op == '>' and data > thresh) or (op == '<' and data < thresh) \
            or (op == '=' and data == thresh):
                if el == 'range':
                        print_str = write_str_range(stn_data_range[idx])
                        results[i].append(print_str)
                if day_cnt == 0: #Start of run
                    run_start = date_val[0]
                    run_start_idx = idx
                    if days_missing != 0:
                        print_str = write_str_missing(str(days_missing), convert_date(date_val[0]))
                        results[i].append(print_str)
                        days_missing = 0
                    if days_not_thresh != 0:
                        if verbose:
                            print_str = write_str_thresh(str(days_not_thresh), convert_date(date_val[0]))
                            results[i].append(print_str)
                        days_not_thresh = 0
                day_cnt+=1
            else: #Run ends here
                days_not_thresh+=1
                run_end = date_val[0]
                flag = 'D'

        #Check if we are in middle of run at end of data
        ################################################
        if flag == 0 or flag.isdigit(): #last value is good
            if day_cnt !=0 and day_cnt >= min_run:
                update_run_cnt(run_cnt, day_cnt)
                if el == 'range':
                    print_str = write_str_range(stn_data_range[idx])
                    results[i].append(print_str)
                print_str = write_str_data(convert_date(run_start), convert_date(run_end), str(day_cnt), el, op, thresh)
                results[i].append(print_str)
            elif days_missing != 0:
                print_str = write_str_missing(str(days_missing), convert_date(date_val[0]))
                results[i].append(print_str)
            elif days_not_thresh != 0:
                if verbose:
                    print_str = write_str_thresh(str(days_not_thresh), convert_date(date_val[0]))
                    results[i].append(print_str)
        elif flag == 'M': #last value is mising
            if days_not_thresh != 0:
                if verbose:
                    print_str = write_str_thresh(str(days_not_thresh), convert_date(date_val[0]))
                    results[i].append(print_str)
        elif flag == 'D': #last value is below threshold
            if day_cnt !=0 and day_cnt >= min_run:
                update_run_cnt(run_cnt, day_cnt)
                if el == 'range':
                    print_str = write_str_range(stn_data_range[run_start_idx])
                    results[i].append(print_str)
                print_str = write_str_data(convert_date(run_start), convert_date(run_end), str(day_cnt), el, op, thresh)
                results[i].append(print_str)
            if days_not_thresh != 0:
                if verbose:
                    print_str = write_str_thresh(str(days_not_thresh), convert_date(date_val[0]))
                    results[i].append(print_str)
        #Check for gap between last data point and run_end given by user
        #################################################################
        if jd_end - jd >0:
            days_missing+= jd_end - jd

        if days_missing != 0:
            print_str = write_str_missing(str(days_missing), convert_date(stn_data[-1][0]))
            results[i].append(print_str)

        #Summarize runs
        ###############
        results[i].append('RUN LENGTH  NUMBER')
        key_list =  sorted(run_cnt)
        key_list.sort()
        for key in key_list:
            results[i].append('%10s%8s' % (key, run_cnt[key]))
    return results

def Sodlist(**kwargs):
    '''
    Summary of the day data lister
    '''
    results = defaultdict(list)
    coop_station_ids = kwargs['coop_station_ids']
    elements = kwargs['elements']
    dates = kwargs['dates']
    #Loop over stations
    for i, stn in enumerate(coop_station_ids):
        stn_data = kwargs['data'][i]
        #first format data to include dates
        for k, date in enumerate(dates):
            for j, el in enumerate(elements):
                stn_data[k][j].insert(0,date)
        results[i]=stn_data
    return results

def Sodlist_new(kwargs):
    results = [];
    '''
    Summary of the day data lister
    '''
    #Find element list
    if kwargs['include_tobs_evap']:
        vx_list = [4,10,11,1,2,3,7]
        el_list = ['pcpn','snow','snwd','maxt','mint','obst','evap']
    else:
        vx_list = [4,10,11,1,2]
        el_list = ['pcpn','snow','snwd','maxt','mint']
    #set up data request parameters
    params = {
        'sdate':kwargs['start_date'],
        'edate':kwargs['end_date'],
        'meta':'name,state,sids,ll,elev,uid,county,climdiv,valid_daterange'
    }
    if 'station_id' in kwargs.keys():params['sids'] = kwargs['station_id']
    if 'station_ids' in kwargs.keys():params['sids'] = kwargs['station_ids']
    if 'county' in kwargs.keys():params['county'] = kwargs['county']
    if 'climate_division' in kwargs.keys():params['climdiv'] = kwargs['climate_division']
    if 'county_warning_area' in kwargs.keys():params['cwa'] = kwargs['county_warning_area']
    if 'basin' in kwargs.keys():params['basin'] = kwargs['basin']
    if 'bbox' in kwargs.keys():params['bbox'] = kwargs['bounding_box']
    elems = []
    for vx in vx_list:
        elem = {
            'vX':vx,
            'add':'f,t'
        }
        elems.append(elem)
    params['elems'] = elems
    #Get data
    request = AcisWS.MultiStnData(params)
    #Sanity check
    if not request:
        return results
    if 'error' in request.keys():
        return [request['error']]
    if not 'data' in request.keys():
        return ['No data found for this station selection!']
    #Find Dates: Multi station calls don't return dates!
    dates = WRCCUtils.get_dates(kwargs['start_date'],kwargs['end_date'],'Sodlist')
    #Find indices for windowed data
    start_indices, end_indices = WRCCUtils.get_windowed_indices(dates, kwargs['start_window'], kwargs['end_window'])
    #format data and add dates
    for stn_data in request['data']:
        stn_dict = {'meta':{}, 'data':[]}
        stn_id = ' '
        if 'meta' in stn_data.keys():
            stn_dict['meta'] =  WRCCUtils.format_station_meta(stn_data['meta'])
            if 'sids' in stn_dict['meta'].keys():
                stn_id = stn_dict['meta']['sids'][0][0]
        if 'data'in stn_data.keys() and isinstance(stn_data['data'], list):
            #stn_dict['data'] = stn_data['data']
            for idx_idx, start_idx in enumerate(start_indices):
                idx = start_idx
                end = end_indices[idx_idx]
                while idx <= end:
                    #fix me: what's tobs?? different for each element
                    dat = [stn_id + dates[idx]]
                    for el_idx, vX in enumerate(vx_list):
                        data_flag_tobs = stn_data['data'][idx][el_idx]
                        #wrcc_data = [data_val, flag1, flag2, tobs]
                        wrcc_data = WRCCUtils.format_sodlist_data(data_flag_tobs)
                        if el_idx ==0:
                            #add hour to data
                            dat[0]+=wrcc_data[-1]
                        dat.append(wrcc_data[0])
                        dat.append(wrcc_data[1])
                        dat.append(wrcc_data[2])
                    stn_dict['data'].append(dat)
                    idx+=1
        results.append(stn_dict)
    return results

def Sodmonline(**kwargs):
    '''
    THIS PROGRAM WAS WRITTEN SPECIFICALLY FOR JOHN HANSON AT PGE, AND
    GIVES THE DAILY AVERAGE TEMPERATURE FOR SPECIFIED STATIONS
    THE FIRST YEARS ARE FROM THE SOD DATA BASE AND THE LATER YEARS
    MAY BE FROM THE MONTHLY NCDC TELEPHONE CALL FILES
    '''
    results = defaultdict(list)
    coop_station_ids = kwargs['coop_station_ids']
    elements = kwargs['elements']
    dates = kwargs['dates']
    #Loop over stations
    for i, stn in enumerate(coop_station_ids):
        stn_data = kwargs['data'][i]
        #first format data to include dates
        for k, date in enumerate(dates):
            stn_data[k].insert(0,date)
        results[i]=stn_data
    return results

def Sodsumm(**kwargs):
    '''
    THIS PROGRAM SUMMARIZES VARIOUS CLIMATIC DATA IN A FORMAT IDENTICAL WITH
    THAT OF MICIS - THE MIDWEST CLIMATE INFORMATION SYSTEM
    '''
    elements = kwargs['elements']
    dates = kwargs['dates']
    tables = ['temp', 'prsn', 'hdd', 'cdd', 'gdd', 'corn']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    time_cats = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Ann', 'Win', 'Spr', 'Sum', 'Aut']
    #time_cats = ['Ja', 'Fe', 'Ma', 'Ap', 'Ma', 'Jn', 'Jl', 'Au', 'Se', 'Oc', 'No', 'De']
    time_cats_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 366, 91, 92, 92, 91]
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #results[i][table]
    results = defaultdict(dict)
    #Loop over stations
    for i, stn in enumerate(kwargs['coop_station_ids']):
        #Check for empty data
        flag_empty = False
        for el_data in kwargs['data'][i]:
            if not el_data:
                flag_empty = True
                break
        if flag_empty:
            results[i] = {}
            continue
        #Initialize results dictionaries
        for table in tables:
            results[i][table] = []
            if table == 'temp':
                results[i]['temp'].append(['Time','Max', 'Min', 'Mean', 'High', 'Date', 'Low', 'Date', 'High', 'Yr', 'Low', 'Yr', '>=90', '<=32', '<=32', '<=0'])
            elif table == 'prsn':
                results[i]['prsn'].append(['Time','Mean', 'High', 'Yr', 'Low', 'Yr', '1-Day Max', 'Date', '>=0.01', '>=0.10', '>=0.50', '>=1.00', 'Mean', 'High', 'Yr'])
            elif table in ['hdd', 'cdd']:
                results[i][table].append(['Base', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Ann'])
            elif table in ['gdd', 'corn']:
                results[i][table].append(['Base', 'M/S','Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Ann'])
        num_yrs = len(kwargs['data'][i])
        start_year = dates[0][0:4]
        end_year = dates[-1][0:4]
        el_data = {}
        el_dates = {}
        base_list = {}
        val_list_d =  defaultdict(list)
        #Degree day base tables
        base_list['hdd'] = [65, 60, 57, 55,50]
        base_list['cdd'] = [55, 57, 60, 65, 70]
        base_list['gdd'] = [40, 45, 50, 55, 60]
        base_list['corn'] = [50]
        val_list_d['hdd'] = [[65], [60], [57], [55], [50]]
        val_list_d['cdd'] = [[55], [57], [60], [65], [70]]
        for tbl in ['gdd', 'corn']:
            val_list_d[tbl]=[]
            for base in base_list[tbl]:
                for ch in ['M', 'S']:
                    val_list_d[tbl].append([base, ch])

        #Sort data
        dd_acc = 0 #for degree days sum
        x_miss = defaultdict(dict) #counts missing days: x_miss[cat_idx][element]=[miss_yr1, miss_yr2, ..., miss_yrlast]

        #Loop over time categories and compute stats
        for cat_idx, cat in enumerate(time_cats):
            #Find indices for each time category
            x_miss[cat_idx] = {}
            if cat_idx < 12: #months
                if cat_idx == 0:
                    idx_start = 0
                    idx_end = 31
                else:
                    idx_start = sum(mon_lens[idx] for idx in range(cat_idx))
                    idx_end = idx_start + mon_lens[cat_idx]
            #Note: all indices computed for leap year
            #since we query ACIS bwith group_by=year --> 366 data entries per year
            #Leap years are taken car of below in analysis code
            elif cat_idx == 12: #Annual
                idx_start = 0
                idx_end = 366
            elif cat_idx == 13: #Winter
                idx_start = 336
                idx_end = 61
            elif cat_idx == 14: #Spring
                idx_start = 61
                idx_end = 153
            elif cat_idx == 15: #Summer
                idx_start = 153
                idx_end = 245
            elif cat_idx == 16: # Fall
                idx_start = 245
                idx_end = 336
            #Read in data, for ease of statistical computation, data and dates for each category are
            #ordered chronolocically in two indexed list: el_data[element], el_dates[element].
            for el_idx, element in enumerate(elements):
                el_data[element] = []
                el_dates[element] = []
                x_miss[cat_idx][element] = []
                current_year = int(start_year) - 1
                for yr in range(num_yrs):
                    current_year+=1
                    flag = False
                    #Winter jumps year
                    if cat_idx == 13:
                        for idx in range(idx_start, 366):
                            el_data[element].append(kwargs['data'][i][yr][el_idx][idx])
                            date_idx  = yr * 366 + idx
                            el_dates[element].append(kwargs['dates'][date_idx])
                        if yr < num_yrs - 1:
                            for idx in range(0,idx_end):
                                el_data[element].append(kwargs['data'][i][yr+1][el_idx][idx])
                                date_idx  = yr+1 * 366 + idx
                                el_dates[element].append(kwargs['dates'][date_idx])
                        mon_l = [11,0,1]
                        for ct in mon_l:
                            if x_miss[ct][element][yr] > kwargs['max_missing_days']:
                                flag = True
                                break
                        if flag:
                            #found a month with too many missing days
                            x_miss[cat_idx][element].append(int(kwargs['max_missing_days']) + 1)
                        else:
                            x_miss[cat_idx][element].append(0)
                    else:
                        data_list = []
                        for idx in range(idx_start, idx_end):
                            data_list.append(kwargs['data'][i][yr][el_idx][idx])
                            el_data[element].append(kwargs['data'][i][yr][el_idx][idx])
                            date_idx  = yr * 366 + idx
                            el_dates[element].append(kwargs['dates'][date_idx])
                        #Count missing days for all categories
                        if cat_idx < 12:
                            days_miss = len([dat for dat in data_list if dat == 'M'])
                            x_miss[cat_idx][element].append(days_miss)
                        else:
                            if cat_idx == 12:mon_l = range(0,12)
                            if cat_idx == 13:mon_l = [10,11,0]
                            if cat_idx == 14:mon_l = [1,2,3]
                            if cat_idx == 15:mon_l = [4,5,6]
                            if cat_idx == 16:mon_l = [7,8,9]
                            for ct in mon_l:
                                if x_miss[ct][element][yr] > kwargs['max_missing_days']:
                                    flag = True
                                    break
                            if flag:
                                #found a month with too many missing days
                                x_miss[cat_idx][element].append(int(kwargs['max_missing_days']) + 1)
                            else:
                                x_miss[cat_idx][element].append(0)
                #strip data of flags and convert unicode to floats for stats calculations
                for idx, dat in enumerate(el_data[element]):
                    val, flag = WRCCUtils.strip_data(dat)
                    #take care of flags: missing data, s,a flags data are ignored, traces count as 0.0
                    # trace behavior needs checking
                    if val == 'M' or val == ' ' or val == '':
                        el_data[element][idx] = -9999.0
                    if flag == 'M':
                        el_data[element][idx] = -9999.0
                    elif flag == 'S':
                        #el_data_Mon[element][idx] = 245
                        el_data[element][idx] = 0.0
                    elif flag == 'A':
                        #el_data_Mon[element][idx] = float(val) +100
                        el_data[element][idx] = float(val)
                    elif flag == 'T':
                        el_data[element][idx] = 0.0
                    else:
                        el_data[element][idx] = float(val)

            #Compute monthly Stats for the different tables

            #1) Temperature Stats
            if kwargs['el_type'] == 'temp' or kwargs['el_type'] == 'both' or kwargs['el_type'] == 'all':
                val_list = [cat]
                #1) Averages and Daily extremes
                max_max = -9999.0
                min_min = 9999.0
                date_min ='00000000'
                date_max = '00000000'
                for el in ['maxt', 'mint', 'avgt']:
                    #Omit data yrs for month where max_missing day threshold is not met
                    data_list = []
                    dates_list = []
                    #keep track of which years to use for ann,sp,su,au,wi calculations
                    current_year = int(start_year) -1
                    for yr in range(num_yrs):
                        if x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                            continue
                        current_year+=1
                        idx_start = time_cats_lens[cat_idx] * yr
                        if cat_idx == 1 and not WRCCUtils.is_leap_year(current_year):
                            cat_l = 28
                        elif cat_idx == 13 and not WRCCUtils.is_leap_year(current_year):
                            cat_l = 90
                        else:
                            cat_l = time_cats_lens[cat_idx]
                        idx_end = idx_start + cat_l
                        data_list.extend(el_data[el][idx_start:idx_end])
                        dates_list.extend(el_dates[el][idx_start:idx_end])
                        '''
                        #Delete Feb 29 if not leap year from annual
                        if cat_idx == 12 and not WRCCUtils.is_leap_year(current_year):
                            del data_list[idx_start + 59]
                            del dates_list[idx_start + 59]
                        '''
                    #Statistics
                    sm = 0
                    cnt = 0
                    for idx, dat in enumerate(data_list):
                        if abs(dat + 9999.0) < 0.05:
                            continue
                        if el == 'maxt' and dat > max_max:
                            max_max = dat
                            date_max = dates_list[idx]
                        if el == 'mint' and dat < min_min:
                            min_min = dat
                            date_min = dates_list[idx]
                        sm+=dat
                        cnt+=1
                    if cnt !=0:
                        ave = round(sm/cnt,2)
                    else:
                        ave = 0.0
                    val_list.append('%.1f' % ave)

                val_list.append(int(round(max_max,0)))
                if cat_idx >=12:
                    val_list.append('%s%s%s' % (date_max[0:4],date_max[4:6],date_max[6:8]))
                else:
                    val_list.append('%s/%s' % (date_max[6:8], date_max[0:4]))
                val_list.append(int(round(min_min,0)))
                if cat_idx >=12:
                    val_list.append('%s%s%s' % (date_min[0:4],date_min[4:6],date_min[6:8]))
                else:
                    val_list.append('%s/%s' % (date_min[6:8], date_min[0:4]))

                #3)  Mean Extremes (over yrs)
                means_yr=[]
                yr_list = []
                for yr in range(num_yrs):
                    #Omit data yrs where month max_missing day threshold is not met
                    if x_miss[cat_idx]['avgt'][yr] > kwargs['max_missing_days']:
                        continue
                    idx_start = time_cats_lens[cat_idx] * yr
                    #idx_end = idx_start + time_cats_lens[cat_idx]
                    idx_end = idx_start + cat_l
                    yr_dat = el_data['avgt'][idx_start:idx_end]
                    sm = 0
                    cnt = 0
                    for yr_dat_idx, dat in enumerate(yr_dat):
                        if abs(dat + 9999.0) < 0.05:
                            continue
                        sm+=dat
                        cnt+=1
                    if cnt!=0:
                        means_yr.append(round(sm/cnt,2))
                        yr_list.append(str(int(start_year) + yr))
                if means_yr:
                    ave_low = round(min(means_yr),2)
                    ave_high = round(max(means_yr),2)
                    yr_idx_low = means_yr.index(ave_low)
                    yr_idx_high = means_yr.index(ave_high)
                    yr_low = yr_list[yr_idx_low]
                    yr_high = yr_list[yr_idx_high]
                    #yr_low = str(int(start_year) + yr_idx_low)
                    #yr_high = str(int(start_year) + yr_idx_high)
                else:
                    ave_low = 99.0
                    ave_high = -99.0
                    yr_low = '****'
                    yr_high = '****'
                val_list.append('%.1f' %ave_high)
                val_list.append(yr_high)
                val_list.append('%.1f' %ave_low)
                val_list.append(yr_low)

                #4) Threshold days for maxt, mint
                for el in ['maxt', 'mint']:
                    if el == 'maxt':
                        threshs = ['90', '32']
                    else:
                        threshs = ['32', '0']
                    for thresh in threshs:
                        cnt_days = []
                        for yr in range(num_yrs):
                            #Omit data yrs where max_missing day threshold is not met
                            if x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                                continue
                            idx_start = time_cats_lens[cat_idx]*yr
                            #idx_end = idx_start + time_cats_lens[cat_idx]
                            idx_end = idx_start + cat_l
                            yr_dat = numpy.array(el_data[el][idx_start:idx_end])
                            if thresh == '90':
                                yr_dat_thresh = numpy.where((yr_dat >= 90) & (abs(yr_dat + 9999.0) >= 0.05))
                            else:
                                yr_dat_thresh = numpy.where((yr_dat <= float(thresh)) & (abs(yr_dat + 9999.0) >= 0.05))
                            cnt_days.append(len(yr_dat_thresh[0]))
                        if cnt_days:
                            try:
                                val_list.append('%.1f' % round(numpy.mean(cnt_days),2))
                            except:
                                val_list.append('***')
                        else:
                            val_list.append('***')
                results[i]['temp'].append(val_list)

            #2) Precip/Snow Stats
            if kwargs['el_type'] == 'prsn' or kwargs['el_type'] == 'both' or kwargs['el_type'] == 'all':
                val_list = [cat]
                #1) Total Precipitation
                for el in ['pcpn', 'snow']:
                    sum_yr=[]
                    yr_list = []
                    current_year = int(start_year) -1
                    for yr in range(num_yrs):
                        current_year+=1
                        #Omit data yrs where max_missing day threshold is not met
                        if x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                            continue
                        if cat_idx == 1 and not WRCCUtils.is_leap_year(current_year):
                            cat_l = 28
                        elif cat_idx == 13 and not WRCCUtils.is_leap_year(current_year):
                            cat_l =  90
                        else:
                            cat_l = time_cats_lens[cat_idx]

                        #idx_start = cat_l * yr
                        idx_start = time_cats_lens[cat_idx] * yr
                        idx_end = idx_start + cat_l
                        yr_dat = el_data[el][idx_start:idx_end]
                        sm = 0
                        for yr_dat_idx, dat in enumerate(yr_dat):
                            #Omit Feb 29 if leap year
                            if cat_idx == 12 and not WRCCUtils.is_leap_year(current_year) and yr_dat_idx == 59:
                                continue
                            if abs(dat + 9999.0) >= 0.05:
                                sm+=dat
                        sum_yr.append(sm)
                        yr_list.append(str(int(start_year) + yr))
                    try:
                        if el == 'snow':
                            val_list.append('%.1f' % round(numpy.mean(sum_yr),2))
                        else:
                            val_list.append('%.2f' % round(numpy.mean(sum_yr),2))
                    except:
                        val_list.append('****')
                    if sum_yr:
                        prec_high = max(sum_yr)
                        yr_idx_high = sum_yr.index(prec_high)
                        yr_high = yr_list[yr_idx_high]
                        if el == 'pcpn':
                            prec_low = min(sum_yr)
                            yr_idx_low = sum_yr.index(prec_low)
                            yr_low = yr_list[yr_idx_low]
                    else:
                        prec_high = -99.0
                        yr_high = '****'
                        if el == 'pcpn':
                            prec_low = 99.0
                            yr_low = '****'
                    if el == 'snow':
                        val_list.append('%.1f' %round(prec_high,2))
                    else:
                        val_list.append('%.2f' %round(prec_high,2))
                    val_list.append(yr_high)
                    if el == 'pcpn':
                        if el == 'snow':
                            val_list.append('%.1f' %round(prec_low,2))
                        else:
                            val_list.append('%.2f' %round(prec_low,2))
                        val_list.append(yr_low)
                        #2) Daily Prec max
                        prec_max = max(el_data['pcpn'])
                        idx_max = el_data['pcpn'].index(prec_max)
                        date_max = el_dates['pcpn'][idx_max]
                        val_list.append('%.2f' %round(prec_max,2))
                        if cat_idx <12:
                            val_list.append('%s/%s' % (date_max[6:8], date_max[0:4]))
                        else:
                            val_list.append(date_max)

                #3) Precip Thresholds
                threshs = [0.01, 0.10, 0.50, 1.00]
                for t_idx, thresh in enumerate(threshs):
                        cnt_days = []

                        for yr in range(num_yrs):
                            #Omit data yrs where max_missing day threshold is not met
                            if x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                                continue
                            idx_start = time_cats_lens[cat_idx]*yr
                            #idx_end = idx_start + time_cats_lens[cat_idx]
                            idx_end = idx_start + cat_l
                            yr_dat = numpy.array(el_data['pcpn'][idx_start:idx_end])
                            yr_dat_thresh = numpy.where(yr_dat >= thresh)
                            cnt_days.append(len(yr_dat_thresh[0]))
                        try:
                            val_list.insert(8+t_idx, '%d' % int(round(numpy.mean(cnt_days),0)))
                            #val_list.append('%d' % int(round(numpy.mean(cnt_days))))
                        except:
                            val_list.insert(8+t_idx,'0')
                            #val_list.append('0')
                results[i]['prsn'].append(val_list)
            #3) Degree Days tables
            if kwargs['el_type'] in ['hc', 'g', 'all', 'gdd', 'hdd', 'cdd', 'corn']:
                if kwargs['el_type'] == 'hc':
                    table_list = ['hdd', 'cdd']
                elif kwargs['el_type'] == 'g':
                    table_list = ['gdd', 'corn']
                elif kwargs['el_type'] == 'gdd':
                    table_list = ['gdd']
                elif kwargs['el_type'] == 'hdd':
                    table_list = ['hdd']
                elif kwargs['el_type'] == 'cdd':
                    table_list = ['cdd']
                elif kwargs['el_type'] == 'corn':
                    table_list = ['corn']
                else:
                    table_list = ['hdd', 'cdd', 'gdd', 'corn']
                if cat_idx >=13:
                    continue


                for table in table_list:
                    for base_idx, base in enumerate(base_list[table]):
                        dd_acc = 0
                        yr_dat = []
                        current_year = int(start_year) -1
                        for yr in range(num_yrs):
                            current_year+=1
                            if cat_idx == 12:
                                if x_miss[cat_idx]['maxt'][yr] > kwargs['max_missing_days'] or x_miss[cat_idx]['mint'][yr] > kwargs['max_missing_days']:
                                    continue
                            #Take care of leap years
                            if cat_idx == 1 and not WRCCUtils.is_leap_year(current_year):
                                cat_l = 28
                            elif cat_idx == 13 and not WRCCUtils.is_leap_year(current_year):
                                cat_l =  90
                            else:
                                cat_l = time_cats_lens[cat_idx]
                            #idx_start = cat_l * yr
                            idx_start = time_cats_lens[cat_idx] * yr
                            idx_end = idx_start + cat_l
                            dd_sum = 0
                            dd_cnt = 0
                            count_missing_days = 0
                            for idx in range(idx_start, idx_end):
                                #Omit feb 29 if leap year
                                if cat_idx == 12 and not WRCCUtils.is_leap_year(current_year) and idx == idx_start + 59:
                                    continue
                                t_x = el_data['maxt'][idx]
                                t_n = el_data['mint'][idx]
                                if abs(t_x + 9999.0) < 0.05 or abs(t_n + 9999.0) < 0.05:
                                    count_missing_days+=1
                                else:
                                    #corn is special:
                                    if table == 'corn' and t_x > 86.0:
                                        t_x = 86.0
                                    if table == 'corn' and t_n < 50.0:
                                        t_n = 50.0
                                    if table == 'corn' and t_x < t_n:
                                        t_x = t_n
                                    ave = (t_x + t_n)/2.0
                                    if table in ['cdd', 'gdd', 'corn']:
                                        dd = ave - base
                                    else:
                                        dd = base - ave
                                    if dd < 0:
                                        dd = 0
                                    dd_sum+=dd
                                    dd_cnt+=1
                            #Discard years where max_missing_days or more are missing
                            if cat_idx != 12 and count_missing_days > kwargs['max_missing_days']:
                                continue
                            #Make adjustments for missing hdd - replace with mean days
                            if table in ['cdd', 'hdd']:
                                if cat_idx != 12 and cat_l - dd_cnt <= kwargs['max_missing_days']:
                                    dd_sum = (dd_sum/dd_cnt)*float(cat_l)
                            yr_dat.append(dd_sum)
                        try:
                            dd_month = int(round(numpy.mean(yr_dat), 0))
                        except:
                            dd_month = 0
                        if table in ['gdd', 'corn']:
                            if cat_idx == 12:
                                val_list_d[table][2*base_idx].append(val_list_d[table][2*base_idx+1][-1])
                                val_list_d[table][2*base_idx+1].append(val_list_d[table][2*base_idx+1][-1])
                            else:
                                val_list_d[table][2*base_idx].append(dd_month)
                                dd_acc = sum(val_list_d[table][2*base_idx][2:])
                                val_list_d[table][2*base_idx+1].append(dd_acc)
                        else:
                            if cat_idx == 12:
                                try:
                                    val_list_d[table][base_idx].append(sum(val_list_d[table][base_idx][1:]))
                                except:
                                    val_list_d[table][base_idx].append(dd_month)
                            else:
                                val_list_d[table][base_idx].append(dd_month)

                    if cat_idx == 12:
                        for val_l in val_list_d[table]:
                            results[i][table].append(val_l)
    return results

def Sodpad(**kwargs):
    '''
    THIS PROGRAM READS IN PRECIPITATION FROM THE NCC SOD SET, AND THEN
    FINDS, FOR EACH DAY OF THE YEAR, THE NUMBER OF TIMES THAT A RANGE OF
    THRESHOLD AMOUNTS WAS EQUALLED, FOR A RANGE OF DURATIONS
    '''
    results = defaultdict(dict)
    #Loop over stations
    for i, stn in enumerate(kwargs['coop_station_ids']):
        num_yrs = len(kwargs['data'][i])
        el_data = kwargs['data'][i]
        if not el_data[0]:
            results[i]={}
            continue
        s_count = 0
        #Take care of data flags, Feb 29's are set to 99.00, missing data to 99.99
        for yr in range(num_yrs):
            for doy in range(366):
                if doy == 59:
                    el_data[yr][0][doy] = 99.00
                    continue
                val, flag = WRCCUtils.strip_data(str(el_data[yr][0][doy]))
                if flag == 'M':
                    el_data[yr][0][doy] = 99.99
                elif flag == 'S':
                    el_data[yr][0][doy] = 0.00
                    s_count+=1
                elif flag == 'A':
                    s_count+=1
                    val_new = float(val) / s_count
                    if s_count > doy: #need to jump back to last year
                        for k in range(doy):
                            el_data[yr][0][k] = val_new
                            for k in range(365,365-(s_count-doy),-1):
                                el_data[yr-1][0][k] = val_new
                    else:
                        for k in range (doy,doy-s_count,-1):
                            el_data[yr][0][k] = val_new
                        s_count = 0
                elif flag == 'T':
                    el_data[yr][0][doy] = 0.0
                else:
                    el_data[yr][0][doy] = float(val)
        #find accumulation-duration tables for each day of the year
        thramt = [.005,.095,.145,.195,.245,.295,.395,.495,.745,.995,1.495,1.995,2.495,2.995,3.995,4.995,5.995,7.995,9.995]
        lenper = [1,2,3,4,5,6,7,8,9,10,12,14,15,16,18,20,22,24,25,26,28,30]
        for doy in range(366):
            results[i][doy] = [[0.0 for k in range(len(thramt)+1)] for j in lenper]
            #skip leap days, too complicated
            if doy == 59:
                continue
            icount = 0
            idur = 0
            sumpre = 0
            sumobs = 0
            leapda = 0
            sumpcpn = [0 for l in range(num_yrs)]
            misdys = [1 for l in range(num_yrs)]
            leap = [1 for l in range(num_yrs)]
            #loop over durations
            #for idx, idur in enumerate(lenper):
            while icount <= 21:
                idur+=1
                for yr in range(num_yrs):
                    ndoyt = doy + idur - 1
                    iyeart = yr
                    if ndoyt > 365:
                        ndoyt-=365
                        iyeart+=1
                    if iyeart > range(num_yrs)[-1]:
                        continue
                    #look for leap days and skip Feb 29 if not a leap year
                    dates = kwargs['dates']
                    if abs(float(el_data[iyeart][0][ndoyt]) - 99.00) < 0.05:
                        leap[yr] = 0
                    if iyeart == int(dates[0][0:4]) and ndoyt == 59:
                        leapda = 1
                    if leap[yr] == 0 and leapda == 1:
                        ndoyt+=1
                    pcp = float(el_data[iyeart][0][ndoyt])
                    #Note that these sums continue to accumulate over all durations
                    if pcp < 98.00:
                        sumpcpn[yr]+=pcp
                        sumpre+=pcp
                        sumobs+=1
                        misdys[yr] = 0

                if lenper[icount] != idur:
                    continue

                #Loop over thresholds
                for ithr in range(19):
                    sumthr = 0
                    pcthr = 111.0
                    thresh = thramt[ithr]
                    nprsnt = 0 #no years with non-missing values
                    #loop over years and compute percentages
                    for yr in range(num_yrs):
                        if misdys[yr] == 1:
                            continue
                        nprsnt+=1
                        if sumpcpn[yr] > thresh:
                            sumthr+=1
                    aveobs = sumobs/float(idur)
                    if nprsnt != 0:
                        pcthr = 100.0 * sumthr/float(nprsnt+1)
                    results[i][doy][icount][ithr] = '%.1f' % pcthr
                if aveobs != 0:
                    avepre = sumpre / aveobs
                    results[i][doy][icount][19] = '%.2f' % avepre
                icount+=1
    return results

def Soddd(**kwargs):
    '''
    This program finds degree days above or below any selected
    base temperature, allowing for heating, cooling, freezing,
    thawing, chilling and other degree day thresholds.
    NCDC round-off can be simulated (truncation rather than rounding).
    Maximum and minimum temperatures can be truncated, and certain days can be skipped.
    The program can find either time series of monthly values,
    or long term averages of daily values.
    '''
    #data[stn_id][el] = [[year1 data], [year2 data], ... [yearn data]]
    #if output_type monthly time series:
    #results[stn_id][yr] =[Year,Jan_dd, Feb_dd, ..., Dec_dd]
    #if output_type daily long-term ave:
    #results[stn_id][doy]=[doy, Jan_ave, Jan_yrs, Feb_ave, Feb_yrs, ..., Dec_ave, Dec_yrs]
    results = defaultdict(list)
    #Loop over stations
    for i, stn in enumerate(kwargs['coop_station_ids']):
        yrs = max(len(kwargs['data'][i][j]) for j in range(len(kwargs['elements'])))
        dd = [[-9999.0 for day in range(366)] for yr in range(yrs)]
        for yr in range(yrs):
            for doy in range(366):
                maxt = str(kwargs['data'][i][0][yr][doy])
                mint = str(kwargs['data'][i][1][yr][doy])
                val_x, flag_x = WRCCUtils.strip_data(maxt)
                val_n, flag_n = WRCCUtils.strip_data(mint)
                try:
                    val_x = int(val_x)
                    val_n = int(val_n)
                except:
                    continue
                #Truncation if desired
                if 'trunc_high' in kwargs.keys() and val_x > kwargs['trunc_high']:
                    val_x = kwargs['trunc_high']
                if 'trunc_low' in kwargs.keys() and val_n < kwargs['trunc_low']:
                    val_n = kwargs['trunc_low']
                ave = (val_x + val_n)/2.0
                #Implement skip days if desired
                if 'skip_max_above' in kwargs.keys() and val_x > kwargs['skip_max_above']:
                    dd[yr][doy] = 0
                    continue
                if 'skip_min_below' in kwargs.keys() and val_n < kwargs['skip_min_below']:
                    dd[yr][doy] = 0
                    continue
                #NCDC roundoff of ave if desired
                if kwargs['ncdc_round']:
                    ave = numpy.ceil(ave)
                #Compute dd
                if kwargs['a_b'] == 'b':
                    dd[yr][doy] = float(kwargs['base_temp']) - ave
                else:
                    dd[yr][doy] = ave - float(kwargs['base_temp'])
                if dd[yr][doy] < 0:
                    dd[yr][doy] = 0
                #NCDC roundoff of dd if desired
                if kwargs['ncdc_round']:
                    dd[yr][doy] = numpy.ceil(dd[yr][doy])

        #Summarize:
        mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        days_miss = map(chr, range(97, 123))
        year = int(kwargs['dates'][0][0:4]) -1
        if kwargs['output_type'] == 'm':
            #monthly time series
            results[i] =  [[]for ys in range(yrs)]
            for yr in range(yrs):
                ann_sum = 0
                ann_miss = 0
                last_day = 0
                year+=1
                results[i][yr].append(year)
                for mon in range(12):
                    sm = 0
                    sm_miss = 0
                    #Take care of leap years
                    if mon == 1 and not WRCCUtils.is_leap_year(year):
                        mon_len = 28
                    else:
                        mon_len = mon_lens[mon]
                    if mon > 0:
                        last_day+= mon_lens[mon-1]
                    for day in range(mon_len):
                        dd_val = dd[yr][last_day+day]
                        if abs(dd_val + 9999.0) > 0.001:
                            sm+=dd_val
                        else:
                            sm_miss+=1
                    #take care of missing days max if desired
                    if 'max_miss' in kwargs.keys() and sm_miss > kwargs['max_miss']:
                        sm = -999
                        ann_miss+=1
                    elif sm_miss > 0.5 and sm_miss <= kwargs['max_miss']:
                        sm = round((sm/(float(last_day)- sm_miss))*float(last_day),1)
                        ann_sum+=sm
                    elif sm_miss == 0:
                        ann_sum+=sm

                    if sm_miss == 0:
                        results[i][yr].append(str(sm)+ ' ')
                    elif sm_miss > 0 and sm_miss <= 26:
                        results[i][yr].append(str(sm) + '%s' % days_miss[sm_miss-1])
                    else:
                        results[i][yr].append(str(sm) + '%s' % days_miss[-1])
                if ann_miss ==0:
                    results[i][yr].append('%s%s' %(round(ann_sum, 1),' '))
                else:
                    results[i][yr].append('%s%s' %(round(ann_sum, 1),days_miss[ann_miss-1]))
        else:
            #long-term daily average
            results[i] = [[] for day in range(31)]
            for day in range(31):
                year = int(kwargs['dates'][0][0:4]) -1
                results[i][day].append(day+1)
                for mon in range(12):
                    sm = 0
                    sm_yrs = 0
                    doy = WRCCUtils.compute_doy(str(mon+1), str(day+1))
                    for yr in range(yrs):
                        year+=1
                        if mon == 1 and not WRCCUtils.is_leap_year(year):
                            mon_len = 28
                        else:
                            mon_len = mon_lens[mon]
                        if day+1 > mon_len:
                            continue
                        if abs(dd[yr][doy-1] + 9999.0)>0.001:
                            sm+=dd[yr][doy-1]
                            sm_yrs+=1
                    if sm_yrs > 0.5:
                        results[i][day].append(int(round(float(sm)/sm_yrs)))
                        results[i][day].append(sm_yrs)
                    else:
                        results[i][day].append(-99)
                        results[i][day].append(0)
    return results

def Soddynorm(data, dates, elements, coop_station_ids, station_names, filter_type, filter_days):
    '''
    FINDS DAILY NORMALS FOR EACH DAY OF THE YEAR FOR EACH STATION
    OVER A MULTI YEAR PERIOD. IT USES EITHER A GAUSSIAN FILTER OR RUNNING MEAN.
    '''
    #data[stn_id][el] = [[year1 data], [year2 data], ... [yearn data]]
    #results[stn_id] = [[doy =1, mon=1, day=1, maxt_ave, yrs, mint_ave, yrs, pcpn_ave, yrs, sd_maxt, sd_mint],[doy=2, ...]...]
    results = defaultdict(list)
    #Loop over stations
    for i, stn in enumerate(coop_station_ids):
        #Find long-term daily averages of each element
        #for each day of the year, el_data_list will hold [average, yrs_in record, standard deviation]
        el_data_list = [[] for el in elements]
        el_data_list2 = [[] for el in elements]
        for j, el in enumerate(elements):
            if el == 'pcpn':
                el_data_list2[j] = [['0.0', '0'] for day in range(366)] #holds filtered data
            else:
                el_data_list2[j] = [['0.0','0.0','0'] for day in range(366)]
        #el_data_list_f = [[] for el in elements] #filtered data
        results[i] = [[] for el in elements]
        #Check for empty data
        if data[i] == [[],[],[]]:
            continue
        for j,el in enumerate(elements):
            if not data[i][j]:
                continue
            el_data = data[i][j]
            if el == 'pcpn': #deal with S, A and T flags
                s_count = 0
                for yr in range(len(el_data)):
                    for doy in range(366):
                        val, flag = WRCCUtils.strip_data(str(el_data[yr][doy]))
                        if flag == 'S':
                            s_count+=1
                        elif flag == 'A':
                            s_count+=1
                            val_new = float(val)/s_count
                            if s_count > doy: #need to jump back to last year
                                for k in range(doy):
                                    el_data[yr][k] = val_new
                                for k in range(365,365-(s_count-doy),-1):
                                    el_data[yr-1][k] = val_new
                            else:
                                for k in range (doy,doy-s_count,-1):
                                    el_data[yr][k] = val_new
                            s_count = 0
                        elif flag == 'T':
                            if val ==' ' or not val:
                                #el_data[yr][doy] = 0.0025
                                el_data[yr][doy] = 0.0
                            else:
                                try:
                                    float(val)
                                    if abs(100*int(val) - float(100*int(val))) < 0.05:
                                        el_data[yr][doy] = 0.00025
                                    else:
                                        el_data[yr][doy] = float(val)
                                except:
                                    el_data[yr][doy] = 0.0
            #loop over day of year and compute averages
            for doy in range(366):
                yr_count = 0
                vals=[]
                sm  = 0
                sms = 0
                n = 0
                ave = 0
                std = 0
                for yr in range(len(el_data)):
                    val, flag = WRCCUtils.strip_data(str(el_data[yr][doy]))
                    if flag == 'M' :
                        continue
                    else:
                        try:
                            vals.append(float(val))
                            yr_count+=1
                            sm+=float(val)
                            sms+= float(val)**2
                            n+=1
                        except:
                            continue

                if sms > 0:
                    if el in ['maxt', 'mint']:
                        ave = round(sm/n,1)
                    else:
                        ave = round(sm/n,3)
                    #ave = sm/n
                    if sms > 1.5:
                        try:
                            std = float(numpy.sqrt((sms-(sm*sm)/n)/(n - 1)))
                        except:
                            std = 0.0
                    else:
                        std = 0.0
                elif abs(sms - 0) < 0.05:
                    ave = 0
                    std = 0
                else:
                    ave = float('NaN')
                    std = float('NaN')

                ave = str(ave)
                if el in ['maxt', 'mint']:
                    el_data_list[j].append([ave, std, str(yr_count)])
                    #el_data_list.append([ave, std, str(yr_count)])
                else:
                    el_data_list[j].append([ave, str(yr_count)])
                    #el_data_list.append([ave, str(yr_count)])

            #implement filter if needed, average of the averages and of the std
            if filter_type == 'gauss':
                fltr = WRCCUtils.bcof(int(filter_days) - 1, normlz=True)
            else:
                fltr = [1.0/int(filter_days) for k in range(int(filter_days))]
            if int(filter_days)%2 == 0:
                nlow = -1 * (int(filter_days)/2 - 1)
                nhigh = int(filter_days)/2
            else:
                nlow = -1 * (int(filter_days) - 1)/2
                nhigh = -1 * nlow

            for doy in range(366):
                icount = -1
                sum_el_ave = 0.0
                sum_el_sd = 0.0
                sum_el_ave_f = 0.0
                sum_el_sd_f = 0.0
                for ifilt in range(nlow, nhigh+1):
                    icount+=1
                    doyt = doy + ifilt
                    if doyt > 365:
                        doyt-=366
                    if doyt < 0:
                        doyt+=366

                    if el !='pcpn':
                        yr_count = float(el_data_list[j][doyt][2])
                    else:
                        yr_count = float(el_data_list[j][doyt][1])

                    try:
                        val_ave = float(el_data_list[j][doyt][0])
                    except:
                        continue

                    if el != 'pcpn':
                        try:
                            val_sd = float(el_data_list[j][doyt][1])
                        except:
                            val_sd = None

                    ft = float(fltr[icount])
                    if yr_count > 0.5:
                        sum_el_ave+=val_ave*ft
                        sum_el_ave_f+=ft
                    if el !='pcpn' and yr_count >=0.5:
                        if val_sd:
                            sum_el_sd+=val_sd*ft
                            sum_el_sd_f+=ft

                #Insert smoothed values
                if sum_el_ave_f !=0:
                    new_ave = sum_el_ave/sum_el_ave_f
                    if el in ['maxt','mint']:
                        el_data_list2[j][doy][0] ='%.1f' % new_ave
                        el_data_list2[j][doy][2] = el_data_list[j][doy][2]
                    else:
                        el_data_list2[j][doy][0] ='%.3f' % new_ave
                        el_data_list2[j][doy][1] = el_data_list[j][doy][1]

                if el != 'pcpn' and sum_el_sd_f !=0:
                    new_sd = sum_el_sd/sum_el_sd_f
                    el_data_list2[j][doy][1] = '%.3f' % new_sd

        #write results
        for doy in range(366):
            mon, day = WRCCUtils.compute_mon_day(doy+1)
            results[i].append([str(doy+1), str(mon), str(day)])
            for j, el in enumerate(elements):
                for k in el_data_list2[j][doy]:
                    results[i][-1].append(k)
    return results

def Soddyrec(data, dates, elements, coop_station_ids, station_names):
    '''
    FINDS DAILY AVERAGES AND RECORD FOR EACH DAY OF THE YEAR
    FOR EACH STATION OVER A MULTI YEAR PERIOD
    '''
    #data[stn_id][el] = smry for station stn_id, element el = [ave, high_or_low, date,yrs_missing]
    #result[stn_id][el] = [[month=1, day=1, ave, no, high_or_low, yr], [month=1, day=2, ave,..]..]
    #for all 365 days a year
    results = defaultdict(dict)
    #Loop over stations
    for i, stn in enumerate(coop_station_ids):
        #results[i] = [[] for el in elements]
        for j, el in enumerate(elements):
            smry_start_idx = 3*j
            smry_end_idx = 3*j +3
            results[i][j] = []
            stn_check_list = []
            for k in range(366):
                mon, day = WRCCUtils.compute_mon_day(k+1)
                row=[mon, day]
                #Loop over summaries: mean, max, min
                for smry_idx in range(smry_start_idx, smry_end_idx):
                    val = data[i][smry_idx][k][0]
                    if smry_idx % 3 == 0:
                        #we are on mean summary, record years missing and compute number of years with records
                        mcnt = data[i][smry_idx][k][2]
                        num_years = int(dates[-1][0:4]) - int(dates[0][0:4])
                        row.append(val)
                        row.append(num_years - mcnt)
                    else:
                        #high and low, record year of occurrence
                        year = data[i][smry_idx][k][1][0:4]
                        row.append(val)
                        row.append(year)
                results[i][j].append(row)
    return results


def Sodsum(data, elements, coop_station_ids, station_names):
    '''
    COUNTS THE NUMBER OF OBSERVATIONS FOR THE PERIOD OF RECORD
    OF EACH STATION IN THE SOD DATA SET. IT ALSO FINDS THE AOUNT OF
    POTENTIAL, PRESENT, MISSING AND CONSECUTIVE PRESENT AND MISSING DAYS.
    ELEMENTS ARE GIVEN IN THIS ORDER:
    [PCPN, SNOW,SNWD,MAXT,MINT,TOBS]
    NOT ALL ELEMENTS MAY BE PREENT. DATA MAY BE OBTAINED FOR A SINGLE ELELMENT ONLY
    OR FOR ALL OF THE ABOVE LISTED.
    '''
    results = defaultdict(dict)
    #Loop over stations
    for i, stn in enumerate(coop_station_ids):
        results[i]['coop_station_id'] = coop_station_ids[i]
        results[i]['station_name'] = station_names[i]
        results_list = []
        for j in elements:
            results_list.append(j)
            results[i][j] = 0
        for j in ['PSBL','PRSNT','LNGPR', 'MISSG', 'LNGMS']:
            results_list.append(j)
            results[i][j] = 0
        if not data[i]:
            results[i]['no_data'] = 'No data to work with'
            results[i]['start'] = 'None'
            results[i]['end'] = 'None'
            continue
        results[i]['start'] = str(''.join(data[i][0][0].split('-')))
        results[i]['end'] = str(''.join(data[i][-1][0].split('-')))
        #Find number of records possible:
        jul_day_start = WRCCUtils.JulDay(int(data[i][0][0][0:4]), int(data[i][0][0][5:7]), int(data[i][0][0][8:10]))
        jul_day_end = WRCCUtils.JulDay(int(data[i][-1][0][0:4]), int(data[i][-1][0][5:7]), int(data[i][-1][0][8:10]))
        results[i]['PSBL'] = str(jul_day_end - jul_day_start+1)

        c_prsnt = 0 #for counting present observations
        c_lngpr = 0 #for counting number of consecutive present observations
        c_missg = 0 #for counting missing observation
        c_lngms = 0  #for counting number of consecutive missing observations

        #Loop over data
        for j in range(len(data[i])):
            flag_found = 0
            if j == 0:
                jd = jul_day_start
                jd_old = jul_day_start -1
            else:
                jd = WRCCUtils.JulDay(int(data[i][j][0][0:4]), \
                int(data[i][j][0][5:7]), int(data[i][j][0][8:10]))
                jd_old = WRCCUtils.JulDay(int(data[i][j-1][0][0:4]), \
                int(data[i][j-1][0][5:7]), int(data[i][j-1][0][8:10]))
            if jd - jd_old != 1:
                c_missg+= jd - jd_old -1
                c_lngms+= jd - jd_old -1

            #Loop over each element for date
            for k, el in enumerate(elements):
                if len(data[i][j])>=len(elements)+1:
                    val = str(data[i][j][k+1])
                else:
                    val = 'M'

                if val == 'M':
                    continue
                else:
                    results[i][el]+=1
                    flag_found = 1

            line_vals = [str(data[i][j][k+1]) for k in range(len(data[i][j][1:]))]
            if j == 0:
                if all(val == 'M' for val in line_vals):
                    c_missg+=1
                    c_lngms+=1
                else:
                    c_prsnt+=1
                    c_lngpr+=1
                continue

            if all(val == 'M' for val in line_vals):
                c_missg+=1
                if all(val == 'M' for val in line_vals):
                    #MISSG streak is continuing
                    c_lngms+=1
                else:
                    #PRSNT streak is ending here, MISSG streak is starting
                    c_lngms=1
                    #Update results[lngpr] if need be
                    if c_lngpr > results[i]['LNGPR']:
                        results[i]['LNGPR'] = c_lngpr
                    c_lngpr = 0
            else:
                c_prsnt+=1
                if all(val == 'M' for val in line_vals):
                    #MISSG steak is endng here, PRSNT streak is starting
                    c_lngpr=1
                    #Update results[lngms] if need be
                    if c_lngms > results[i]['LNGMS']:
                        results[i]['LNGMS'] = c_lngms
                    c_lngms = 0
                else:
                    #PRSNT streak continuing
                    c_lngpr+=1

        #Update results at end of run
        results[i]['MISSG'] = c_missg
        results[i]['PRSNT'] = c_prsnt
        if c_lngms > results[i]['LNGMS']:
            results[i]['LNGMS'] = c_lngms
        if c_lngpr > results[i]['LNGPR']:
            results[i]['LNGPR'] = c_lngpr

    return results


def SodsumMulti(data, dates, elements, coop_station_ids, station_names):
    '''
    Executes Sodsum on multiple stations
    element in elements correspond to data values in data, i.e data[i][j] is value corresponding to elements[j]
    Results.keys():
        coop_station_id, stn_name, start, end, pcpn, snow, snwd, maxt, mint, tobs, evap, wdmv, wesf, posbl, prsnt, lngpr, missg, lngms
    '''
    results = defaultdict(dict)
    #Loop over stations
    for i, stn in enumerate(coop_station_ids):
        results[i]['coop_station_id'] = coop_station_ids[i]
        results[i]['station_name'] = station_names[i]
        results_list = []
        for j in elements:
            results_list.append(j)
            results[i][j] = 0
        for j in ['PSBL','PRSNT','LNGPR', 'MISSG', 'LNGMS']:
            results_list.append(j)
            results[i][j] = 0
        if not data[i]:
            results[i]['no_data'] = 'No data to work with'
        results[i]['start'] = dates[0]
        results[i]['end'] = dates[-1]
        for el in elements:
            results[i][el] = 0
        #Find number of records possible:
        #FIX ME: Acis_WS MultiStndata calls do not return dates
        #For now, need to get start/end dates from AcissWS call and presume no gaps in data
        jul_day_start = WRCCUtils.JulDay(int(dates[0][0:4]), int(dates[0][4:6]), int(dates[0][6:8]))
        jul_day_end = WRCCUtils.JulDay(int(dates[-1][0:4]), int(dates[-1][4:6]), int(dates[-1][6:8]))
        results[i]['PSBL'] = str(jul_day_end - jul_day_start)

        c_prsnt = 0 #for counting present observations
        c_lngpr = 0 #for counting number of consecutive present observations
        c_missg = 0 #for counting missing observations
        c_lngms = 0  #for counting number of consecutive missing observations
        #Loop over data
        for j in range(len(data[i])):
            flag_found = 0
            if j == 0:
                jd = jul_day_start
                jd_old = jul_day_start -1
            else:
                jd = WRCCUtils.JulDay(int(dates[j][0:4]), int(dates[j][4:6]), int(dates[j][6:8]))
                jd_old = WRCCUtils.JulDay(int(dates[j-1][0:4]), int(dates[j-1][4:6]), int(dates[j-1][6:8]))

            if jd - jd_old != 1:
                c_missg+= jd - jd_old -1
                c_lngms+= jd - jd_old -1

            #Loop over each element for date
            for k, el in enumerate(elements):
                if len(data[i][j])>=len(elements):
                    val = str(data[i][j][k])
                else:
                    val = 'M'

                if val == 'M':
                    continue
                else:
                    results[i][el]+=1
                    flag_found = 1

            line_vals = [str(data[i][j][k]) for k in range(len(data[i][j]))]
            if j == 0:
                if all(val == 'M' for val in line_vals):
                    c_missg+=1
                    c_lngms+=1
                else:
                    c_prsnt+=1
                    c_lngpr+=1
                continue


            if all(val == 'M' for val in line_vals):
                c_missg+=1
                if all(val == 'M' for val in line_vals):
                    #MISSG streak is continuing
                    c_lngms+=1
                else:
                    #PRSNT streak is ending here, MISSG streak is starting
                    c_lngms=1
                    #Update results[lngpr] if need be
                    if c_lngpr > results[i]['LNGPR']:
                        results[i]['LNGPR'] = c_lngpr
                    c_lngpr = 0
            else:
                c_prsnt+=1
                if all(val == 'M' for val in line_vals):
                    #MISSG steak is endng here, PRSNT streak is starting
                    c_lngpr=1
                    #Update results[lngms] if need be
                    if c_lngms > results[i]['LNGMS']:
                        results[i]['LNGMS'] = c_lngms
                    c_lngms = 0
                else:
                    #PRSNT streak continuing
                    c_lngpr+=1

        #Update results at end of run
        results[i]['MISSG'] = c_missg
        results[i]['PRSNT'] = c_prsnt
        if c_lngms > results[i]['LNGMS']:
            results[i]['LNGMS'] = c_lngms
        if c_lngpr > results[i]['LNGPR']:
            results[i]['LNGPR'] = c_lngpr

    return results
