import sys
import os
import datetime
import unittest
import requests
import ast
from datadiff import diff
from utils import byteify, remove_from_dictionary

import uempowering 


class EmpoweringTestContract(unittest.TestCase):
    client = None
    to_delete = []

    @classmethod
    def tearDown(self):
        for delete in self.to_delete:
            (contractId,etag) = delete
            if contractId is not None and etag is not None:
                self.client.delete_contract(contractId,etag)
                self.to_delete.remove(delete)

    @classmethod
    def setUpClass(self):
        config = {
            'url': os.getenv('EMPOWERING_URL', None),
            'key': os.getenv('EMPOWERING_KEY_FILE', None),
            'cert': os.getenv('EMPOWERING_CERT_FILE', None),
            'company_id': os.getenv('EMPOWERING_COMPANY_ID', None)
            }
        self.client = uempowering.Empowering(config,debug=False)

    def _test_OK(self, result):
        self.assertEqual(result['_status'], 'OK')
        if result and isinstance(result,dict):
            self.to_delete.append((result['contractId'], result['_etag']))

    def _test_new_OK(self, filename, field):
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', filename))
        result = self.client.add_contract(new_contract.dump())
        self.assertEqual(result[field], new_contract.root[field])
        self._test_OK(result)

    def _test_new_missing_OK(self, filename, child, field):
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', filename))
        new_contract.root.get(child,new_contract.root).pop(field)

        result = self.client.add_contract(new_contract.dump())
        self._test_OK(result)

    def _test_update_OK(self, contract_filename, update_filename):
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        self.client.add_contract(new_contract.dump())
        contract = self.client.get_contract(new_contract.root['contractId'])

        update_contract = uempowering.EmpoweringContract()
        update_contract.load_from_file(os.path.join('data', update_filename))
        self.client.debug = True
        result = self.client.update_contract(contract['contractId'], contract['_etag'], update_contract.dump())
        self._test_OK(result)

    def _test_ERROR(self, new_contract, field, error):
        result = None
        try:
            result = self.client.add_contract(new_contract.dump())
        except requests.exceptions.HTTPError, e:
            self.assertEqual(e.response.status_code,422)
            self.assertEqual(e.response.reason, 'UNPROCESSABLE ENTITY')
            content = ast.literal_eval(e.response.content)
            self.assertEqual(content['_status'], 'ERR')
            self.assertDictEqual(content['_issues'],
                                 {field: error})

        if result and isinstance(result,dict):
            self.to_delete.append((result.get('contractId'),
                                   result.get('_etag')))
            self.fail('Request should fail')

    def _test_new_missing_ERROR(self, filename, child, field):
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data',filename))
        new_contract.root.get(child,new_contract.root).pop(field)
        self._test_ERROR(new_contract, field, "required field")

    def test_new_1(self):
        """ Post new contract with all data
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_OK(contract_filename, 'contractId')

    def test_new_2(self):
        """ Post new contract with data missing: contractId
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_ERROR(contract_filename, None, 'contractId')

    def test_new_3(self):
        """ Post new contract with data missing: meteringPointId
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_ERROR(contract_filename, None, 'meteringPointId')

    def test_new_4(self):
        """ Post new contract with data missing: date start
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_ERROR(contract_filename, None, 'dateStart')

    def test_new_5(self):
        """ Post new contract with data missing: customer
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_ERROR(contract_filename, None, 'customer')

    def test_new_6(self):
        """ Post new contract with data missing: devices
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_ERROR(contract_filename, None, 'devices')

    def test_new_7(self):
        """ Post new contract with optional data missing: customer address
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_OK(contract_filename, 'customer', 'address')

    def test_new_8(self):
        """ Post new contract with optional data missing: customer buildingData
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_OK(contract_filename, 'customer', 'buildingData')

    def test_new_9(self):
        """ Post new contract with optional data missing: customer profile
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_OK(contract_filename, 'customer', 'profile')

    def test_new_10(self):
        """ Post new contract with optional data missing: customisedGroupingCriteria
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_OK(contract_filename, 'customer',
                                  'customisedGroupingCriteria')

    def test_new_11(self):
        """ Post new contract with optional data missing: customisedServiceParameters
        """
        contract_filename = 'test_new_contract1.json'
        self._test_new_missing_OK(contract_filename, 'customer',
                                  'customisedServiceParameters')

    def test_new_12(self):
        """ Post new contract with wrong data: start_date > today()
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data',contract_filename))
        new_contract.root['dateStart'] = (datetime.datetime.now() +
                                          datetime.timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._test_ERROR(new_contract, 'dateStart', None) # TBD: Error message

    def test_new_13(self):
        """ Post new contract with wrong data: end_data > start_date
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        new_contract.root['dateEnd'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        new_contract.root['dateStart'] = (datetime.datetime.now() + \
                datetime.timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._test_ERROR(new_contract, 'dateEnd', None) # TBD: Error message

    def test_new_14(self):
        """ Post new contract with wrong data: fake citycode
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        new_contract.root['customer']['address']['cityCode'] = '9999999999'
        self._test_ERROR(new_contract, 'cityCode', None) # TBD: Error message

    def test_new_15(self):
        """ Post new contract with wrong data: fake countrycode
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        new_contract.root['customer']['address']['countryCode'] = '9999999999'
        self._test_ERROR(new_contract, 'countryCode', None) # TBD: Error message

    def test_new_16(self):
        """ Post new contract with wrong data: fake postal code
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        new_contract.root['customer']['address']['postalCode'] = '9999999999'
        self._test_ERROR(new_contract, 'postalCode', None) # TBD: Error message

    def test_new_17(self):
        """ Post new contract with wrong data: fake provincecode
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        new_contract.root['customer']['address']['provinceCode'] = '9999999999'
        self._test_ERROR(new_contract, 'provinceCode', None) # TBD: Error message

    def test_get_1(self):
        """ Get contract
        """
        contract_filename = 'test_new_contract1.json'
        contract_filename_diff = 'test_new_contract1.diff'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        self.client.add_contract(new_contract.dump())
        contract  = self.client.get_contract(new_contract.root['contractId'])
        remove_from_dictionary(contract, ['_id', '_etag', '_created', '_updated', '_version', '_links'])

        new_diff = str(diff(byteify(new_contract.root), contract))
        test_diff = open(os.path.join('data', contract_filename_diff)).read()
        self.assertEqual(new_diff, test_diff[:-1])

        if contract and isinstance(contract, dict):
            self.to_delete.append((contract.get('contractId'),
                                   contract.get('_etag')))

    def test_get_2(self):
        """ Get unknown contract
        """
        contract = None
        try:
            contract  = self.client.get_contract('AXXXXXXXXX')
        except requests.exceptions.HTTPError, e:
            self.assertEqual(e.response.status_code, 404)
            self.assertEqual(e.response.reason, 'NOT FOUND')

        if contract and isinstance(contract, dict):
            self.to_delete.append(contract.get('contractId'),
                                   contract.get('_etag'))
            self.assertTrue(False)

    @unittest.skip('BeeData PATCH failing')
    def test_update_1(self):
        """ Update update contract with all data
        """

    @unittest.skip('BeeData PATCH failing')
    def test_update_2(self):
        """ Update update contract with data missing: contractId
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_3(self):
        """ Update update contract with data missing: meteringPointId
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_4(self):
        """ Update update contract with data missing: date start
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_5(self):
        """ Update update contract with data missing: customer
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_6(self):
        """ Update update contract with data missing: devices
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_7(self):
        """ Update update contract with optional data missing: customer address
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_8(self):
        """ Update update contract with optional data missing: customer buildingData
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_9(self):
        """ Update update contract with optional data missing: customer profile
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_10(self):
        """ Update update contract with optional data missing: customisedGroupingCriteria
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_11(self):
        """ Update update contract with optional data missing: customisedServiceParameters
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_12(self):
        """ Update update contract with wrong data: start_date > today()
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_13(self):
        """ Update update contract with wrong data: end_data > start_date
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_14(self):
        """ Update update contract with wrong data: fake citycode
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_15(self):
        """ Update update contract with wrong data: fake countrycode
        """
        pass

    @unittest.skip('BeeData PATCH failing')
    def test_update_16(self):
        """ Update update contract with wrong data: fake provincecode
        """
        pass

    def test_delete_1(self):
        """ Delete contract
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        self.client.add_contract(new_contract.dump())
        contract = self.client.get_contract(new_contract.root['contractId'])

        result = None
        try:
            result = self.client.delete_contract(contract['contractId'], contract['_etag'])
        except Exception, e:
            self.fail('Exception raised')
        self.assertEqual(result, [])

    def test_delete_2(self):
        """ Delete wrong _etag
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        self.client.add_contract(new_contract.dump())
        contract = self.client.get_contract(new_contract.root['contractId'])

        result = None
        try:
            result = self.client.delete_contract(contract['contractId'], 'XXXXXXXXXXXXXX')
        except Exception, e:
            self.assertEqual(e.response.status_code,412)
            self.assertEqual(e.response.reason,'PRECONDITION FAILED')

        if contract and isinstance(contract,dict):
            self.to_delete.append((contract.get('contractId'),
                                   contract.get('_etag')))

    def test_delete_3(self):
        """ Delete wrong contractId
        """
        contract_filename = 'test_new_contract1.json'
        new_contract = uempowering.EmpoweringContract()
        new_contract.load_from_file(os.path.join('data', contract_filename))
        self.client.add_contract(new_contract.dump())
        contract = self.client.get_contract(new_contract.root['contractId'])

        result = None
        try:
            result = self.client.delete_contract('AXXXXXXXXX', contract['_etag'])
        except Exception, e:
            self.assertEqual(e.response.status_code,404)

        if contract and isinstance(contract,dict):
            self.to_delete.append((contract.get('contractId'),
                                   contract.get('_etag')))

if __name__ == '__main__':
    unittest.main()
