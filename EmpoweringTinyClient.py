import requests
import collections
import json
import os
from urlparse import urlparse

from empowering.utils import remove_none, make_uuid, make_utc_timestamp


class EmpoweringEngine(object):
    methods = {
        'GET': requests.get,
        'POST': requests.post,
        'DELETE': requests.delete,
        'PATCH': requests.patch
    }

    def __init__(self, config, debug=False):
        self.url = config['url']
        self.username = config['username']
        self.password = config['password']
        self.key = config['key']
        self.cert = config['cert']
        self.company_id = config['company_id']
        self.debug = debug
        self.auth = None

    def login(self, headers):
        data = json.dumps({
            "username": self.username, "password": self.password
        })
        url_parts = urlparse(self.url)
        login_url = url_parts.scheme + '://' + url_parts.netloc + '/authn/login'
        headers.update({'Content-type': 'application/json'})
        result = self.methods['POST'](login_url,
                                      data=data,
                                      headers=headers,
                                      cert=(self.cert, self.key),
                                      verify=False)
        return result.json()['token']

    def req_to_service(self, req):
        headers = {'X-CompanyId': self.company_id}

        url = requests.compat.urljoin(self.url, req.url)
        data = req.data
        req.headers.update(headers)

        if not self.auth:
            self.auth = self.login(headers)
        req.headers.update({'Cookie': "iPlanetDirectoryPro=%s" % self.auth})


        result = self.methods[req.command](url,
                                           data=json.dumps(data),
                                           headers=req.headers,
                                           cert=(self.cert, self.key),
                                           verify=False)
        result.raise_for_status()

        if result.status_code == 204:
            return []

        r = result.json()
        if isinstance(r, dict):
            return r.get('_items', r)
        return r

    def req_to_curl(self,req):
        url = requests.compat.urljoin(self.url, req.url)
        data = req.data
        req.headers.update({'X-CompanyId': self.company_id})

        header_ = ''
        for header_key, header_value in req.headers.iteritems():
            header_ += ' -H "{header_key}:{header_value}"'.format(**locals())

        data_ = ''
        if data:
            data_ = '-d \'{data}\''.format(**locals())

        curl_command = 'curl -k -X {req.command} -i --cert {self.cert} --key {self.key} {header_} \'{url}\' {data_}'.format(**locals())
        return curl_command

    def req(self, req):
        if self.debug:
            return self.req_to_curl(req)
        else:
            return self.req_to_service(req)


class Empowering_REQ(object):
    url = None
    data = None
    headers = {'Content-type': 'application/json'}

    def __init__(self, url, data=None):
        self.url = requests.compat.urljoin(self.url, url)
        self.data = data


class Empowering_GET(Empowering_REQ):
    command = 'GET'


class Empowering_POST(Empowering_REQ):
    command = 'POST'


class Empowering_DELETE(Empowering_REQ):
    command = 'DELETE'

    def __init__(self, url, etag):
        self.headers.update({'If-Match': etag})
        return super(Empowering_DELETE, self).__init__(url)


class Empowering_PATCH(Empowering_REQ):
    command = 'PATCH'

    def __init__(self, url, etag, data):
        self.headers.update({'If-Match': etag})
        return super(Empowering_PATCH, self).__init__(url, data)


class EmpoweringOTResults(object):
    SUPPORTED_OT = ['OT101', 'OT102', 'OT103', 'OT105', 'OT106', 'OT201', 'OT204', 'OT205', 'OT301', 'OT302',
                    'OT303', 'OT304', 'OT305', 'OT401', 'OT501', 'OT501', 'OT503', 'OT504', 'OT603', 'OT603g',
                    'OT701', 'OT703', 'OT900', 'OT910', 'OT920'
                    ]
    name = None
    path = None

    @classmethod
    def ot_is_supported(cls, ot):
        return ot in cls.SUPPORTED_OT

    @classmethod
    def path(cls, ot):
        if ot not in cls.SUPPORTED_OT:
            raise NotImplementedError()
        return ot + 'Results/'


