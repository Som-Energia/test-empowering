import sys
import os
import datetime
import unittest
import requests
import ast
from datadiff import diff
from utils import byteify, remove_from_dictionary, read_list_from_file, setup_pg

from amoniak import tasks
from amoniak.utils import (
    setup_peek, setup_mongodb, setup_empowering_api, setup_redis,
    sorted_by_key, Popper, setup_queue
)

import EmpoweringTinyClient


class EmpoweringTestContract(unittest.TestCase):
    erp_client = None
    pg_client = None
    emp_client = None
    to_delete = []

    @classmethod
    def tearDown(self):
        for delete in self.to_delete:
            (contractId,etag) = delete
            if contractId is not None and etag is not None:
                self.emp_client.delete_contract(contractId, etag)
                self.to_delete.remove(delete)

    @classmethod
    def setUpClass(self):
        self.erp_client = setup_peek()
        config = {
            'url': os.getenv('EMPOWERING_URL', None),
            'key': os.getenv('EMPOWERING_KEY_FILE', None),
            'cert': os.getenv('EMPOWERING_CERT_FILE', None),
            'company_id': os.getenv('EMPOWERING_COMPANY_ID', None)
            }
        self.emp_client = EmpoweringTinyClient.Empowering(config, debug=False)
        self.pg_client = setup_pg()

    def _test_OK(self, delete):
        contracts_id = read_list_from_file((os.path.join('data', 'test_som_new_contract1.csv')), int)
        new_contracts = []
        for contract_id in contracts_id:
            fields_to_read = ['name', 'create_date', 'etag']
            contract = self.erp_client.GiscedataPolissa.read(contract_id, fields_to_read)
            if not contract:
                self.fail('Contract {contract_id} does not exists in ERP database'.format(**locals()))

            if delete and contract['etag']:
                try:
                    self.emp_client.delete_contract(contract['name'], contract['etag'])
                except Exception, e:
                    print 'Contract {contractId} already in database'.format(**{'contractId': contract['name']})

            del os.environ['EMPOWERING_URL']
            old_date = self.pg_client.update_record(contract_id, 'create_date',
                                                         datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
            # REQUIREMENT: ASYNC commit disabled
            old_etag = self.pg_client.update_record(contract_id, 'etag', None)
            tasks.enqueue_new_contracts(False, [contract['id']])
            self.pg_client.update_record(contract_id, 'create_date', old_date)
            #self.pg_client.update_record(contract_id, 'etag', old_etag)
            os.environ["EMPOWERING_URL"] = self.emp_client.engine.url

            try:
                new_contracts.append(self.emp_client.get_contract(contract['name']))
            except Exception, e:
                self.fail('Contract was not created')
        return new_contracts

    def test_new_1(self):
        """ Post new contract with all data
        """
        new_contracts = self._test_OK(delete=True)
        for new_contract in new_contracts:
            contract_filename = os.path.join('data', 'contracts',
                                             '{contractId}.json'.format(**{'contractId': new_contract['contractId']}))
            contract_filename_diff = os.path.join('contracts',
                                                  '{contractId}.diff'.format(**{'contractId': new_contract['contractId']}))
            contract = EmpoweringTinyClient.EmpoweringContract()
            contract.load_from_file(contract_filename)
            remove_from_dictionary(new_contract, ['_id', '_etag', '_created', '_updated', '_version', '_links'])

            new_diff = str(diff(byteify(new_contract), contract.root))
            test_diff = open(os.path.join('data', contract_filename_diff)).read()
            self.assertEqual(new_diff, test_diff[:-1])

    @unittest.skip('No unittest contract in ERP database')
    def test_new_2(self):
        """ Post new contract with required data (without extra data available)
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_3(self):
        """ Post new contract with data missing: meteringPointId
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_4(self):
        """ Post new contract with data missing: date start
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_5(self):
        """ Post new contract with data missing: customer
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_6(self):
        """ Post new contract with data missing: devices
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_7(self):
        """ Post new contract with optional data missing: customer address
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_8(self):
        """ Post new contract with optional data missing: customer buildingData
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_9(self):
        """ Post new contract with optional data missing: customer profile
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_10(self):
        """ Post new contract with optional data missing: customisedGroupingCriteria
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_11(self):
        """ Post new contract with optional data missing: customisedServiceParameters
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_12(self):
        """ Post new contract with wrong data: start_date > today()
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_13(self):
        """ Post new contract with wrong data: end_data > start_date
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_14(self):
        """ Post new contract with wrong data: fake citycode
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_15(self):
        """ Post new contract with wrong data: fake countrycode
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_16(self):
        """ Post new contract with wrong data: fake postal code
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_new_17(self):
        """ Post new contract with wrong data: fake provincecode
        """

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_1(self):
        """Post contract with all data - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_2(self):
        """ Post contract with required data (without extra data available) - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_3(self):
        """ Post contract with data missing: meteringPointId - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_4(self):
        """ Post contract with data missing: date start - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_5(self):
        """ Post contract with data missing: customer - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_6(self):
        """ Post contract with data missing: devices - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_7(self):
        """ Post contract with optional data missing: customer address - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_8(self):
        """ Post contract with optional data missing: customer buildingData - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_9(self):
        """ Post contract with optional data missing: customer profile - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_10(self):
        """ Post contract with optional data missing: customisedGroupingCriteria - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_11(self):
        """ Post contract with optional data missing: customisedServiceParameters - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_12(self):
        """ Post contract with wrong data: start_date > today() - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_13(self):
        """ Post contract with wrong data: end_data > start_date - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_14(self):
        """ Post contract with wrong data: fake citycode - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_15(self):
        """ Post contract with wrong data: fake countrycode - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_16(self):
        """ Post contract with wrong data: fake postal code - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_17(self):
        """ Post contract with wrong data: fake provincecode - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_18(self):
        """Post contract with all data - Contract in EMPOWERING_DB
        """
        pass

    @unittest.skip('No unittest contract in ERP database')
    def test_renew_2(self):
        """ Post contract with required data (without extra data available) - Contract not in EMPOWERING_DB
        """
        pass

    # Modificacions contractuals

if __name__ == '__main__':
    unittest.main()