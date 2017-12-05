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
import os
from durable.lang import ruleset, when_start
import werkzeug.routing
from subprocess import Popen, PIPE
from werkzeug.wrappers import Response

import six
from taucmdr import CONDA_HOME


class _RuleClassifierApplication(durable.interface.Application):
    """Rule based classifier server derived from Durable Rules"""

    _backend_process = None
    _backend_count = 0

    def __init__(self, host, host_name, port, routing_rules=None, run=None):
        super(_RuleClassifierApplication, self).__init__(host, host_name, port, routing_rules, run)
        # Durable Rules runs forever, which isn't usually what we want, so we add the ability to shut it down through
        # a special endpoint.
        self._url_map.add(werkzeug.routing.Rule('/shutdown', endpoint=self._shutdown_request))

    def stop(self):
        """Stop the rules engine."""
        # When stopping the rules engine, we need to prevent existing periodic timers from attempting
        # to contact the no-longer-running backend.
        if self._host._d_timer: # pylint: disable=protected-access
            self._host._d_timer.cancel() # pylint: disable=protected-access
        if self._host._t_timer: # pylint: disable=protected-access
            self._host._t_timer.cancel() # pylint: disable=protected-access
        self.stop_backend()

    @classmethod
    def run_backend(cls):
        """Run the rules engine backend as a subprocess, if not already running."""
        cls._backend_count = cls._backend_count + 1
        if cls._backend_process is None:
            backend_path = os.path.join(CONDA_HOME, 'redis-server')
            cls._backend_process = Popen([backend_path, '--save', '""', '--appendonly', 'no'], stdout=PIPE, stderr=PIPE)
            while True:
                line = cls._backend_process.stdout.readline()
                if not line:
                    break
                if 'Ready to accept connections' in line:
                    break
        return cls._backend_process

    @classmethod
    def stop_backend(cls):
        """Terminate the rules engine subprocess, if it is running."""
        if cls._backend_count > 0:
            cls._backend_count = cls._backend_count - 1
        if cls._backend_count == 0:
            cls._backend_process.terminate()
            cls._backend_process.wait()
            cls._backend_process = None

    @staticmethod
    def _shutdown_request(environ, start_response):
        func = environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('No shutdown function found')
        func()
        response = Response('Shutting down...', mimetype='plain/text')
        return response(environ, start_response)

    @classmethod
    def run_classifier_host(cls, databases=None, state_cache_size=1024):
        cls.run_backend()
        main_host = durable.lang.create_host(databases, state_cache_size)
        return main_host

    @classmethod
    def get_classifier_app(cls, databases=None, host_name='127.0.0.1', port=5000, routing_rules=None,
                           run=None, state_cache_size=1024):
        main_host = cls.run_classifier_host(databases, state_cache_size)
        main_app = _RuleClassifierApplication(main_host, host_name, port, routing_rules, run)
        return main_app


class FactAsserter(six.with_metaclass(ABCMeta, object)):
    """Instances of this class assert facts about models into a ruleset.

    Attributes:
        name (str): A name for this asserter to be displayed to the user.
        description (str): A description of the type of facts asserted by this object, to be displayed to the user.
        """

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    @abstractmethod
    def assert_facts(self, models, ruleset, host):
        """Process the models specified in `models`, extracting facts and posting assertions into the
        ruleset associated with this asserter instance.

        args:
            models (list of :obj:`model`): tam objects to be processed.
            ruleset (str): the name of the ruleset into which this asserter posts.
            host (:obj:`durable.lang.host`): the durable rules host into which this asserter posts.
        """


class RuleAsserter(six.with_metaclass(ABCMeta, object)):
    """Instances of this class assert rules into a ruleset.

    Attributes:
        name (str): A name for this asserter to be displayed to the user.
        description (str): A description of the type of facts asserted by this object, to be displayed to the user.
        ruleset (str): The name of the ruleset into which this asserter posts.
    """

    def __init__(self, name, description=None):
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
        models (list of :obj:`Model`): The models from which facts will be derived
    """

    def __init__(self, name, ruleset, models, fact_asserters=None, rule_asserters=None, description=None):
        self.name = name
        self.description = description
        self.ruleset = ruleset
        self.models = []
        if models:
            self.models.extend(models)
        self.fact_asserters = []
        if fact_asserters:
            self.append_fact_asserters(fact_asserters)
        self.rule_asserters = []
        if rule_asserters:
            self.rule_asserters.extend(fact_asserters)
        self._app = None

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
        """Run the ruleset defined by this classifier."""
        current_ruleset = ruleset(self.ruleset)
        for rule_asserter in self.rule_asserters:
            rule_asserter.assert_rules(self.ruleset)
        with current_ruleset:
            @when_start
            def on_start(host):
                for fact_asserter in self.fact_asserters:
                    fact_asserter.assert_facts(self.models, host, self.ruleset)
        self._app = _RuleClassifierApplication.get_classifier_app()

    def stop(self):
        """Stop running the ruleset defined by this classifier"""
        if self._app:
            self._app.stop()
