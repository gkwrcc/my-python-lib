#!/usr/bin/python

'''
Module WRCCDataApps
'''
from collections import defaultdict
import WRCCUtils
import numpy

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
        for table in tables:
            results[i][table] = []
        num_yrs = len(kwargs['data'][i])
        start_year = dates[0][0:4]
        end_year = dates[-1][0:4]
        el_data = {}
        el_dates = {}
        #Sort data
        dd_acc = 0 #for degree days sum
        for cat_idx, cat in enumerate(time_cats):
            if cat_idx < 12: #months
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
            #Find data for each element
            for el_idx, element in enumerate(elements):
                el_data[element] = []
                el_dates[element] = []
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
                        for idx in range(idx_start, idx_end):
                            el_data[element].append(kwargs['data'][i][yr][el_idx][idx])
                            date_idx  = yr * 366 + idx
                            el_dates[element].append(kwargs['dates'][date_idx])
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
                '''
                #Delete missing data
                for idx, dat in enumerate(el_data[element]):
                    #el_data_Mon[element][idx] = float(el_data_Mon[element][idx])
                    if  abs(dat - 9999.0) < 0.05:
                        del el_data[element][idx]
                        del el_dates[element][idx]
                '''
            #Compute monthly Stats for the different tables
            #1) Temperature Stats
            if kwargs['el_type'] == 'temp' or kwargs['el_type'] == 'both':
                val_list = [cat]
                #1) Averages and Daily extremes
                max_max = -9999.0
                min_min = 9999.0
                date_min ='0000-00-00'
                date_max = '0000-00-00'
                for el in ['maxt', 'mint', 'avgt']:
                    sm = 0
                    cnt = 0
                    for idx, dat in enumerate(el_data[el]):
                        if abs(dat + 9999.0) < 0.05:
                            continue

                        if el == 'maxt' and dat > max_max:
                            max_max = dat
                            date_max = el_dates[el][idx]
                        if el == 'mint' and dat < min_min:
                            min_min = dat
                            date_min = el_dates[el][idx]
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
                    #means_yr.append(numpy.mean(yr_dat))
                    if cnt!=0:
                        means_yr.append(sm/cnt)
                    else:
                        means_yr.append(0.0)

                ave_low = min(means_yr)
                ave_high = max(means_yr)
                yr_idx_low = means_yr.index(ave_low)
                yr_idx_high = means_yr.index(ave_high)
                yr_low = str(int(start_year) + yr_idx_low - 1900)
                yr_high = str(int(start_year) + yr_idx_high - 1900)
                val_list.append('%.4f' %ave_high)
                val_list.append(yr_high)
                val_list.append('%.4f' %ave_low)
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
                            idx_start = time_cats_lens[cat_idx]*yr
                            idx_end = idx_start + time_cats_lens[cat_idx]
                            yr_dat = numpy.array(el_data[el][idx_start:idx_end])
                            if thresh == '90':
                                yr_dat_thresh = numpy.where((yr_dat >= 90) & (abs(yr_dat + 9999.0) >= 0.05))
                            else:
                                yr_dat_thresh = numpy.where((yr_dat <= int(thresh)) & (abs(yr_dat + 9999.0) >= 0.05))
                            cnt_days.append(len(yr_dat_thresh[0]))
                        val_list.append('%.1f' % numpy.mean(cnt_days))
                results[i]['temp'].append(val_list)
            #2) Precip/Snow Stats
            if kwargs['el_type'] == 'prsn' or kwargs['el_type'] == 'both':
                val_list = [cat]
                #1) Total Precipitation
                for el in ['pcpn', 'snow']:
                    sum_yr=[]
                    for yr in range(num_yrs):
                        idx_start = time_cats_lens[cat_idx] * yr
                        idx_end = idx_start + time_cats_lens[cat_idx]
                        yr_dat = el_data['pcpn'][idx_start:idx_end]
                        sm = 0
                        for yr_dat_idx, dat in enumerate(yr_dat):
                            if abs(dat + 9999.0) >= 0.05:
                                sm+=dat
                        sum_yr.append(sm)
                    val_list.append('%.2f' % numpy.mean(sum_yr))
                    if el == 'pcpn':
                        prec_high = max(sum_yr)
                        yr_idx_high = sum_yr.index(prec_high)
                        prec_low = min(sum_yr)
                        yr_idx_low = sum_yr.index(prec_low)
                        yr_low = str(int(start_year) + yr_idx_low - 1900)
                        yr_high = str(int(start_year) + yr_idx_high - 1900)
                        val_list.append('%.2f' %prec_high)
                        val_list.append(yr_high)
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
                            idx_start = time_cats_lens[cat_idx]*yr
                            idx_end = idx_start + time_cats_lens[cat_idx]
                            yr_dat = numpy.array(el_data['pcpn'][idx_start:idx_end])
                            yr_dat_thresh = numpy.where(yr_dat >= thresh)
                            cnt_days.append(len(yr_dat_thresh[0]))
                        val_list.append('%d' % int(round(numpy.mean(cnt_days))))
                results[i]['prsn'].append(val_list)
            #3) Degree Days tables
            if kwargs['el_type'] in ['hc', 'g', 'all']:
                #get base list
                base_list = {}
                val_list =  defaultdict(list)
                base_list['hdd'] = [65, 60, 57, 55,50]
                base_list['cdd'] = [55, 57, 60, 65, 70]
                base_list['gdd'] = [40, 45, 50, 55, 60]
                base_list['corn'] = [50]

                val_list['hdd'] = [[65], [60], [57], [55], [50]]
                val_list['cdd'] = [[55], [57], [60], [65], [70]]
                for tbl in ['gdd', 'corn']:
                    val_list[tbl]=[]
                    for base in base_list[tbl]:
                        for ch in ['M', 'S']:
                            val_list[tbl].append([base, ch])

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
                            idx_start = time_cats_lens[cat_idx]*yr
                            idx_end = idx_start + time_cats_lens[cat_idx]
                            dd_sum = 0
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
                            yr_dat.append(dd_sum)
                        dd_month = int(round(numpy.mean(yr_dat)))
                        dd_acc+=dd_month

                        if table in ['gdd', 'corn']:
                            val_list[table][2*base_idx].append(dd_month)
                            val_list[table][2*base_idx+1].append(dd_acc)
                        else:
                            val_list[table][base_idx].append(dd_month)
                    for val_l in val_list[table]:
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
                            #sumthr[ithr]+=1
                            sumthr+=1
                    aveobs = sumobs/float(idur)
                    if nprsnt != 0:
                        pcthr = 100.0 * sumthr/float(nprsnt)
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
                        std = float(numpy.sqrt((sms-(sm*sm)/n)/(n - 1)))
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

