#
# meta_tables.py defines ACIS database tables
# as SQLAlchemy objects.
#

import sqlalchemy as SA
import sqlalchemy.orm as SAO
from sqlalchemy.engine import create_engine, url


def get_engine(config={}, *args, **kwargs):
    URL = url.URL(**config)
    return create_engine(URL, *args, **kwargs)


def get_session():
    Session = SAO.scoped_session(SAO.sessionmaker(bind=engine, autoflush=False, autocommit=False, weak_identity_map=False))
    return Session()

DB_CONFIG = {
    'drivername': 'postgres',
    'username': 'acis',
    'password': None,
    'host': 'air.dri.edu',
    'port': '55432',
    'database': 'metadata',
    'query': None,
}

engine = get_engine(DB_CONFIG)
meta = SA.MetaData(engine)

station_table = SA.Table('station', meta,
                    SA.Column('ucan_station_id', SA.Integer, primary_key=True),
                    SA.Column('state_key', SA.Integer, SA.ForeignKey('state.state_key')),
                    autoload=True)

station_network_table = SA.Table('station_network', meta,
                    SA.Column('ucan_station_id', SA.Integer, SA.ForeignKey('station.ucan_station_id'), primary_key=True),
                    SA.Column('network_station_id', SA.String, primary_key=True),
                    SA.Column('id_type_key', SA.Integer, SA.ForeignKey('id_type.id_type_key'), primary_key=True),
                    SA.Column('end_date', SA.Date, primary_key=True),
                    autoload=True)

station_location_table = SA.Table('station_location', meta,
                    SA.Column('ucan_station_id', SA.Integer, SA.ForeignKey('station.ucan_station_id'), primary_key=True),
                    autoload=True)

station_county_table = SA.Table('station_county', meta,
                    SA.Column('ucan_station_id', SA.Integer, primary_key=True),
                    SA.Column('county_key', SA.Integer, SA.ForeignKey('county.county_key'), primary_key=True),
                    autoload=True)

station_digital_table = SA.Table('station_digital', meta,
                    autoload=True)

station_variable_table = SA.Table('variable', meta,
                    SA.Column('ucan_station_id', SA.Integer, SA.ForeignKey('station.ucan_station_id'), primary_key=True),
                    SA.Column('network_station_id', SA.String(20), SA.ForeignKey('station_network.network_station_id'), primary_key=True),
                    SA.Column('network_key', SA.Integer, primary_key=True),
                    SA.Column('var_major_id', SA.Integer, SA.ForeignKey('global_variable_maj_min.major_id'), primary_key=True),
                    SA.Column('var_minor_id', SA.Integer, SA.ForeignKey('global_variable_maj_min.minor_id'), primary_key=True),
                    SA.Column('begin_date', SA.Date, primary_key=True),
                    SA.Column('end_date', SA.Date, primary_key=True),
                    autoload=True)

network_table = SA.Table('network', meta, autoload=True)

id_type_table = SA.Table('id_type', meta,
                    SA.Column('id_type_key', SA.Integer, primary_key=True),
                    autoload=True)
state_table = SA.Table('state', meta,
                    SA.Column('state_key', SA.Integer, primary_key=True),
                    autoload=True)

county_table = SA.Table('county', meta,
                    SA.Column('county_key', SA.Integer, primary_key=True),
                    autoload=True)

global_variable_maj_min_table = SA.Table('global_variable_maj_min', meta,
                    SA.Column('major_id', SA.Integer, primary_key=True),
                    SA.Column('minor_id', SA.Integer, primary_key=True),
                    autoload=True)

########################
# WRCC Extended tables #
########################
station_subnetwork_table = SA.Table('subnetwork_stations', meta,
                    SA.Column('subnetwork_key', SA.Integer, SA.ForeignKey('subnetwork.subnetwork_key'), primary_key=True),
                    SA.Column('ucan_station_id', SA.Integer, SA.ForeignKey('station.ucan_station_id'), primary_key=True),
                    SA.Column('network_station_id', SA.String(20), SA.ForeignKey('station_network.network_station_id'), primary_key=True),
                    )
subnetwork_table = SA.Table('subnetwork', meta,
                    SA.Column('subnetwork_key', SA.Integer, primary_key=True),
                    SA.Column('network_key', SA.Integer, SA.ForeignKey('network.network_key')),
                    autoload=True)
