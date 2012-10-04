#!/usr/bin/python

'''
Module WRCCDataApps
'''
from collections import defaultdict
import WRCCUtils
import numpy
import sys

'''
This program can be used to find the latest spring and   '/
earliest fall frost (or other temperature(s)) each year. '/
However, it is written much more generally to allow      '/
finding the latest or earliest occurrence above or below '/
a threshold value, for a period up to 12-months long,    '/
which may extend from one year into the next (for example,'/
the winter season from July thru June), for up to 10 sets '/
of values.  Furthermore, the "midpoint" of the period can '/
be set anywhere between the starting and ending dates.    '/
For example, July 31 can be used as mid-year, rather than '/
June 30 (is a frost on July 2 the "last frost" of  spring,'/
or the "first frost" of autumn??)  A time series of the   '/
values for each half of the interval is formed, and the   '/
probability of exceedance is calculated, using only those '/
years with less missing data than the user specifies as a '/
minimum.
'''
def Sodthr(**kwargs):
    results = defaultdict(dict)
    dates = kwargs['dates']
    start_year = int(dates[0][0:4])
    end_year = int(dates[0][0:4])
    for i, stn in enumerate(kwargs['coop_station_ids']):
        elements = kwargs['elements']
        el_type = kwargs['el_type'] # maxt, mint, avgt, dtr (daily temp range)
        el_data = kwargs['data'][i]
        num_yrs = len(el_data)
        #el_data[el_idx][yr] ; if element_type is hdd, cdd, dtr or gdd: el_data[0] = maxt, el_data[1]=mint

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
        print thresholds
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
                            if nddoy1 < 60:
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
                        '''
                        if period == 1 and k == 2:
                            print ndoypc, nmopc, ndypc
                        '''
                        results[i][period][thresh][k] = '%s %s' % (str(nmopc), str(ndypc))
                else:
                    for k in range(1,12):
                        results[i][period][thresh][k] = '%.1f' % thrpct[period][thresh][k -1]

    return results
'''
Sodpct
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

def Sodpct(**kwargs):
    results = defaultdict(list)
    dates = kwargs['dates']
    start_year = int(dates[0][0:4])
    end_year = int(dates[0][0:4])
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
                            val = kwargs['base_temperature'] - ave
                        else:
                            val = ave - kwargs['base_temperature']
                        if val < 0:
                            val = 0
                    elif el_type == 'gdd':
                        high = nval_x
                        low = nval_n
                        if high > kwargs['max_temperature']:
                            high = kwargs['max_temperature']
                        if low < kwargs['min_temperature']:
                            low = kwargs['min_temperature']
                        val = (high + low)/2.0 - kwargs['base_temperature']
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

'''
Sodrun and Sodrunr
THESE PROGRAMS FIND ALL RUNS OF CONSECUTIVE DAYS WHERE REQUESTED THRESHOLD
CONDITIONS ARE MET. SODRUNR CONSIDERS 2 DAYS A TIME. OTHERWISE, THE TWO
PROGRAMS ARE IDENTICAL.
'''

def Sodrun(**kwargs):
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
    jd_start = WRCCUtils.JulDay(int(dates[0][0:4]), int(dates[0][5:7]), int(dates[0][8:10]))#Julian day odf start date
    jd_end = WRCCUtils.JulDay(int(dates[-1][0:4]), int(dates[-1][5:7]), int(dates[-1][8:10]))#Julian day of end date
    app_name = kwargs['app_name']
    op = kwargs['op']
    if elements == ['maxt', 'mint']:
        el = 'range'
    else:
        el = elements[0]
    thresh = kwargs['thresh']
    min_run = kwargs['minimum_run']
    verbose = kwargs['verbose']
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
            date_split = date_val[0].split('-')
            jd = WRCCUtils.JulDay(int(date_split[0]), int(date_split[1]), int(date_split[2]))
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
'''
Sodlist

