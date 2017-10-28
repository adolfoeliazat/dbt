import pyodbc

from contextlib import contextmanager

import dbt.adapters.default
import dbt.compat
import dbt.exceptions

from dbt.logger import GLOBAL_LOGGER as logger


class AzureDataWarehouseAdapter(dbt.adapters.default.DefaultAdapter):

    @classmethod
    @contextmanager
    def exception_handler(cls, profile, sql, model_name=None,
                          connection_name=None):
        ## scaffold -- see https://github.com/mkleehammer/pyodbc/wiki/Exceptions
        try:
            yield

        except Exception as e:
            logger.debug("Error running SQL: %s", sql)
            logger.debug("Rolling back transaction.")
            cls.release_connection(profile, connection_name)
            raise dbt.exceptions.RuntimeException(e)

    @classmethod
    def type(cls):
        return 'azure_dw'

    @classmethod
    def date_function(cls):
        return 'CURRENT_TIMESTAMP()'

    @classmethod
    def get_status(cls, cursor):
        return cursor.rowcount

    @classmethod
    def get_odbc_connection_string(cls, credentials):
        return 'DRIVER={ODBC Driver 13 for SQL Server};SERVER={host};PORT={port};DATABASE={database};UID={username};PWD={password}'.format(**profile)  # noqa

    @classmethod
    def open_connection(cls, connection):
        if connection.get('state') == 'open':
            logger.debug('Connection is already open, skipping open.')
            return connection

        result = connection.copy()

        try:
            credentials = connection.get('credentials', {})
            handle = pyodbc.connect(
                cls.get_odbc_connection_string(credentials))

            result['handle'] = handle
            result['state'] = 'open'
        except Exception as e:
            logger.debug("Got an error when attempting to open a postgres "
                         "connection: '{}'"
                         .format(e))

            result['handle'] = None
            result['state'] = 'fail'

            raise dbt.exceptions.FailedToConnectException(str(e))

        return result

    @classmethod
    def drop_relation(cls, profile, schema, rel_name, rel_type, model_name):
        #  SQL server doesn't have a 'drop ... cascade'. so we have to
        #  get the dependent things and drop them.
        #  see https://stackoverflow.com/questions/4858488/sql-server-drop-table-cascade-equivalent

    @classmethod
    def rename(cls, profile, schema, from_name, to_name, model_name=None):
        from_relation = cls.quote_schema_and_table(profile, schema, from_name)
        to_relation = cls.quote(to_name)
        sql = 'sp_rename {}, {}'.format(from_relation, to_relation)

        connection, cursor = cls.add_query(profile, sql, model_name)

    @classmethod
    def get_columns_in_table(cls, profile, schema_name, table_name,
                             model_name=None):
        pass

    @classmethod
    def alter_column_type(cls, profile, schema, table, column_name,
                          new_column_type, model_name=None):
        pass

    @classmethod
    def query_for_existing(cls, profile, schemas, model_name=None):
        pass

    @classmethod
    def get_existing_schemas(cls, profile, model_name=None):
        pass

    @classmethod
    def check_schema_exists(cls, profile, schema, model_name=None):
        pass

    @classmethod
    def cancel_connection(cls, profile, connection):
        pass

    @classmethod
    def get_create_schema_sql(cls, schema):
        pass

    @classmethod
    def get_drop_schema_sql(cls, schema):
        pass

    @classmethod
    def quote(cls, identifier):
        return '[{}]'.format(identifier)