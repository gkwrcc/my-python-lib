import copy

# WRCCWrappers.py is in the `acis` directory, but if moved,
# import will need changed here.
from acis.WRCCWrappers import Wrapper


def f1(a, b):
    return a + b


def test_f1():
    assert f1(1, 2) == 3


class TestSodsum:
    def setup_method(self, test_method):
        self.data_params = {
            'sid': '266779',
            'start_date': '20100101',
            'end_date': '20100131',
            'element': 'maxt'
        }
        self.app_params = {}

    def test_sodsum(self):
        """
        Test that Sodsum works on the normal path.
        """
        data_params = self.data_params
        sodsum = Wrapper('Sodsum',
                         data_params=data_params,
                         app_specific_params=self.app_params)
        data = sodsum.get_data()
        results = sodsum.run_app(data)
        results = results[0]
        # results is a defaultdict(<type 'dict'>,
        # {0: {
        #    'coop_station_id': '266779',
        #    'PRSNT': 31, 'LNGMS': 0, 'LNGPR': 31,
        #    'PSBL': '30', 'MISSG': 0, 'maxt': 31,
        #    'start': '20100101', 'end': '20100131',
        #    'station_name': 'RENO TAHOE INTL AP'}})

        assert 'coop_station_id' in results
        assert 'PRSNT' in results
        assert 'LNGMS' in results
        assert 'LNGPR' in results
        assert 'PSBL' in results
        assert 'MISSG' in results
        assert 'maxt' in results
        assert 'start' in results
        assert 'end' in results
        assert 'station_name' in results

    def test_sodsum_bad_dates(self):
        """
        Test that Sodsum handles bad `start_date` and `end_date`.
        """
        bad_params = copy.deepcopy(self.data_params)
        bad_params['start_date'] = 'ABCDEFGH'
        bad_params['end_date'] = '1234'
        sodsum = Wrapper('Sodsum',
                         data_params=bad_params,
                         app_specific_params=self.app_params)
        data = sodsum.get_data()
        results = sodsum.run_app(data)
        results = results[0]
        assert results == 0

    def test_sodsum_bad_station_id(self):
        """
        Test that Sodsum handles a bad `sid`.
        """
        bad_params = copy.deepcopy(self.data_params)
        bad_params['sid'] = ''
        sodsum = Wrapper('Sodsum',
                         data_params=bad_params,
                         app_specific_params=self.app_params)
        data = sodsum.get_data()
        results = sodsum.run_app(data)
        results = results[0]
        assert results == 0