'''

def Sodlist(**kwargs):
    results = defaultdict(list)
    coop_station_ids = kwargs['coop_station_ids']
    elements = kwargs['elements']
    dates = kwargs['dates']
    for i, stn in enumerate(coop_station_ids):
        stn_data = kwargs['data'][i]
        #first format data to include dates
        for k, date in enumerate(dates):
            for j, el in enumerate(elements):
                stn_data[k][j].insert(0,date)
        results[i]=stn_data
    return results

'''
Sodmonline
THIS PROGRAM WAS WRITTEN SPECIFICALLY FOR JOHN HANSON AT PGE, AND
GIVES THE DAILY AVERAGE TEMPERATURE FOR SPECIFIED STATIONS
THE FIRST YEARS ARE FROM THE SOD DATA BASE AND THE LATER YEARS
MAY BE FROM THE MONTHLY NCDC TELEPHONE CALL FILES
'''
def Sodmonline(**kwargs):
    results = defaultdict(list)
    coop_station_ids = kwargs['coop_station_ids']
    elements = kwargs['elements']
    dates = kwargs['dates']
    for i, stn in enumerate(coop_station_ids):
        stn_data = kwargs['data'][i]
        #first format data to include dates
        for k, date in enumerate(dates):
            stn_data[k].insert(0,date)
        results[i]=stn_data
    return results
'''
Sodsumm
THIS PROGRAM SUMMARIZES VARIOUS CLIMATIC DATA IN A FORMAT IDENTICAL WITH
THAT OF MICIS - THE MIDWEST CLIMATE INFORMATION SYSTEM
'''
def Sodsumm(**kwargs):
    elements = kwargs['elements']
    dates = kwargs['dates']
    tables = ['temp', 'prsn', 'hdd', 'cdd', 'gdd', 'corn']
    months = ['Ja', 'Fe', 'Ma', 'Ap', 'Ma', 'Jn', 'Jl', 'Au', 'Se', 'Oc', 'No', 'De']
    time_cats = ['Ja', 'Fe', 'Ma', 'Ap', 'Ma', 'Jn', 'Jl', 'Au', 'Se', 'Oc', 'No', 'De', 'An', 'Wi', 'Sp', 'Su', 'Fa']
    time_cats_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 366, 91, 92, 92, 91]
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #results[i][table]
    results = defaultdict(dict)
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
                results[i]['prsn'].append(['Time','Mean', 'High', 'Yr', 'Low', 'Yr', '1-Day Max', 'Date','Mean', 'High', 'Yr', '>=0.01', '>=0.10', '>=0.50', '>=1.00'])
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
            if cat_idx < 12: #months
                x_miss[cat_idx] = {}
                if cat_idx == 0:
                    idx_start = 0
                    idx_end = 31
                else:
                    idx_start = sum(mon_lens[idx] for idx in range(cat_idx))
                    idx_end = idx_start + mon_lens[cat_idx]
            elif cat_idx == 12: #Annual
                idx_start = 0
                idx_end = 366
            elif cat_idx == 13: #Winter
                idx_start = 335
                idx_end = 60
            elif cat_idx == 14: #Spring
                idx_start = 60
                idx_end = 152
            elif cat_idx == 15: #Summer
                idx_start = 152
                idx_end = 244
            elif cat_idx == 16: # Fall
                idx_start = 244
                idx_end = 335
            #Read in data, for ease of statistical computation, data and dates for each category are
            #ordered chronolocically in two indexed list: el_data[element], el_dates[element].
            for el_idx, element in enumerate(elements):
                el_data[element] = []
                el_dates[element] = []
                x_miss[cat_idx][element] = []
                for yr in range(num_yrs):
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
                    else:
                        data_list = []
                        for idx in range(idx_start, idx_end):
                            data_list.append(kwargs['data'][i][yr][el_idx][idx])
                            el_data[element].append(kwargs['data'][i][yr][el_idx][idx])
                            date_idx  = yr * 366 + idx
                            el_dates[element].append(kwargs['dates'][date_idx])
                        #Count missing days for monthly categories
                        if cat_idx < 12:
                            days_miss = len([dat for dat in data_list if dat == 'M'])
                            x_miss[cat_idx][element].append(days_miss)
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
                date_min ='0000-00-00'
                date_max = '0000-00-00'
                for el in ['maxt', 'mint', 'avgt']:
                    #Omit data yrs for month where max_missing day threshold is not met
                    data_list = []
                    dates_list = []
                    for yr in range(num_yrs):
                        if cat_idx == 1 and not WRCCUtils.is_leap_year(int(start_year)):
                            cat_l = 28
                        else:
                            cat_l = time_cats_lens[cat_idx]
                        idx_start = cat_l * yr
                        idx_end = idx_start + cat_l
                        if cat_idx < 12 and x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                            continue
                        data_list.extend(el_data[el][idx_start:idx_end])
                        dates_list.extend(el_dates[el][idx_start:idx_end])

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
                        ave = sm/cnt
                    else:
                        ave = 0.0
                    val_list.append('%.1f' % ave)

                val_list.append(int(max_max))
                val_list.append('%s/%s' % (date_max[8:10], date_max[0:4]))
                val_list.append(int(min_min))
                val_list.append('%s/%s' % (date_min[8:10], date_min[0:4]))

                #3)  Mean Extremes (over yrs)
                means_yr=[]
                for yr in range(num_yrs):
                    #Omit data yrs where month max_missing day threshold is not met
                    if cat_idx < 12 and x_miss[cat_idx]['avgt'][yr] > kwargs['max_missing_days']:
                        continue
                    idx_start = time_cats_lens[cat_idx] * yr
                    idx_end = idx_start + time_cats_lens[cat_idx]
                    yr_dat = el_data['avgt'][idx_start:idx_end]
                    sm = 0
                    cnt = 0
                    for yr_dat_idx, dat in enumerate(yr_dat):
                        if abs(dat + 9999.0) < 0.05:
                            continue
                        sm+=dat
                        cnt+=1
                    if cnt!=0:
                        means_yr.append(sm/cnt)
                    else:
                        means_yr.append(0.0)
                if means_yr:
                    ave_low = min(means_yr)
                    ave_high = max(means_yr)
                    yr_idx_low = means_yr.index(ave_low)
                    yr_idx_high = means_yr.index(ave_high)
                    yr_low = str(int(start_year) + yr_idx_low - 1900)
                    yr_high = str(int(start_year) + yr_idx_high - 1900)
                else:
                    ave_low = 99.0
                    ave_high = -99.0
                    yr_low = '***'
                    yr_high = '***'
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
                            if cat_idx < 12 and x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                                continue
                            idx_start = time_cats_lens[cat_idx]*yr
                            idx_end = idx_start + time_cats_lens[cat_idx]
                            yr_dat = numpy.array(el_data[el][idx_start:idx_end])
                            if thresh == '90':
                                yr_dat_thresh = numpy.where((yr_dat >= 90) & (abs(yr_dat + 9999.0) >= 0.05))
                            else:
                                yr_dat_thresh = numpy.where((yr_dat <= int(thresh)) & (abs(yr_dat + 9999.0) >= 0.05))
                            cnt_days.append(len(yr_dat_thresh[0]))
                        try:
                            val_list.append('%.1f' % numpy.mean(cnt_days))
                        except:
                            val_list.append('0.0')
                results[i]['temp'].append(val_list)

            #2) Precip/Snow Stats
            if kwargs['el_type'] == 'prsn' or kwargs['el_type'] == 'both' or kwargs['el_type'] == 'all':
                val_list = [cat]
                #1) Total Precipitation
                for el in ['pcpn', 'snow']:
                    sum_yr=[]
                    for yr in range(num_yrs):
                        #Omit data yrs where max_missing day threshold is not met
                        if cat_idx < 12 and x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                            continue
                        if cat_idx == 1 and not WRCCUtils.is_leap_year(int(start_year)):
                            cat_l = 28
                        else:
                            cat_l = time_cats_lens[cat_idx]
                        idx_start = cat_l * yr
                        idx_end = idx_start + cat_l
                        #idx_start = time_cats_lens[cat_idx] * yr
                        #idx_end = idx_start + time_cats_lens[cat_idx]
                        yr_dat = el_data[el][idx_start:idx_end]
                        sm = 0
                        for yr_dat_idx, dat in enumerate(yr_dat):
                            if abs(dat + 9999.0) >= 0.05:
                                sm+=dat
                        sum_yr.append(sm)
                    try:
                        val_list.append('%.2f' % numpy.mean(sum_yr))
                    except:
                        val_list.append('****')
                    if sum_yr:
                        prec_high = max(sum_yr)
                        yr_idx_high = sum_yr.index(prec_high)
                        yr_high = str(int(start_year) + yr_idx_high - 1900)
                        if el == 'pcpn':
                            prec_low = min(sum_yr)
                            yr_idx_low = sum_yr.index(prec_low)
                            yr_low = str(int(start_year) + yr_idx_low - 1900)
                    else:
                        prec_high = -99.0
                        yr_high = '***'
                        if el == 'pcpn':
                            prec_low = 99.0
                            yr_low = '***'
                    val_list.append('%.2f' %prec_high)
                    val_list.append(yr_high)
                    if el == 'pcpn':
                        val_list.append('%.2f' %prec_low)
                        val_list.append(yr_low)
                        #2) Daily Prec max
                        prec_max = max(el_data['pcpn'])
                        idx_max = el_data['pcpn'].index(prec_max)
                        date_max = el_dates['pcpn'][idx_max]
                        val_list.append('%.2f' %prec_max)
                        val_list.append('%s/%s' % (date_max[8:10], date_max[0:4]))

                #3) Precip Thresholds
                threshs = [0.01, 0.10, 0.50, 1.00]
                for thresh in threshs:
                        cnt_days = []

                        for yr in range(num_yrs):
                            #Omit data yrs where max_missing day threshold is not met
                            if cat_idx < 12 and x_miss[cat_idx][el][yr] > kwargs['max_missing_days']:
                                continue
                            idx_start = time_cats_lens[cat_idx]*yr
                            idx_end = idx_start + time_cats_lens[cat_idx]
                            yr_dat = numpy.array(el_data['pcpn'][idx_start:idx_end])
                            yr_dat_thresh = numpy.where(yr_dat >= thresh)
                            cnt_days.append(len(yr_dat_thresh[0]))
                        try:
                            val_list.append('%d' % int(round(numpy.mean(cnt_days))))
                        except:
                            val_list.append('0')
                results[i]['prsn'].append(val_list)
            #3) Degree Days tables
            if kwargs['el_type'] in ['hc', 'g', 'all']:
                if kwargs['el_type'] == 'hc':
                    table_list = ['hdd', 'cdd']
                elif kwargs['el_type'] == 'g':
                    table_list = ['gdd', 'corn']
                else:
                    table_list = ['hdd', 'cdd', 'gdd', 'corn']

                if cat_idx >=13:
                    continue


                for table in table_list:
                    for base_idx, base in enumerate(base_list[table]):
                        dd_acc = 0
                        yr_dat = []
                        for yr in range(num_yrs):
                            #Take care of leap years
                            if cat_idx == 1 and not WRCCUtils.is_leap_year(int(start_year)):
                                cat_l = 28
                            else:
                                cat_l = time_cats_lens[cat_idx]
                            idx_start = cat_l * yr
                            idx_end = idx_start + cat_l
                            #idx_start = time_cats_lens[cat_idx]*yr
                            #idx_end = idx_start + time_cats_lens[cat_idx]
                            dd_sum = 0
                            dd_cnt = 0
                            for idx in range(idx_start, idx_end):
                                t_x = el_data['maxt'][idx]
                                t_n = el_data['mint'][idx]
                                if abs(t_x + 9999.0) < 0.05 or abs(t_n + 9999.0) < 0.05:
                                    continue
                                #corn is special:
                                if table == 'corn' and t_x > 86.0:
                                    t_x = 86.0
                                if table == 'corn' and t_n < 50.0 and abs(t_x + 9999.0) >= 0.05:
                                    t_n = 50.0
                                if table == 'corn' and t_x < t_n:
                                    tx = t_n
                                ave = (t_x + t_n)/2.0
                                if table in ['cdd', 'gdd', 'corn']:
                                    dd = ave - base
                                else:
                                    dd = base - ave
                                if dd < 0:
                                    dd = 0
                                dd_sum+=dd
                                dd_cnt+=1

                            #Make adjustments for missing hdd - replace with mean days
                            if table in ['hdd','cdd']:
                                if time_cats_lens[cat_idx] - dd_cnt <= kwargs['max_missing_days']:
                                    dd_sum = (dd_sum/dd_cnt)*float(time_cats_lens[cat_idx])
                            yr_dat.append(dd_sum)
                        try:
                            dd_month = int(round(numpy.mean(yr_dat)))
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

'''
Sodpad
THIS PROGRAM READS IN PRECIPITATION FROM THE NCC SOD SET, AND THEN
FINDS, FOR EACH DAY OF THE YEAR, THE NUMBER OF TIMES THAT A RANGE OF
THRESHOLD AMOUNTS WAS EQUALLED, FOR A RANGE OF DURATIONS.
'''
def Sodpad(**kwargs):
    results = defaultdict(dict)
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

'''
Soddd
This program finds degree days above or below any selected
base temperature, allowing for heating, cooling, freezing,
thawing, chilling and other degree day thresholds.
NCDC round-off can be simulated (truncation rather than rounding).
Maximum and minimum temperatures can be truncated, and certain days can be skipped.
The program can find either time series of monthly values,
or long term averages of daily values.
'''
def Soddd(**kwargs):
    #data[stn_id][el] = [[year1 data], [year2 data], ... [yearn data]]
    #if output_type monthly time series:
    #results[stn_id][yr] =[Year,Jan_dd, Feb_dd, ..., Dec_dd]
    #if output_type daily long-term ave:
    #results[stn_id][doy]=[doy, Jan_ave, Jan_yrs, Feb_ave, Feb_yrs, ..., Dec_ave, Dec_yrs]
    results = defaultdict(list)
    for i, stn in enumerate(kwargs['coop_station_ids']):
        yrs = max(len(kwargs['data'][i][j]) for j in range(len(kwargs['elements'])))
        dd = [[-9999 for day in range(366)] for yr in range(yrs)]
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
                    dd[yr][doy] = kwargs['base_temp'] - ave
                else:
                    dd[yr][doy] = ave - kwargs['base_temp']
                if dd[yr][doy] < 0:
                    dd[yr][doy] = 0
                #NCDC roundoff of dd if desired
                if kwargs['ncdc_round']:
                    dd[yr][doy] = numpy.ceil(dd[yr][doy])

        #Summarize:
        mon_lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        days_miss = map(chr, range(97, 123))
        year = int(kwargs['dates'][0][0:4]) -1
        if kwargs['output_type'] == 'm':
            #monthly time series
            results[i] =  [[]for ys in range(yrs)]
            for yr in range(yrs):
                last_day = 0
                year+=1
                results[i][yr].append(year)
                for mon in range(12):
                    sm = 0
                    sm_miss = 0
                    if mon == 1 and WRCCUtils.is_leap_year(year):
                        mon_len = 29
                    else:
                        mon_len = mon_lens[mon]
                    if mon > 0:
                        last_day+= mon_lens[mon-1]
                    for day in range(mon_len):
                        dd_val = dd[yr][last_day+day]
                        if dd_val != -9999:
                            sm+=dd_val
                        else:
                            sm_miss+=1
                    #take care of missing days max if desired
                    if 'max_miss' in kwargs.keys() and sm_miss > kwargs['max_miss']:
                        sm = -999
                    elif sm_miss > 0.5:
                        sm = (sm/(float(mon_len)- sm_miss))*float(last_day)

                    if sm_miss == 0:
                        results[i][yr].append(str(sm)+ ' ')
                    elif sm_miss > 0 and sm_miss <= 26:
                        results[i][yr].append(str(sm) + '%s' % days_miss[sm_miss-1])
                    else:
                        results[i][yr].append(str(sm) + '%s' % days_miss[-1])
        else:
            #long-term daily average
            results[i] = [[] for day in range(31)]
            for day in range(31):
                year = int(kwargs['dates'][0][0:4]) -1
                results[i][day].append(day)
                for mon in range(12):
                    sm = 0
                    sm_yrs = 0
                    doy = WRCCUtils.compute_doy(str(mon+1), str(day+1))
                    for yr in range(yrs):
                        year+=1
                        if mon == 1 and WRCCUtils.is_leap_year(year):
                            mon_len = 29
                        else:
                            mon_len = mon_lens[mon]
                        if day+1 > mon_len:
                            continue
                        if dd[yr][doy] != -9999:
                            sm+=dd[yr][doy]
                            sm_yrs+=1
                    if sm_yrs > 0.5:
                        results[i][day].append(int(round(float(sm)/sm_yrs)))
                        results[i][day].append(sm_yrs)
                    else:
                        results[i][day].append(-99)
                        results[i][day].append(0)
    return results

'''
Soddynorm
FINDS DAILY NORMALS FOR EACH DAY OF THE YEAR FOR EACH STATION
OVER A MULTI YEAR PERIOD. IT USES EITHER A GAUSSIAN FILTER OR RUNNING MEAN.
'''
def Soddynorm(data, dates, elements, coop_station_ids, station_names, filter_type, filter_days):
    #data[stn_id][el] = [[year1 data], [year2 data], ... [yearn data]]
    #results[stn_id] = [[doy =1, mon=1, day=1, maxt_ave, yrs, mint_ave, yrs, pcpn_ave, yrs, sd_maxt, sd_mint],[doy=2, ...]...]
    results = defaultdict(list)
    #for each station and element compute normals
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
                                el_data[yr][doy] = 0.0025
                            elif abs(100*val - float(int(100*val))) < 0.05:
                                el_data[yr][doy] = 0.0025
                            else:
                                try:
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
                    ave = sm/n
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

                if el in ['maxt','mint']:
                    ave = '%.1f' % ave
                else:
                    ave = '%.3f' % ave
                std = '%.3f' % std

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

'''
Soddyrec
FINDS DAILY AVERAGES AND RECORD FOR EACH DAY OF THE YEAR
FOR EACH STATION OVER A MULTI YEAR PERIOD
'''
def Soddyrec(data, dates, elements, coop_station_ids, station_names):
    #data[stn_id][el] = smry for station stn_id, element el = [ave, high_or_low, date,yrs_missing]
    #result[stn_id][el] = [[month=1, day=1, ave, no, high_or_low, yr], [month=1, day=2, ave,..]..]
    #for all 365 days a year
    results = defaultdict(dict)
    for i, stn in enumerate(coop_station_ids):
        for j,el in enumerate(elements):
            results[i][j] = []
            stn_check_list = []
            #check if the station returned valid data
            for k in range(366):
                for l in range(len(data[i][j][k])):
                    stn_check_list.append(data[i][j][k][l])
            if all(map(lambda x: x == '#',stn_check_list)):
                continue
            for doy,vals in enumerate(data[i][j]):
                mon, day = WRCCUtils.compute_mon_day(doy+1)
                no  = vals[-1] #no of years with records
                results[i][j].append([mon, day,vals[0], no, vals[1], vals[2][0:4]])

    return results


'''
Sodsum:
COUNTS THE NUMBER OF OBSERVATIONS FOR THE PERIOD OF RECORD
OF EACH STATION IN THE SOD DATA SET. IT ALSO FINDS THE AOUNT OF
POTENTIAL, PRESENT, MISSING AND CONSECUTIVE PRESENT AND MISSING DAYS.
ELEMENTS ARE GIVEN IN THIS ORDER:
[PCPN, SNOW,SNWD,MAXT,MINT,TOBS]
NOT ALL ELEMENTS MAY BE PREENT. DATA MAY BE OBTAINED FOR A SINGLE ELELMENT ONLY
OR FOR ALL OF THE ABOVE LISTED.
'''

def Sodsum(data, elements, coop_station_ids, station_names):
    results = defaultdict(dict)
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
    #element in elements correspond to data values in data, i.e data[i][j] is value corresponding to elements[j]
    #Results.keys()=[coop_station_id, stn_name, start, end, pcpn, snow, snwd, maxt, mint, tobs, evap, wdmv, wesf, posbl, prsnt, lngpr, missg, lngms]
    results = defaultdict(dict)
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

