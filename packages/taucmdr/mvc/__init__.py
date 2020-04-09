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
"""TODO: FIXME: Docs

TAU Commander core software architecture.

TAU Commander follows the `Model-View-Controller (MVC)`_ architectural pattern.
Packages in :py:mod:`taucmdr.model` define models and controllers.  The `model` module
declares the model attributes as a dictionary named `ATTRIBUTES` in the form::

    <attribute>: {
        property: value,
        [[property: value], ...]
    }

Attribute properties can be anything you wish, including these special properties:

* ``type`` (str): The attribute is of the specified type.
* ``required`` (bool): The attribute must be specified in the data record.
* ``model`` (str): The attribute associates this model with another data model.
* ``collection`` (str): The attribute associates this model with another data model.
* ``via`` (str): The attribute associates with another model "via" the specified attribute.

The `controller` module declares the controller as a subclass of :any:`Controller`.  Controller
class objects are not bound to any particular data record and so can be used to create, update,
and delete records.  Controller class instances **are** bound to a single data record.

Models may have **associations** and **references**.  An association creates a relationship between
an attribute of this model and an attribute of another (a.k.a foreign) model.  If the associated
attribute changes then the foreign model will update its associated attribute.  A reference indicates
that this model is being referened by one or more attributes of a foreign model.  If a record of the
referenced model changes then the referencing model, i.e. the foreign model, will update all referencing
attributes.

Associations, references, and attributes are constructed when :py:mod:`taucmdr.model`  is imported.

Examples:

    *One-sided relationship*
    ::

        class Pet(Controller):
            attributes = {'name': {'type': 'string'}, 'hungry': {'type': 'bool'}}

        class Person(Controller):
            attributes = {'name': {'type': 'string'}, 'pet': {'model': 'Pet'}}

    We've related a Person to a Pet but not a Pet to a Person.  That is, we can query a Person
    to get information about their Pet, but we can't query a Pet to get information about their Person.
    If a Pet record changes then the Person record that referenced the Pet record is notified of the
    change. If a Person record changes then nothing happens to Pet.  The Pet and Person classes codify
    this relationship as:

        * Pet.references = set( (Person, 'pet') )
        * Pet.associations = {}
        * Person.references = set()
        * Person.associations = {}

    Some example data for this model::

        {
         'Pet': {1: {'name': 'Fluffy', 'hungry': True}},
         'Person': {0: {'name': 'Bob', 'pet': 1}}
        }

    *One-to-one relationship*
    ::

        class Husband(Controller):
            attributes = {'name': {'type': 'string'}, 'wife': {'model': 'Wife'}}

        class Wife(Controller):
            attributes = {'name': {'type': 'string'}, 'husband': {'model': 'Husband'}}

    We've related a Husband to a Wife.  The Husband may have only one Wife and the Wife may have
    only one Husband.  We can query a Husband to get information about their Wife and we can query a
    Wife to get information about their Husband.  If a Husband/Wife record changes then the Wife/Husband
    record that referenced the Husband/Wife record is notified of the change.  The Husband and Wife classes
    codify this relationship as:

        * Husband.references = set( (Wife, 'husband') )
        * Husband.associations = {}
        * Wife.references = set( (Husband, 'wife') )
        * Wife.associations = {}

    Example data::

        {
         'Husband': {2: {'name': 'Filbert', 'wife': 1}},
         'Wife': {1: {'name': 'Matilda', 'husband': 2}}
        }

    *One-to-many relationship*
    ::

        class Brewery(Controller):
            attributes = {'address': {'type': 'string'},
                          'brews': {'collection': 'Beer',
                                    'via': 'origin'}}

        class Beer(Controller):
            attributes = {'origin': {'model': 'Brewery'},
                          'color': {'type': 'string'},
                          'ibu': {'type': 'int'}}

    We've related one Brewery to many Beers.  A Beer has only one Brewery but a Brewery has zero or
    more Beers.  The `brews` attribute has a `via` property along with a `collection` property to specify
    which attribute of Beer relates Beer to Brewery, i.e. you may want a model to have multiple
    one-to-many relationship with another model.  The Brewery and Beer classes codify this relationship as:

        * Brewery.references = set()
        * Brewery.associations = {'brews': (Beer, 'origin')}
        * Beer.references = set()
        * Beer.associations = {'origin': (Brewery, 'brews')}

    Example data::

        {
         'Brewery': {100: {'address': '4615 Hollins Ferry Rd, Halethorpe, MD 21227',
                           'brews': [10, 12, 14]}},
         'Beer': {10: {'origin': 100, 'color': 'gold', 'ibu': 45},
                  12: {'origin': 100, 'color': 'dark', 'ibu': 15},
                  14: {'origin': 100, 'color': 'pale', 'ibu': 30}}
        }

    *Many-to-many relationship*
    ::

        class Actor(Controller):
            attributes = {'home_town': {'type': 'string'},
                          'appears_in': {'collection': 'Movie',
                                         'via': 'cast'}}

        class Movie(Controller):
            attributes = {'title': {'type': 'string'},
                          'cast': {'collection': 'Actor',
                                   'via': 'appears_in'}}

    An Actor may appear in many Movies and a Movie may have many Actors.  Changing the `cast` of a Movie
    notifies Actor and changing the movies an Actor `apppears_in` notifies Movie.  This relationship is
    codified as:

        * Actor.references = set()
        * Actor.associations = {'appears_in': (Movies, 'cast')}
        * Movie.references = set()
        * Movie.associations = {'cast': (Actor, 'appears_in')}

.. _Model-View-Controller (MVC): https://en.wikipedia.org/wiki/Model-view-controller
"""
