# -*- coding: utf-8 -*-
import os
from io import BytesIO
import tempfile
import unittest
import shutil
import zipfile

from dulwich.client import get_transport_and_path
from dulwich.repo import Repo
from plone.resource.interfaces import IResourceDirectory
from zope.component import getUtility

from collective.gitresource.directory import ResourceDirectory
from collective.gitresource.file import File
from collective.gitresource.iterator import BytesIterator
from collective.gitresource.testing import GITRESOURCE_FUNCTIONAL_TESTING


class TestResourceDirectoryTraverse(unittest.TestCase):

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


class TestResourceDirectoryAPI(unittest.TestCase):

    layer = GITRESOURCE_FUNCTIONAL_TESTING

    paths = None

    def setUp(self):
        self.portal = self.layer['portal']
        self.a = getUtility(IResourceDirectory, name='++test++repo')
        self.b = getUtility(IResourceDirectory, name='++test++sub-repo')
        self.repo = self.layer['repo']
        self.paths = []

    def tearDown(self):
        for path in self.paths:
            shutil.rmtree(path)

    def _mkdtemp(self):
        path = tempfile.mkdtemp()
        self.paths.append(path)
        return path

    def test_is_file(self):
        self.assertTrue(self.a.isFile('foo'))
        self.assertTrue(self.a.isFile('bar'))
        self.assertTrue(self.a.isFile('sub/foo'))
        self.assertTrue(self.a.isFile('sub/bar'))

        self.assertTrue(self.b.isFile('foo'))
        self.assertTrue(self.b.isFile('bar'))

    def test_is_not_file(self):
        self.assertFalse(self.a.isFile('sub'))

    def test_is_directory(self):
        self.assertTrue(self.a.isDirectory('sub'))

    def test_is_not_directory(self):
        self.assertFalse(self.a.isDirectory('foo'))
        self.assertFalse(self.a.isDirectory('bar'))
        self.assertFalse(self.a.isDirectory('sub/foo'))
        self.assertFalse(self.a.isDirectory('sub/bar'))

        self.assertFalse(self.b.isDirectory('foo'))
        self.assertFalse(self.b.isDirectory('bar'))

    def test_read_file(self):
        self.assertEqual(self.a.readFile('foo'), 'monty')
        self.assertEqual(self.a.readFile('bar'), 'python')
        self.assertEqual(self.a.readFile('sub/foo'), 'sub_monty')
        self.assertEqual(self.a.readFile('sub/bar'), 'sub_python')

        self.assertEqual(self.b.readFile('foo'), 'sub_monty')
        self.assertEqual(self.b.readFile('bar'), 'sub_python')

    def test_open_file(self):
        self.assertIsInstance(self.a.openFile('foo'), BytesIterator)
        self.assertEqual(self.a.openFile('foo').read(), 'monty')
        self.assertIsInstance(self.a.openFile('bar'), BytesIterator)
        self.assertEqual(self.a.openFile('bar').read(), 'python')
        self.assertIsInstance(self.a.openFile('sub/foo'), BytesIterator)
        self.assertEqual(self.a.openFile('sub/foo').read(), 'sub_monty')
        self.assertIsInstance(self.a.openFile('sub/bar'), BytesIterator)
        self.assertEqual(self.a.openFile('sub/bar').read(), 'sub_python')  # noqa

        self.assertIsInstance(self.b.openFile('foo'), BytesIterator)
        self.assertEqual(self.b.openFile('foo').read(), 'sub_monty')
        self.assertIsInstance(self.b.openFile('bar'), BytesIterator)
        self.assertEqual(self.b.openFile('bar').read(), 'sub_python')

    def test_contains(self):
        self.assertIn('foo', self.a)
        self.assertIn('bar', self.a)
        self.assertIn('sub', self.a)
        self.assertIn('sub/foo', self.a)
        self.assertIn('sub/bar', self.a)

        self.assertIn('foo', self.b)
        self.assertIn('bar', self.b)

    def test_list_directory(self):
        a = list(self.a.listDirectory())
        self.assertIn('foo', a)
        self.assertIn('bar', a)
        self.assertIn('sub', a)

        self.assertNotIn('sub/foo', a)
        self.assertNotIn('sub/bar', a)

        b = list(self.b.listDirectory())
        self.assertIn('foo', b)
        self.assertIn('bar', b)

    def test_not_contains(self):
        self.assertNotIn('sub', self.b)
        self.assertNotIn('sub/foo', self.b)
        self.assertNotIn('sub/bar', self.b)

    def test_getitem(self):
        self.assertIsInstance(self.a['foo'], File)
        self.assertIsInstance(self.a['foo'].bytes, BytesIterator)
        self.assertEqual(self.a['foo'].bytes.getvalue(), 'monty')
        self.assertIsInstance(self.a['bar'], File)
        self.assertIsInstance(self.a['bar'].bytes, BytesIterator)
        self.assertEqual(self.a['bar'].bytes.getvalue(), 'python')
        self.assertIsInstance(self.a['sub/foo'], File)
        self.assertIsInstance(self.a['sub/foo'].bytes, BytesIterator)
        self.assertEqual(self.a['sub/foo'].bytes.getvalue(), 'sub_monty')
        self.assertIsInstance(self.a['sub/bar'], File)
        self.assertIsInstance(self.a['sub/bar'].bytes, BytesIterator)
        self.assertEqual(self.a['sub/bar'].bytes.getvalue(), 'sub_python')

        self.assertIsInstance(self.b['foo'], File)
        self.assertIsInstance(self.b['foo'].bytes, BytesIterator)
        self.assertEqual(self.b['foo'].bytes.getvalue(), 'sub_monty')
        self.assertIsInstance(self.b['bar'], File)
        self.assertIsInstance(self.b['bar'].bytes, BytesIterator)
        self.assertEqual(self.b['bar'].bytes.getvalue(), 'sub_python')

    def test_getitem_raise(self):
        self.assertRaises(KeyError, self.b.__getitem__, 'sub/foo')
        self.assertRaises(KeyError, self.b.__getitem__, 'sub/bar')

    def test_export_zip(self):
        fp = BytesIO()
        self.a.exportZip(fp)
        fp.seek(0)
        zf = zipfile.ZipFile(fp)

        namelist = zf.namelist()
        self.assertIn('repo/foo', namelist)
        self.assertEqual(zf.read('repo/foo'), 'monty')
        self.assertIn('repo/bar', namelist)
        self.assertEqual(zf.read('repo/bar'), 'python')
        self.assertIn('repo/sub/foo', namelist)
        self.assertEqual(zf.read('repo/sub/foo'), 'sub_monty')
        self.assertIn('repo/sub/bar', namelist)
        self.assertEqual(zf.read('repo/sub/bar'), 'sub_python')

        fp = BytesIO()
        self.b.exportZip(fp)
        fp.seek(0)
        zf = zipfile.ZipFile(fp)

        namelist = zf.namelist()
        self.assertIn('sub-repo/foo', namelist)
        self.assertEqual(zf.read('sub-repo/foo'), 'sub_monty')
        self.assertIn('sub-repo/bar', namelist)
        self.assertEqual(zf.read('sub-repo/bar'), 'sub_python')

    def test_make_directory(self):
        self.a.makeDirectory('sub-new')
        self.assertTrue(self.a.isDirectory('sub-new'))
        self.assertFalse(self.a.isFile('sub-new'))

    def test_write_file(self):
        self.a.writeFile('foo', BytesIO('hello'))
        self.assertTrue(self.a.isFile('foo'))
        self.assertEqual(self.a.readFile('foo'), 'hello')

    def test_write_file_auto_commit_push(self):
        with open(os.path.join(self.layer['checkout'].path, 'foo'), 'r') as fp:
            self.assertEqual(fp.read(), 'monty')

        self.test_write_file()

        repo = Repo.init(self._mkdtemp())
        client, host_path = get_transport_and_path(self.layer['repo'].path)
        refs = client.fetch(
            host_path, repo,
            determine_wants=repo.object_store.determine_wants_all
        )
        repo["HEAD"] = refs["HEAD"]
        repo["refs/heads/master"] = refs["refs/heads/master"]
        repo._build_tree()

        with open(os.path.join(repo.path, 'foo'), 'r') as fp:
            self.assertEqual(fp.read(), 'hello')

    def test_write_file_empty(self):
        self.a.writeFile('foo', BytesIO(''))
        self.assertTrue(self.a.isFile('foo'))
        self.assertEqual(self.a.readFile('foo'), '')

    def test_write_file_empty_auto_commit_push(self):
        with open(os.path.join(self.layer['checkout'].path, 'foo'), 'r') as fp:
            self.assertEqual(fp.read(), 'monty')

        self.test_write_file_empty()

        repo = Repo.init(self._mkdtemp())
        client, host_path = get_transport_and_path(self.layer['repo'].path)
        refs = client.fetch(
            host_path, repo,
            determine_wants=repo.object_store.determine_wants_all
        )
        repo["HEAD"] = refs["HEAD"]
        repo["refs/heads/master"] = refs["refs/heads/master"]
        repo._build_tree()

        with open(os.path.join(repo.path, 'foo'), 'r') as fp:
            self.assertEqual(fp.read(), '')

    def test_write_file_new(self):
        self.a.writeFile('world', BytesIO('hello'))
        self.assertTrue(self.a.isFile('world'))
        self.assertEqual(self.a.readFile('world'), 'hello')

    def test_write_file_new_auto_commit_push(self):
        self.test_write_file_new()

        repo = Repo.init(self._mkdtemp())
        client, host_path = get_transport_and_path(self.layer['repo'].path)
        refs = client.fetch(
            host_path, repo,
            determine_wants=repo.object_store.determine_wants_all
        )
        repo["HEAD"] = refs["HEAD"]
        repo["refs/heads/master"] = refs["refs/heads/master"]
        repo._build_tree()

        with open(os.path.join(repo.path, 'world'), 'r') as fp:
            self.assertEqual(fp.read(), 'hello')

    def test_write_file_new_empty(self):
        self.a.writeFile('world', BytesIO(''))
        self.assertTrue(self.a.isFile('world'))
        self.assertEqual(self.a.readFile('world'), '')

    def test_write_file_new_empty_auto_commit_push(self):
        self.test_write_file_new_empty()

        repo = Repo.init(self._mkdtemp())
        client, host_path = get_transport_and_path(self.layer['repo'].path)
        refs = client.fetch(
            host_path, repo,
            determine_wants=repo.object_store.determine_wants_all
        )
        repo["HEAD"] = refs["HEAD"]
        repo["refs/heads/master"] = refs["refs/heads/master"]
        repo._build_tree()

        with open(os.path.join(repo.path, 'world'), 'r') as fp:
            self.assertEqual(fp.read(), '')
