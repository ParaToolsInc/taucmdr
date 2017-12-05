# -*- coding: utf-8 -*- #
# Copyright (c) 2017, ParaTools, Inc.
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

"""Rule-based classification"""

from abc import ABCMeta, abstractmethod

import durable.interface
import durable.lang
from durable.lang import ruleset, when_start
from werkzeug.wrappers import Response

import six


class _RuleClassifierApplication(durable.interface.Application):
    """Rule based classifier server derived from Durable Rules"""
    def __init__(self, host, host_name, port, routing_rules=None, run=None):
        super(_RuleClassifierApplication, self).__init__(host, host_name, port, routing_rules, run)

    # Durable Rules runs forever, which isn't usually what we want, so we add the ability to shut it down
    # by posting to the special ruleset name 'shutdown'
    @staticmethod
    def _shutdown_request(environ, start_response):
        func = environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('No shutdown function found')
        func()
        response = Response('Shutting down...', mimetype='plain/text')
        return response(environ, start_response)

    def _ruleset_definition_request(self, environ, start_response, ruleset_name):
        if ruleset_name == 'shutdown':
            return self._shutdown_request(environ, start_response)
        return super(_RuleClassifierApplication, self)._ruleset_definition_request(
            environ, start_response, ruleset_name)

    def _state_request(self, environ, start_response, ruleset_name, sid):
        if ruleset_name == 'shutdown':
            return self._shutdown_request(environ, start_response)
        return super(_RuleClassifierApplication, self)._state_request(
            environ, start_response, ruleset_name, sid)

    def _default_state_request(self, environ, start_response, ruleset_name):
        if ruleset_name == 'shutdown':
            return self._shutdown_request(environ, start_response)
        return super(_RuleClassifierApplication, self)._default_state_request(
            environ, start_response, ruleset_name)

    def _events_request(self, environ, start_response, ruleset_name, sid):
        if ruleset_name == 'shutdown':
            return self._shutdown_request(environ, start_response)
        return super(_RuleClassifierApplication, self)._events_request(
            environ, start_response, ruleset_name, sid)

    def _default_events_request(self, environ, start_response, ruleset_name):
        if ruleset_name == 'shutdown':
            return self._shutdown_request(environ, start_response)
        return super(_RuleClassifierApplication, self)._default_events_request(
            environ, start_response, ruleset_name)

    def _facts_request(self, environ, start_response, ruleset_name, sid):
        if ruleset_name == 'shutdown':
            return self._shutdown_request(environ, start_response)
        return super(_RuleClassifierApplication, self)._facts_request(
            environ, start_response, ruleset_name, sid)

    def _default_facts_request(self, environ, start_response, ruleset_name):
        if ruleset_name == 'shutdown':
            return self._shutdown_request(environ, start_response)
        return super(_RuleClassifierApplication, self)._default_facts_request(
            environ, start_response, ruleset_name)

    @staticmethod
    def run_all(databases=None, host_name='127.0.0.1', port=5000, routing_rules=None, run=None, state_cache_size=1024):
        main_host = durable.lang.create_host(databases, state_cache_size)
        main_app = _RuleClassifierApplication(main_host, host_name, port, routing_rules, run)
        main_app.run()


class FactAsserter(six.with_metaclass(ABCMeta, object)):
    """Instances of this class assert facts about models into a ruleset.

    Attributes:
        name (str): A name for this asserter to be displayed to the user.
        description (str): A description of the type of facts asserted by this object, to be displayed to the user.
        """
    def __init__(self, name, description = None):
        self.name = name
        self.description = description

    @abstractmethod
    def assert_facts(self, models, ruleset, host):
        """Process the models specified in `models`, extracting facts and posting assertions into the
        ruleset associated with this asserter instance.

        Args:
            models (list of :obj:`Model`): TAM objects to be processed.
            ruleset (str): The name of the ruleset into which this asserter posts.
            host (:obj:`durable.lang.host`): The Durable Rules host into which this asserter posts.
        """


class RuleAsserter(six.with_metaclass(ABCMeta, object)):
    """Instances of this class assert rules into a ruleset.

    Attributes:
        name (str): A name for this asserter to be displayed to the user.
        description (str): A description of the type of facts asserted by this object, to be displayed to the user.
        ruleset (str): The name of the ruleset into which this asserter posts.
    """
    def __init__(self, name, description = None):
        self.name = name
        self.description = description

    @abstractmethod
    def assert_rules(self, ruleset):
        """Assert rules into this asserter's ruleset.
        Args:
        ruleset (str): The name of the ruleset into which this asserter posts.
        """


class RuleBasedClassifier(object):
    """The RuleBasedClassifier asserts a set of rules specified by :obj:`RuleAsserter` instances
    and

    Attributes:
        name (str): A name for this asserter to be displayed to the user.
        description (str): A description of the type of facts asserted by this object, to be displayed to the user.
        ruleset (str): The name of the ruleset into which this asserter posts.
    """
    def __init__(self, name, ruleset, fact_asserters = None, rule_asserters = None, description = None):
        self.name = name
        self.description = description
        self.ruleset = ruleset
        self.fact_asserters = []
        if fact_asserters:
            self.append_fact_asserters(fact_asserters)
        self.rule_asserters = []
        if rule_asserters:
            self.rule_asserters.extend(fact_asserters)

    def append_fact_asserters(self, fact_asserters):
        """Add fact asserters to this classifier.

        Args:
            fact_asserters (list of :obj:`FactAsserter`): The fact asserters to add to the classifier.
        """
        if isinstance(fact_asserters, list):
            self.fact_asserters.extend(fact_asserters)
        else:
            self.fact_asserters.append(fact_asserters)

    def append_rule_asserters(self, rule_asserters):
        """Add rule asserters to this classifier.

        Args:
            rule_asserters (list of :obj:`RuleAsserter`): The rule asserters to add to the classifier.
        """
        if isinstance(rule_asserters, list):
            self.rule_asserters.extend(rule_asserters)
        else:
            self.rule_asserters.append(rule_asserters)

    def run(self):
        current_ruleset = ruleset(self.ruleset)
        for rule_asserter in self.rule_asserters:
            rule_asserter.assert_rules(self.ruleset)
        with current_ruleset:
            @when_start
            def on_start(host):
                for fact_asserter in self.fact_asserters:
                    fact_asserter.assert_facts(host, ruleset)
                host.post()
        _RuleClassifierApplication.run_all()
