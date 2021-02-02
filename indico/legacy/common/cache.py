# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import datetime
import hashlib
import pickle

import redis
from flask import current_app, g

from indico.core.config import config
from indico.core.logger import Logger
from indico.util.string import truncate


# To cache `None` we need to actually store something else since memcached
# does not distinguish between a None value and a cache miss...
class _NoneValue:
    @classmethod
    def replace(cls, value):
        """Replace `None` with a `_NoneValue`."""
        return cls() if value is None else value

    @classmethod
    def restore(cls, value):
        """Replace `_NoneValue` with `None`."""
        return None if isinstance(value, cls) else value


class CacheClient:
    """
    This is an abstract class. A cache client provide a simple API to
    get/set/delete cache entries.

    Implementation must provide the following methods:
    - set(self, key, val, ttl)
    - get(self, key)
    - delete(self, key)

    The unit for the ttl arguments is a second.
    """

    def set_multi(self, mapping, ttl=0):
        for key, val in mapping.items():
            self.set(key, val, ttl)

    def get_multi(self, keys):
        values = {}
        for key in keys:
            val = self.get(key)
            if val is not None:
                values[key] = val
        return values

    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)

    def set(self, key, val, ttl=0):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError


class NullCacheClient(CacheClient):
    """Do nothing."""

    def set(self, key, val, ttl=0):
        pass

    def get(self, key):
        return None

    def delete(self, key):
        pass


class RedisCacheClient(CacheClient):
    """Redis-based cache client with a simple API."""

    key_prefix = 'cache/gen/'

    def __init__(self, url):
        self._client = redis.StrictRedis.from_url(url)
        self._client.connection_pool.connection_kwargs['socket_timeout'] = 1

    def _unpickle(self, val):
        if val is None:
            return None
        return pickle.loads(val)

    def hash_key(self, key):
        # Redis keys are even binary-safe, no need to hash anything
        return key

    def set_multi(self, mapping, ttl=0):
        try:
            self._client.mset({k: pickle.dumps(v) for k, v in mapping.items()})
            if ttl:
                for key in mapping:
                    self._client.expire(key, ttl)
        except redis.RedisError:
            Logger.get('cache.redis').exception('set_multi(%r, %r) failed', mapping, ttl)

    def get_multi(self, keys):
        try:
            return dict(zip(keys, map(self._unpickle, self._client.mget(keys))))
        except redis.RedisError:
            Logger.get('cache.redis').exception('get_multi(%r) failed', keys)

    def delete_multi(self, keys):
        try:
            self._client.delete(*keys)
        except redis.RedisError:
            Logger.get('cache.redis').exception('delete_multi(%r) failed', keys)

    def set(self, key, val, ttl=0):
        try:
            if ttl:
                self._client.setex(key, ttl, pickle.dumps(val))
            else:
                self._client.set(key, pickle.dumps(val))
        except redis.RedisError:
            val_repr = truncate(repr(val), 1000)
            Logger.get('cache.redis').exception('set(%r, %s, %r) failed', key, val_repr, ttl)

    def get(self, key):
        try:
            return self._unpickle(self._client.get(key))
        except redis.RedisError:
            Logger.get('cache.redis').exception('get(%r) failed', key)

    def delete(self, key):
        try:
            self._client.delete(key)
        except redis.RedisError:
            Logger.get('cache.redis').exception('delete(%r) failed', key)


class GenericCache:
    """A simple cache interface that supports various backends.

    The backends are accessed through the CacheClient interface.
    """

    def __init__(self, namespace):
        self._client = None
        self._namespace = namespace

    def __repr__(self):
        return 'GenericCache(%r)' % self._namespace

    def _connect(self):
        """Connect to the CacheClient.

        This method must be called before accessing ``self._client``.
        """
        # Maybe we already have a client in this instance
        if self._client is not None:
            return
        # If not, we might have one from another instance
        self._client = g.get('generic_cache_client', None)

        if self._client is not None:
            return

        # If not, create a new one
        if not current_app.config['TESTING']:
            self._client = RedisCacheClient(config.REDIS_CACHE_URL)
        else:
            self._client = NullCacheClient()

        g.generic_cache_client = self._client

    def _hashKey(self, key):
        if hasattr(self._client, 'hash_key'):
            return self._client.hash_key(key)
        return hashlib.sha256(key.encode()).hexdigest()

    def _makeKey(self, key):
        if not isinstance(key, str):
            # In case we get something not a string (number, list, whatever)
            key = repr(key)
        # Hashlib doesn't allow unicode so let's ensure it's not!
        return '{}{}.{}'.format(getattr(self._client, 'key_prefix', ''), self._namespace, self._hashKey(key))

    def _processTime(self, ts):
        if isinstance(ts, datetime.timedelta):
            ts = ts.seconds + (ts.days * 24 * 3600)
        return ts

    def set(self, key, val, time=0):
        """Set key to val with optional validity time.

        :param key: the key of the cache entry
        :param val: any python object that can be pickled
        :param time: number of seconds or a datetime.timedelta
        """
        self._connect()
        time = self._processTime(time)
        Logger.get('cache.generic').debug('SET %s %r (%d)', self._namespace, key, time)
        self._client.set(self._makeKey(key), _NoneValue.replace(val), time)

    def set_multi(self, mapping, time=0):
        self._connect()
        time = self._processTime(time)
        mapping = {self._makeKey(key): _NoneValue.replace(val) for key, val in mapping.items()}
        self._client.set_multi(mapping, time)

    def get(self, key, default=None):
        self._connect()
        res = self._client.get(self._makeKey(key))
        Logger.get('cache.generic').debug('GET %s %r (%s)', self._namespace, key, 'HIT' if res is not None else 'MISS')
        if res is None:
            return default
        return _NoneValue.restore(res)

    def get_multi(self, keys, default=None, asdict=True):
        self._connect()
        real_keys = list(map(self._makeKey, keys))
        data = self._client.get_multi(real_keys)
        # Add missing keys
        for real_key in real_keys:
            if real_key not in data:
                data[real_key] = default
        # Get data in the same order as our keys
        sorted_data = (default if data[rk] is None else _NoneValue.restore(data[rk]) for rk in real_keys)
        if asdict:
            return dict(zip(keys, sorted_data))
        else:
            return list(sorted_data)

    def delete(self, key):
        self._connect()
        Logger.get('cache.generic').debug('DEL %s %r', self._namespace, key)
        self._client.delete(self._makeKey(key))

    def delete_multi(self, keys):
        self._connect()
        keys = list(map(self._makeKey, keys))
        self._client.delete_multi(keys)
