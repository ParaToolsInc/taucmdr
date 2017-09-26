# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""TODO: FIXME: Docs"""
import six
from taucmdr import logger
from taucmdr.cf.storage import StorageRecord
from taucmdr.error import InternalError, UniqueAttributeError, ModelError

LOGGER = logger.get_logger(__name__)


class Controller(object):
    """The "C" in `MVC`_.

    Attributes:
        model (AbstractModel): Data model.
        storage (AbstractDatabase): Record storage. 
    
    .. _MVC: https://en.wikipedia.org/wiki/Model-view-controller
    """
    
    messages = {}
    
    def __init__(self, model_cls, storage):
        self.model = model_cls
        self.storage = storage
        
    @classmethod
    def push_to_topic(cls, topic, message):
        cls.messages.setdefault(topic, []).append(message)
        
    @classmethod
    def pop_topic(cls, topic):
        return cls.messages.pop(topic, [])

    def one(self, key):
        """Get a record.
        
        Args:
            key: See :any:`AbstractStorage.get`.
            
        Returns:
            Model: The model for the matching record or None if no such record exists.
        """
        record = self.storage.get(key, table_name=self.model.name)
        return self.model(record) if record else None

    def all(self):
        """Get all records.
        
        Returns:
            list: Models for all records or an empty lists if no records exist.
        """
        return [self.model(record) for record in self.storage.search(table_name=self.model.name)]
    
    def count(self):
        """Return the number of records.
        
        Returns:
            int: Effectively ``len(self.all())``
        """
        return self.storage.count(table_name=self.model.name)
    
    def search(self, keys=None):
        """Return records that have all given keys.
        
        Args:
            keys: See :any:`AbstractStorage.search`.
            
        Returns:
            list: Models for records with the given keys or an empty lists if no records have all keys.
        """
        return [self.model(record) for record in self.storage.search(keys=keys, table_name=self.model.name)]

    def search_hash(self, digests):
        """Returns records which match the hash or partial hash.

        Args:
            digest: One or more partial hex digests, of a hash of the record(s) to find.
            If partial, provide rightmost digits.

        Returns:
            list: Models for records that match the provided hash
        """
        # If this controller is backed by remote storage, have the remote server
        # do the hash lookup for performance reasons
        if self.storage.is_remote():
            return [self.model(record) for record in self.storage.search_hash(digests, table_name=self.model.name)]
        records = self.all()
        if not isinstance(digests, list):
            digests = [digests]
        results = []
        for digest in digests:
            if isinstance(digest, six.string_types):
                results.extend([record for record in records if record.hash_digest()[-len(digest):] == digest])
        return results

    def match(self, field, regex=None, test=None):
        """Return records that have a field matching a regular expression or test function.
        
        Args:
            field: See :any:`AbstractStorage.match`.
            regex: See :any:`AbstractStorage.match`.
            test: See :any:`AbstractStorage.match`.
            
        Returns:
            list: Models for records that have a matching field.
        """
        return [self.model(record) 
                for record in self.storage.match(field, table_name=self.model.name, regex=regex, test=test)]

    def exists(self, keys):
        """Check if a record exists.
        
        Args:
            keys: See :any:`AbstractStorage.exists`.
            
        Returns:
            bool: True if a record matching `keys` exists, False otherwise.
        """
        return self.storage.contains(keys, table_name=self.model.name)

    def populate(self, model, attribute=None, defaults=False):
        """Merges associated data into the model record.
        
        Example:
            Suppose we have the following Person records::
            
                1: {'name': 'Katie', 'friends': [2, 3]}
                2: {'name': 'Ryan', 'friends': [1]}
                3: {'name': 'John', 'friends': [1]}

            Populating ``Person({'name': 'Katie', 'friends': [2, 3]})`` produces this dictionary::
            
                {'name': 'Katie',
                 'friends': [Person({'name': 'Ryan', 'friends': [1]}),
                             Person({'name': 'John', 'friends': [1]}]})
                             
        Args:
            attribute (Optional[str]): If given, return only the populated attribute.
            defaults (Optional[bool]): If given, set undefined attributes to their default values.
        
        Returns:
            If attribute is None, a dictionary of controlled data merged with associated records.
            If attribute is not None, the value of the populated attribute. 
            
        Raises:
            KeyError: `attribute` is undefined in the record. 
        """
        if attribute:
            LOGGER.debug("Populating %s(%s)[%s]", model.name, model.eid, attribute)
            return self._populate_attribute(model, attribute, defaults)
        else:
            LOGGER.debug("Populating %s(%s)", model.name, model.eid)
            if self.storage.is_remote():
                return self._populate_remote(model, defaults=defaults)
            return {attr: self._populate_attribute(model, attr, defaults) for attr in model}

    def _populate_remote(self, model, defaults=None):
        to_populate = []
        for key, props in six.iteritems(model.attributes):
            if 'model' in props or 'collection' in props:
                to_populate.append(key)
        # Populate fields server-side
        populated = dict(self.storage.get(model.eid, table_name=model.name, populate=to_populate))
        # Then convert the returned raw records to their corresponding models
        for key in to_populate:
            if not key in populated:
                continue
            prop = model.attributes[key]
            foreign = prop['model'] if 'model' in prop else prop['collection']
            value = populated[key]
            if isinstance(value, StorageRecord):
                value = foreign(value)
            elif isinstance(value, list):
                value = [foreign(e) for e in value]
            populated[key] = value
        # And add defaults for any missing fields
        if defaults:
            for key, props in six.iteritems(model.attributes):
                if key not in populated:
                    if 'default' in props:
                        populated[key] = props['default']
        return populated

    def _populate_attribute(self, model, attr, defaults):
        try:
            props = model.attributes[attr]
        except KeyError:
            raise ModelError(model, "no attribute '%s'" % attr)
        if not defaults or 'default' not in props:
            value = model[attr]
        else:
            value = model.get(attr, props['default'])
        try:
            foreign = props['model']
        except KeyError:
            try:
                foreign = props['collection']
            except KeyError:
                return value
            else:
                return foreign.controller(self.storage).search(value)
        else:
            return foreign.controller(self.storage).one(value)

    def create(self, data):
        """Atomically store a new record and update associations.
        
        Invokes the `on_create` callback **after** the data is recorded.  If this callback raises
        an exception then the operation is reverted.
        
        Args:
            data (dict): Data to record.
            
        Returns:
            Model: The newly created data. 
        """
        data = self.model.validate(data)
        unique = {attr: data[attr] for attr, props in self.model.attributes.iteritems() if 'unique' in props}
        if unique and self.storage.contains(unique, match_any=True, table_name=self.model.name):
            raise UniqueAttributeError(self.model, unique)
        with self.storage as database:
            record = database.insert(data, table_name=self.model.name)
            for attr, foreign in self.model.associations.iteritems():
                if 'model' or 'collection' in self.model.attributes[attr]:
                    affected = record.get(attr, None)
                    if affected:
                        foreign_cls, via = foreign
                        self._associate(record, foreign_cls, affected, via)
            model = self.model(record)
            model.check_compatibility(model)
            model.on_create()
            return model
    
    def update(self, data, keys):
        """Change recorded data and update associations.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: update the record with that element identifier.
            * dict: update all records with attributes matching `keys`.
            * list or tuple: apply update to all records matching the elements of `keys`.
            * ``bool(keys) == False``: raise ValueError.
            
        Invokes the `on_update` callback **after** the data is modified.  If this callback raises
        an exception then the operation is reverted.

        Args:
            data (dict): New data for existing records.
            keys: Fields or element identifiers to match.
        """
        for attr in data:
            if attr not in self.model.attributes:
                raise ModelError(self.model, "no attribute named '%s'" % attr)
        with self.storage as database:
            # Get the list of affected records **before** updating the data so foreign keys are correct
            old_records = self.search(keys)
            database.update(data, keys, table_name=self.model.name)
            changes = {}
            for model in old_records:
                changes[model.eid] = {attr: (model.get(attr), new_value) for attr, new_value in data.iteritems()
                                      if not (attr in model and model.get(attr) == new_value)}
                for attr, foreign in self.model.associations.iteritems():
                    try:
                        # 'collection' attribute is iterable
                        new_foreign_keys = set(data[attr])
                    except TypeError:
                        # 'model' attribute is not iterable, so make a tuple
                        new_foreign_keys = set((data[attr],))
                    except KeyError:
                        continue
                    try:
                        # 'collection' attribute is iterable
                        old_foreign_keys = set(model[attr])
                    except TypeError:
                        # 'model' attribute is not iterable, so make a tuple
                        old_foreign_keys = set((model[attr],))
                    except KeyError:
                        old_foreign_keys = set()
                    foreign_cls, via = foreign
                    added = list(new_foreign_keys - old_foreign_keys)
                    deled = list(old_foreign_keys - new_foreign_keys)
                    if added:
                        self._associate(model, foreign_cls, added, via)
                    if deled:
                        self._disassociate(model, foreign_cls, deled, via)
            updated_records = self.search(keys)
            for model in updated_records:
                model.check_compatibility(model)
                model.on_update(changes[model.eid])

    def unset(self, fields, keys):
        """Unset recorded data fields and update associations.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: update the record with that element identifier.
            * dict: update all records with attributes matching `keys`.
            * list or tuple: apply update to all records matching the elements of `keys`.
            * ``bool(keys) == False``: raise ValueError.

        Invokes the `on_update` callback **after** the data is modified.  If this callback raises
        an exception then the operation is reverted.

        Args:
            fields (list): Names of fields to unset.
            keys: Fields or element identifiers to match.
        """
        for attr in fields:
            if attr not in self.model.attributes:
                raise ModelError(self.model, "no attribute named '%s'" % attr)
        with self.storage as database:
            # Get the list of affected records **before** updating the data so foreign keys are correct
            old_records = self.search(keys)
            database.unset(fields, keys, table_name=self.model.name)
            changes = {}
            for model in old_records:
                changes[model.eid] = {attr: (model.get(attr), None) for attr in fields if attr in model}
                for attr, foreign in self.model.associations.iteritems():
                    if attr in fields:
                        foreign_cls, via = foreign
                        old_foreign_keys = model.get(attr, None)
                        if old_foreign_keys:
                            self._disassociate(model, foreign_cls, old_foreign_keys, via)
            updated_records = self.search(keys)
            for model in updated_records:
                model.check_compatibility(model)
                model.on_update(changes[model.eid])

    def delete(self, keys):
        """Delete recorded data and update associations.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: delete the record with that element identifier.
            * dict: delete all records with attributes matching `keys`.
            * list or tuple: delete all records matching the elements of `keys`.
            * ``bool(keys) == False``: raise ValueError.

        Invokes the `on_delete` callback **after** the data is deleted.  If this callback raises
        an exception then the operation is reverted.

        Args:
            keys (dict): Attributes to match.
            keys: Fields or element identifiers to match.
        """
        with self.storage as database:
            removed_data = []
            changing = self.search(keys)
            for model in changing:
                for attr, foreign in model.associations.iteritems():
                    foreign_model, via = foreign
                    affected_keys = model.get(attr, None)
                    if affected_keys:
                        LOGGER.debug("Deleting %s(%s) affects '%s' in %s(%s)", 
                                     self.model.name, model.eid, via, foreign_model.name, affected_keys)
                        self._disassociate(model, foreign_model, affected_keys, via)
                for foreign_model, via in model.references:
                    affected = database.search_inside(via, model.eid, table_name=foreign_model.name)
                    affected_keys = [record.eid for record in affected]
                    if affected_keys:
                        LOGGER.debug("Deleting %s(%s) affects '%s' in %s(%s)",
                                     self.model.name, model.eid, via, foreign_model.name, affected_keys)
                        self._disassociate(model, foreign_model, affected_keys, via)
                removed_data.append(dict(model))
            database.remove(keys, table_name=self.model.name)
            for model in changing:
                model.on_delete()

    def traverse_records(self, base_records, direction = 'down', visited = None):
        # From the anchor record we need to push those records which are:
        #   - Down from the anchor record, and all records down AND up from those
        #   - Up from the anchor record, and all records up from those
        if visited is None:
            visited = set()
        records_to_push = []
        for base_record in base_records:
            if base_record.hash_digest() in visited:
                continue
            visited.add(base_record.hash_digest())
            full_record = base_record.populate()
            attrs = base_record.attributes
            down = []
            up = []
            for field, values in six.iteritems(full_record):
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    if field in attrs and 'direction' in attrs[field]:
                        if value is None or value.hash_digest() in visited:
                            continue
                        if direction == 'down' and attrs[field]['direction'] == 'down':
                            down.append(value)
                        elif attrs[field]['direction'] == 'up':
                            up.append(value)
            rec_down = []
            rec_up = []
            for d in down:
                rec_down.extend(self.traverse_records([d], direction='down', visited=visited))
            for u in up:
                rec_up.extend(self.traverse_records([u], direction='up', visited=visited))
            records_to_push.extend(rec_up)
            records_to_push.append(base_record)
            records_to_push.extend(rec_down)
        return records_to_push

    def transport_record(self, record, destination, eid_map, mode):
        LOGGER.debug("Will attempt to transport %s %s to %s.", record.name, record.hash_digest(), destination.name)
        # First, check if this record is already at the destination.
        if destination.is_remote():
            remote_record = destination.search_hash(record.hash_digest(), table_name=self.model.name)
        else:
            remote_record = destination.search_hash(record.hash_digest())
        if remote_record:
            if len(remote_record) > 1:
                raise InternalError("Multiple matches for hash %s on %s!" % record.hash_digest(),
                                    destination.name)
            LOGGER.debug("Record %s %s already exists on %s.", record.name, record.hash_digest(),
                         destination.name)
            return remote_record[0].eid, True

        full_record = record.populate()
        attrs = record.attributes
        data_for_server = {}
        for field, value in six.iteritems(full_record):
            if field in attrs and 'direction' in attrs[field]:
                # Strip out any 'down' references
                if attrs[field]['direction'] == 'down':
                    data_for_server[field] = []
                # Replace any up references with eid to remote record
                elif attrs[field]['direction'] == 'up':
                    if isinstance(value, list):
                        data_for_server[field] = [eid_map[ref.hash_digest()] for ref in value]
                    else:
                        data_for_server[field] = eid_map[value.hash_digest()]
                else:
                    raise InternalError("Invalid direction %s for model %s" % (attrs[field]['direction'], record.name))
            else:
                data_for_server[field] = value
        if destination.is_remote():
            # If the destination is remote, for performance reasons we do association on the server
            # rather than through the local controller.
            data_for_server['_hash'] = record.hash_digest()
            new_remote_record = destination.insert(data_for_server, table_name=record.name, propagate=True)
        else:
            new_remote_record = destination.create(data_for_server)
        LOGGER.debug("Inserted new record in %s as %s." % (destination.name, new_remote_record.eid))
        return new_remote_record.eid, False

    @staticmethod
    def import_records(data):
        """Import data records.
        
        TODO: Docs
        """
        
    @classmethod
    def export_records(cls, keys=None, eids=None):
        """Export data records.
        
        Constructs a dictionary containing records matching `keys` or `eids` and all their
        associated records.  Association fields (`model` and `collection`) are **not** updated
        and may contain eids of undefined records. 

        Args:
            keys (dict): Attributes to match.
            eids (list): Record identifiers to match.

        Returns:
            dict: Dictionary of tables containing records.
            
        Example:
        ::
            
            {
             'Brewery': {100: {'address': '4615 Hollins Ferry Rd, Halethorpe, MD 21227',
                               'brews': [10, 12, 14]}},
             'Beer': {10: {'origin': 100, 'color': 'gold', 'ibu': 45},
                      12: {'origin': 100, 'color': 'dark', 'ibu': 15},
                      14: {'origin': 100, 'color': 'pale', 'ibu': 30}}
            }
        
            Beer.export_records(eids=[10])
            
            {
             'Brewery': {100: {'address': '4615 Hollins Ferry Rd, Halethorpe, MD 21227',
                               'brews': [10, 12, 14]}},
             'Beer': {10: {'origin': 100, 'color': 'gold', 'ibu': 45}}
            }

        """
        def export_record(record, root):
            if isinstance(record, cls) and record is not root:
                return
            data = all_data.setdefault(record.model_name, {})
            if record.eid not in data:
                data[record.eid] = record.data
                for attr, foreign in record.associations.iteritems():
                    for foreign_record in foreign[0].search(eids=record[attr]):
                        export_record(foreign_record, root)
        all_data = {}
        for record in cls.search(keys, eids):
            export_record(record, record)
        return all_data
          
    def _associate(self, record, foreign_model, affected, via):
        """Associates a record with another record.
        
        Args:
            record (Record): Record to associate.
            foreign_model (Model): Foreign record's data model.
            affected (list): Identifiers for the records that will be updated to associate with `record`.
            via (str): The name of the associated foreign attribute.
        """ 
        LOGGER.debug("Adding %s to '%s' in %s(eids=%s)", record.eid, via, foreign_model.name, affected)
        if not isinstance(affected, list):
            affected = [affected]
        with self.storage as database:
            for key in affected:
                foreign_record = database.get(key, table_name=foreign_model.name)
                if not foreign_record:
                    raise ModelError(foreign_model, "No record with ID '%s'" % key)
                if 'model' in foreign_model.attributes[via]:
                    updated = record.eid
                elif 'collection' in foreign_model.attributes[via]:
                    updated = list(set(foreign_record[via] + [record.eid]))
                else:
                    raise InternalError("%s.%s has neither 'model' nor 'collection'" % (foreign_model.name, via))
                foreign_model.controller(database).update({via: updated}, key)

    def _disassociate(self, record, foreign_model, affected, via):
        """Disassociates a record from another record.
        
        Args:
            record (Record): Record to disassociate.
            foreign_model (Model): Foreign record's data model.
            affected (list): Identifiers for the records that will be updated to disassociate from `record`.
            via (str): The name of the associated foreign attribute.
        """ 
        LOGGER.debug("Removing %s from '%s' in %s(eids=%s)", record.eid, via, foreign_model.name, affected)
        if not isinstance(affected, list):
            affected = [affected]
        foreign_props = foreign_model.attributes[via]
        if 'model' in foreign_props:
            if 'required' in foreign_props:
                LOGGER.debug("Empty required attr '%s': deleting %s(keys=%s)", via, foreign_model.name, affected)
                foreign_model.controller(self.storage).delete(affected)
            else:
                with self.storage as database:
                    database.unset([via], affected, table_name=foreign_model.name)
        elif 'collection' in foreign_props:
            with self.storage as database:
                for key in affected:
                    foreign_record = database.get(key, table_name=foreign_model.name)
                    updated = list(set(foreign_record[via]) - set([record.eid]))
                    if 'required' in foreign_props and len(updated) == 0:
                        LOGGER.debug("Empty required attr '%s': deleting %s(key=%s)", via, foreign_model.name, key)
                        foreign_model.controller(database).delete(key)
                    else:
                        database.update({via: updated}, key, table_name=foreign_model.name)

    @property
    def name(self):
        return self.storage.name

    def is_remote(self):
        return self.storage.is_remote()
