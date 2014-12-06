# -*- coding: utf-8 -*-
import unittest
from zope.component import getUtility
from collective.gitresource.interfaces import IRepositoryManager
from collective.gitresource.iterator import BytesIterator
from collective.gitresource.testing import GITRESOURCE_FUNCTIONAL_TESTING


class TestRepository(unittest.TestCase):

    layer = GITRESOURCE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.repo = self.layer['repo']
        self.manager = getUtility(IRepositoryManager)

    def test_repository(self):
        self.assertIn(self.repo.path, self.manager)

    def test_repository_master(self):
        self.assertIn('master', self.manager[self.repo.path])

    def test_repository_master_names(self):
        self.assertIn('foo', self.manager[self.repo.path]['master'])
        self.assertIn('bar', self.manager[self.repo.path]['master'])
        self.assertIn('sub/foo', self.manager[self.repo.path]['master'])
        self.assertIn('sub/bar', self.manager[self.repo.path]['master'])

    def test_repository_master_data(self):
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
