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
Finds daily normals for each day
of the year for each station over a multi year period. It uses either a Gaussian filter or running mean.
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

                    #replace data values with smoothed values
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
            if filter_type == 'gauss':
               for j, el in enumerate(elements):
                   for k in el_data_list2[j][doy]:
                       results[i][-1].append(k)
            else:
                for j, el in enumerate(elements):
                    for k in el_data_list[j][doy]:
                        results[i][-1].append(k)
    return results

'''
Soddyrec
Finds daily averages and record  for each day
of the year for each station over a multi year period
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
This function counts the number of observations for the period of record
at each station in the SOD data set.
It also finds the amount of potential, present, missing and
consecutive present and missing days.
Elements are given in this order:
[pcpn, snow, snwd, maxt, mint, tobs]
Not all elements may be present. Data may be obtained for
a single element only or all of the above listed.
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

