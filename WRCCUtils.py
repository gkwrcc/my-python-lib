#!/usr/bin/python

'''
Module WRCCUtils
'''

import datetime, time, sys, os
import re
import json
import numpy,math
import re
from collections import defaultdict, Mapping, Iterable
import smtplib
from email.mime.text import MIMEText
from ftplib import FTP
from math import sqrt
import colorsys

from django.http import HttpResponse, HttpResponseRedirect

import WRCCClasses, AcisWS, WRCCData, WRCCUtils
####################################
#FUNCTIONS
#####################################
def get_station_ids(stn_json_file_path):
    '''
    finds all station ids of the
    stations listed in the json file
    Used at statiion locator app to set initial station ids for
    link to data find
    '''
    stn_ids = ''
    json_data = {'stations':[]}
    try:
        with open(stn_json_file_path, 'r') as json_f:
            json_data = u_convert(json.loads(json_f.read()))
    except:
        passs
    name_previous = ''
    for idx,stn in enumerate(json_data['stations']):
        if stn['name'] == name_previous:
            continue
        name_previous = stn['name']
        stn_ids+=stn['sids'][0]
        if idx < len(json_data['stations']) - 1:
            stn_ids+=','
    return stn_ids

def convert_to_metric(element, value):
    el,base_temp = get_el_and_base_temp(element)
    try:
        float(value)
    except:
        return value
    if el in ['maxt','mint','avgt','obst', 'yly_maxt', 'yly_mint', 'mly_maxt', 'mly_mint']:
        v = round((float(value) - 32.0)*5.0/9.0,1)
    elif el in ['hdd','cdd','gdd']:
        #Since a temperature difference of 1C is equivalent to a temperature difference of 1.8F,
        #Fahrenheit-based degree days are 1.8 times bigger than their equivalent Celsius-based degree days.
        v = int(round(float(value)*10.0/18.0))
    elif el in ['pcpn','snow','snwd','evap','yly_pcpn', 'mly_pcpn']:
        v = round(float(value)*25.4,2)
    elif el in ['wdmv']:
        v = round(float(value)*1.60934,1)
    elif el =='elev':
        #Feet to meter
        v = round(float(value)/3.280839895,1)
    else:
        v = value
    return v

def convert_to_english(element, value):
    el,base_temp = get_el_and_base_temp(element)
    try:
        float(value)
    except:
        return value
    if el in ['maxt','mint','avgt','obst','yly_maxt', 'yly_mint', 'mly_maxt', 'mly_mint']:
        v = int(round(9.0/5.0*float(value) + 32.0,1))
    elif el in ['hdd','cdd','gdd']:
        #Since a temperature difference of 1C is equivalent to a temperature difference of 1.8F,
        #Fahrenheit-based degree days are 1.8 times bigger than their equivalent Celsius-based degree days.
        v = int(round(float(value)*18.0/10.0))
    elif el in ['pcpn','snow','snwd','evap','mly_pcpn', 'yly_pcpn']:
        v = round(float(value)/25.4,2)
    elif el in ['wdmv']:
        v = int(round(float(value)/1.60934,1))
    elif el =='elev':
        #meter to feet
        v = round(float(value)*3.280839895,1)
    else:
        v = value
    return v

def set_back_date(days_back):
    '''
    Calculates today - days_back
    and returns the back date in format
    yyyymmdd
    '''
    try:
        int(days_back)
    except:
        return '99990101'
    tdy = datetime.datetime.today()
    #Choose default start_date 4 weeks back
    b = datetime.datetime.today() - datetime.timedelta(days=int(days_back))
    yr_b = str(b.year);mon_b = str(b.month);day_b = str(b.day)
    if len(mon_b) == 1:mon_b = '0%s' % mon_b
    if len(day_b) == 1:day_b = '0%s' % day_b
    back_date = '%s%s%s' % (yr_b, mon_b, day_b)
    return back_date

def get_N_HexCol(N=5):
    '''
    Generates HEX color list of size N
    '''
    HSV_tuples = [(x*1.0/N, 0.5, 0.5) for x in range(N)]
    RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
    RGB_tuples = map(lambda x: tuple(map(lambda y: int(y * 255),x)),RGB_tuples)
    HEX_tuples = map(lambda x: tuple(map(lambda y: chr(y).encode('hex'),x)), RGB_tuples)
    HEX_list = map(lambda x: "".join(x), HEX_tuples)

    return HEX_list


def check_for_file(dir_location, file_name):
    '''
    Checks if file exists in dir_location
    '''
    #Check if kml file exists, if not generate it
    file_path =  dir_location + file_name
    file_exists = True
    try:
        with open(file_path, 'r') as kml_f:
            pass
    except:
        file_exists = False
    return file_exists


def generate_kml_file(area_type, state, kml_file_name, dir_location):
    '''
    This functions makes a call to ACIS General
    Server=/General/<area_type>   params={"state":<state>,"meta":"id,name,bbox,geojson"}
    Then uses the information to generate a kml
    file with name kml_file, that is used to generate an overlay map
    of the area_type in the state.
    Returned is a status update. If file already existed or was successfully
    created, a 'Success' string is returned. Else and error message string is returned
    The kml file is put into dir_location. dir_location is an
    absolute path on local host
    '''
    #Check if kml file already exists in dir_loc
    if str(dir_location)[-1]!='/':
        dr = str(dir_location) + '/'
    elif str(dir_location)[0]!='/':
        return 'Need absolute path of directory. You entered: %s' %str(dir_location)
    else:
        dr = str(dir_location)
    '''
    try:
        with open(dr + kml_file_name):
            pass

        os.remove(dr + kml_file_name)
    except:
        pass
    '''
    try:
        with open(dr + kml_file_name):
            if os.stat(dr + kml_file_name).st_size==0:
                os.remove(dr + kml_file_name)
            else:
                return 'Success'
    except IOError:
        pass

    #Make General call to get the geojson for the input params
    req = AcisWS.make_gen_call_by_state(WRCCData.SEARCH_AREA_FORM_TO_ACIS[str(area_type)], str(state))
    #Sanity Check:
    if 'error' in req.keys():
        return str(req['error'])
    else:
        if not 'meta' in req.keys():
            return 'No meta data found for search area %s and state %s' %(str(area_type), str(state))
    json_data = req['meta']
    if not isinstance(json_data, list):
        return 'Not a valid json_data list: %s' % str(json_data)
    #Write kml file
    try:
         kml_file = open(dr + kml_file_name, 'w+')
    except:
        return 'Could not open kml file: %s' %(dr + kml_file_name)
    num = len(json_data)
    colors = get_N_HexCol(N=num)

    #Header
    kml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    kml_file.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    kml_file.write('  <Document>\n')
    #Styles
    for poly_idx, poly in enumerate(json_data):
        kml_file.write('    <Style id="poly%s">\n' %poly_idx)
        kml_file.write('      <LineStyle>\n')
        #kml_file.write('        <color>%s</color>\n' %str(colors[poly_idx]))
        kml_file.write('        <width>1.5</width>\n')
        kml_file.write('      </LineStyle>\n')
        kml_file.write('      <PolyStyle>\n')
        #kml_file.write('        <color>%s</color>\n' %str(colors[poly_idx]))
        kml_file.write('        <color>0000FF</color>\n')
        #kml_file.write('        <colorMode>normal</colorMode>\n')
        kml_file.write('        <fill>1</fill>\n')
        #kml_file.write('        <outline>1</outline>\n')
        kml_file.write('      </PolyStyle>\n')
        kml_file.write('    </Style>\n')
    #Polygons
    for poly_idx, poly in enumerate(json_data):
        poly_bbox = poly['bbox']
        if 'state' in poly.keys():
            poly_state = poly['state']
        else:
            poly_state = ''
        coords = poly['geojson']['coordinates'][0][0]
        #Remove special characters from name
        name = re.sub('[^a-zA-Z0-9\n\.]', ' ', poly['name'])

        kml_file.write('    <Placemark>\n')
        kml_file.write('      <name>%s</name>\n' %poly['id'])
        kml_file.write('      <description>%s, %s</description>\n' %(name, poly['id']))
        kml_file.write('      <styleUrl>#poly%s</styleUrl>\n' %poly_idx)
        kml_file.write('      <Polygon>\n')
        kml_file.write('      <tessellate>1</tessellate>\n')
        kml_file.write('        <extrude>1</extrude>\n')
        kml_file.write('        <altitudeMode>relativeToGround</altitudeMode>\n')
        kml_file.write('        <outerBoundaryIs>\n')
        kml_file.write('          <LinearRing>\n')
        kml_file.write('            <coordinates>\n')

        for idx, lon_lat in enumerate(coords):
            kml_file.write('              %s,%s,%s\n' %(lon_lat[0], lon_lat[1],0))
        #Add first coordinate to close polygon
        #kml_file.write('              %s,%s,%s\n' %(coords[0][0], coords[0][1],0))
        kml_file.write('            </coordinates>\n')
        kml_file.write('          </LinearRing>\n')
        kml_file.write('        </outerBoundaryIs>\n')
        kml_file.write('      </Polygon>\n')
        kml_file.write('    </Placemark>\n')

    #Footer
    kml_file.write('  </Document>\n')
    kml_file.write('</kml>\n')
    kml_file.close

    return 'Success'


def find_bbox_of_shape(shape):
    '''
    Given a shape, i.e., a list of lon, lat coordinates
    defining the shape, this function find the enclosing bounding box
    '''
    lons_shape = [s for idx,s in enumerate(shape) if idx%2 == 0]
    lats_shape = [s for idx,s in enumerate(shape) if idx%2 == 1]
    try:
        bbox = str(min(lons_shape)) + ',' + str(min(lats_shape)) + ',' + str(max(lons_shape)) + ',' + str(max(lats_shape))
    except:
        bbox= None
    return bbox

def find_bbox_of_circle(lon, lat, r):
    '''
    Given center coordinates lon, lat of a circle
    and radius r in meters, this function returns the W,S,E,N
    coordinates of the enclosing bounding box
    lon, lat are given in degrees
    r is given in meters
    '''
    R = 6378.1 #Radius of the Earth in km
    brngs = [3*math.pi/2,math.pi,math.pi/2,0]  #Bearing radians W,S,E,N.
    d = r / 1000.0  #Distance in km

    lat1 = math.radians(lat) #Current lat point converted to radians
    lon1 = math.radians(lon) #Current long point converted to radians

    bbox = ''
    for idx,brng in enumerate(brngs):
        lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +math.cos(lat1)*math.sin(d/R)*math.cos(brng))
        if idx %2 == 0: #90, 180%, want to pick up lon
            coord = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),math.cos(d/R)-math.sin(lat1)*math.sin(lat2))
        else:#pick lat
            coord = lat2
        #Convert back to degrees
        coord = math.degrees(coord)
        if idx == 0:
            bbox+=str(coord)
        else:
            bbox+=',' + str(coord)
    return bbox

def get_bbox(shape):
    '''
    shape is a str of lon, lat coordinates of
    a polygon or lon, lat, r of a circle
    output is the type of the shape (circle or polygon)
    and the enclosing bounding_box of the polygon or circle
    '''
    s = shape.split(',')
    s = [float(k) for k in s]
    if len(s)==3:
        t = 'circle'
        bbox = find_bbox_of_circle(s[0], s[1], s[2])
    elif len(s) == 4: #bbox
        t = 'bbox'
        bbox = find_bbox_of_shape(s)
    elif len(s) == 2:
        t = 'location'
        bbox = str(s[0] - 0.1) + ',' + str(s[1] - 0.1) + ',' + str(s[0] + 0.1) + ',' + str(s[1] + 0.1)
    else:
        t = 'polygon'
        bbox = find_bbox_of_shape(s)

    return t, bbox


