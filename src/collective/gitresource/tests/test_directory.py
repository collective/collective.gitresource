# -*- coding: utf-8 -*-
import unittest
from collective.gitresource.directory import ResourceDirectory
from collective.gitresource.file import File
from collective.gitresource.iterator import BytesIterator
from collective.gitresource.testing import GITRESOURCE_FUNCTIONAL_TESTING


class TestResourceDirectory(unittest.TestCase):

    layer = GITRESOURCE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_traverse(self):
        a = self.portal.restrictedTraverse('++test++repo')
        self.assertIsInstance(a, ResourceDirectory)
        self.assertIn(('_type', 'test'), a.__dict__.items())
        self.assertIn(('_branch', 'master'), a.__dict__.items())
        self.assertIn(('_directory', ''), a.__dict__.items())
        self.assertIn(('__name__', 'repo'), a.__dict__.items())

        b = self.portal.restrictedTraverse('++test++sub-repo')
        self.assertIsInstance(a, ResourceDirectory)
        self.assertIn(('_type', 'test'), b.__dict__.items())
        self.assertIn(('_branch', 'master'), b.__dict__.items())
        self.assertIn(('_directory', 'sub'), b.__dict__.items())
        self.assertIn(('__name__', 'sub-repo'), b.__dict__.items())

    def test_traverse_path(self):
        foo = self.portal.restrictedTraverse('++test++repo/foo')
        self.assertIsInstance(foo, File)
        self.assertIsInstance(foo.bytes, BytesIterator)
        self.assertEqual(foo.bytes.getvalue(), 'monty')

        bar = self.portal.restrictedTraverse('++test++repo/bar')
        self.assertIsInstance(bar, File)
        self.assertIsInstance(bar.bytes, BytesIterator)
        self.assertEqual(bar.bytes.getvalue(), 'python')

    def test_traverse_sub_path(self):
        sub_foo = self.portal.restrictedTraverse('++test++repo/sub/foo')
        self.assertIsInstance(sub_foo, File)
        self.assertIsInstance(sub_foo.bytes, BytesIterator)
        self.assertEqual(sub_foo.bytes.getvalue(), 'sub_monty')

        sub_bar = self.portal.restrictedTraverse('++test++repo/sub/bar')
        self.assertIsInstance(sub_bar, File)
        self.assertIsInstance(sub_bar.bytes, BytesIterator)
        self.assertEqual(sub_bar.bytes.getvalue(), 'sub_python')

    def test_traverse_sub_repo_path(self):
        sub_foo = self.portal.restrictedTraverse('++test++sub-repo/foo')
        self.assertIsInstance(sub_foo, File)
        self.assertIsInstance(sub_foo.bytes, BytesIterator)
        self.assertEqual(sub_foo.bytes.getvalue(), 'sub_monty')

        sub_bar = self.portal.restrictedTraverse('++test++sub-repo/bar')
        self.assertIsInstance(sub_bar, File)
        self.assertIsInstance(sub_bar.bytes, BytesIterator)
        self.assertEqual(sub_bar.bytes.getvalue(), 'sub_python')
