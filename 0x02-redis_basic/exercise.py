#!/usr/bin/env python3
""" Introduction to the basics of redis """


import redis
from typing import Any, Union, Callable
import uuid
from functools import wraps


def replay(method):
    """get the history"""
    outputs = method.__qualname__ + ':outputs'
    keys = method.__self__._redis.lrange(outputs, 0, -1)
    print('{} was called {} times:'.format(method.__qualname__, len(keys)))
    for key in keys:
        actual_key = key.decode('utf-8')
        val = method.__self__.get(
            actual_key, lambda x: x.decode('utf-8'))
        print("{}(*('{}',)) -> {}".format(
            method.__qualname__, val, actual_key))


def count_calls(method: Callable) -> Callable:
    """function that counts calls to Cache"""
    @wraps(method)
    def wrapper(*args, **kwargs):
        """the wrapper class"""
        args[0]._redis.incr(method.__qualname__)
        return method(*args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """logs the history of original function"""
    @wraps(method)
    def wrapper(*args, **kwargs):
        """the wrapper class"""
        method_name_in = method.__qualname__ + ':inputs'
        method_name_out = method.__qualname__ + ':outputs'
        redis = args[0]._redis
        redis.rpush(method_name_in, str((args[1],)))
        result = method(*args, **kwargs)
        args[0]._redis.rpush(method_name_out, result)
        return result
    return wrapper


class Cache:
    """a cache interaction with redis"""
    def __init__(self) -> None:
        """ constructor method"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, float, bytes]) -> str:
        """store redis db"""
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return(key)

    def get(self, key: str, fn: Callable = None) -> Any:
        """convert a value"""
        val = self._redis.get(key)
        if fn is None:
            return(val)
        val = fn(val)
        return val

    def get_str(self) -> Callable:
        """return a string"""
        return lambda x: str(x)

    def get_int(self) -> Callable:
        """return a int"""
        return lambda x: int(x)