def point_in_circle(x,y,circle):
    '''
    Determine if a point is inside a given cicle
    [lon, lat, radius]
    lon, lat are given in degrees, r is given in meters
    the distance between the point and the center of the circle is
    computed via the Haversine formula
    '''
    R = 6378.1 #Radius of the Earth in km
    #Find distance between point and center of circle
    try:
        dlat = math.radians((y - circle[1]))
        dlon = math.radians((x - circle[0]))
        lat1 = math.radians(y)
        lat2 = math.radians(circle[1])
        #Haversine Formula
        a = math.sin(dlat/2)**2 + math.sin(dlon/2)**2 * math.cos(lat1)*math.cos(lat2)
        c = 2*math.atan2(math.sqrt(a),math.sqrt(1-a))
        dist = R*c
        if dist <= circle[2] / 1000.0:
            return True
        else:
            return False
    except:
        return False

def point_in_poly(x,y,poly):
    '''
    Determine if a point is inside a given polygon or not
    Polygon is a list of (x,y) pairs. This function
    returns True or False.  The algorithm is called
    the "Ray Casting Method".
    '''
    n = len(poly)
    inside = False
    try:
        p1x,p1y = poly[0]
        for i in range(n+1):
            p2x,p2y = poly[i % n]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x,p1y = p2x,p2y
    except:
        pass
    return inside

def set_poly_and_PointIn(prms):
    poly = None;PointIn=None
    if 'shape' in prms.keys():
        shape = prms['shape']
        if isinstance(shape, basestring):
            shape = shape.replace(' ','').split(',')
        if not isinstance(shape, list):
            shape = list(shape)
        shape = [float(sh) for sh in shape]
        if len(shape) == 3:#circle
            poly = shape
            PointIn = getattr(WRCCUtils,'point_in_circle')
        elif len(shape)== 4:#bbox
            poly = [(shape[0],shape[1]),(shape[0],shape[3]),(shape[2],shape[3]),(shape[2],shape[1])]
            PointIn = getattr(WRCCUtils,'point_in_poly')
        else:
            poly = [(shape[2*idx],shape[2*idx+1]) for idx in range(len(shape)/2)]
            PointIn = getattr(WRCCUtils,'point_in_poly')
    else:
        if 'basin' in prms.keys():
            sh = AcisWS.find_geojson_of_area('basin', prms['basin'])
        if 'location' in prms.keys():
            s = prms['location'].replace(' ','').split(',')
            sh = [(s[0],s[1])]
        if 'county_warning_area' in prms.keys():
            sh = AcisWS.find_geojson_of_area('cwa', prms['county_warning_area'])
        if 'climate_division' in prms.keys():
            sh = AcisWS.find_geojson_of_area('climdiv', prms['climate_division'])
        if 'county' in prms.keys():
            sh = AcisWS.find_geojson_of_area('county', prms['county'])
        if 'bounding_box' not in prms.keys() and not 'state' in prms.keys():
            poly = [(s[0],s[1]) for s in sh]
            PointIn = getattr(WRCCUtils,'point_in_poly')
    return poly, PointIn

def check_for_int(string):
    try:
        int(string)
        return True
    except:
        return False

def convert_db_dates(messy_date):
    '''
    Converts postgres dates into format yyyy-mm-dd
    For metadata tool: metadata load tables population
    '''
    #Check if input is datetime object, convert if necessary
    if type(messy_date) is datetime.date or type(messy_date) is datetime.datetime:
        return datetime.datetime.strftime(messy_date,"%Y-%m-%d")
    #Check if data is already in form yyyy-mm-dd
    date_list = messy_date.split('-')
    if len(date_list) == 3 and len(date_list[0]) == 4:
        if check_for_int(date_list[0]) and check_for_int(date_list[1]) and check_for_int(date_list[2]):
            for idx,dat in enumerate(date_list[1:3]):
                if len(dat) ==1:date_list[idx] = '0' + dat
            return '-'.join(date_list)
    date_list = messy_date.split(' ')
    #Sanity check
    if len(date_list)!= 3:
        return '0000-00-00'

    try:
        mon = WRCCData.MONTH_NAME_TO_NUMBER[date_list[0][0:3]]
    except:
        mon = '00'
    try:
        day = date_list[1][0:2]
        if day[-1] == ',' or len(day) ==1:
            day = '0' + day[0]
    except:
        day = '00'
    year = date_list[2]
    if len(year) != 4:
        year = '0000'
    try:
        int(year)
    except:
        year = '0000'

    return '-'.join([year, mon, day])



def upload(ftp_server,pub_dir,f):
    '''
    Uploads file to ftp_server
    in directory pub_dir
    '''
    try:
        fname = os.path.split(f)[1]
        ftp = FTP(ftp_server)
        ftp.login()
        ftp.set_debuglevel(0)
        try:
            ftp.cwd(pub_dir)
        except:
            #Need to create sub_directories one by one
            dir_list = pub_dir.strip('/').split('/')
            sub_dir = ''
            for d in dir_list:
                sub_dir = sub_dir +  '/' + d
                try:
                    ftp.cwd(sub_dir)
                except:
                    print 'Creating Directory: %s on %s' % (sub_dir, ftp_server)
                    ftp.mkd(sub_dir)
        try:
            ftp.cwd(pub_dir)
        except:
            error = 'File: %s Upload error. Could not create directory %s on server %s' %(f,pub_dir, ftp_server)
        ext = os.path.splitext(f)[1]
        #Check if file is already there
        print ftp.nlst()
        if fname in ftp.nlst():
            pass
        else:
            if ext in (".txt", ".htm", ".html", ".json"):
                ftp.storlines('STOR %s' % fname, open(f))
            else:
                ftp.storbinary('STOR %s' % fname, open(f, 'rb'), 1024)
        ftp.quit()
        error = None
    except Exception, e:
        error = 'File: %s Upload error: %s' %(f, str(e))
    return error


def write_email(mail_server,fromaddr,toaddr,subject, message):
    '''
    Write e-mail via pythons  smtp module
    '''
    msg = "From: %s\nTo: %s\nSubject:%s\n\n%s" % ( fromaddr, toaddr, subject, message )

    try:
        server = smtplib.SMTP(mail_server)
        server.set_debuglevel(1)
        server.sendmail(fromaddr, toaddr, msg)
        server.quit()
        error = None
    except Exception, e:
        error = 'Email attempt to recipient %s failed with error %s' %(toaddr, str(e))
    return error


def u_convert(data):
    '''
    Unicode converter, needed to write json files
    '''
    if isinstance(data, unicode):
        return str(data)
    elif isinstance(data, Mapping):
        return dict(map(u_convert, data.iteritems()))
    elif isinstance(data, Iterable):
        return type(data)(map(u_convert, data))
    else:
        return data

def find_mon_len(year,mon):
    if is_leap_year(int(year)):
        feb = 29
    else:
        feb = 28
    mon_lens = [31,feb, 31,30, 31,30, 31, 31,30, 31, 30, 31]
    m_idx = int(str(mon).lstrip('0')) -1
    return mon_lens[m_idx]

def write_griddata_to_file(data, form, f=None, request=None):
    '''
    Writes gridded data to a file.

    Keyword aruments:
    data             -- data to write to file
    form             -- form input dictionary containing:
        elements         -- list of climate elements
        delim            -- delimiter used to separate data vaules
        file_extension   -- format of output data file (.dat, .txt, .xls)
        output_file_name -- Name of output file. If default DataRequest, a time stamp will be added.
    f                -- file name (default None)
    request          -- data request object (default None)
    If a file f is given, data will be written to file.
    If a request object is given, the file will be generated
    via the CSC webpages
    '''
    time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    file_extension = WRCCData.FILE_EXTENSIONS[form['data_format']]
    elev_unit = 'ft'
    if form['units'] == 'metric':elev_unit = 'm'
    if isinstance(form['elements'],list):
        el_list = form['elements']
    else:
        el_list = form['elements'].replace(' ','').split(',')
    #set file name
    if 'output_file_name' in form.keys():
        file_name = form['output_file_name']
    else:
        file_name = 'DataRequest_'+ time_stamp
    #sanity check:
    if not f and not request:
        return 'Error! Need either a file or a reqest object!'
    elif f and request:
        return 'Error! Choose one of file f or request object'

    if file_extension in ['.dat', '.txt']:
        delim = WRCCData.DELIMITERS[form['delimiter']]
        import csv
        if request:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (file_name,file_extension)
            writer = csv.writer(response, delimiter=delim )
        else: #file f given
            try:
                csvfile = open(f, 'w+')
                writer = csv.writer(csvfile, delimiter=delim )
                response = None
            except Exception, e:
                #Can' open user given file, create emergency writer object
                writer = csv.writer(open('/tmp/csv.txt', 'w+'), delimiter=delim)
                response = 'Error! Cant open file' + str(e)

        #Find length of date values
        #header
        header_seperator = ':'
        if delim== ':':
            header_seperator = ' '
        row = ['*'+ str(WRCCData.DISPLAY_PARAMS[form['select_grid_by']]),str(form[form['select_grid_by']])]
        writer.writerow(row)
        if form['data_summary'] == 'none':
            row = ['*'+'DataSummary','None']
        else:
            row = ['*DataSummary',form['data_summary']+'_'+form[form['data_summary'] + '_summary']]
        writer.writerow(row)
        row = ['*Units',form['units']]
        writer.writerow(row)
        if form['data_summary'] == 'spatial':
            row = ['*Date']
        elif form['data_summary'] == 'temporal':
            row = ['*DateRange', 'Lat', 'Lon', 'Elev']
        else:
            row = ['*Date', 'Lat', 'Lon', 'Elev(' + elev_unit + ')' ]
        for el in el_list:
            el_strip, base_temp = get_el_and_base_temp(el)
            if form['units'] == 'metric':
                el_unit = WRCCData.UNITS_METRIC[el_strip]
            else:
                el_unit = WRCCData.UNITS_ENGLISH[el_strip]
            row.append('%s(%s)' %(str(el),el_unit))
        writer.writerow(row)
        for date_idx, date_vals in enumerate(data):
            row = []
            for idx, dat in enumerate(date_vals):
                row.append('%s' % str(dat))
            writer.writerow(row)
        try:
            csvfile.close()
        except:
            pass
    elif file_extension == '.json':
        with open(f, 'w+') as jsonf:
            import json
            json.dump(data, jsonf)
            response = None
    else: #Excel
        from xlwt import Workbook
        wb = Workbook()
        #Note row number limit is 65536 in some excel versions
        row_number = 0
        flag = 0
        sheet_counter = 0
        for date_idx, date_vals in enumerate(data): #row
            for j, val in enumerate(date_vals):#column
                if row_number == 0:
                    flag = 1
                else:
                    row_number+=1
                if row_number == 65535:flag = 1

                if flag == 1:
                    sheet_counter+=1
                    #add new workbook sheet
                    ws = wb.add_sheet('Sheet_%s' %sheet_counter)
                    #Header lines
                    ws.write(0,0,WRCCData.DISPLAY_PARAMS[form['select_grid_by']])
                    ws.write(0,1,form[form['select_grid_by']])
                    if form['data_summary'] == 'none':
                        ws.write(0,2,'Data Summary:')
                        ws.write(0,3,'None')
                    else:
                        ws.write(0,2,'Data Summary:')
                        ws.write(0,3,form['data_summary'])
                        ws.write(0,4,form[form['data_summary'] + '_summary'])
                    ws.write(2, 0, 'Units')
                    ws.write(2, 1, form['units'])
                    ws.write(3, 0, 'Date')
                    if form['data_summary'] != 'spatial':
                        ws.write(3, 1, 'Lat')
                        ws.write(3, 2, 'Lon')
                        ws.write(3, 3, 'Elev' + '(' + elev_unit + ')')
                        for k, el in enumerate(el_list):
                            el_strip, base_temp = get_el_and_base_temp(el)
                            if form['units'] == 'metric':
                                el_unit = WRCCData.UNITS_METRIC[el_strip]
                            else:
                                el_unit = WRCCData.UNITS_ENGLISH[el_strip]
                            ws.write(3, k+4, el + '('+ el_unit + ')')
                    else:
                        for k, el in enumerate(el_list):
                            el_strip, base_temp = get_el_and_base_temp(el)
                            if form['units'] == 'metric':
                                el_unit = WRCCData.UNITS_METRIC[el_strip]
                            else:
                                el_unit = WRCCData.UNITS_ENGLISH[el_strip]
                            ws.write(3, k+4, el + '('+ el_unit + ')')
                    row_number = 1
                    flag = 0
                try:
                    try:
                        ws.write(date_idx+4, j, float(val))
                    except:
                        ws.write(date_idx+4, j, str(val))#row, column, label
                except Exception, e:
                    response = 'Excel write error:' + str(e)
                    break
        if f:
            try:
                wb.save(f)
                response = None
            except Exception, e:
                response = 'Excel save error:' + str(e)
        else: # request
            response = HttpResponse(content_type='application/vnd.ms-excel;charset=UTF-8')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (file_name,file_extension)
            wb.save(response)
    return response

