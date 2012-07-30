#!/usr/bin/python

'''
Module WRCCDataApps
'''
from collections import defaultdict
import WRCCUtils

'''
SodSum:
This function counts the number of observations for the period of record
at each station in the SOD data set.
It also finds the amount of potential, present, missing and
consecutive present and missing days.
Elements are given in this order:
[pcpn, snow, snwd, maxt, mint, tobs, evap, wdmv, wesf]
Not all elements may be present. Data may be obtained for
a single element only or all of the above listed.
'''
def SodSum(data, dates, elements, coop_station_ids, station_names):
	#element in elements correspond to data values in data, i.e data[i][j] is value corresponding to elements[j]
	#Results.keys()=[coop_station_id, stn_name, start, end, pcpn, snow, snwd, maxt, mint, tobs, evap, wdmv, wesf, posbl, prsnt, lngpr, missg, lngms]
	results = defaultdict(dict)
	for i, stn in enumerate(coop_station_ids):
		results[i]['coop_station_id'] = coop_station_ids[i]
		results[i]['station_name'] = station_names[i]
		results_list = []
		for j in elements:
			results_list.append(j)
		for j in ['PSBL','PRSNT','LNGPR', 'MISSG', 'LNGMS']:
			results_list.append(j)
			results[i][j] = 0
		if not data[i]:
			results[i]['no_data'] = 'No data to work with'
		'''
		results[i]['start'] = str(''.join(data[i][0][0].split('-')))
		results[i]['end'] = str(''.join(data[i][-1][0].split('-')))
		'''
		results[i]['start'] = dates[0]
		results[i]['end'] = dates[-1]
		for el in elements:
			results[i][el] = 0
		#Find number of records possible:
		#FIX ME: Acis_WS MultiStndata calls do not return dates
		#For now, need to get start/end dates from AcissWS call and presume no gaps in data
		'''
		jul_day_start = WRCCUtils.JulDay(int(data[i][0][0][0:4]), int(data[i][0][0][5:7]), int(data[i][0][0][8:10]))
		jul_day_end = WRCCUtils.JulDay(int(data[i][-1][0][0:4]), int(data[i][-1][0][5:7]), int(data[i][-1][0][8:10]))
		results[i]['PSBL'] = str(jul_day_end - jul_day_start)
		'''
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
				'''
				jd = WRCCUtils.JulDay(int(data[i][j][0][0:4]), int(data[i][j][0][5:7]), int(data[i][j][0][8:10]))
				jd_old = WRCCUtils.JulDay(int(data[i][j-1][0][0:4]), int(data[i][j-1][0][5:7]), int(data[i][j-1][0][8:10]))
'''
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

