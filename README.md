Western Regional Climate Center (WRCC) data application centric python library.
Data is acquired through the Apllied Climate Information System (ACIS)
http://rcc-acis.org/.
Used in django my_acis project which is the content manager for the 
Southwest Climate and ENvironmental Information Collaborative (SCENIC) web interface
http://wrcc.dri.edu/csc/scenic/.

CONTENT

******
AcisWS
******
Handles all ACIS Web Services calls.

***********
WRCCClasses
***********
Classes used in my_acis project.

********
WRCCData
********
Contains useful dictionaries and lists used in my_acis.
django project

************
WRCCDataApps
************
Data Analysis functions.

*************
WRCCFormCheck
*************
Functons to perform sanity checks on form fields.
by SCENIC users via the UI

*********
WRCCUtils
*********
Utility functions used in my_acis django project.


************
WRCCWrappers
************
Contains wrapper scriptts needed to port WRCC data analysis application
to the WRCC main web pages: http://wrcc.dri.edu.


**********************
arealstats, pii.dat.2
**********************
Data tables used in Sodpiii data application.

********************
scenic_data_requests
********************
Script that handles data requests between 1GB and 1MB. 
Data requests are executed as background jobs and 
after successful completetion of request data is made
available on ftp server hostd by the Desert Reserach Institute (DRI).
