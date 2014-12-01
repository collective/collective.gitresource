# -*- coding: utf-8 -*-
import logging
import os
import datetime
import time

import dateutil
from dulwich.client import get_transport_and_path
from dulwich.index import cleanup_mode
from dulwich.index import commit_tree
from dulwich.objects import Blob
from dulwich.objects import Commit
from dulwich.repo import MemoryRepo
from zope.component.hooks import getSite
from zope.interface import implementer

from collective.gitresource.interfaces import IHead
from collective.gitresource.interfaces import IRepository
from collective.gitresource.interfaces import IRepositoryManager
from collective.gitresource.iterator import BytesIterator


logger = logging.getLogger('collective.gitresource')


@implementer(IHead)
class Head(dict):

    # noinspection PyProtectedMember,PyTypeChecker
    def __init__(self, repo, head, name='refs/heads/master'):
        self.__parent__ = repo
        self.__name__ = name

        self._repo = repo._repo
        self._head = head

        entries = {}
        tree = self._repo.object_store[head].tree
        for entry in self._repo.object_store.iter_tree_contents(tree):
            entries[entry.path] = entry.sha, entry.mode
        for path in set(filter(bool, map(os.path.dirname, entries))):
            entries.setdefault(path, (None, None))
            while os.path.dirname(path):
                path = os.path.dirname(path)
                entries.setdefault(path, (None, None))
        super(Head, self).__init__(entries)

    def __repr__(self):
        return '<{0:s} object at {1:s} of {2:s}>'.format(
            self.__class__.__name__,
            self.__name__,
            repr(self.__parent__)[1:-1]
        )

    # noinspection PyProtectedMember
    def __getitem__(self, path):
        sha, mode = super(Head, self).__getitem__(path)
        if sha is not None:
            blob = self._repo.object_store[sha]
            last_modified = self._repo.object_store[self._head]._commit_time
            return BytesIterator(blob.as_raw_string(), last_modified)
        else:
            return None

    # noinspection PyProtectedMember
    def __setitem__(self, path, raw):
        # XXX: I don't have much idea, what I'm doing here and I might
        # just corrupt your repository...

        # Mark directory as special (None, None) marker value
        if raw is None:
            super(Head, self).__setitem__(path, (None, None))
            return

        # Get old mode or use the default
        try:
            mode = super(Head, self).__getitem__(path)[1]
        except KeyError:
            mode = 0100644

        # Get existing entries for the content tree
        entries = [(key, sha_mode[0], cleanup_mode(sha_mode[1]))
                   for key, sha_mode in super(Head, self).iteritems()
                   if sha_mode[0] is not None and key is not path]

        # Get author
        # TODO: refactor to use plone.api or maybe use product_config
        from Products.CMFCore.utils import getToolByName
        portal_members = getToolByName(getSite(), 'portal_membership')
        member = portal_members.getAuthenticatedMember()
        author = '{0:s} <{1:s}>'.format(
            member.getProperty('fullname', '') or member.getId(),
            member.getProperty('email', '') or 'noreply@example.com'
        )

        # Get timezone
        tz_diff = dateutil.tz.tzlocal().utcoffset(datetime.datetime.now())

        # Create commit
        commit = Commit()
        commit.author = author
        commit.committer = commit.author
        commit.commit_time = int(time.time())
        commit.author_time = commit.commit_time
        commit.commit_timezone = tz_diff.seconds
        commit.author_timezone = tz_diff.seconds
        if tz_diff < datetime.timedelta(0):
            commit._author_timezone_neg_utc = True
            commit._commit_timezone_neg_utc = True
        commit.encoding = 'UTF-8'
        commit.message = 'Update {0:s}'.format(path)
        commit.parents = [self._head]

        # Create blob and commit tree
        blob = Blob.from_string(raw)
        entries.append((path, blob.id, cleanup_mode(mode)))
        commit.tree = commit_tree(self._repo.object_store, entries)

        # Save blob and commit
        self._repo.object_store.add_object(blob)
        self._repo.object_store.add_object(commit)

        def determine_wants(haves):
            # Set new head for the branch
            return {self.__name__: commit.id}

        # Push to remote
        self.__parent__._client.send_pack(
            self.__parent__._host_path,
            determine_wants,
            self._repo.object_store.generate_pack_contents,
            progress=logger.info
        )

        # Update "index"
        super(Head, self).__setitem__(path, (blob._sha, mode))


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
            (name.split('/')[-1], Head(self, ref, name))
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
