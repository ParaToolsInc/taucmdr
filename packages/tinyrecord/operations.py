def null_query(x):
    """
    Returns false regardless of the document
    passed to the function.
    """
    return False


class Operation(object):
    """
    An operation represents a single, atomic
    sequence of things to do to in-memory data.
    Every operation must implement the abstract
    ``perform`` method.
    """
    def perform(self):
        raise NotImplementedError


class InsertMultiple(Operation):
    """
    Insert multiple records *iterable* into the
    database.

    :param iterable: The iterable of elements to
        be inserted into the DB.
    """
    def __init__(self, iterable):
        self.iterable = iterable

    def perform(self, data):
        eid = max(data) if data else 0
        for element in self.iterable:
            eid += 1
            data[eid] = element


class UpdateCallable(Operation):
    """
    Mutate each of the records with a given
    *function* for all records that match a
    certain *query*.

    :param fields: The fields to update.
    """
    def __init__(self, function, query=null_query, eids=[]):
        self.function = function
        self.query = query
        self.eids = eids

    def perform(self, data):
        for key in data:
            value = data[key]
            if key in self.eids or self.query(value):
                self.function(value)


class Remove(Operation):
    """
    Remove documents from the DB matching
    the given *query*.

    :param query: The query to remove.
    """
    def __init__(self, query=null_query, eids=[]):
        self.query = query
        self.eids = eids

    def perform(self, data):
        for key in list(data):
            if key in self.eids or self.query(data[key]):
                del data[key]