#############################
# END WRCC Extended tables  #
#############################


class TableBase(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class Station(TableBase):
    def __repr__(self):
        return "<Station: %d %s, %s>" % (self.ucan_station_id, self.station_best_name, self.fips_state_abbr)


class StationNetwork(TableBase):
    def __repr__(self):
        return "<StationNetwork: %d - %s>" % (self.ucan_station_id, self.network_station_id)


class StationLocation(TableBase):
    def __repr__(self):
        return "<StationLocation: %d %.4f %.4f>" % (self.ucan_station_id, self.latitude, self.longitude)


class StationCounty(TableBase):
    def __repr__(self):
        return "<StationCounty: %d - %s>" % (self.ucan_station_id, self.county_name)


class NetworkId(object):
    def __repr__(self):
        return "<NetworkId: %s>" % (self.id_type)


class Network(object):
    def __repr__(self):
        return "<Network: %s>" % (self.network_key)


class IdType(object):
    def __repr__(self):
        return "<IdType: %d - %s>" % (self.id_type_key, self.name)


class County(object):
    def __repr__(self):
        return "<County: %s %s>" % (self.county_name, self.fips_state_abbr)


class State(object):
    def __repr__(self):
        return "<State: %s>" % (self.state_name,)


class Variable(object):
    def __repr__(self):
        return "<Variable: (%d,%d) %s>" % (self.major_id, self.minor_id, self.long_name)


class StationVariable(object):
    def __repr__(self):
        return "<StationVariable: (%d,%d) %s>" % (self.var_major_id, self.var_minor_id, self.network_station_id)


class StationSubnetwork(TableBase):
    def __repr__(self):
        return "<StationSubnetwork: %d %s>" % (self.ucan_station_id, self.network_station_id)


class Subnetwork(TableBase):
    def __repr__(self):
        return "<Subnetwork: %d>" % (self.subnetwork_key,)


station_map = SAO.mapper(Station, station_table,
                properties={
                    'state': SAO.relation(State, backref='station_set'),
                    'nIds': SAO.relation(NetworkId, order_by=[
                            station_network_table.c.id_type_key, station_network_table.c.end_date]),
                    'sDate': SAO.column_property(
                        SA.select([SA.sql.func.min(station_digital_table.c.begin_date)],
                            station_table.c.ucan_station_id == station_digital_table.c.ucan_station_id).as_scalar(), deferred=True),
                    'eDate': SAO.column_property(
                        SA.select([SA.sql.func.max(station_digital_table.c.end_date)],
                            station_table.c.ucan_station_id == station_digital_table.c.ucan_station_id).as_scalar(), deferred=True),
                    'variables': SAO.relation(StationVariable),
                    'subnetworks': SAO.relation(StationSubnetwork),
                }
            )
station_network_map = SAO.mapper(StationNetwork, station_network_table)
station_location_map = SAO.mapper(StationLocation, station_location_table)
station_county_map = SAO.mapper(StationCounty, station_county_table,
                properties={
                    'county': SAO.relation(County, backref='station_set'),
                }
            )
state_map = SAO.mapper(State, state_table)
county_map = SAO.mapper(County, county_table)
id_type_map = SAO.mapper(IdType, id_type_table)
network_map = SAO.mapper(Network, network_table)
networkid_map = SAO.mapper(NetworkId, station_network_table, include_properties=[],
    properties={
        'uid': station_network_table.c.ucan_station_id,
        'sid': station_network_table.c.network_station_id,
        'id_type_key': station_network_table.c.id_type_key,
        'id_type': SAO.relation(IdType),
        'sDate': station_network_table.c.begin_date,
        'eDate': station_network_table.c.end_date,
        },
    )
variable_map = SAO.mapper(Variable, global_variable_maj_min_table)
station_variable_map = SAO.mapper(StationVariable, station_variable_table)
subnetwork_map = SAO.mapper(Subnetwork, subnetwork_table)
station_subnetwork_map = SAO.mapper(StationSubnetwork, station_subnetwork_table,
                            properties={
                                'subnetwork': SAO.relation(Subnetwork),
                            })


if __name__ == '__main__':
    # An example of creating a session and querying a station.
    session = get_session()
    s = session.query(Station).filter(Station.ucan_station_id==1505).one()

