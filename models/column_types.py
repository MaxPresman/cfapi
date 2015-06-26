import json
from sqlalchemy import types
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.mutable import Mutable

class JsonType(Mutable, types.TypeDecorator):
    ''' JSON wrapper type for TEXT database storage.

        References:
        http://stackoverflow.com/questions/4038314/sqlalchemy-json-as-blob-text
        http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/mutable.html
    '''
    impl = types.Unicode

    def process_bind_param(self, value, engine):
        return unicode(json.dumps(value))

    def process_result_value(self, value, engine):
        if value:
            return json.loads(value)
        else:
            # default can also be a list
            return {}

class TSVectorType(types.TypeDecorator):
    ''' TSVECTOR wrapper type for database storage.

        References:
        http://stackoverflow.com/questions/13837111/tsvector-in-sqlalchemy
    '''
    impl = types.UnicodeText

@compiles(TSVectorType, 'postgresql')
def compile_tsvector(element, compiler, **kw):
    return 'tsvector'