def write_station_data_to_file(resultsdict, form, f=None, request=None):
#def write_station_data_to_file(resultsdict, delimiter, file_extension, request=None, f= None, output_file_name=None, show_flags='F', show_observation_time='F'):
    '''
    Writes station data to a file.

    Keyword aruments:
    resultsdict      -- output of get_station_data call, has keys:
        stn_data             -- data to write to file
        dates            -- list of dates of data request
        stn_names    -- list of station names of data request
        stn_ids      -- list of station ids of data request
        elements         -- list of climate elements
        stn_state        -- list of station states
        stn_lat          -- list of station latitiudes
        stn_lon          -- list of station longitudes
        stn_elev         -- list of station elevations
    delimiter        -- delimiter used to separate data vaules
    file_extension   -- format of output data file (.dat, .txt, .xls)
    f                -- file name (default None)
    request          -- data request object (default None)
    output_file_name -- Name of output file. If default DataRequest, a time stamp will be added.

    If a file f is given, data will be written to file.
    If a request object is given, the file will be generated
    via the CSC webpages
    '''
    time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    file_extension = WRCCData.FILE_EXTENSIONS[form['data_format']]
    elev_unit = 'ft'
    if form['units'] =='metric':elev_unit = 'm'
    #set file name
    if 'output_file_name' in form.keys():
        file_name = form['output_file_name']
    else:
        file_name = 'DataRequest_'+ time_stamp
    #sanity check:
    if not f and not request:
        return 'Error! Need either a file or a reqest object!'
    elif f and request:
        return 'Error! Choose one of file f or request object'

    if file_extension in ['.dat', '.txt']:
        delim = form['delimiter']
        import csv
        if request:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (file_name,file_extension)
            writer = csv.writer(response, delimiter=delim )
        else: #file f given
            try:
                csvfile = open(f, 'w+')
                writer = csv.writer(csvfile, delimiter=delim )
                response = None
            except Exception, e:
                #Can' open user given file, create emergency writer object
                writer = csv.writer(open('/tmp/csv.txt', 'w+'), delimiter=delim,quoting=csv.QUOTE_NONE)
                response = 'Error!' + str(e)
        for stn, dat in enumerate(resultsdict['stn_data']):
            #NOTE: row writer does not like delimiter characters in string,
            #need to set space char to be used in header string
            stn_name = str(resultsdict['stn_names'][stn])
            header_seperator = ':'
            if delim == ' ':
                stn_name = ' '.join(str(resultsdict['stn_names'][stn]).split(' '))
            if delim== ':':
                header_seperator = ' '
            row = ['*StationID' + header_seperator + str(resultsdict['stn_ids'][stn][0]).split(' ')[0], 'StationName' + header_seperator+stn_name]
            writer.writerow(row)
            row = ['*State' + header_seperator+str(resultsdict['stn_state'][stn]),'Latitude'+ header_seperator+str(resultsdict['stn_lat'][stn]),'Longitude'+ header_seperator+str(resultsdict['stn_lon'][stn]),'Elevation(' + elev_unit + ')' + header_seperator+str(resultsdict['stn_elev'][stn])]
            writer.writerow(row)
            row = ['*Units'+ header_seperator,form['units']]
            writer.writerow(row)
            row = ['*DataFlags' + header_seperator + 'M=Missing' + header_seperator + 'T=Trace' + header_seperator + 'S=Subsequent' + header_seperator + 'A=Accumulated']
            writer.writerow(row)
            row = ['*date']
            for el in resultsdict['elements']:
                el_strip,base_temp = get_el_and_base_temp(el)
                if form['units'] == 'metric':
                    el_unit = WRCCData.UNITS_METRIC[el_strip]
                else:
                    el_unit = WRCCData.UNITS_ENGLISH[el_strip]
                if form['show_flags'] == 'F' and form['show_observation_time'] == 'F':
                    row.append(str(el) + '(' + el_unit + ')')
                elif form['show_flags'] == 'T' and form['show_observation_time'] == 'F':
                    row.append(str(el) + '(' + el_unit + ')');row.append('flag')
                elif form['show_flags'] == 'F' and form['show_observation_time'] == 'T':
                    row.append(str(el) + '(' + el_unit + ')');row.append('ObsTime')
                else:
                    row.append(str(el) + '(' + el_unit + ')');row.append('flag');row.append('ObsTime')
            writer.writerow(row)

            for j, vals in enumerate(dat):
                row = []
                #date
                row.append(vals[0])
                for val in vals[1:]:
                    if form['show_flags'] == 'F' and form['show_observation_time'] == 'F':
                        row.append(str(val[0]))
                    elif form['show_flags'] == 'T' and form['show_observation_time'] == 'F':
                        row.append(str(val[0]))
                        row.append(str(val[1]))
                    elif form['show_flags'] == 'F' and form['show_observation_time'] == 'T':
                        row.append(str(val[0]))
                        row.append(str(val[2]))
                    else:
                        row.append(str(val[0]))
                        row.append(str(val[1]))
                        row.append(str(val[2]))
                writer.writerow(row)
    elif file_extension == '.json':
        with open(f, 'w+') as jsonf:
            jsonf.write(json.dumps(resultsdict['stn_data']))
            response = None
    elif file_extension == '.xls': #Excel
        from xlwt import Workbook
        wb = Workbook()
        for stn, dat in enumerate(resultsdict['stn_data']):
            #ws = wb.add_sheet('Station_%s_%s' %(str(resultsdict['stn_ids'][stn][0]).split(' ')[0], str(stn)))
            ws = wb.add_sheet('%s' %(str(resultsdict['stn_ids'][stn][0]).split(' ')[0]))
            #Header
            ws.write(0,0,'Stn Name');ws.write(0,1,'Stn ID');ws.write(0,2,'State');ws.write(0,3,'Lat');ws.write(0,4,'Lon');ws.write(0,5,'Elev');
            ws.write(1,0,str(resultsdict['stn_names'][stn]))
            ws.write(1,1,str(resultsdict['stn_ids'][stn][0]).split(' ')[0])
            ws.write(1,2,str(resultsdict['stn_state'][stn]))
            ws.write(1,3,str(resultsdict['stn_lat'][stn]))
            ws.write(1,4,str(resultsdict['stn_lon'][stn]))
            ws.write(1,5,str(resultsdict['stn_elev'][stn]))
            ws.write(3,0,'Units')
            ws.write(3,1,form['units'])
            ws.write(4,0,'DataFlags')
            ws.write(4,1,'M=Missing')
            ws.write(4,2,'T=Trace')
            ws.write(4,3,'S=Subsequent')
            ws.write(4,4,'A=Accumulated')
            ws.write(5, 0, 'Date')
            idx = 0
            for k, el in enumerate(resultsdict['elements']):
                el_strip,base_temp = get_el_and_base_temp(el)
                if form['units'] == 'metric':
                    el_unit = WRCCData.UNITS_METRIC[el_strip]
                else:
                    el_unit = WRCCData.UNITS_ENGLISH[el_strip]
                idx+=1
                if form['show_flags'] == 'F' and form['show_observation_time'] == 'F':
                    ws.write(5, k+1, el + '(' + el_unit + ')')
                elif form['show_flags'] == 'T' and form['show_observation_time'] == 'F':
                    ws.write(5, idx, el + '(' + el_unit + ')')
                    ws.write(5, idx+1,'flag')
                    idx+=1
                elif form['show_flags'] == 'F' and form['show_observation_time'] == 'T':
                    ws.write(5, idx, el + '(' + el_unit + ')')
                    ws.write(5, idx+1,'obs time')
                    idx+=1
                else:
                    ws.write(5, idx, el + '(' + el_unit + ')')
                    ws.write(5, idx+1,'flag')
                    ws.write(5, idx+2,'obs time')
                    idx+=2
            #Data
            for j, vals in enumerate(dat):
                idx = 0
                ws.write(j+6,0,vals[0])
                for l,val in enumerate(vals[1:]):
                    idx+=1
                    if form['show_flags'] == 'F' and form['show_observation_time'] == 'F':
                        try:
                            ws.write(j+6, idx, float(val[0]))
                        except:
                            ws.write(j+6, idx, val[0])
                    elif form['show_flags'] == 'T' and form['show_observation_time'] == 'F':
                        ws.write(j+6, idx, val[0]) #row, column, label
                        ws.write(j+6, idx+1, val[1])
                        idx+=1
                    elif form['show_flags'] == 'F' and form['show_observation_time'] == 'T':
                        ws.write(j+6, idx, val[0]) #row, column, label
                        ws.write(j+6, idx+1, int(val[2]))
                        idx+=1
                    else:
                        try:
                            ws.write(j+6, idx, float(val[0])) #row, column, label
                        except:
                            ws.write(j+6, idx, val[0])
                        ws.write(j+6, idx+1, val[1])
                        ws.write(j+4, idx+2, int(val[2]))
                        idx+=2
        if f:
            try:
                wb.save(f)
                response = None
            except:
                response = 'Error saving excel work boook to file %s' % f
        else: # request
            response = HttpResponse(content_type='application/vnd.ms-excel;charset=UTF-8')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (file_name, file_extension)
            wb.save(response)
    return response

