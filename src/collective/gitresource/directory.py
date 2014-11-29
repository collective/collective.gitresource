# -*- coding: utf-8 -*-
import logging

from zExceptions import NotFound
from dulwich.client import get_transport_and_path
from dulwich.repo import MemoryRepo
from plone.resource.interfaces import IResourceDirectory
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.location import ILocation

from collective.gitresource.file import File
from collective.gitresource.iterator import BytesIterator

logger = logging.getLogger('collective.gitresource')


# TODO: GitRepository must be refactored implicitly into its own "named
# utility" to make it possible for multiple GitResourceDirectory to use the
# same GitRepository.


class GitRepository(object):

    def __init__(self, uri, fetch=True):
        self.client, self.host_path = get_transport_and_path(uri)
        self.repo = MemoryRepo()
        self.refs = {}
        self.index = {}

        if fetch:
            self.fetch()

    def fetch(self):
        # Fetch bare repository
        self.refs = self.client.fetch(
            self.host_path, self.repo,
            determine_wants=self.repo.object_store.determine_wants_all,
            progress=logger.info
        )

        # Set repository head
        self.repo['HEAD'] = self.refs['HEAD']

        # Create minimal index
        head = self.repo['HEAD'].tree
        for item in self.repo.object_store.iter_tree_contents(head):
            self.index[item.path] = item.sha

    def keys(self):
        return self.index.keys()

    def __iter__(self):
        for key in iter(self.index):
            yield key

    def __contains__(self, path):
        return path in self.index

    # noinspection PyProtectedMember
    def __getitem__(self, path):
        name = self.index[path]
        blob = self.repo.object_store[self.repo.object_store._to_hexsha(name)]
        length = blob.raw_length()
        last_commit = self.repo['HEAD']
        modified = last_commit._commit_time
        return BytesIterator(blob.as_raw_string()), length, modified

@implementer(ILocation)
@implementer(IResourceDirectory)
class GitResourceDirectory(object):
    """A resource directory based on files in the filesystem.
    """

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, uri, directory, name, parent=None, repo=None):
        self.__name__ = name
        self.__parent = parent

        self.directory = directory.strip('/')

        if repo is not None:
            self.repo = repo
        else:
            self.repo = GitRepository(uri)

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
            iterator, length, modified = self.repo[path]
            return File(self, request, name, iterator, length, modified)
        elif self.isDirectory(name):
            return self.__class__(None, path, self.__name__, self, self.repo)
        raise NotFound

    def __getitem__(self, name):
        return self.publishTraverse(None, name)

    def __repr__(self):
        sub_path = '/'.join([self.repo.host_path, self.directory])
        return '<%s object at %s>' % (self.__class__.__name__, sub_path)

    def __contains__(self, name):
        path = '/'.join([self.directory, name])
        return path in self.repo

    def openFile(self, path):
        path = '/'.join([self.directory, path])
        return self.repo[path][0]

    def readFile(self, path):
        path = '/'.join([self.directory, path])
        return self.repo[path][0].read()

    def listDirectory(self):
        directory = self.directory + '/'
        for path in self.repo:
            if str(path).startswith(directory):
                if '/' not in path[len(directory):]:
                    yield path[len(directory):]

    def isDirectory(self, name):
        directory = '/'.join([self.directory, name]) + '/'
        for path in self.repo:
            if str(path).startswith(directory):
                return True
        return False

    def isFile(self, path):
        path = '/'.join([self.directory, path])
        return path in self.repo

    def exportZip(self, out):
        raise NotImplementedError()

    # def exportZip(self, out):
    #     prefix = self.__name__
    #     zf = zipfile.ZipFile(out, 'w')
    #
    #     toStrip = len(self.directory.replace(os.path.sep, '/')) + 1
    #
    #     for (dirpath, dirnames, filenames) in os.walk(self.directory):
    #         subpath = dirpath.replace(os.path.sep, '/')[toStrip:].strip('/')
    #
    #         for filename in filenames:
    #             path = '/'.join([subpath, filename]).strip('/')
    #
    #             if any(any(filter.match(n) for filter in FILTERS)
    #                    for n in path.split('/')
    #             ):
    #                 continue
    #
    #             zf.writestr('/'.join([prefix, path,]), self.readFile(path))
    #
    #     zf.close()

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
