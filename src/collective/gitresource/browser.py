# -*- coding: utf-8 -*-
import os
import json
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
import datetime
from zope.cachedescriptors import property

from plone.resourceeditor.browser import FileManager as FileManagerBase
from zope.i18n import translate


class FileManager(FileManagerBase):
    """Render the file manager and support its AJAX requests.
    """

    # noinspection PyProtectedMember
    @property.Lazy
    def resourceType(self):
        return self.context._type

    # Methods that are their own views
    def getFile(self, path):
        self.setup()

        path = self.normalizePath(path.encode('utf-8'))
        file_ = self.context[path]
        ext = os.path.splitext(file_.__name__)[1][1:].lower()
        result = {'ext': ext}

        if ext not in self.imageExtensions:
            result['contents'] = str(file_.bytes.read())
        else:
            info = self.getInfo(path)
            info['properties']['dateModified'] = \
                datetime.datetime.fromtimestamp(file_.bytes.last_modified)
            info['properties']['dateCreated'] = \
                datetime.datetime.fromtimestamp(file_.bytes.last_modified)
            size = len(file_.bytes) / 1024
            if size < 1024:
                size_specifier = u'kb'
            else:
                size_specifier = u'mb'
                size /= 1024
            info['properties']['size'] = '%i%s' % (
                size,
                translate(u'filemanager_%s' % size_specifier, domain='plone',
                          default=size_specifier, context=self.request)
            )
            result['info'] = self.previewTemplate(info=info)

        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(result)
