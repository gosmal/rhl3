#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import json
import getpass
import time

from ansible.module_utils._text import to_bytes
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'gm_log'
    CALLBACK_NEEDS_WHITELIST = False
    seconds = 0

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.ansible_task = ""
        self.sys_argv = sys.argv
        self.user = getpass.getuser()

        if self.seconds == 0:
            self.seconds = time.time()

        log_dir = "/tmp"
        log_file = "gmlog-" + str(self.seconds) + ".json"

        self.path = os.path.join(log_dir, log_file)
        self.gmlog_fd = open(self.path, "ab")

    def log(self, host, category, data):
        if isinstance(data, MutableMapping):
            if '_ansible_verbose_override' in data:
                # avoid logging extraneous data
                data = 'omitted'
            else:
                data = data.copy()
                data = json.dumps(
                    dict(sys_argv=self.sys_argv,
                         task=self.ansible_task,
                         category=category,
                         host=host,
                         user=self.user,
                         data=data),
                    cls=AnsibleJSONEncoder)

        msg = to_bytes("%(data)s\n\n" % dict(data=data))

        if self.gmlog_fd.closed:
            self.gmlog_fd = open(self.path, "ab")

        self.gmlog_fd.write(msg)

    def runner_on_ok(self, host, res):
        self.log(host, "OK", res)

    def runner_on_skipped(self, host, item=None):
        self.log(host, "SKIPPED", "...")

    def runner_on_unreachable(self, host, res):
        self.log(host, "UNREACHABLE", res)

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.log(host, "FAILED", res)

    def runner_on_async_failed(self, host, res, jid):
        self.log(host, "ASYNC_FAILED", res)

    def playbook_on_import_for_host(self, host, imported_file):
        self.log(host, "IMPORTED", imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.log(host, "NOTIMPORTED", missing_file)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.ansible_task = task.get_name()
