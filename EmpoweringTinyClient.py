import requests
import collections
import json
import os

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
        self.key = config['key']
        self.cert = config['cert']
        self.company_id = config['company_id']
        self.debug = debug

    def req_to_service(self,req):
        url = requests.compat.urljoin(self.url, req.url)
        data = req.data
        req.headers.update({'X-CompanyId': self.company_id})

        result = self.methods[req.command](url,
                                           data=data,
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

    def __init__(self,url,data=None):
        self.url = requests.compat.urljoin(self.url,url)
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

    def get_contract(self, contract_id=None):
        url = 'contracts/'

        if contract_id:
            url = requests.compat.urljoin(url, contract_id)

        req = Empowering_GET(url)
        return self.engine.req(req)

    def add_contract(self,data):
        url = 'contracts/'
        req = Empowering_POST(url,data)
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