def format_grid_data(req, params):
    '''
    Format grid data. Output are lists of form [date, lat, lon, value_element1, value_element2, ...]

    Keyword arguments:
    req    -- Data request object, result of GridData call to ACIS-WS
    params -- parameter dictionary
    '''
    #Make sure params are formatted correctly
    prms = {}
    dlm = WRCCData.DATE_FORMAT[params['date_format']]
    for key, val in params.iteritems():
        if key != 'elements':
            prms[key] = str(val)
        else:
            if isinstance(val, list):
                prms[key] = val
            else:
                prms[key] = val.replace(' ', '').split(',')
    if 'data_summary' in prms.keys():
        data_summary = prms['data_summary']
    else:
        data_summary = 'none'
    el_list_input = prms['elements']
    el_list = el_list_input
    poly, PointIn = set_poly_and_PointIn(prms)
    #strip base temp of degree days:
    for el_idx,el in enumerate(el_list):
        el_strip, base_temp = get_el_and_base_temp(el)
        if base_temp:
            el_list[el_idx] = el_strip
    #Sanity check
    data = {'meta':{'lat':[[]], 'lon':[[]], 'elev':[[]]}, 'data':[]}
    if 'error' in req.keys():
        data['error'] = req['error']
        if 'meta' in req.keys():
            data['meta'] = req['meta']
    if 'data' in req.keys():
        data['data'] = req['data']
    if 'meta' in req.keys():
        if 'lat' in req['meta'].keys():
            if 'location' in prms.keys():
                #make look like multi grid point output
                data['meta']['lat'] = [[req['meta']['lat']]]
            else:
                data['meta']['lat'] = req['meta']['lat']
        if 'lon' in req['meta'].keys():
            if 'location' in prms.keys():
                #make look like multi grid point output
                data['meta']['lon'] = [[req['meta']['lon']]]
            else:
                data['meta']['lon'] =req['meta']['lon']
        if 'elev'in req['meta'].keys():
            if 'location' in prms.keys():
                #make look like multi grid point output
                data['meta']['elev'] = [[req['meta']['elev']]]
            else:
                data['meta']['elev'] = req['meta']['elev']
    if data_summary == 'temporal':
        if 'smry' in req.keys():
            data['data'] = req['smry']
        else:
            data['data'] = []


    #Format data depending out data_format choice: json, summarized data or raw data request
    if prms['data_format'] == 'json':
        return req
    elif data_summary == 'temporal':
        #TEMPORAL SUMMARY
        #has different format than raw data
        lats = data['meta']['lat']
        lons = data['meta']['lon']
        elevs = data['meta']['elev']
        if 'start_date' in prms.keys():
            d = prms['start_date'].replace(' ','').replace(':','').replace('/','').replace('-','')
            start_date = d[0:4] + dlm + d[4:6] + dlm + d[6:8]
        else:
            start_date = '0000'+dlm+'00'+dlm+'00'
        if 'end_date' in prms.keys():
            d = prms['end_date'].replace(' ','').replace(':','').replace('/','').replace('-','')
            end_date = d[0:4] + dlm + d[4:6] + dlm + d[6:8]
        else:
            end_date = '0000'+dlm+'00'+dlm+'00'
        date_range = '%s-%s' %(start_date, end_date)
        if 'location' in prms.keys():
            #Single gridpoint format
            if prms['units'] == 'metric':
                ll = WRCCUtils.convert_to_metric('elev', elevs[0][0])
            else:
                ll = elevs[0][0]
            data_out = [[date_range, round(lons[0][0],2), round(lats[0][0],2), ll]]
            for el_idx, val in enumerate(data['data']):
                if prms['units'] == 'metric':
                    data_out[0].append(WRCCUtils.convert_to_metric(el_list[el_idx], val))
                else:
                    data_out[0].append(val)
            return data_out
        else:
            #check for irregular shapes and define poly if so
            lat_num = 0
            for lat_idx, lat_grid in enumerate(data['meta']['lat']):
                lat_num+=len(lat_grid)
            length = lat_num
            #length = len(data['data'])
            data_out = [[] for i in range(length)]
            #Multiple gridpoints
            idx = -1
            for grid_idx, lat_grid in enumerate(lats):
                lat = lat_grid[0]
                for lon_idx, lon in enumerate(lons[grid_idx]):
                    idx+=1
                    #if custom shape, check if  stn lies within shape
                    if poly:
                        try:
                            point_in = PointIn(lon, lat, poly)
                        except:
                            point_in = False
                        if not point_in:
                            del data_out[idx]
                            idx-=1
                            continue
                    data_out[idx].append(date_range)
                    data_out[idx].append(round(lon,2))
                    data_out[idx].append(round(lat,2))
                    if prms['units'] == 'metric':
                        data_out[idx].append(WRCCUtils.convert_to_metric('elev',elevs[grid_idx][lon_idx]))
                    else:
                        data_out[idx].append(elevs[grid_idx][lon_idx])

                    for el_idx in range(len(data['data'])):
                        if prms['units'] == 'metric':
                            data_out[idx].append(WRCCUtils.convert_to_metric(el_list[el_idx],data['data'][el_idx][grid_idx][lon_idx]))
                        else:
                            data_out[idx].append(data['data'][el_idx][grid_idx][lon_idx])
        return data_out
    else:
        poly = None
        #RAW DATA REQUEST OR SPATIAL SUMMARY
        if isinstance(data['meta']['lat'],float):
            #shape is location
            lats = [[data['meta']['lat']]]
            lons = [[data['meta']['lon']]]
            elevs = [[data['meta']['elev']]]
        else:
            lats = data['meta']['lat']
            lons = data['meta']['lon']
            elevs = data['meta']['elev']
        if 'location' in prms.keys() or isinstance(data['meta']['lat'],float):
            data_out = [[] for i in range(len(data['data']))]
        else:
            #check for irregular shapes and define poly if so
            #set output data_out
            lat_num = 0
            for lat_idx, lat_grid in enumerate(data['meta']['lat']):
                lat_num+=len(lat_grid)
            length = len(data['data']) * lat_num
            data_out = [[] for i in range(length)]
        #Loop over data
        idx = -1
        #Spatial summary output
        data_s_summ = [[] for d in data['data']]
        for date_idx, date_vals in enumerate(data['data']):
            d = str(date_vals[0]).replace(' ','').replace(':','').replace('/','').replace('-','')
            if prms['temporal_resolution'] == 'yly':
                data_s_summ[date_idx].append(d[0:4])
            elif prms['temporal_resolution'] == 'mly':
                data_s_summ[date_idx].append(d[0:4]+dlm+d[4:6])
            else:
                data_s_summ[date_idx].append(d[0:4]+dlm+d[4:6]+dlm+d[6:8])
            #for spatial summary
            data_summ = [[] for el in el_list]
            if 'location' in prms.keys() or isinstance(data['meta']['lat'],float):
                if prms['temporal_resolution'] == 'yly':
                    data_out[date_idx].append(d[0:4])
                elif prms['temporal_resolution'] == 'mly':
                    data_out[date_idx].append(d[0:4]+dlm+d[4:6])
                else:
                    data_out[date_idx].append(d[0:4]+dlm+d[4:6]+dlm+d[6:8])
                data_out[date_idx].append(round(lons[0][0],2))
                data_out[date_idx].append(round(lats[0][0],2))
                if prms['units'] == 'metric':
                    data_out[date_idx].append(WRCCUtils.convert_to_metric('elev',elevs[0][0]))
                else:
                    data_out[date_idx].append(elevs[0][0])
                for el_idx in range(1,len(el_list) + 1):
                    if prms['units'] == 'metric':
                        data_out[date_idx].append(WRCCUtils.convert_to_metric(el_list[el_idx -1],str(date_vals[el_idx]).strip(' ')))
                    else:
                        data_out[date_idx].append(str(date_vals[el_idx]).strip(' '))
                    try:
                        v = float(date_vals[el_idx])
                        if abs(v + 999.0)>0.0001:
                            if prms['units'] == 'metric':
                                data_summ[el_idx-1].append(WRCCUtils.convert_to_metric(el_list[el_idx -1],v))
                            else:
                                data_summ[el_idx-1].append(v)
                    except:
                        pass
            else:
                for grid_idx, lat_grid in enumerate(lats):
                    lat = lat_grid[0]
                    for lon_idx, lon in enumerate(lons[grid_idx]):
                        idx+=1

                        #if custom shape, check if  stn lies within shape
                        if poly:
                            try:
                                point_in = PointIn(lon, lat, poly)
                            except:
                                point_in = False
                            if not point_in:
                                del data_out[idx]
                                idx-=1
                                continue
                        if prms['temporal_resolution'] == 'yly':
                            data_out[idx].append(d[0:4])
                        elif prms['temporal_resolution'] == 'mly':
                            data_out[idx].append(d[0:4]+dlm+d[4:6])
                        else:
                            data_out[idx].append(d[0:4]+dlm+d[4:6]+dlm+d[6:8])
                        data_out[idx].append(round(lons[grid_idx][lon_idx],2))
                        data_out[idx].append(round(lat,2))
                        if prms['units'] == 'metric':
                            data_out[idx].append(WRCCUtils.convert_to_metric('elev',elevs[grid_idx][lon_idx]))
                        else:
                            data_out[idx].append(elevs[grid_idx][lon_idx])

                        for el_idx in range(1,len(el_list) + 1):
                            if prms['units'] == 'metric':
                                data_out[idx].append(WRCCUtils.convert_to_metric(el_list[el_idx - 1],date_vals[el_idx][grid_idx][lon_idx]))
                            else:
                                data_out[idx].append(date_vals[el_idx][grid_idx][lon_idx])
                            try:
                                v = float(date_vals[el_idx][grid_idx][lon_idx])
                                if abs(v + 999.0)>0.0001:
                                    if prms['units'] == 'metric':
                                        data_summ[el_idx-1].append(WRCCUtils.convert_to_metric(el_list[el_idx - 1],v))
                                    else:
                                        data_summ[el_idx-1].append(v)
                            except:
                                pass
            if data_summary == "spatial":
                if prms['spatial_summary'] == "max":
                    for el_idx, el in enumerate(el_list):
                        if data_summ[el_idx]:
                            data_s_summ[date_idx].append(max(data_summ[el_idx]))
                        else:
                            data_s_summ[date_idx].append(-999.0)
                if prms['spatial_summary'] == "min":
                    for el_idx, el in enumerate(el_list):
                        if data_summ[el_idx]:
                            data_s_summ[date_idx].append(min(data_summ[el_idx]))
                        else:
                            data_s_summ[date_idx].append(-999.0)
                if prms['spatial_summary'] == "mean":
                    for el_idx, el in enumerate(el_list):
                        if data_summ[el_idx]:
                            data_s_summ[date_idx].append(round(sum(data_summ[el_idx]) / float(len(data_summ[el_idx])),2))
                        else:
                            data_s_summ[date_idx].append(-999.0)
                if prms['spatial_summary'] == "sum":
                    for el_idx, el in enumerate(el_list):
                        if data_summ[el_idx]:
                            data_s_summ[date_idx].append(sum(data_summ[el_idx]))
                        else:
                            data_s_summ[date_idx].append(-999.0)
        if data_summary == 'spatial':
            return data_s_summ
        else:
            return data_out

def get_station_meta(station_id):
    meta_params = {"sids":station_id,"meta":"name,state,sids,ll ,elev,uid,county,climdiv"}
    try:
        stn_meta = AcisWS.StnMeta(meta_params)
    except:
        stn_meta = {'name':'', 'sids':[], 'county':'', 'state':'', \
        'elev':-999, 'climdiv':'', 'uid':-999, 'll':''}
    return stn_meta

