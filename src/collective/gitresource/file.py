# -*- coding: utf-8 -*-
import os
import os.path
import mimetypes
from email.utils import formatdate

from zope.component import adapter
from zope.interface import implementer
from zope.location import ILocation


@implementer(ILocation)
class File(object):
    """Representation of a file. When called, it will set response headers
    and return the file's contents
    """

    def __init__(self, parent, request, name, iterator, length, modified):
        self.request = request
        self.__name__ = name
        self.__parent__ = parent

        self.lastModifiedTimestamp = modified
        self.iterator = iterator
        self.length = length

    def getContentType(self, default='application/octet-stream'):
        extension = os.path.splitext(self.__name__)[1].lower()
        return getattr(mimetypes, 'types_map', {}).get(extension, default)

    def __call__(self, REQUEST=None, RESPONSE=None):
        if REQUEST is not None:
            request = REQUEST
        else:
            request = self.request

        if RESPONSE is not None:
            response = RESPONSE
        else:
            response = request.response

        contentType = self.getContentType()
        lastModifiedHeader = formatdate(
            self.lastModifiedTimestamp, usegmt=True)

        response.setHeader('Content-Type', contentType)
        response.setHeader('Content-Length', self.length)
        response.setHeader('Last-Modified', lastModifiedHeader)

        return self.iterator


@adapter(File)
def rawReadFile(context):
    return context.iterator.read()
