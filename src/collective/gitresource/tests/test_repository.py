# -*- coding: utf-8 -*-
import unittest
from dulwich.repo import MemoryRepo

from zope.component import getUtility

from collective.gitresource.interfaces import IRepositoryManager

from collective.gitresource.iterator import BytesIterator
from collective.gitresource.repository import Repository
from collective.gitresource.repository import RedisRepo
from collective.gitresource.repository import Head
from collective.gitresource.testing import GITRESOURCE_FUNCTIONAL_TESTING
from collective.gitresource.testing import HAS_REDIS


class TestRepository(unittest.TestCase):

    layer = GITRESOURCE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.repo = self.layer['repo']
        self.manager = getUtility(IRepositoryManager)

    def test_repository(self):
        self.assertIsInstance(self.manager[self.repo.path], Repository)
        if HAS_REDIS:
            self.assertIsInstance(
                self.manager[self.repo.path]._repo, RedisRepo)
        else:
            self.assertIsInstance(
                self.manager[self.repo.path]._repo, MemoryRepo)

    def test_repository_branch(self):
        self.assertIsInstance(self.manager[self.repo.path]['master'], Head)

    def test_repository_branch_names(self):
        self.assertIn('foo', self.manager[self.repo.path]['master'])
        self.assertIn('bar', self.manager[self.repo.path]['master'])
        self.assertIn('sub/foo', self.manager[self.repo.path]['master'])
        self.assertIn('sub/bar', self.manager[self.repo.path]['master'])

    def test_repository_branch_data(self):
        self.assertIsInstance(
            self.manager[self.repo.path]['master']['foo'], BytesIterator)
        self.assertEqual(
            'monty',
            self.manager[self.repo.path]['master']['foo'].getvalue())

        self.assertIsInstance(
            self.manager[self.repo.path]['master']['bar'], BytesIterator)
        self.assertEqual(
            'python',
            self.manager[self.repo.path]['master']['bar'].getvalue())

        self.assertIsInstance(
            self.manager[self.repo.path]['master']['sub/foo'], BytesIterator)
        self.assertEqual(
            'sub_monty',
            self.manager[self.repo.path]['master']['sub/foo'].getvalue())

        self.assertIsInstance(
            self.manager[self.repo.path]['master']['sub/bar'], BytesIterator)
        self.assertEqual(
            'sub_python',
            self.manager[self.repo.path]['master']['sub/bar'].getvalue())
