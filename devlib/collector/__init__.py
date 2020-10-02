#    Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging

from devlib.utils.types import caseless_string


class CollectorBase(object):

    def __init__(self, target):
        self.target = target
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_path = None

    def reset(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def set_output(self, output_path):
        self.output_path = output_path

    def get_data(self):
        return CollectorOutput()

    def __enter__(self):
        self.reset()
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


class CollectorOutputEntry(object):

    kinds = ['file', 'directory', 'metric']

    @property
    def path(self):
        if self.kind in ['file', 'directory']:
            return self.value
        return None

    def __init__(self, value, path_kind):
        self.value = value

        kind = caseless_string(kind)
        if kind not in self.kinds:
            msg = '{} is not a valid kind [{}]'
            raise ValueError(msg.format(kind, ' '.join(self.kinds)))
        self.kind = kind

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<{} ({})>'.format(self.value, self.kind)

    def __fspath__(self):
        """Allow using with os.path operations"""
        return self.path


class CollectorOutput(list):
    pass
