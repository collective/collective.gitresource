# -*- coding: utf-8 -*-
import logging
import os
import datetime
import time

from App.config import getConfiguration
import dateutil
from dulwich.client import get_transport_and_path
from dulwich.client import HttpGitClient
from dulwich.objects import ZERO_SHA
from dulwich.config import ConfigFile
from dulwich.index import cleanup_mode
from dulwich.index import commit_tree
from dulwich.object_store import MemoryObjectStore
from dulwich.objects import Blob
from dulwich.objects import Commit
from dulwich.refs import DictRefsContainer
from dulwich.repo import MemoryRepo, BaseRepo
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implementer
import pkg_resources

from collective.gitresource.interfaces import IHead
from collective.gitresource.interfaces import IRepository
from collective.gitresource.interfaces import IRepositoryManager
from collective.gitresource.iterator import BytesIterator


try:
    pkg_resources.get_distribution('redis_collections')
except pkg_resources.DistributionNotFound:
    HAS_REDIS = False
else:
    import cPickle
    from redis import StrictRedis
    from redis_collections import Dict
    HAS_REDIS = True


logger = logging.getLogger('collective.gitresource')


class RedisObjectStore(MemoryObjectStore):
    def __init__(self, redis, prefix):
        super(RedisObjectStore, self).__init__()
        self._data = Dict(redis=redis, pickler=cPickle,
                          key='{0:s}:data'.format(prefix))


class RedisDictRefsContainer(DictRefsContainer):

    def __init__(self, redis, prefix):
        super(RedisDictRefsContainer, self).__init__(
            Dict(redis=redis, pickler=cPickle,
                 key='{0:s}:refs'.format(prefix))
        )
        self._peeled = Dict(redis=redis, pickler=cPickle,
                            key='{0:s}:peeled'.format(prefix))


# noinspection PyAbstractClass
class RedisRepo(MemoryRepo):

    def __init__(self, redis, prefix):
        BaseRepo.__init__(self,
                          RedisObjectStore(redis, prefix),
                          RedisDictRefsContainer(redis, prefix))
        self._named_files = Dict(redis=redis, pickler=cPickle,
                                 key='{0:s}:named_files'.format('prefix'))
        self._config = ConfigFile()
        self.bare = True


# noinspection PyTypeChecker
def get_index(head, repo):
    index = {}
    tree = repo.object_store[head].tree
    for entry in repo.object_store.iter_tree_contents(tree):
        index[entry.path] = entry.sha, entry.mode
    for path in set(filter(bool, map(os.path.dirname, index))):
        index.setdefault(path, (None, None))
        while os.path.dirname(path):
            path = os.path.dirname(path)
            index.setdefault(path, (None, None))
    return index


@implementer(IHead)
class Head(dict):

    # noinspection PyProtectedMember
    def __init__(self, repo, head, name='refs/heads/master'):
        self.__parent__ = repo
        self.__name__ = name

        self._repo = repo._repo
        self._head = head

        super(Head, self).__init__(get_index(self._head, self._repo))

    def __repr__(self):
        return '<{0:s} object at {1:s} of {2:s}>'.format(
            self.__class__.__name__,
            self.__name__,
            repr(self.__parent__)[1:-1]
        )

    # noinspection PyProtectedMember
    def __getitem__(self, path):
        # Re-build index when out of sync
        head = self._repo.refs[self.__name__]
        if self._head != head:
            self._head = head
            super(Head, self).__init__(get_index(self._head, self._repo))

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
        refs = self.__parent__._client.send_pack(
            self.__parent__._host_path,
            determine_wants,
            self._repo.object_store.generate_pack_contents,
            progress=logger.info
        )
        # Update heads
        for ref, sha in refs.items():
            if sha in self._repo.object_store:
                self._repo.refs[ref] = sha

        # Update "index"
        super(Head, self).__setitem__(path, (blob.id, mode))


@implementer(IRepository)
class Repository(dict):
    def __init__(self, uri):
        self._client, self._host_path = get_transport_and_path(uri)

        # Choose repo
        if HAS_REDIS and getUtility(IRepositoryManager).redis is not None:
            self._repo = RedisRepo(redis=getUtility(IRepositoryManager).redis,
                                   prefix=uri)
        else:
            self._repo = MemoryRepo()

        # Set HTTP Basic Authorization header when available and supported
        product_config = getattr(getConfiguration(), 'product_config', {})
        my_config = product_config.get('collective.gitresource', {})
        if uri in my_config and isinstance(self._client, HttpGitClient):
            self._client.opener.addheaders.append(
                'Authorization', 'Basic {0:s}'.format(
                    my_config[uri].encode('base64').strip()))

        def determine_wants(haves):
            wants = dict([(r, s) for (r, s) in haves.iteritems()
                          if not r.endswith("^{}")
                          and (r == 'HEAD' or r.startswith('refs/heads'))
                          and not s == ZERO_SHA])
            assert wants, 'No heads found. Cannot continue without any.'
            new_heads = [s for s in wants.values()
                         if s not in self._repo.object_store]
            # MemoRepo needs always at least one head to work
            return set(new_heads) or [wants.get('HEAD', wants.values()[0])]

        # Do initial fetch
        refs = self._client.fetch(
            self._host_path, self._repo,
            determine_wants=determine_wants,
            progress=logger.info
        )
        # Update only those heads, which have been fetched from remote
        for ref, sha in refs.items():
            if sha in self._repo.object_store:
                self._repo.refs[ref] = sha

        # Init branches
        branches = dict([
            (name.split('/')[-1], Head(self, ref, name))
            for name, ref in refs.items()
            if name.startswith('refs/heads')
        ])

        # Finish init
        super(Repository, self).__init__(branches)

    def __repr__(self):
        return '<{0:s} object at {1:s}>'.format(self.__class__.__name__,
                                                self._host_path)


@implementer(IRepositoryManager)
class RepositoryManager(dict):

    redis = None

    def __init__(self):
        super(RepositoryManager, self).__init__()

        product_config = getattr(getConfiguration(), 'product_config', {})
        gitresource_config = product_config.get('collective.gitresource', {})

        if HAS_REDIS:
            # Parse configuration
            redis = {}
            for key, value in gitresource_config.items():
                if key.startswith('redis.'):
                    try:
                        redis[key[6:]] = int(value)
                    except ValueError:
                        redis[key[6:]] = value

            # Create connection
            self.redis = StrictRedis(**redis)

    def __getitem__(self, uri):
        if uri not in self:
            self[uri] = Repository(uri)
        return super(RepositoryManager, self).__getitem__(uri)
