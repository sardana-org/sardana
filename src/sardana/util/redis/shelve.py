# -*- coding: utf-8 -*-

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""Shelf object for the Redis backend"""

from shelve import Shelf as _Shelf


class Shelf(_Shelf):
    def __init__(self, redis, key_prefix=None, separator=':',
                 protocol=None, writeback=False):
        self._prefix = '{}{}'.format(
            key_prefix, separator) if key_prefix else ''
        _Shelf.__init__(
            self, dict=redis, protocol=protocol, writeback=writeback)

    def _prefix_key(self, key):
        if not self._prefix:
            return key
        if key.startswith('{}'.format(self._prefix)):
            # with writeback, shelf values are added by keys from cache.keys(),
            # but the cache keys are already prefixed.
            return key
        return "{prefix}{key}".format(prefix=self._prefix, key=key)

    def _remove_key_prefix(self, prefixed_key):
        return prefixed_key[len(self._prefix):]

    def __setitem__(self, key, value):
        return _Shelf.__setitem__(self, self._prefix_key(key), value)

    def __getitem__(self, key):
        return _Shelf.__getitem__(self, self._prefix_key(key))

    def __delitem__(self, key):
        return _Shelf.__delitem__(self, self._prefix_key(key))

    def get(self, key, default=None):
        # Redis supports __getitem__ for getting values from redis
        # like redis['somevalue']. But redis.get actually gets things from
        # cache, breaking the dict-like behaviour.
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self):
        return len(self._redis_keys())

    def _redis_keys(self):
        # self.dict is actually redis.
        return self.dict.keys(pattern='{}*'.format(self._prefix))

    def __iter__(self):
        for key in self._redis_keys():
            yield self._remove_key_prefix(key.decode())

    def __contains__(self, key):
        return self.dict.exists(self._prefix_key(key))


def open(redis, key_prefix=None, separator=':',
         protocol=None, writeback=False):
    if isinstance(redis, str):
        from redis import from_url
        redis = from_url(redis)
    return Shelf(redis, key_prefix, separator=separator,
                 protocol=protocol, writeback=writeback)
