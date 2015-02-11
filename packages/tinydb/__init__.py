"""
TinyDB is a tiny, document oriented database optimized for your happiness :)

TinyDB stores differrent types of python data types using a configurable
backend. It has support for handy querying and tables.

.. codeauthor:: Markus Siemens <markus@m-siemens.de>

Usage example:

>>> db = TinyDB(storage=MemoryStorage)
>>> db.insert({'data': 5})  # Insert into '_default' table
>>> db.search(where('data') == 5)
[{'data': 5, '_id': 1}]
>>> # Now let's create a new table
>>> tbl = db.table('our_table')
>>> for i in range(10):
...     tbl.insert({'data': i})
...
>>> len(tbl.search(where('data') < 5))
5
"""

from tinydb.queries import where
from tinydb.storages import Storage, JSONStorage
from tinydb.database import TinyDB

__all__ = ('TinyDB', 'Storage', 'JSONStorage', 'where')
