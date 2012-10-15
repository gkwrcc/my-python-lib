#!/usr/bin/python

'''
Module WRCCUtils
'''

import datetime
import time
import sys
import numpy
############################################################################################
#Utils
############################################################################################
'''
JulDay; Function utilized to check for gap in data
This program is based on and algorithm presented in 'Sky And Telescope Magazine, March 1984.'
It will correctly calculate any date A.D. to the correct Julian date through at least 3500 A.D.
Note that Julain dates begin at noon GMT. For this reason, the number is incremented by one to
correspond to a day beginning at midnight.
'''
def JulDay(year, mon, day):
    jd = 367 * year - 7 * (year + (mon + 9) / 12) / 4\
    - 3 * ((year + (mon - 9) / 7) / 100 +1) / 4\
    + 275 * mon / 9 + day + 1721029

    jd+=1
    return int(jd)

#Routine  to convert calendar days to yearly Julian days,
#All years are leap years, used in Sodthr
def Catoju(mnth, dy):
    month = int(mnth.lstrip('0'))
    nday = int(dy.lstrip('0'))
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ndoy =0
    for  mon in range(1,month+1):
        if mon < month:ndoy+=mon_lens[mon]
        if mon == month: ndoy+=nday
    if month == -1 and nday == -1:ndoy = -1
    return ndoy

#Routine to convert yearly Julian Days to Calenday days,
#All years are leap years, used in Sodthr
def Jutoca(ndoy):
    jstart = [1, 32, 61, 92, 122, 153, 183, 214, 245, 275, 306, 336]
    month = 0
    for mon in range(12):
        if ndoy >= jstart[mon]:
            month = mon + 1
            if month == 12:
                if ndoy < 367:
                    nday = ndoy - 336 +1
                else:
                    month = -1
                    nday = -1
        else:
            nday = ndoy - jstart[month-1] +1
            break

    nday = str(nday)
    month = str(month)
    if len(nday)== 1:
        nday = '0%s' % nday
    if len(month) == 1:
        month = '0%s' % month
    return month, nday



#Routine to compute binomial coefficients for Soddynorm
#######################################################
def bcof(n, normlz=True):
    C = []
    S = 0
    for k in range(n+1):
        bc = [1 for i in range(0,k+1)]
        for j in range(1,n-k+1):
            for i in range(1,k+1):
                bc[i] = bc[i-1]+bc[i]
        C.append(bc[k])
        S+=bc[k]
    if normlz:
        C = ['%.6f' % (c/float(S)) for c in C ]
    return C

#Routine to strip data of attached flags
########################################
def strip_data(val):
    if not val:
        pos_val = ' '
        flag = ' '
    elif val[0] == '-':
        pos_val = val[1:]
    else:
        pos_val = val
    #Note: len(' ') =1!
    if len(pos_val) ==1:
        if pos_val.isdigit():
            strp_val = val
            flag = ' '
        else:
            strp_val = ' '
            if pos_val in ['M', 'T', 'S', 'A', ' ']:
                flag = pos_val
            else:
                print 'Error! Found invalid flag: %s' % pos_val
                sys.exit(0)
    else: #len(pos_val) >1
        if not pos_val[-1].isdigit():
            flag = val[-1]
            strp_val = val[0:-1]
        else:
            flag = ' '
            strp_val = val

    return strp_val, flag


