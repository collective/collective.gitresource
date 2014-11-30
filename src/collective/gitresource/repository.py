# -*- coding: utf-8 -*-
import os
from dulwich.client import get_transport_and_path
from dulwich.repo import MemoryRepo
from zope.interface import implementer
from collective.gitresource.directory import logger
from collective.gitresource.interfaces import IHead
from collective.gitresource.interfaces import IRepository
from collective.gitresource.interfaces import IRepositoryManager
from collective.gitresource.iterator import BytesIterator


@implementer(IHead)
class Head(dict):

    def __init__(self, repo, head):
        self._repo = repo
        self._head = head

        index = {}
        tree = repo.object_store[head].tree
        for entry in self._repo.object_store.iter_tree_contents(tree):
            path, sha = entry.path, entry.sha
            index[path] = sha
            while os.path.dirname(path):
                path = os.path.dirname(path)
                index[path] = None
        super(Head, self).__init__(index)

    def __repr__(self):
        return '<{0:s} object at {1:s} of {2:s}>'.format(
            self.__class__.__name__,
            self.branch,
            repr(self._repo)[1:-1]
        )

    # noinspection PyProtectedMember
    def __getitem__(self, path):
        sha = super(Head, self).__getitem__(path)
        if sha is not None:
            blob = self._repo.object_store[sha]
            last_modified = self._repo.object_store[self._head]._commit_time
            return BytesIterator(blob.as_raw_string(), last_modified)
        else:
            return None



@implementer(IRepository)
class Repository(dict):
    def __init__(self, uri):
        self._client, self._host_path = get_transport_and_path(uri)
        self._repo = MemoryRepo()

        # Do initial fetch
        # TODO: Should be more lazy (currently fetches the whole repo)
        refs = self._client.fetch(
            self._host_path, self._repo,
            determine_wants=self._repo.object_store.determine_wants_all,
            progress=logger.info
        )

        # Init branches
        branches = dict([
            (name.split('/')[-1], Head(self._repo, ref))
            for name, ref in refs.items()
            if name.startswith('refs/head')
        ])

        # Finish init
        super(Repository, self).__init__(branches)

    def __repr__(self):
        return '<{0:s} object at {1:s}>'.format(self.__class__.__name__,
                                                self._host_path)


@implementer(IRepositoryManager)
class RepositoryManager(dict):

    def __getitem__(self, uri):
        if uri not in self:
            self[uri] = Repository(uri)
        return super(RepositoryManager, self).__getitem__(uri)