class Empowering(object):
    engine = None

    def __init__(self, config, debug=False):
        self.engine = EmpoweringEngine(config, debug)

    @property
    def debug(self):
        return self.engine.debug

    @debug.setter
    def debug(self, x):
        self.engine.debug = x

    def get_contract(self, contract_id=None, page=1, max_results=200):
        url = 'contracts/'

        if contract_id:
            url = requests.compat.urljoin(url, contract_id)
        else:
            search_pattern = '?page={page}&max_results={max_results}'.format(**locals())
            url = requests.compat.urljoin(url, search_pattern)

        req = Empowering_GET(url)
        return self.engine.req(req)

    def add_contract(self, data):
        url = 'contracts/'
        req = Empowering_POST(url, data)
        return self.engine.req(req)

    def update_contract(self, contract_id, etag, data):
        url = 'contracts/'
        
        if not contract_id:
            raise Exception

        url = requests.compat.urljoin(url, contract_id)
        req = Empowering_PATCH(url, etag, data)
        return self.engine.req(req)

    def delete_contract(self, contract_id, etag):
        url = 'contracts/'

        if not contract_id:
            raise Exception

        url = requests.compat.urljoin(url, contract_id)
        req = Empowering_DELETE(url, etag)
        return self.engine.req(req)

    def add_measurements(self, data):
        url = 'amon_measures/'

        req = Empowering_POST(url,data)
        return self.engine.req(req)

    def get_measurements_by_device(self, device_id=None):
        url = 'amon_measures_measurements/'

        if not device_id:
            raise Exception

        search_pattern = '?where="deviceId"=="{device_id}"'.format(**locals())
        url = requests.compat.urljoin(url, search_pattern)
        req = Empowering_GET(url)
        return self.engine.req(req)

    def get_dh_measurements_by_device(self, device_id=None):
        url = 'residential_timeofuse_amon_measures_measurements/'

        if not device_id:
            raise Exception

        search_pattern = '?where="deviceId"=="{device_id}"'.format(**locals())
        url = requests.compat.urljoin(url, search_pattern)
        req = Empowering_GET(url)
        return self.engine.req(req)

    def get_measurements_by_contract(self, contract_id):
        url = 'contracts/'

        if not contract_id:
            raise Exception

        contract = self.get_contract(contract_id)
        measurements = []
        for device in contract['devices']:
            measurements += self.get_measurements_by_device(device['deviceId'])
        return measurements

    def get_dh_measurements_by_contract(self, contract_id):
        url = 'contracts/'

        if not contract_id:
            raise Exception

        contract = self.get_contract(contract_id)
        measurements = []
        for device in contract['devices']:
            measurements += self.get_dh_measurements_by_device(device['deviceId'])
        return measurements

    def delete_measurements(self, contract_id):
        url = 'delete_measures'

        if not contract_id:
            raise Exception

        data = {"contractId": contract_id,
                "companyId": int(self.engine.company_id),
                "type": "electricityConsumption"
        }
        req = Empowering_POST(url, data)
        return self.engine.req(req)

    def get_results_by_filter(self, url, search_pattern):
        url = requests.compat.urljoin(url, search_pattern)
        req = Empowering_GET(url)
        return self.engine.req(req)

    def get_results_by_contract(self, ot, contract_id, start_date=None, end_date=None):
        if not EmpoweringOTResults.ot_is_supported(ot):
            raise NotImplementedError

        url = EmpoweringOTResults.path(ot)

        search_pattern = '?where="contractId"=="{contract_id}"'.format(**locals())
        if start_date:
            search_pattern += '&"dateStart">"{start_date}"'.format(**locals())
        if end_date:
            search_pattern += '&"endStart">"{end_date}"'.format(**locals())
        return self.get_results_by_filter(url, search_pattern)


class EmpoweringDataObject(object):
    def update(self,new_values):
        def update_(d, u):
            for k, v in u.iteritems():
                if isinstance(v, collections.Mapping):
                    r = update_(d.get(k, {}), v)
                    d[k] = r
                else:
                    d[k] = u[k]
            return d
        update_(self.root, new_values)

    def dump(self):
        return json.dumps(remove_none(self.root))

    def dump_to_file(self, filename):
        with open(filename, 'w') as data_file:
            json.dump(remove_none(self.root), data_file, indent=4)

    def load_from_file(self, filename):
        with open(filename) as data_file:
            data = json.load(data_file)
            self.update(data)


class EmpoweringContract(EmpoweringDataObject):
    root = None

    def __init__(self):
        self.root = {
            'ownerId': None,
            'payerId': None,
            'dateStart': None,
            'dateEnd': None,
            'contractId': None,
            'tariffId': None,
            'power': None,
            'version': None,
            'activityCode': None,
            'climaticZone': None,
            'customer': {
                'customerId': None,
                'address': {
                  'buildingId': None,
                  'city': None,
                  'cityCode': None,
                  'countryCode': None,
                  'country': None,
                  'street': None,
                  'postalCode': None,
                  'province': None,
                  'provinceCode': None,
                  'parcelNumber': None
                },
                'buildingData':
                {
                    'buildingConstructionYear': None,
                    'dwellingArea': None,
                    'buildingType': None,
                    'dwellingPositionInBuilding': None,
                    'dwellingOrientation': None,
                    'buildingWindowsType': None,
                    'buildingWindowsFrame': None,
                    'buildingHeatingSource': None,
                    'buildingHeatingSourceDhw': None,
                    'buildingSolarSystem': None
                },
                'profile': {
                    'totalPersonsNumber': None,
                    'minorsPersonsNumber': None,
                    'workingAgePersonsNumber': None,
                    'retiredAgePersonsNumber': None,
                    'malePersonsNumber': None,
                    'femalePersonsNumber': None,
                    'educationLevel': {
                        'edu_prim': None,
                        'edu_sec': None,
                        'edu_uni': None,
                        'edu_noStudies': None
                    }
                },
                'customisedGroupingCriteria': {
                },
                'customisedServiceParameters': {
                }
            },
            'devices': [{
                'dateStart': None,
                'dateEnd': None,
                'deviceId': None
            }]
        }


class EmpoweringMeasurement(EmpoweringDataObject):
    root = None

    def __init__(self):
        self.root = {
            "deviceId": None,
            "meteringPointId": None,
            "measurements":
            [{
                "timestamp": None,
                "type": None,
                "value": None
            }],
            "readings":
            [
                {"type": None, "period": None, "unit": None},
            ]
        }