def format_station_meta(meta_data):
    '''
    Formats meta data coming out of ACIS
    Deals with unicoe issues and assigns networks to each station id
    '''
    meta = {}
    if not meta_data:
        return {}
    if not isinstance(meta_data, dict):
        return {}
    for key,val in meta_data.iteritems():
        if key == 'name':
            #strip apostrophes from name
            meta['name'] = str(meta_data['name']).replace("\'"," ")
        elif key == 'sids':
            #find networks
            meta['sids'] = []
            for sid in meta_data['sids']:
                sid_split = sid.split(' ')
                #put coop id up front (for csc application metagraph  and possibly others)
                if str(sid_split[1]) == '2':
                    meta['sids'].insert(0,[str(sid_split[0]).replace("\'"," "), 'COOP'])
                else:
                    if str(sid_split[1]) in WRCCData.NETWORK_CODES.keys():
                        meta['sids'].append([str(sid_split[0]).replace("\'"," "),WRCCData.NETWORK_CODES[str(sid_split[1])]])
                    else:
                        meta['sids'].append([str(sid_split[0]).replace("\'"," "),'Misc'])
        elif key == 'll':
            meta[str(key)]=val
        elif key == 'valid_daterange':
            meta['valid_daterange']=[]
            for date_range in meta_data['valid_daterange']:
                if not date_range or len(date_range) != 2:
                    meta['valid_daterange'].append([])
                else:
                    meta['valid_daterange'].append([str(date_range[0]), str(date_range[1])])
        else:
            meta[str(key)] = str(val)
    return meta

def metadict_to_display(metadata, key_order_list):
    meta = [[WRCCData.DISPLAY_PARAMS[key]] for key in key_order_list]
    for key, val in metadata.iteritems():
        try:
            idx = key_order_list.index(str(key))
        except:
            continue
        if key == 'sids':
            sid_str = ''
            for sid in val:
                sid_l = sid.split()
                sid_str+='%s/%s, ' %(str(sid_l[0]), WRCCData.NETWORK_CODES[str(sid_l[1])])
                #sid_list.append(sid.encode('ascii', 'ignore'))
            meta[idx].append(sid_str)
        else:
            meta[idx].append(str(val))

    return meta

def get_el_and_base_temp(el):
    '''
    strips base temp xx from gddxx ( hddxx, cddxx)
    return element name gdd( hdd, cdd) and base temp xx

    Keyword arguments:
    el -- climate element abbreviation
    '''
    element = el
    base_temp = None
    el_strip = re.sub(r'(\d+)(\d+)', '', el)   #strip digits from gddxx, hddxx, cddxx
    b = el[-2:len(el)]
    try:
        base_temp = int(b)
        element = el_strip
    except:
        if b == 'dd' and el in ['hdd', 'cdd']:
            base_temp = '65'
        elif b == 'dd' and el == 'gdd':
            base_temp = '50'
    return element, base_temp


def get_start_date(time_unit, end_date, number):
    '''
    Given a time unit (days, months or years),
    an end date and the number of days/months/years to
    go back, this routine calculates the start date.
    Leap years are taken into consideratiion. start date is given as
    string of length 8, eg: "20000115", the resulting end date is of same format
    '''
    x = int(number)
    yr = int(end_date[0:4])
    mon = int(end_date[4:6])
    day = int(end_date[6:8])
    if time_unit == 'years':
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=x*365)
    elif time_unit == 'months':
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=(x*365)/12)
    else:
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=x)
    yr_start = str(start.year)
    mon_start = str(start.month)
    day_start = str(start.day)
    if len(mon_start) == 1:mon_start = '0%s' % mon_start
    if len(day_start) == 1:day_start = '0%s' % day_start
    start_date = '%s%s%s' %(yr_start, mon_start,day_start)
    return start_date

def format_stn_meta(meta_dict):
    '''
    This routine deals with meta data issues:
    1)jQuery does not like ' in station names
    2) unicode output can cause trouble
    '''
    #deal with meta data issues:
    #1)jQuery does not like ' in station names
    #2) unicode output can cause trouble
    Meta = {}
    for key, val in meta_dict.items():
        if key == 'sids':
            Val = []
            for sid in val:
                Val.append(str(sid).replace("\'"," "))
        elif key == 'valid_daterange':
            Val = []
            for el_idx, rnge in enumerate(val):
                if rnge and len(rnge) == 2:
                    start = str(rnge[0])
                    end = str(rnge[1])
                else:
                    start = '00000000'
                    end = '00000000'
                dr = [start, end]
                Val.append(dr)
        else:
            Val = str(val)
        Meta[str(key)] = Val
    return Meta

def strip_data(val):
    '''
    Routine to strip data of attached flags
    '''
    v = str(val)
    if not v:
        pos_val = ' '
        flag = ' '
    elif v[0] == '-':
        pos_val = v[1:]
    else:
        pos_val = v
    #Note: len(' ') =1!
    if len(pos_val) ==1:
        if pos_val.isdigit():
            strp_val = v
            flag = ' '
        else:
            strp_val = ' '
            if pos_val in ['M', 'T', 'S', 'A', ' ']:
                flag = pos_val
            else:
                strp_val = ' '
                flag = ' '
    else: #len(pos_val) >1
        if not pos_val[-1].isdigit():
            flag = v[-1]
            strp_val = v[0:-1]
        else:
            flag = ' '
            strp_val = v

    return strp_val, flag

