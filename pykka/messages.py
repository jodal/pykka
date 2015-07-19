from __future__ import absolute_import

from collections import namedtuple

PykkaStop = object()
PykkaCall = namedtuple('PykkaCall', ['attr_path', 'args', 'kwargs'])
PykkaGetattr = namedtuple('PykkaGetattr', ['attr_path'])
PykkaSetattr = namedtuple('PykkaSetattr', ['attr_path', 'value'])
