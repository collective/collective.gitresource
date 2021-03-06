# -*- coding: utf-8 -*-
import zipfile

from zExceptions import NotFound
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.location import ILocation

from collective.gitresource.file import File
from collective.gitresource.git import GitView
from collective.gitresource.interfaces import IRepositoryManager
from collective.gitresource.interfaces import IGitRemoteResourceDirectory


@implementer(ILocation)
@implementer(IGitRemoteResourceDirectory)
class ResourceDirectory(object):
    """A resource directory based on files in the filesystem.
    """

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, uri, branch, directory,
                 resource_type, name, parent=None):
        self.__name__ = name
        self.__parent = parent

        self._type = resource_type
        self._uri = uri
        self._branch = branch

        self._directory = directory.strip('/')

    @property
    def repository(self):
        return getUtility(IRepositoryManager)[self._uri][self._branch]

    # XXX: No interface defines resource directory requiring self.context...
    @property
    def context(self):
        if self.__parent is None:
            return getSite()
        return self.__parent

    # XXX: Required to make work as resource registry rendering context
    # from Acquisition.interfaces.IAcquisitionWrapper
    @property
    def aq_explicit(self):
        return getSite().aq_explicit

    # XXX: Required to make work as resource registry rendering context
    # from OFS.interfaces.ITraversable
    def absolute_url(self):
        return getSite().absolute_url() + '/++{0:s}++{1:s}'.format(
            self._type, self.__name__)

    # XXX: Required to make work as resource registry rendering context
    # from Products.CMFCore.Skinnable.SkinnableObjectManager
    # noinspection PyMethodMayBeStatic
    @property
    def getCurrentSkinName(self):
        return getSite().getCurrentSkinName

    @property
    def __parent__(self):
        if self.__parent is None:
            return getSite()
        return self.__parent

    @__parent__.setter
    def __parent__(self, value):
        self.__parent = value

    def publishTraverse(self, request, name):
        # GIT
        environ = getattr(request, 'environ', {})
        content_type = environ.get('CONTENT_TYPE', '')
        if (request and content_type.startswith('application/x-git')
                or request and request.get('service', '').startswith('git-')):
            key = 'TraversalRequestNameStack'
            path = '/'.join([name] + list(request.get(key) or ())).strip('/')
            request[key] = []  # end of traversal
            return GitView(self, request, path)
        # Browser
        else:
            path = '/'.join([self._directory, name]).strip('/')
            if self.isFile(name):
                return File(self, request, name, self.repository[path])
            elif self.isDirectory(name):
                return self.__class__(self._uri, self._branch, path,
                                      self._type, self.__name__, self)
        raise NotFound

    def __getitem__(self, name):
        try:
            return self.publishTraverse(None, name)
        except NotFound:
            raise KeyError(name)

    def __repr__(self):
        return '<{0:s} object at {1:s} of {2:s}>'.format(
            self.__class__.__name__, self._directory or '/',
            repr(self.repository)[1:-1]
        )

    def __contains__(self, name):
        path = '/'.join([self._directory, name]).strip('/')
        return path in self.repository

    def openFile(self, name):
        path = '/'.join([self._directory, name]).strip('/')
        return self.repository[path]

    def readFile(self, name):
        path = '/'.join([self._directory, name]).strip('/')
        return self.repository[path].read()

    def listDirectory(self):
        directory = (self._directory + '/').lstrip('/')
        for path in self.repository:
            if path.startswith(directory):
                if '/' not in path[len(directory):]:
                    yield path[len(directory):]

    def isDirectory(self, name):
        path = '/'.join([self._directory, name]).strip('/')
        return path in self.repository and self.repository[path] is None

    def isFile(self, name):
        path = '/'.join([self._directory, name]).strip('/')
        return path in self.repository and self.repository[path] is not None

    def exportZip(self, out):
        base = (self._directory + '/').lstrip('/')
        prefix = self.__name__
        zf = zipfile.ZipFile(out, 'w')

        def export(directory, output):
            for name in directory.listDirectory():
                if directory.isFile(name):
                    # noinspection PyProtectedMember
                    path = '/'.join([directory._directory, name]).strip('/')
                    output.writestr('/'.join([prefix, path[len(base):]]),
                                    directory.readFile(name))
                elif directory.isDirectory(name):
                    export(directory[name], output)

        export(self, zf)
        zf.close()

    def makeDirectory(self, name):
        path = '/'.join([self._directory, name]).strip('/')
        self.repository[path] = None

    def writeFile(self, name, data):
        path = '/'.join([self._directory, name]).strip('/')
        try:
            self.repository[path] = data.read()
        except AttributeError:
            self.repository[path] = data

    def importZip(self, file_):
        # """Imports the contents of a zip file into this directory.
        #
        # ``file`` may be a filename, file-like object, or instance of
        # zipfile.ZipFile. The file data must be a ZIP archive.
        # """
        raise NotImplementedError()

    def __delitem__(self, name):
        # """Delete a file or directory inside this directory
        # """
        raise NotImplementedError()

    def __setitem__(self, name, item):
        # """Add a file or directory as returned by ``__getitem__()``
        # """
        raise NotImplementedError()

    def rename(self, oldName, newName):
        # """Rename a child file or folder
        # """
        raise NotImplementedError()