def compute_doy(mon,day):
    '''
    Routine to compute day of year ignoring leap years
    '''
    mon_len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(str(mon).lstrip('0'))
    nday = int(str(day).lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

def compute_doy_leap(mon, day):
    '''
    Routine to compute day of leap years
    '''
    mon_len = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(str(mon).lstrip('0'))
    nday = int(str(day).lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

def compute_mon_day(doy):
    '''
    Reverse of compute_doy but counting every feb as having 29 days
    '''
    ndoy = int(doy)
    mon = 0
    day = 0
    if ndoy >366 or ndoy < 1:
        return None,None
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
    '''
    Check if year is leap year.
    '''
    yr = int(year)
    if yr % 100 != 0 and yr % 4 == 0:
        return True
    elif yr % 100 == 0 and yr % 400 == 0:
        return True
    else:
        return False

def date_to_datetime(date_str):
    '''
    Function to convert acis date_str of forms
    yyyy-mm-dd
    yyyy/mm/dd
    yyyy:mm:dd
    yyyymmdd
    to datetime. The datetime object is returned
    '''
    eight_date = date_str.replace('-','').replace('/','').replace(':','')
    if len(eight_date) != 8:
        return None
    dt = datetime.datetime(int(eight_date[0:4]),int(eight_date[4:6]), int(eight_date[6:8]))
    return dt

def find_valid_daterange(sid, start_date='por', end_date='por', el_list=None, max_or_min='max'):
    '''
    This function makes a StnMeta call to find either the
    maximum or minimum valid daterange for a
    station with station ID sid and elements in the list of climate elements el_list.

    Keyword arguments:
    sid  -- station ID
    el_list -- list of elements required.
               If el-list==None, we query for the 8 base elements
               [maxt,mint,pcpn,snow,snwd, hdd,cdd,gdd]

    Each element has its own valid daterange.
    If max_or_min == max, the largest daterange is returned.
    If max_or_min == min, the smallest daterange is returned.
    '''
    #Format start/end date into 8 digit strings
    s_date = start_date.replace('-','').replace('/','').replace(':','')
    e_date = end_date.replace('-','').replace('/','').replace(':','')
    if s_date.lower() != 'por' and e_date.lower() != 'por':
        return [s_date, e_date]

    if el_list is None:
        #el_tuple = 'maxt,mint,pcpn,snow,snwd,hdd,gdd,cdd'
        el_tuple = '1,2,4,10,11,45'
    else:
        el_tuple =''
        for idx, el in enumerate(el_list):
            el_tuple+=str(WRCCData.ACIS_ELEMENTS_DICT[el]['vX'])
            if idx < len(el_list) - 1:
                el_tuple+=','

        #el_tuple = ','.join(el_list)
    meta_params = {'sids':sid, 'elems':el_tuple, 'meta':'name,state,sids,ll,elev,uid,county,climdiv,valid_daterange'}
    try:
        request = AcisWS.StnMeta(meta_params)
    except:
        return []
    if 'error' in request.keys() or not 'meta' in request.keys():
        return []

    #Find valid daterange
    #format first test date
    el_idx = 0
    vd_start = None;vd_end = None
    idx_start = 0
    if not request['meta']:
        return []
    for el_idx, el_vdr in enumerate(request['meta'][0]['valid_daterange']):
        if s_date.lower() != 'por':
            vd_start = date_to_datetime(s_date)
        else:
            if request['meta'][0]['valid_daterange'][el_idx]:
                vd_start = date_to_datetime(request['meta'][0]['valid_daterange'][el_idx][0])
        if e_date.lower() != 'por':
            vd_end = date_to_datetime(e_date)
        else:
            if request['meta'][0]['valid_daterange'][el_idx]:
                vd_end =  date_to_datetime(request['meta'][0]['valid_daterange'][el_idx][1])
        if vd_start is not None and vd_end is not None and vd_start <= vd_end:
            idx_start = el_idx + 1
            break
    if vd_start is None or vd_end is None:
        return ['','']
    vd_start_date = ''
    vd_end_date = ''
    #loop over valid dateranges for each elements and find max or min valid daterange
    for el_idx, el_vdr in enumerate(request['meta'][0]['valid_daterange'][idx_start:]):
        vd_start_test = None;vd_end_test = None
        if s_date.lower() == 'por':
            if el_vdr:
                vd_start_test = date_to_datetime(el_vdr[0])
        if e_date.lower() == 'por':
            if el_vdr:
                vd_end_test = date_to_datetime(el_vdr[1])
        if max_or_min == 'min':
            if vd_start_test is not None and vd_start_test > vd_start and vd_start_test <= vd_end:
                vd_start = vd_start_test
            if vd_end_test is not None and vd_end_test < vd_end and vd_end_test >= vd_start:
                vd_end = vd_end_test
        elif max_or_min == 'max':
            if vd_start_test is not None and vd_start_test < vd_start and vd_start_test <= vd_end:
                vd_start = vd_start_test
            if vd_end_test is not None and vd_end_test > vd_end and vd_end_test >= vd_start:
                vd_end = vd_end_test
    #convert back to date string
    if s_date.lower() == 'por':
        yr_start = str(vd_start.year);mon_start=str(vd_start.month);day_start = str(vd_start.day)
    else:
        yr_start = s_date[0:4];mon_start = s_date[4:6];day_start = s_date[6:8]
    if e_date.lower() == 'por':
        yr_end = str(vd_end.year);mon_end=str(vd_end.month);day_end = str(vd_end.day)
    else:
        yr_end = e_date[0:4];mon_end = e_date[4:6];day_end = e_date[6:8]

    if len(mon_start) ==1:mon_start='0' + mon_start
    if len(day_start) ==1:day_start='0' + day_start
    if len(mon_end) ==1:mon_end='0' + mon_end
    if len(day_end) ==1:day_end='0' + day_end
    vd_start_date = '%s%s%s' %(yr_start, mon_start, day_start)
    vd_end_date = '%s%s%s' %(yr_end, mon_end, day_end)
    return [vd_start_date, vd_end_date]

def get_dates(s_date, e_date, app_name):
    '''
    This function is in place because Acis_WS's MultiStnCall does not return dates
    it takes as arguments a start date and an end date (format yyyymmdd)
    and returns the list of dates [s_date, ..., e_date] assuming that there are no gaps in the data
    '''
    if not s_date or not e_date:
        dates = []
    elif s_date.lower() == 'por' or e_date.lower() == 'por':
        dates = []
    else:
        dates = []
        #convert to datetimes
        start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
        end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
        for n in range(int ((end_date - start_date).days +1)):
            next_date = start_date + datetime.timedelta(n)
            n_year = str(next_date.year)
            n_month = str(next_date.month)
            n_day = str(next_date.day)
            if len(n_month) == 1:n_month='0%s' % n_month
            if len(n_day) == 1:n_day='0%s' % n_day
            acis_next_date = '%s%s%s' %(n_year,n_month,n_day)
            dates.append(acis_next_date)
            #dates.append(str(time.strftime('%Y%m%d', next_date.timetuple())))
            #note, these apps are grouped by year and return a 366 day year even for non-leap years
            if app_name in ['Sodpad', 'Sodsumm', 'Soddyrec', 'Soddynorm', 'Soddd']:
                if dates[-1][4:8] == '0228' and not is_leap_year(int(dates[-1][0:4])):
                    dates.append(dates[-1][0:4]+'0229')
    return dates

def strip_n_sort(station_list):
    '''
    Strips station ids of leading zero,
    sorts in ascending order, re-inserts leading zeros.
    '''
    c_ids_strip_list = [int(stn.lstrip('0')) for stn in station_list]
    stn_list = sorted(c_ids_strip_list)
    for i, stn in enumerate(stn_list):
        if len(str(stn)) == 5:
            stn_list[i] = '0' + str(stn)
        else:
            stn_list[i] = str(stn)
    return stn_list

def find_start_end_dates(form_input):
    '''
    Converts form_input['start_date'] and form_input['end_date']
    to 8 digit start, end dates of format yyyymmdd.
    '''
    end_date = str(form_input['start_date'].replace('-','').replace(':','').replace('/','').replace(' ',''))
    mon_lens = ['31', '28', '31','30','31','30', '31','31','30','31','30','31']
    if 'start_date' not in form_input.keys():
        s_date = 'por'
    elif form_input['start_date'].lower() == 'por':
        s_date = 'por'
    else:
        start_date = str(form_input['start_date']).replace('-','').replace(':','').replace('/','').replace(' ','')
        if start_date == '' or start_date == ' ':
            s_date = 'por'
        else:
            if len(start_date) == 4:
                s_date = start_date + '0101'
            elif len(start_date) == 6:
                s_date = start_date + '01'
            elif len(start_date) == 8:
                s_date = start_date
            else:
                print 'Invalid start date format, should be yyyy or yyyymmdd!'
                s_date = None
    if 'end_date' not in form_input.keys():
        e_date = 'por'
    elif form_input['end_date'].lower() == 'por':
        e_date = 'por'
    else:
        end_date = str(form_input['end_date'].replace('-','').replace(':','').replace('/','').replace(' ',''))
        if end_date == '' or end_date == ' ':
            e_date = 'por'
        else:
            if len(end_date) == 4:
                e_date = end_date + '1231'
            elif len(end_date) == 6:
                if end_date[4:6] == '02' and WRCCUtils.is_leap_year(end_date[0:4]):
                    mon_len = '29'
                else:
                    mon_len = mon_lens[int(end_date[4:6]) - 1]
                e_date = end_date + mon_len
            elif len(end_date) == 8:
                e_date = end_date
            else:
                print 'Invalid end date format, should be yyyy or yyyymmdd!'
                e_date = None
    return s_date, e_date

def get_element_list(form_input, program):
    '''
    Finds element list for program data query

    Keyword arguments:
    form_input -- webpage user form fields
    program    -- application name
    '''
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
        #Check if elements is given as string, if so, convert to list
        if isinstance(form_input['elements'], basestring):
            elements = form_input['elements'].replace(' ', '').split(',')
        else:
            elements = [str(el) for el in form_input['elements']]
    return elements

def format_sodlist_data(data_flag_tobs):
    '''
    Formats the data coming out of ACIS
    to conform with Kelly's sodlist output
    data_flags_tobs = [data_val, flag, time_obs]
    data_val and flag are strings
    time _obs is an interger
    output is a list with 4 objects
    [wrcc_data_val, flag_1= ACIS flag, flag_2='', str(time_obs)]
    '''
    wrcc_data = ['', ' ',' ', '-1']
    if not isinstance(data_flag_tobs, list):
        return wrcc_data
    if len(data_flag_tobs)!= 3:
        return wrcc_data
    data = str(data_flag_tobs[0])
    acis_flag = str(data_flag_tobs[1])
    tobs = str(data_flag_tobs[2])
    if acis_flag in ['M', 'T', 'S']:
        if data in ['M','S','T','',' ']:
            wrcc_data[0] = '0'
        else:
            try:
                float(data)
                wrcc_data[0] = data
            except:
                pass
    elif acis_flag in ['',' ']:
        try:
            float(data)
            wrcc_data[0] = data
        except:
            pass
    if acis_flag not in ['',' ']:
        wrcc_data[1] = acis_flag
    if tobs not in ['',' ','-1']:
        if len(tobs) ==1:
            wrcc_data[3] = '0'+tobs
        else:
            wrcc_data[3] = tobs
    return wrcc_data

def get_windowed_indices(dates, start_window, end_window):
    '''
    Finds start and end incdices for windowed data
    start_date   -- start date of data array
    end_date     -- end date of data array
    start_window -- start date of window
    end_window   -- end date of window
    output: list of start_indices, list of end_indices
    '''
    if start_window == '0101' and end_window == '1231':
        return [0],[len(dates)- 1]
    start_indices = [];end_indices = []
    for idx, date in enumerate(dates):
        #put date in format yyyymmdd
        d = ''.join(date.split('-'))
        d = ''.join(d.split('/'))
        if d[4:] == start_window:
            start_indices.append(idx)
        #deal with Feb 29 start
        if start_window == '0229':
            if end_window != '0229' and not is_leap_year(d[0:4]) and d[4:] == '0301':
                start_indices.append(idx)
        if d[4:] == end_window:
            end_indices.append(idx)
    #Date formatting needed to deal with end of data and window size
    start_d = dates[0];end_d = dates[-1]
    start_yr = int(start_d[0:4]);start_mon = int(start_d[4:6]);start_day = int(start_d[6:8])
    end_yr = int(end_d[0:4]);end_mon = int(end_d[4:6]);end_day = int(end_d[6:8])
    #Date formatting needed to deal with end of data and window size
    #doy = day of year
    if WRCCUtils.is_leap_year(start_yr) and start_mon > 2:
        doy_first = datetime.datetime(start_yr, start_mon, start_day).timetuple().tm_yday -1
    else:
        doy_first = datetime.datetime(start_yr, start_mon, start_day).timetuple().tm_yday

    if WRCCUtils.is_leap_year(end_yr) and end_mon > 2:
        doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday - 1
    else:
        doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday
    doy_window_st = WRCCUtils.compute_doy(start_window[0:2], start_window[2:4])
    doy_window_end = WRCCUtils.compute_doy(end_window[0:2], end_window[2:4])
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
        return [],[]
    return start_indices, end_indices

def get_windowed_data(data, start_date, end_date, start_window, end_window):
    '''
    Routine to filter out data according to window specification(sodlist)

    Keyword arguments:
    data         -- data array
    start_date   -- start date of data array
    end_date     -- end date of data array
    start_window -- start date of window
    end_window   -- end date of window
    '''
    if start_window == '0101' and end_window == '1231':
        windowed_data = data
    else:
        windowed_data = []
        start_indices=[]
        end_indices=[]
        if start_date.lower() == 'por':
            start_d = ''.join(data[0][0].split('-'))
        else:
            start_d = start_date
        if end_date.lower() == 'por':
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
            return []
        for j in range(len(start_indices)):
            add_data = data[start_indices[j]:end_indices[j]+1]
            windowed_data = windowed_data + add_data
    return windowed_data

###########################################################
#KELLY's routines
#These are mostly copied directly from Kelly's Fortran code
###########################################################

def JulDay(year, mon, day):
    '''
    JulDay; Function utilized to check for gap in data
    This program is based on and algorithm presented in 'Sky And Telescope Magazine, March 1984.'
    It will correctly calculate any date A.D. to the correct Julian date through at least 3500 A.D.
    Note that Julain dates begin at noon GMT. For this reason, the number is incremented by one to
    correspond to a day beginning at midnight.
    '''
    jd = 367 * year - 7 * (year + (mon + 9) / 12) / 4\
    - 3 * ((year + (mon - 9) / 7) / 100 +1) / 4\
    + 275 * mon / 9 + day + 1721029

    jd+=1
    return int(jd)

def Catoju(mnth, dy):
    '''
    Routine  to convert calendar days to yearly Julian days,
    All years are leap years, used in Sodthr
    '''
    month = int(mnth.lstrip('0'))
    nday = int(dy.lstrip('0'))
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ndoy =0
    for  mon in range(1,month+1):
        if mon < month:ndoy+=mon_lens[mon -1]
        if mon == month: ndoy+=nday
    if month == -1 and nday == -1:ndoy = -1
    return ndoy

def Jutoca(ndoy):
    '''
    Routine to convert yearly Julian Days to Calenday days,
    All years are leap years, used in Sodthr
    '''
    jstart = [1, 32, 61, 92, 122, 153, 183, 214, 245, 275, 306, 336]
    month = 0
    for mon in range(1,13):
        if ndoy >= jstart[mon-1]:
            month = mon
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

def Doymd(idoy, most, iyear):
    '''
    Routine to find the month and day given the day of the year,
    the start month and the year of the starting month
    Used in WRCCDataApps.Sodpiii
    '''
    lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #n732 has no blank spaces so we set February to have length 28
    iidoy = idoy
    iyeart = iyear
    imo = most
    while imo < 13:
        if imo == 2 and is_leap_year(iyeart):
            length = 29
        else:
            length = lens[imo - 1]

        if iidoy <= length:
            imon = imo
            iday = iidoy
        else:
            iidoy = iidoy - length
            imo+=1
            if imo == 13:
                imo = 1
                iyear+=1
            continue

        idate = 100 * imon + iday
        return idate

def bcof(n, normlz=True):
    '''
    Routine to compute binomial coefficients for Soddynorm
    '''
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

def pctil(app_name, data, number, npctil):
    '''
    Routine to compute percentiles, needed for Sodpct

    Keyword arguments:
    app_name -- application name
    data     -- data array
    number   -- number of data elements
    npctil   -- number of percentiles
    '''
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

##################
#Sodxrmts routines
##################

####################################
#PearsonIII routines: Pintp3, Capiii
####################################
def Pintp3(prnoex, piii, piiili, npiili,skew):
    '''
    This routine interpolates in the piii table.

    Keyword arguments:
    prnoex -- probability of non-exceedance
    averag -- average of the distribution
    stdev  -- standard deviation of the distribution
    skew   -- skewness of the distribution
    piii   -- input array of PearsonIII frequency distribution
    piiili -- list of probabilities in piii array
    npiili -- len(piiili)

    Output:
    psdout -- probability of non-exceedance expressed in standard deviations
    '''
    if skew > 9.0:skew = 9.0
    if skew < -9.0:skew = -9.0
    nsklo = int(round(10.0*skew))
    if nsklo < -90:nsklo = -90
    nskhi = nsklo + 1
    if nskhi > 90:nskhi = 90
    #Index if non-exceedace probabilty
    iretrn = 0
    while iretrn <= 26:
        iretrn+=1
        test = piiili[iretrn - 1]
        if test > prnoex:
            if iretrn == 1:
                npnolo = iretrn - 1
                pnoxlo = piiili[npnolo] - 0.00001
            else:
                npnolo = iretrn - 2
                pnoxlo = piiili[npnolo]
            npnohi = iretrn - 1
            pnoxhi = piiili[npnohi]
            break
        else:
            if iretrn != 27:
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
    y1 = y1 / 1000.0
    y2 = y2 / 1000.0
    y3 = y3 / 1000.0
    y4 = y4 / 1000.0
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
def Capiii(xdata, numdat, piii, piiili,npiili, pnlist,numpn):
    '''
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
        psd[ipn] = Pintp3(prnoex, piii, piiili, npiili, sk)

    return psd, ave, stdev, sk, cv, xmax, xmin

###########################################################################
#GEV routines: Samlmr Gev, Quantgev, Cdfgev, Lmrgev, Pelgev, Quagev, Reglmr, Salmr,
#Ampwm, Derf, Diagmd, Dlgama, Durand, Gamind, Quastn, Sort
##########################################################################
#Obtained from Jim Angel @ MrCC in Champaign, Illinois

def Samlmr(x, n, nmom, a, b):
    '''
    SAMPLE L-MOMENTS OF A DATA ARRAY

    PARAMETERS OF ROUTINE:
    X      * INPUT* ARRAY OF LENGTH N. CONTAINS THE DATA, IN ASCENDING
             ORDER.
    N      * INPUT* NUMBER OF DATA VALUES
    XMOM   *OUTPUT* ARRAY OF LENGTH NMOM. ON EXIT, CONTAINS THE SAMPLE
           L-MOMENTS L-1, L-2, T-3, T-4, ... .
    NMOM   * INPUT* NUMBER OF L-MOMENTS TO BE FOUND. AT MOST MAX(N,20).
    A      * INPUT* ) PARAMETERS OF PLOTTING
    B      * INPUT* ) POSITION (SEE BELOW)

    FOR UNBIASED ESTIMATES (OF THE LAMBDA'S) SET A=B=ZERO. OTHERWISE,
    PLOTTING-POSITION ESTIMATORS ARE USED, BASED ON THE PLOTTING POSITION
    (J+A)/(N+B)  FOR THE J'TH SMALLEST OF N OBSERVATIONS. FOR EXAMPLE,
    A=-0.35D0 AND B=0.0D0 YIELDS THE ESTIMATORS RECOMMENDED BY
    HOSKING ET AL. (1985, TECHNOMETRICS) FOR THE GEV DISTRIBUTION.
    '''

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

def Dlgama(x):
    '''
    Logarithm of Gamma function
    '''
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

def Pelgev(xmom):
    '''
    Parameter Estomation via L-Moments for the generalized extreme value distribution
    XMOM   * INPUT* ARRAY OF LENGTH 3. CONTAINS THE L-MOMENTS LAMBDA-1,
    LAMBDA-2, TAU-3.
    PARA   *OUTPUT* ARRAY OF LENGTH 3. ON EXIT, CONTAINS THE PARAMETERS
    IN THE ORDER XI, ALPHA, K (LOCATION, SCALE, SHAPE).
    Uses Dlgama
    '''
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

def Quagev(f,para):
    '''
    Quantile function of the generalized extreme value distribiution
    '''
    u = para[0]
    a = para[1]
    g = para[2]
    if a > 0:
        if f > 0 and f < 1:
            y = -numpy.log(f)
            if g != 0:
                y = 1.0 - numpy.exp(-g*y) / g
                quagev = u + a*y
            else:
                quagev = 0
        else:
            if (f == 0 and g < 0) or (f== 1 and g > 0):
                quagev = u + a / g
            else:
                quagev = 0
    else:
        quagev = 0
    return quagev

def Quantgev(para, probs, nprobs):
    results = [0.0 for iq in range(nprobs)]
    for iq in range(nprobs):
        results[iq] = Quagev(probs[iq], para)
    return results
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

################
#beta-p routines
################
def Sortb(rdata, n):
    ra = rdata
    l = n/2 + 1
    ir = n
    while l >1:
        if l > 1:
            l-=1
            rra = ra[l-1]
        else:
            rra = ra[ir -1]
            ra[ir-1] = ra[0]
            ir-=1
            if ir ==1:
                ra[0] = rra
                break
        i = l
        j = l + l
        while j <= ir:
            if j < ir:
                if ra[j-1] < ra[j]:j+=1
            if rra < ra[j-1]:
                ra[i-1] = ra[j-1]
                i = j
                j+=j
            else:
                j = ir +1
        ra[i-1] = rra
    return ra

def Dda(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    dda = rn/alpha
    for i in range(n):
        xb = x[i]/beta
        if numpy.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            dda-= float(numpy.log(1.0 + xbt))
        else:
            dda-=theta*numpy.log(xb)
    return dda

def Ddt(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    ddt = rn/beta
    for i in range(n):
        xb = float(x[i]/beta)
        if numpy.log(xb) <= 85.0/theta:
            xbt = xb**theta
            ddt+=float(numpy.log(xb)) - (alpha + 1.0)*float(numpy.log(xb)/(1.0 + xbt))*float(xbt)
        else:
            ddt-=alpha*float(numpy.log(xb))
    return ddt

def Ddb(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    ddb = -rn
    for i in range(n):
        xb = x[i]/beta
        if numpy.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            ddb+= (alpha + 1.0)*float(xbt/(1.0 + xbt))
        else:
            ddb+=alpha + 1
    ddb = theta*ddb/beta
    return ddb


def Betapll(alpha, theta, beta, n, x, ndim):
    betapll = float(n)*numpy.log(alpha*theta/beta)
    for i in range(n):
        xb = x[i]/beta
        if numpy.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            betapll+=(theta - 1.0)*numpy.log(xb) - (alpha + 1.0)*float(numpy.log(1+xbt))
        else:
            betapll-=(1.0 + alpha*theta)*numpy.log(xb)
    return betapll



def Fitbetap(x, n, ndim):
    '''
    Maximum likelihood fit for the "Beta-P" distribution
    Data x assumed to be sorted in ascending order.
    '''
    itmax = 2000
    epsilon = 0.0005
    efd = 0.00001
    pinit = [.1, .2, .5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
    trllbst = -1.0e20
    tbeta = 1.01*x[0]
    ig = int(round(0.8*float(n+1)))
    factor = -numpy.log(1.0 - 0.8)/numpy.log(x[ig-1]/tbeta)
    alpha0 = 0.0
    beta0 = 0.0
    theta0 = 0.0
    for ith in range(13):
        tthet = pinit[ith]*100.0
        talph = factor / tthet
        test = Betapll(talph, tthet, tbeta, n , x, ndim)
        if test > trllbst:
            trllbst = test
            alpha0 = talph
            beta0 = tbeta
            theta0 = tthet
            break
    #Begin iterations
    rll0 = Betapll(alpha0, theta0, beta0, n, x, ndim)
    bestll = rll0
    besta = alpha0
    bestb = beta0
    bestt = theta0
    dlambda = 0.001
    score = [0.0 for k in range(3)]
    #finf = [[0.0 for j in range(3)] for k in range(3)]
    finf = numpy.zeros((3,3))
    adj = [0.0 for k in range(3)]
    for it in range(itmax):
        itact = it
        ea = efd*alpha0
        et = efd*theta0
        eb = efd*beta0
        score[0] = Dda(alpha0, theta0, beta0, n, x, ndim)
        score[1] = Ddt(alpha0, theta0, beta0, n, x, ndim)
        score[2] = Ddb(alpha0, theta0, beta0, n, x, ndim)

        finf[0][0] = (Dda(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Dda(alpha0-ea, theta0, beta0, n, x, ndim))/2.0*ea
        finf[1][1] = (Ddt(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Ddt(alpha0, theta0 -et, beta0, n, x, ndim))/2.0*et
        finf[2][2] = (Ddb(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Ddb(alpha0, theta0, beta0 - eb, n, x, ndim))/2.0*eb

        finf[0][1] = (Dda(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Dda(alpha0, theta0 + et, beta0, n, x, ndim))/4.0*et +\
                    (Ddt(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Ddt(alpha0-ea, theta0, beta0, n, x, ndim))/4.0*ea

        finf[1][0] = finf[0][1]

        finf[0][2] = (Ddb(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Ddb(alpha0 + ea, theta0, beta0, n, x, ndim))/4.0*ea +\
                    (Dda(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Dda(alpha0, theta0, beta0 + eb, n, x, ndim))/4.0*eb

        finf[2][0] = finf[0][2]

        finf[1][2] = (Ddb(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Ddb(alpha0, theta0 + et, beta0, n, x, ndim))/4.0*et +\
                    (Ddt(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Ddt(alpha0, theta0, beta0 + eb, n, x, ndim))/4.0*eb

        finf[2][1] = finf[1][2]

        for i in range(3):
            finf[i][i]*=(1.0 + dlambda)

        #invert
        finv = numpy.linalg.inv(finf)
        for i in range(3):
            for j in range(3):
                adj[j] = adj[i] + finv[i][j]*score[j]
        alpha = abs(alpha0 - adj[0])
        if alpha/alpha0 > 1.1:alpha = 1.1*alpha0
        if alpha/alpha0< 0.9:alpha = 0.9*alpha0
        beta = abs(beta0 - adj[2])
        if beta/beta0 > 1.1:beta = 1.1*beta0
        if beta/beta0< 0.9:beta = 0.9*beta0
        theta = abs(theta0 - adj[1])
        if theta/theta0 > 1.1:theta = 1.1*theta0
        if theta/theta0< 0.9:theta = 0.9*theta0

        #Try to ensuer that this is an improvement
        iflag = 0
        for iback in range(4):
            rll = Betapll(alpha, theta, beta, n, x, ndim)
            if rll > bestll:
                bestll = rll
                besta = alpha
                bestb = beta
                bestt = theta

            if rll < rll0:
                iflag = 1
                alpha = (alpha + alpha0)/2
                beta = (beta + beta0)/2
                theta = (theta + theta0)/2
                dlambda=dlambda*2
            else:
                if iflag == 0:
                    dlambda = dlambda/2
                    break

        #Test for convergenceif no backing off the parameter estimates
        #was necessary
        if iflag == 0:
            if abs((alpha -alpha0)/alpha0) >= epsilon or \
            abs((beta -beta0)/beta0) >= epsilon or \
            abs((theta -theta0)/theta0) >= epsilon:
                alpha0 = alpha
                theta0 = theta
                beta0 = beta
                ll0 = rll
            else:
                break
    #end it loop
    rll = bestll
    alpha = besta
    beta = bestb
    theta = bestt
    return alpha, theta,beta, rll, itact

def Pintbetap(alpha, beta, theta, prob):
    #Check for conditions that will lead to floating overflow
    check1 = -1.0*numpy.log(1.0 - prob)
    check2 = 31.0*alpha*numpy.log(2.0)
    if check1 < check2:
        psd = (1.0 - prob)**(-1.0/alpha)
        psd = (psd - 1.0)**(1.0/theta)
        psd = psd * beta
    else:
        power = -1.0/(alpha*theta)
        psd = beta*((1.0 - prob)**power)
    return psd

def Cabetap(rdata, numdat, pnlist, numpn):
    #rdata = Sortb(rdata, numdat)
    r_sorted = []
    r_sorted_keys = sorted(rdata, key=rdata.get)
    for key in r_sorted_keys:
        r_sorted.append(rdata[key])
    alpha, theta, beta, rll, itact = Fitbetap(r_sorted, numdat, numdat)
    psd = [0.0 for i in range(numpn)]
    for i in range(numpn):
        psd[i] = Pintbetap(alpha, beta, theta, pnlist[i])
    return psd
########################
#Censored Gamma routines
########################
def Func(beta, alpha, p):
    func = Gammp(alpha, x/beta) - p
    return func

def Gammln(z):
    stp = 2.50662827465
    cof = [76.18009173,-86.50532033,24.01409822, -1.231739516,.120858003e-2,-.536382e-5]
    fpf = 5.5
    if z < 1.0:
        xx = z + 1.0
    else:
        xx = z
    x = xx - 1.0
    tmp = x + fpf
    tmp = (x + 0.5)*numpy.log(tmp) - tmp
    ser = 10
    for j in range(6):
        x+=1.0
        ser+=cof[j]/x
    gammln = tmp + numpy.log(stp*ser)
    if z < 1.0:
        gammln-=numpy.log(z)
    return gammln

def Gcf(a,x):
    itmax = 100
    eps = 3.0e-7
    gln = Gammln(a)
    gold = 0.0
    a0 = 1.0
    a1 = x
    bo = 0.0
    b1 = 1.0
    fac = 1.0
    for n in range(itmax):
        an = float(n)
        ana = an - a
        a0 = (a1 + a0*ana)*fac
        b0 = (b1 + b0*ana)*fac
        anf = an*fac
        a1 = x*a0 + anf*a1
        b1 = x*b0 + anf*b1
        if abs(a1) >  0.00001:
            ffac = 1.0/a1
            g = b1*fac
            if abs((g - gold)/g) >= eps:
                gold = g
    gammfc = numpy.exp(-z + a*numpy.log(x) - gln)*g
    return gammfc


def Gser(a,x):
    itmax = 100
    eps = 3.0e-7
    gln = Gammln(a)
    gamser = 0.0
    if x >= 0.0:
        ap =a
        summ = 1.0/a
        dl = summ
        for n in range(maxit):
            ap+=1
            dl*=x/ap
            summ+=dl
            if abs(dl) < abs(summ)*eps:
                gamser = summ*numpy.exp(-x + a*numpy.log(x) -gln)
                break
    return gamser

def Gammp(a,x):
    if x < 0.0 or a <= 0.0:
        gammp = 0.0
    if x < a + 1:
        gammp, gln = Gser(a,x)
    else:
        gammcf, gln = Gcf(a,x)
        gammp = 1.0 - gammcf
    return gammp


def Zbrent(beta, alpha, prob, x1, x2, tol):
    itmax = 100
    eps = 3.0e-8
    a = x1
    b = x2
    fa = Func(a, beta,alpha, prob)
    fb = func(b, beta, alpha, prob)
    fc =  fb
    for it in range(itmax):
        if fb*fc > 0.0:
            c = a
            fc = fa
            d = b - a
            e = d
        if abs(fc) < abs(fb):
            a = b
            b = c
            c = a
            fa = fb
            fb = fc
            fc = fa
        tol1 = 2.0*eps*abs(b) + 0.5*tol
        xm = 0.5*(c-b)
        if abs(xm) <= tol1 or fb == 0.0:
            zbrent = b
            break
        if abs(e) > tol1 and abs(fa) > abs(fb):
            s = fb/fa
            if abs(a-c) < 0.00001:
                p = 2.0*xm*s
                q =  1.0 - s
            else:
                q = fa/fc
                r = fb/fc
                p = s*(2.0*xm*q*(q - r) - (b - a)*(r - 1.0))
                q = (q - 1.0)*(r - 1.0)*(s - 1.0)
            if p > 0.0:q = -q
            p = abs(p)
            if 2.0*p < min(3.0*xm*q - abs(tol1*q), abs(e*q)):
                e = d
                d = p/q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d
        a = b
        fa = fb
        if abs(d) > tol1:
            b+=d
        else:
            if xm < 0.0:
                b-= tol1
            else:
                b+=tol1
            fb = Func(b, beta, alpha, prob)

    zbrent = b
    return zbrent

def Rloglike(nc, nw,sumx, sumlnx, a, b):
    try:
        ff = Gammp(a, nc/b)
    except:
        ff = 1.0
    rloglike = -nw*(a*numpy.log(b) + Gammln(a)) + (a - 1.0)*sumlnx - sumx/b
    if nc > 0.0: rloglike+=float(nc)*numpy.log(ff)
    return rloglike

def Psi(shape):
    z = shape
    if z < 1.0:
        a = z + 1.0
    else:
       a = z
    psi = numpy.log(a)-1.0/(2.0*a)-1.0/(12.0*a**2)+1.0/(120.0*a**4) - \
    1.0/(256.0*a**6)+1.0/(240.0*a**8)
    return psi

def Psipr(shape):
    z = shape
    if z < 1.0:
        a = z + 1.0
    else:
       a = z
    psipr=1.0/a+1.0/(2.0*a**2)+1.0/(6.0*a**3)-1.0/(30.0*a**5) + \
    1.0/(42.0*a**7)-1.0/(30.0*a**9)
    if z < 1.0:psipr+=1.0/z**2
    return psipr

def Dcdf(c, shape, scale, iflag):
    dp = 0.1
    ff = Gammp(shape, c/scale)
    da = shape*dp
    db = scale*dp

    fp = f(c, shape + da, scale)
    fm = f(c, shape - da, scale)
    dfda = (fp - fm)/(2.0*da)
    d2fda2 = (fp -2.0*ff + fm)/db**2

    fp=f(c,shape,scale+db)
    fm=f(c,shape,scale-db)
    dfdb=(fp-fm)/(2.0*db)
    d2fdb2=(fp-2.0*ff+fm)/db**2

    fapbp = f(c,shape+da,scale+db)
    fapbm=f(c,shape+da,scale-db)
    fambp=f(c,shape-da,scale+db)
    fambm=f(c,shape-da,scale-db)
    d2fdab=(fapbp-fambp-fapbm+fambm)/(4.0*da*db)
    return  ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp

def Dlda(nc, nw, sumlnx, shape, scale, ff, dfda): #dfda, ff extra coming from Dcdf
    dlda=sumlnx-float(nw)*(numpy.log(scale)+Psi(shape))
    if nc < 0.0:dlda== float(nc)*dfda/ff
    return dlda

def Dldb(nc,nw,sumx,shape,scalei, ff, dfdb):
    dldb=-shape*float(nw)/scale+sumx/(scale**2)
    if nc < 0.0:dldb+=float(nc)*dfdb/ff
    return dldb

def D2lda2(nc,nw,shape, ff, d2fda2, dfda):#ff, d2fda2, dfda from Dcdf
    d2lda2=-float(nw)*Psipr(shape)
    if nc < 0.0: d2lda2+=float(nc)*(ff*d2fda2-dfda**2)/ff**2
    return d2lda2

def D2ldb2(nc,nw,sumx,shape,scale, ff, d2fdb2, dfdb):
    d2ldb2=shape*float(nw)/scale**2-2.0*sumx/scale**3
    if nc < 0.0:d2ldb2+=float(nc)*(ff*d2fdb2-dfdb**2)/ff**2
    return d2ldb2

def D2ldab(nc,nw,scale, ff, d2fdab,dfdb):
    d2ldab=-float(nw)/scale
    if nc < 0.1:d2ldab+=float(nc)*(ff*d2fdab-dfda*dfdb)/ff**2
    return d2ldab


def Cengam(nc, nw, c, sumx, sumlnx):
    fininv = [[0.0 for k in range(2)] for j in range(2)]
    score = [0.0 for k in range(2)]
    itmax = 1000
    epsilon = 0.001
    dp = 0.1

    #Initial parameter guesses
    if nc == 0:
        sx = sumx
        slx = sumlnx
    else:
        sx = sumx + float(nc)*c/10.0
        slx = sumlnx + float(nc)*numpy.log(c/10)
    amean = sx/float(nc + nw)
    gmean = numpy.exp(slx/float(nc + nw))
    y = numpy.log(amean/gmean)
    if y > 17.0:
        shape = 0.05
    elif y <= 0:
        shape = numpy.sqrt(amean)
    elif y <= 0.5772:
        shape = (.5000876+.1648852*y-.0544274*y**2)/y
    else:
        shape=(8.898919+9.05995*y+.9775373*y**2)/(y*(17.79728+11.968477*y+y**2))
    scale = amean/shape

    #Begin iterations
    nocon = 0
    shapen = 0.0
    scale = 0.0
    shapen = 0.0
    scalen = 0.0
    for it in range(itmax):
        ki = 0
        if nc > 0:
            ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp = Dcdf(c,shape,scale,1)
            oldll = Rloglike(nc, nw, sumx, sumlnx, shape, scale)
            a = D2lda2(nc,nw,shape, ff, d2fda2, dfda)
            b = D2ldab(nc,nw,scale, ff, d2fdab,dfdb)
            d = D2ldb2(nc,nw,sumx,shape,scale,ff, d2fdb2, dfdb)
            det = a*d - b**2
            fininv[0][1] = b/det
            fininv[1][0] = fininv[0][1]
            score[0] = Dlda(nc, nw, sumlnx, shape, scale, ff, dfda)
            score[1] = Dldb(nc,nw,sumx,shape,scalei, ff, dfdb)
            fininv[0][0] = d/det
            fininv[1][1] = a/det

            shapen = shape - fininv[0][0]*score[1] - fininv[0][1]*score[1]
            if shapen < 0.001:shapen = 0.001
            scalen = scale - fininv[1][0]*score[1] - fininv[1][1]*score[1]
            if scalen < 0.001:scalen = 0.001

        #Test whether this is an improvement
        ki = 0
        while ki < 5:
            if nc > 0.0:
                ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp = Dcdf(c,shapen,scalen,0)
            if Rloglike(nc,nw,sumx,sumlnx,shapen,scalen) < oldll:
                ki+=1
                scalen = (scale+scalen)/2.
                shapen=(shape+shapen)/2.
        #Test for convergence
        if ki != 0 or abs(shape-shapen) > epsilon or abs(scale-scalen) > epsilon:
            shape = shapen
            scale = scalen
            nocon = 1
        else:
            shape = shapen
            scale = scalen
            nocon = 0
            break
    return shape, scale, nocon

def Gampctle(pcentile, beta, alpha):
    '''
    Returns as x the value of the gamma distribution variate corresponding to the decimal
    fraction pcentile
    '''
    x1 = 0
    x2 = 100.0*beta
    x = Zbrent(beta, alpha, pcentile, x1, x2, 1.0e-7)
    return x

def Cagamma(rdata, numdat, pnlist, numpn):
    cen_level = 0.004
    #Initialize counters
    sumx = 0.0
    sumlnx = 0.0
    num_cen = 0
    num_wet = 0

    for i in range(numdat):
        if rdata[i] > cen_level:
            sumx+=rdata[i]
            sumlnx+= numpy.log(rdata[i])
            num_wet+=1
        else:
            num_cen+=1
    #Calculate parameters
    shape = -999
    scale = -999
    shape, scale, nocon = Cengam(num_cen, num_wet, cen_level, sumx, sumlnx)
    #Calculate values
    for i in range(numpn):
        psd[i] = Gampctle(pnlist[i], scale, shape)
    return psd
