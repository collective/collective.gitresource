# -*- coding: utf-8 -*-
import logging
import zipfile

from zExceptions import NotFound
from plone.resource.interfaces import IResourceDirectory
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.location import ILocation

from collective.gitresource.file import File
from collective.gitresource.interfaces import IRepositoryManager


logger = logging.getLogger('collective.gitresource')


@implementer(ILocation)
@implementer(IResourceDirectory)
class ResourceDirectory(object):
    """A resource directory based on files in the filesystem.
    """

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, uri, branch, directory, name, parent=None):
        self.__name__ = name
        self.__parent = parent

        self._uri = uri
        self._branch = branch

        self.directory = directory.strip('/')
        self.repository = getUtility(IRepositoryManager)[uri][branch]

    @property
    def __parent__(self):
        if self.__parent is None:
            return getSite()
        return self.__parent

    @__parent__.setter
    def __parent__(self, value):
        self.__parent = value

    def publishTraverse(self, request, name):
        path = '/'.join([self.directory, name])
        if self.isFile(name):
            return File(self, request, name, self.repository[path])
        elif self.isDirectory(name):
            return self.__class__(self._uri, self._branch, path,
                                  self.__name__, self)
        raise NotFound

    def __getitem__(self, name):
        return self.publishTraverse(None, name)

    def __repr__(self):
        return '<{0:s} object at {1:s} of {2:s}>'.format(
            self.__class__.__name__, self.directory,
            repr(self.repository)[1:-1]
        )

    def __contains__(self, name):
        path = '/'.join([self.directory, name])
        return path in self.repository

    def openFile(self, name):
        path = '/'.join([self.directory, name])
        return self.repository[path]

    def readFile(self, name):
        path = '/'.join([self.directory, name])
        return self.repository[path].read()

    def listDirectory(self):
        directory = self.directory + '/'
        for path in self.repository:
            if path.startswith(directory):
                if '/' not in path[len(directory):]:
                    yield path[len(directory):]

    def isDirectory(self, name):
        path = '/'.join([self.directory, name])
        return path in self.repository and self.repository[path] is None

    def isFile(self, name):
        path = '/'.join([self.directory, name])
        return path in self.repository and self.repository[path] is not None

    def exportZip(self, out):
        base = self.directory
        prefix = self.__name__
        zf = zipfile.ZipFile(out, 'w')

        def export(directory, output):
            for name in directory.listDirectory():
                if directory.isFile(name):
                    path = '/'.join([directory.directory, name]).strip('/')
                    output.writestr('/'.join([prefix, path[len(base):]]),
                                    directory.readFile(name))
                elif directory.isDirectory(name):
                    export(directory[name], output)

        export(self, zf)
        zf.close()

    # IWritableResourceDirectory

    def makeDirectory(self, path):
        """Create the given path as a directory. (Returns successfully without
        doing anything if the directory already exists.)
        """
        raise NotImplementedError()

    def writeFile(self, path, data):
        """Write a file at the specified path.

        Parent directories will be added if necessary. The final path component
        gives the filename. If the file already exists, it will be overwritten.

        ``data`` may be a string or file-like object.
        """
        raise NotImplementedError()

    def importZip(self, file):
        """Imports the contents of a zip file into this directory.

        ``file`` may be a filename, file-like object, or instance of
        zipfile.ZipFile. The file data must be a ZIP archive.
        """
        raise NotImplementedError()

    def __delitem__(self, name):
        """Delete a file or directory inside this directory
        """
        raise NotImplementedError()

    def __setitem__(self, name, item):
        """Add a file or directory as returned by ``__getitem__()``
        """
        raise NotImplementedError()

    def rename(self, oldName, newName):
        """Rename a child file or folder
        """
        raise NotImplementedError()
