#!/usr/bin/python

'''
Module WRCCDataApps
'''
from collections import defaultdict
import WRCCUtils
import numpy

'''
Soddynorm
Finds daily normals for each day
of the year for each station over a multi year period. It uses either a Gaussian filter or running mean.
'''
def Soddynorm(data, dates, elements, coop_station_ids, station_names, filter_type, filter_days):
    #data[stn_id][el] = [[year1 data], [year2 data], ... [yearn data]]
    #results[stn_id] = [[doy =1, mon=1, day=1, maxt_ave, yrs, mint_ave, yrs, pcpn_ave, yrs, sd_maxt, sd_mint],[doy=2, ...]...]
    results = defaultdict(list)
    #for each station and element compute
    for i, stn in enumerate(coop_station_ids):
        #for each day of the year, el_list will hold [average, yrs_in record, standard deviation]
        el_data_list = [[] for el in elements]
        #el_data_list_f = [[] for el in elements] #filtered data
        results[i] = []
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
                        if flag == 'A':
                            s_count+=1
                        elif flag == 'S':
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
                        elif flag == 'T':
                            if val ==' ' or not val:
                                el_data[yr][doy] = 0.0025
                            elif abs(100*val - float(int(100*val))) < 0.05:
                                el_data[yr][doy] = 0.0025

            #loop over day of year and compute averages
            for doy in range(366):
                yr_count = 0
                vals=[]
                for yr in range(len(el_data)):
                    val, flag = WRCCUtils.strip_data(str(el_data[yr][doy]))
                    if flag == 'M' :
                        continue
                    else:
                        try:
                            vals.append(float(val))
                            yr_count+=1
                        except:
                            pass
                ave = numpy.average(vals)
                std = numpy.std(vals)
                if el in ['maxt','mint']:
                    ave = '%.1f' % ave
                else:
                    ave = '%.3f' % ave
                std = '%.3f' % std
                if el in ['maxt', 'mint']:
                    el_data_list[j].append([ave, std, str(yr_count)])
                else:
                    el_data_list[j].append([ave, str(yr_count)])

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
                    icount = 0
                    sum_el_ave = 0.0
                    sum_el_sd = 0.0
                    sum_el_ave_f = 0.0
                    sum_el_sd_f = 0.0
                    for ifilt in range(nlow, nhigh+1):
                        icount+=1
                        doyt = doy + ifilt
                        if doyt > 365:
                            doyt-=365
                        if doyt < 0:
                            doyt+=365
                        val_ave = float(el_data_list[j][doyt][0])*float(fltr[icount-1])
                        val_sd = float(el_data_list[j][doyt][1])*float(fltr[icount-1])
                        ft = float(fltr[icount-1])
                        if val_ave >= 0.5:
                            sum_el_ave+=val_ave
                            sum_el_ave_f+=ft
                        if val_sd >= 0.5:
                            sum_el_sd+=val_sd
                            sum_el_sd_f+=ft
                    #replace data values with smoothed values
                    if sum_el_ave_f !=0:
                        new_ave = sum_el_ave/sum_el_ave_f
                        if el in ['maxt','mint']:
                            el_data_list[j][doy][0] ='%.1f' % new_ave
                        else:
                            el_data_list[j][doy][0] ='%.3f' % new_ave
                    if sum_el_sd_f !=0:
                        new_sd = sum_el_sd/sum_el_sd_f
                        if el in ['maxt','mint']:
                            el_data_list[j][doy][1] = '%.3f' % new_sd
        #write results
        for doy in range(366):
            mon, day = WRCCUtils.compute_mon_day(doy+1)
            results[i].append([str(doy+1), str(mon), str(day)])
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

