import os
import csv
import psycopg2
import datetime

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def remove_from_dictionary(_dict, _keys):
    for _key in _keys:
        _dict.pop(_key)


def read_list_from_file(filename, cast_type):
    if filename:
        with open(filename, 'rb') as f:
            return [cast_type(row[0]) for row in csv.reader(f)]
    else:
        return None


class PgClient(object):
    conn = None
    cr = None

    def __init__(self, config):
            pg_con = " host=" + config.get('DB_HOSTNAME') + \
                     " port=" + config.get('DB_PORT') + \
                     " dbname=" + config.get('DB_NAME') + \
                     " user=" + config.get('DB_USER') + \
                     " password=" + config.get('DB_PASSWORD')
            self.conn = psycopg2.connect(pg_con)
            self.cr = self.conn.cursor()

    def query(self, query):
        try:
            self.cr.execute(query)
        except Exception, ex:
            print 'Failed executing query'
            raise ex

    def select(self, query):
        self.query(query)
        return [record[0] for record in self.cr.fetchall()]

    def update(self, query):
        self.query(query)
        self.conn.commit()

    def update_record(self, contract_id, field, new_value):
        if not new_value:
            new_value = 'NULL'
        else:
            if isinstance(new_value, datetime.datetime):
                new_value = str(new_value)
            if isinstance(new_value,str) or isinstance(new_value,unicode):
                new_value = "'{new_value}'".format(**locals())

        sql_query = "SELECT {field} FROM giscedata_polissa WHERE id={contract_id}".format(**locals())
        old_value = self.select(sql_query)[0]
        sql_query = "UPDATE giscedata_polissa SET {field}={new_value} WHERE id={contract_id}".format(**locals())
        self.update(sql_query)
        return old_value


def setup_pg():
    pg_vars = ['DB_HOSTNAME', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']

    def get_env(var):
        value = os.getenv(var, None)
        if not value:
            raise Exception
        return value

    config = {var: get_env(var) for var in pg_vars}
    return PgClient(config)