#Routine to compute day of year ignoring leap years
###################################################
def compute_doy(mon,day):
    mon_len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(mon.lstrip('0'))
    nday = int(day.lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

def compute_doy_leap(mon, day):
    mon_len = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(mon.lstrip('0'))
    nday = int(day.lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

#reverse of compute_doy but counting every feb as having 29 days
def compute_mon_day(doy):
    ndoy = int(doy)
    mon = 0
    day = 0
    if ndoy >366 or ndoy < 1:
        print 'Error in WRCCUtils.compute_mon_day , day of year: %s not in [1,366]' %ndoy
        sys.exit(1)

    mon_day_sum = [31,60,91,121,152,182,213,244,274,305,335,366]
    for i in range(12):
        if i == 0:
            if ndoy <=31:
                mon = 1
                day = ndoy
                break
        else:
            if mon_day_sum[i-1] < ndoy and ndoy <= mon_day_sum[i]:
                mon = i+1
                day = ndoy - mon_day_sum[i-1]
                break
            else:
                continue

    return mon,day

def is_leap_year(year):
    if year % 100 != 0 and year % 4 == 0:
        return True
    elif year % 100 == 0 and year % 400 == 0:
        return True
    else:
        return False

#This function is in place because Acis_WS's MultiStnCall does not return dates
#it takes as arguments a start date and an end date (format yyyymmdd)
#and returns the list of dates [s_date, ..., e_date] assuming that there are no gaps in the data
def get_dates(s_date, e_date, app_name):
    if s_date and e_date:
        dates = []
        #convert to datetimes
        start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
        end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
        for n in range(int ((end_date - start_date).days +1)):
            next_date = start_date + datetime.timedelta(n)
            dates.append(str(time.strftime('%Y%m%d', next_date.timetuple())))
            #note, these apps are grouped by year and return a 366 day year even for non-leap years
            if app_name in ['Sodpad', 'Sodsumm', 'Soddyrec', 'Soddynorm', 'Soddd']:
                if dates[-1][4:8] == '0228' and not is_leap_year(int(dates[-1][0:4])):
                    dates.append('dates[-1][0:4]0229')
    else:
        dates = []
    #convert to acis format
    for i,date in enumerate(dates):
        dates[i] = '%s-%s-%s' % (dates[i][0:4], dates[i][4:6], dates[i][6:8])
    return dates

def strip_n_sort(station_list):
    c_ids_strip_list = [int(stn.lstrip('0')) for stn in station_list]
    stn_list = sorted(c_ids_strip_list)
    for i, stn in enumerate(stn_list):
        if len(str(stn)) == 5:
            stn_list[i] = '0' + str(stn)
        else:
            stn_list[i] = str(stn)
    return stn_list

#Utility functions
def find_start_end_dates(form_input):
    if 'start_date' not in form_input.keys():
        s_date = 'por'
    else:
        if form_input['start_date'] == '' or form_input['start_date'] == ' ':
            s_date = 'por'
        else:
            if len(form_input['start_date']) == 4:
                s_date = form_input['start_date'] + '0101'
            elif len(form_input['start_date']) == 6:
                s_date = form_input['start_date'] + '01'
            elif len(form_input['start_date']) == 8:
                s_date = form_input['start_date']
            else:
                print 'Invalid start date format, should be yyyy or yyyymmdd!'
                s_date = None
    if 'end_date' not in form_input.keys():
        e_date = 'por'
    else:
        if form_input['end_date'] == '' or form_input['end_date'] == ' ':
            e_date = 'por'
        else:
            if len(form_input['end_date']) == 4:
                e_date = form_input['end_date'] + '1231'
            elif len(form_input['end_date']) == 6:
                e_date = form_input['end_date'] + '31'
            elif len(form_input['end_date']) == 8:
                e_date = form_input['end_date']
            else:
                print 'Invalid end date format, should be yyyy or yyyymmdd!'
                e_date = None
    return s_date, e_date

def get_element_list(form_input, program):
    if program == 'Soddyrec':
        if form_input['element'] == 'all':
            elements = ['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd']
        elif form_input['element'] == 'tmp':
            elements = ['maxt', 'mint', 'pcpn']
        elif form_input['element'] == 'wtr':
            elements = ['pcpn', 'snow', 'snwd']
        else:
            elements = [form_input['element']]
    elif program == 'Soddynorm':
        elements = ['maxt', 'mint', 'pcpn']
    elif program == 'Sodsumm':
        if form_input['element'] == 'all':
            elements = ['maxt', 'mint', 'avgt', 'pcpn', 'snow']
        elif form_input['element'] == 'temp':
            elements = ['maxt', 'mint', 'avgt']
        elif form_input['element'] == 'prsn':
            elements = ['pcpn', 'snow']
        elif form_input['element'] == 'both':
            elements = ['maxt', 'mint', 'avgt', 'pcpn', 'snow']
        elif form_input['element'] in ['hc', 'g']:
            elements = ['maxt', 'mint']
    elif program in ['Sodxtrmts', 'Sodpct', 'Sodpiii', 'Sodrunr', 'Sodrun', 'Sodthr']:
        if program in ['Sodrun', 'Sodrunr'] and form_input['element'] == 'range':
            elements = ['maxt', 'mint']
        elif program in ['Sodpct', 'Sodthr', 'Sodxtrmts', 'Sodpiii']:
            if form_input['element'] in ['dtr', 'hdd', 'cdd', 'gdd', 'avgt', 'range']:
                elements = ['maxt', 'mint']
            else:
                elements = ['%s' % form_input['element']]
        else:
            elements = ['%s' % form_input['element']]
    elif program == 'Sodpad':
        elements = ['pcpn']
    elif program == 'Soddd':
        elements = ['maxt', 'mint']
    elif program in ['Sodmonline', 'Sodmonlinemy']:
        elements = [form_input['element']]
    elif program == 'Sodlist':
        elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst']
    elif program == 'Sodcnv':
        elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint']
    else:
        elements = []
    return elements

#Routine to compute percentiles, needed for Sodpct
def pctil(app_name, data, number, npctil):
    #number  number of data elements
    #sort contains sorted values low to high
    #npctil number of percentiles
    #pctile percentiles in ascending order
    #xmed median of distribution
    xmax = -100000000.0
    dummy = [data[i] for i in range(number)]
    sort = [0.0 for i in range(number)]
    pctile = [0.0 for i in range(npctil-1)]
    for i in range(number):
        try:
            xmax = max(xmax,dummy[i])
        except:
            pass
    for islow in range(number):
        xmin = 100000000.0
        # For each element of sort, find lowest of the vaues
        iskip = None
        for ifast in range(number):
            if dummy[ifast] <= xmin:
                xmin = dummy[ifast]
                iskip = ifast

        sort[islow] = xmin
        if iskip is not None:
            dummy[iskip] = xmax + 1
    #Find the median:
    if number % 2  == 0:
        xmed = (sort[number/2 - 1 ] + sort[(number/2)]) / 2
    else:
        xmed = sort[(number/2)]

    #Find percentiles
    frac = float(number) /  float(npctil)

    # Note that there are one less percentile separators than percentiles
    for i in range(npctil -1 ):
        dum = frac * float(i+1) + 0.5
        idum = int(dum)

        if app_name == 'Sodthr':
            if sort[idum - 1] < -0.5 or sort[idum] < -0.5:
                pctile[i] = -1
            elif sort[idum - 1] > 366.5 or sort[idum] > 366.5:
                pctile[i] =  367
            else:
                pctile[i] = sort[idum -1] + (dum - float(idum)) * (sort[idum] - sort[idum-1])
        else:
            pctile[i] = sort[idum -1] + (dum - float(idum)) * (sort[idum] - sort[idum-1])
    if app_name == 'Sodpct':
        return pctile, sort
    elif app_name == 'Sodthr':
        return pctile, sort, xmed

#Routine to filter out data according to window specification(sodlist)
#######################################################################
def get_windowed_data(data, start_date, end_date, start_window, end_window):
    if start_window == '0101' and end_window == '1231':
        windowed_data = data
    else:
        windowed_data = []
        start_indices=[]
        end_indices=[]
        if start_date == 'por':
            start_d = ''.join(data[0][0].split('-'))
        else:
            start_d = start_date
        if end_date == 'por':
            end_d = ''.join(data[-1][0].split('-'))
        else:
            end_d = end_date
        st_yr = int(start_d[0:4])
        st_mon = int(start_d[4:6])
        st_day = int(start_d[6:8])
        end_yr = int(end_d[0:4])
        end_mon = int(end_d[4:6])
        end_day = int(end_d[6:8])
        #Date formatting needed to deal with end of data and window size
        #doy = day of year
        if WRCCUtils.is_leap_year(st_yr) and st_mon > 2:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday -1
        else:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday
        if WRCCUtils.is_leap_year(end_yr) and end_mon > 2:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday - 1
        else:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday
        doy_window_st = WRCCUtils.compute_doy(start_window[0:2], start_window[2:4])
        doy_window_end = WRCCUtils.compute_doy(end_window[0:2], end_window[2:4])
        dates = [data[i][0] for i  in range(len(data))]
        start_w = '%s-%s' % (start_window[0:2], start_window[2:4])
        end_w = '%s-%s' % (end_window[0:2], end_window[2:4])
        #silly python doesn't have list.indices() method
        #Look for windows in data
        for i, date in enumerate(dates):
            if date[5:] == start_w:
                start_indices.append(i)
            if date[5:] == end_w:
                end_indices.append(i)
        #Check end conditions at endpoints:
        if doy_window_st == doy_window_end:
            pass
        elif doy_window_st < doy_window_end:
            if doy_first <= doy_window_end and doy_window_st < doy_first:
                start_indices.insert(0, 0)
            if doy_last < doy_window_end and doy_window_st <= doy_last:
                end_indices.insert(len(dates),len(dates)-1)
        else: #doy_window_st > doy_window_end
            if (doy_window_st > doy_first and doy_first <= doy_window_end) or (doy_window_st < doy_first and doy_first >= doy_window_end):
                start_indices.insert(0, 0)
            if (doy_last <= doy_window_st and doy_last < doy_window_end) or (doy_window_st <= doy_last and doy_last > doy_window_end):
                end_indices.insert(len(dates),len(dates)-1)
        #Sanity check
        if len(start_indices)!= len(end_indices):
            print 'Index error when finidng window. Maybe your window is not chronologically defined?'
            sys.exit(1)

        for j in range(len(start_indices)):
            add_data = data[start_indices[j]:end_indices[j]+1]
            windowed_data = windowed_data + add_data
    return windowed_data


##################
#Sodxrmts routines
##################

####################################
#PearsonIII routines: Pintp3, Capiii
####################################

'''
Pintp3
This routine interpolates in the piii table
Inputs:
prnoex = probability of non-exceedance
averag = average of the distribution
stdev = standard deviation of the distribution
skew = skewness of the distribution
piii = input array of PearsonIII frequency distribution
piiili = list of probabilities in piii array
npiili = len(piiili)
Output:
psdout = probability of non-exceedance expressed in standard deviations
'''
def Pintp3(prnoex, piii, piiili, npiili, averag, stdev, skew):
    if skew > 9.0:skew = 9.0
    if skew < -9.0:skew = -9.0

    nsklo = int(10.0*skew)
    if nsklo < -90:nsklo = -90
    nskhi = nsklo + 1
    if nskhi > 90: snkhi = 90
    #Index if non-exceedace probabilty
    inonpr = 0
    while inonpr <= 26:
        inonpr+=1
        test = piiili[inonpr - 1]
        if test > prnoex:
            npnolo = inonpr - 2
            npnohi = inonpr - 1
            if inonpr != 1:
                pnoxlo = piiili[npnolo]
                pnoxhi = piiili[npnohi]
            else:
                npnolo = inonpr - 1 #Check this, cant find what IRETRN is
                npohi = inonpr - 1 #Check this, cant find what IRETRN is
                pnoxlo = piiili[npnolo] - 0.00001
                pnoxhi = piiili[npnohi]
        else:
            if inonpr != 27:
                continue
            else:
                npnolo = 25 # Check this whole section, Kelly's does not make sense to me
                npnohi = 26
                pnoxlo = piiili[npnolo]
                pnoxhi = piiili[npnohi]

    if nsklo < -90:
        y1 = piii[-90][npnolo]
        y2 = piii[-90][npnolo]
        y3 = piii[-90][npnohi]
        y4 = piii[-90][npnohi]
    elif nskhi > 90:
        y1 = piii[90][npnolo]
        y2 = piii[90][npnolo]
        y3 = piii[90][npnohi]
        y4 = piii[90][npnohi]
    else:
        y1 = piii[nsklo][npnolo]
        y2 = piii[nskhi][npnolo]
        y3 = piii[nskhi][npnohi]
        y4 = piii[nsklo][npnohi]

    if abs(pnoxhi - pnoxlo) > 0.000001:
        t = (prnoex - pnoxlo) / (pnoxhi - pnoxlo)
    else:
        t = 0.0
    nskhi = nsklo +1
    u = (10.0 * skew - float(nsklo)) / (float(nskhi) - float(nsklo))
    a1 = u * (y2 - y1) + y1
    a2 = u * (y3 - y4) + y4
    psdout = t * (a2 - a1) + a1
    #psdout =  (1.0 - t)*(1.0 - u)*y1 + t*(1.0 - u)*y2 + t*u*y3 + (1.0 - t)*u*y4
    return psdout
'''
Capiii
Subroutine adapted from old Fortran program, mixture of cases thus results.
Finds values of the Pearson III distribution from lookup tables calculated
by Jim Goodridge.  For non-exceedance probabilities not in these tables,
simple linear interpolation is used.
Reference:  Selection of Frequency Distributions, with tables for
Pearson Type III, Log-Normal, Weibull, Normal and Gumbel
Distributions.  Baolin Wu and Jim Goodridge, June 1976,
California Department of Water Resources, 85 pp.
data is a large array (n=50000) containing the data
numdat is the actual number of data points in the array 'data'
pnlist is an array with the list of nonexceedance probabilities desired
piii is a 2-dimensional array containing the Pearson III look-up tables
piiili is an array containing the npiili nonexceedance values in the tables
npiili is the number (27) of values in piiili
ave is the average
sk is the skewness
cv is the coefficient of variation
xmax is the max value
xmin is the min value
psd is an array containing the numpn nonexceedance values
'''
def Capiii(xdata, numdat, piii, piiili,npiili, pnlist,numpn):
    xmax = -9999.0
    xmin = 9999.0
    summ = 0.0
    summ2 = 0.0
    summ3 = 0.0
    count = 0.0
    #loop over the number of values in the array
    for ival in range(numdat):
        value = xdata[ival]
        if value >= -9998.0:
            summ+=value
            summ2+=value*value
            summ3+=value*value*value
            count+=1
            if value > xmax:xmax = value
            if value < xmin:xmin = value
    if count > 0.5:
        ave = summ / count
    else:
        ave = 0.0
    if count > 1.5:
        try:
            stdev = numpy.sqrt((summ2 - summ*summ/count)/(count - 1.0))
        except:
            stdev = 0.0
    else:
        stdev = 0.0

    if abs(ave) > 0.00001:
        cv = stdev / ave
    else:
        cv = 0
    if count > 1.5:
        h1 = summ / count
        h2 = summ2 / count
        h3 = summ3 /count
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
    #loop over the desired non-exceedance probabilities
    psd = [0 for k in range(numpn)]
    for ipn in range(numpn):
        prnoex  = pnlist[ipn]
        psd[ipn] = Pintp3(prnoex, piii, piiili, npiili, ave, stdev, sk)

    return psd, ave, stdev, sk, cv, xmax, xmin

###########################################################################
#GEV routines: Samlmr Gev, Quantgev, Cdfgev, Lmrgev, Pelgev, Quagev, Reglmr, Salmr,
#Ampwm, Derf, Diagmd, Dlgama, Durand, Gamind, Quastn, Sort
##########################################################################
#Obtained from Jim Angel @ MrCC in Champaign, Illinois

#Samlmr
#SAMPLE L-MOMENTS OF A DATA ARRAY
#
#  PARAMETERS OF ROUTINE:
#  X      * INPUT* ARRAY OF LENGTH N. CONTAINS THE DATA, IN ASCENDING
#                  ORDER.
#  N      * INPUT* NUMBER OF DATA VALUES
#  XMOM   *OUTPUT* ARRAY OF LENGTH NMOM. ON EXIT, CONTAINS THE SAMPLE
#                  L-MOMENTS L-1, L-2, T-3, T-4, ... .
#  NMOM   * INPUT* NUMBER OF L-MOMENTS TO BE FOUND. AT MOST MAX(N,20).
#  A      * INPUT* ) PARAMETERS OF PLOTTING
#  B      * INPUT* ) POSITION (SEE BELOW)
#
#  FOR UNBIASED ESTIMATES (OF THE LAMBDA'S) SET A=B=ZERO. OTHERWISE,
#  PLOTTING-POSITION ESTIMATORS ARE USED, BASED ON THE PLOTTING POSITION
#  (J+A)/(N+B)  FOR THE J'TH SMALLEST OF N OBSERVATIONS. FOR EXAMPLE,
#  A=-0.35D0 AND B=0.0D0 YIELDS THE ESTIMATORS RECOMMENDED BY
#  HOSKING ET AL. (1985, TECHNOMETRICS) FOR THE GEV DISTRIBUTION.
def Samlmr(x, n, nmom, a, b):
    summ = [0.0 for k in range(nmom)]
    xmom = [0.0 for k in range(nmom)]

    #if a <= -1 or a > b:
    #    xmom = [-99999 for k in range(nmom)]

    if a != 0 or b != 0:
        #Plotting-Position estimates of PWM's
        for i in range(n):
            ppos = (i+1 + a) / (n + b)
            term = x[i]
            summ[0]+=term
            for j in range(1,nmom):
                term*=ppos
                summ[j]+=term
        for j in range(nmom):
            summ[j] = summ[j] /n

    else: #a and b are zero
        #Unbiased estimates of of pwm's
        for i in range(n):
            z = i+1
            term = x[i]
            summ[0]+=term
            for j in range(1,nmom):
                z-=1
                term*=z
                summ[j]+=term
        y = n
        z = n
        summ[0] = summ/z
        for j in range(1,nmom):
            y-=1
            z*=y
            summ[j] = summ[j]/z

    #L-Moments
    k = nmom
    p0 = 1
    if nmom - nmom / 2 * 2 == p0:p0 = -1
    for kk in range(1,nmom):
        ak = k
        p0 = -p0
        p =  p0
        temp = p * summ[0]
        for i in range(k-1):
            ai = i+1
            p = -p*(ak+ai-1) * (ak - ai) / (ai**2)
            temp+=p*summ[i+1]
        summ[k-1] = temp
        k-=1
    xmom[0] = summ[0]
    xmom[1] = summ[1]
    if abs(summ[1] - 0.0) > 0.001:
        for k in range(2, nmom):
            xmom[k] = summ[k] / summ[1]
    return xmom

#Dlgama: LOGARITHM OF GAMMA FUNCTION
def Dlgama(x):
    #c[0] - c[7] are the coeffs of the asymtotic expansion of dlgama
    c = [0.91893, 0.83333, -0.27777, 0.79365, \
        -0.59523, 0.84175, -0.19175, 0.64102]
    s1 = -0.57721 #Euler constant
    s2 = 0.82246  #pi**2/12
    dlgama =  0
    if x < 0 or x > 2.0e36:
        pass
    #Use small-x approximation if x is near 0,1 or 2
    if abs(x - 2)  <= 1.0e-7:
        dlgama = numpy.log(x - one)
        xx = x - 2
        dlgama+=xx*(s1+xx*s2)
    elif abs(x - 1) <= 1.0e-7:
        xx = x - 1
        dlgama+=xx*(s1+xx*s2)
    elif abs(x) <= 1.0e-7:
        dlgama = -numpy.log(x) + s1*x
    else:
        #Reduce to dlgama(x+n) where x+n >= 13
        sum1 = 0
        y = x
        if y <13:
            z =1
            while y < 13:
                z*=y
                y+=1
            sum1+= - numpy.log(z)
        #Use asymtotic expansion if y >=13
        sum1+=(y - 0.5)* numpy.log(y) -y +c[0]
        sum2 = 0
        if y < 1.0e9:
            z = 1 / y*y
            sum2 = ((((((c[7]*z + c[6])*z + c[5])*z + c[4])*z + c[3])*z + c[2])*z +c[1]) / y

        dlgama = sum1 + sum2
    return dlgama

#Pelgev
#Parameter Estomation via L-Moments for the generalized extreme value distribution
#XMOM   * INPUT* ARRAY OF LENGTH 3. CONTAINS THE L-MOMENTS LAMBDA-1,
#LAMBDA-2, TAU-3.
#PARA   *OUTPUT* ARRAY OF LENGTH 3. ON EXIT, CONTAINS THE PARAMETERS
#IN THE ORDER XI, ALPHA, K (LOCATION, SCALE, SHAPE).
#Uses Dlgama
def Pelgev(xmom):
    eu = 0.57721566
    dl2 = 0.69314718
    dl3 = 1.0986123
    z0 = 0.63092975
    c = [7.817740,2.930462,13.641492,17.206675]
    maxit = 20
    #Initial estimate of k
    t3 = xmom[2]
    if xmom[1] <= 0 or abs(t3) > 1:
        para = [-9999, -9999, -9999]
    else:
        z = 2 /(t3 + 3) - z0
        g = z*(c[0] + z*(c[1] + z*(c[2] + z*c[3])))

        #Newton-Raphson, if required

        if t3 < - 0.1 or t3 > 0.5:
            if t3 < -0.9: g = 1 - numpy.log(1 + t3) / dl2
            t0 = (t3 + 3) / 2
            for it in range(1, maxit+1):
                x2 = 2**(-g)
                x3 = 3**(-g)
                xx2 = 1 - x2
                xx3 = 1 - x3
                t = xx3 / xx2
                deri = (xx2*x3*dl3 - xx3*x2*dl2) / (xx2*xx2)
                gold = g
                g = g - (t -t0) / deri
                if abs(g - gold)< 1.0e-6: break
                if g > 1 and abs(g - gold) <= 1.0e-6*g:break
        para = [0, 0, 0]
        if abs(g) >= 1.0e-5:
            para[2] = g
            gam = numpy.exp(Dlgama(1+g))
            para[1] = xmom[1]*g / (gam*(1 - 2**(-g)))
            para[0] = xmom[0] -para[1]*(1 - gam) / g
        else:
            para[2] = 0
            para[1] = xmom[1] / dl2
            para[0] = xmom[0] - eu * para[1]
    return para




#Gev
#Subroutine to calculate the three parameters of the Gev
def Gev(x, n):
    x_sorted = []
    x_sorted_keys = sorted(x, key=x.get)
    for key in x_sorted_keys:
        x_sorted.append(x[key])
    nmom = 3
    xmom = Samlmr(x_sorted, n, nmom, -0.35, 0)
    para = Pelgev(xmom)
    return para

#######################################################################
#beta-p routines
########################################################################
