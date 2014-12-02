# -*- coding: utf-8 -*-
from plone.resource.interfaces import IWritableResourceDirectory
from zope.interface import Interface
from zope.interface import Attribute
from zope.interface.common.mapping import IIterableMapping


class ILastModified(Interface):
    last_modified = Attribute('Last modification timestamp (integer)')


class IHead(IIterableMapping):
    """In-memory GIT-repository
    mapping file paths to bytes iterators
    """


class IRepository(IIterableMapping):
    """In-memory GIT-repository
    mapping branch names to branches
    """


class IRepositoryManager(IIterableMapping):
    """Utility for managing in-memory GIT-repositories
    mapping repository URIs to repositories
    """
    redis = Attribute('Redis connection')


class IGitRemoteResourceDirectory(IWritableResourceDirectory):
    """Writable GIT remote resource directory"""
