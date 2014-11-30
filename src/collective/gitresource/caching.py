# -*- coding: utf-8 -*-
import datetime

from dateutil.tz import tzlocal
from zope.component import adapter

from collective.gitresource.file import File


@adapter(File)
class FileLastModified(object):
    def __init__(self, context):
        self.context = context

    def __call__(self):
        return datetime.datetime.fromtimestamp(
            self.context.bytes_iterator.last_modified,
            tz=tzlocal()
        )
