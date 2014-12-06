# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
import shutil
from dulwich.client import get_transport_and_path
from dulwich.repo import Repo

from plone.app.testing.interfaces import PLONE_SITE_ID
from plone.app.testing.interfaces import SITE_OWNER_NAME
from plone.app.testing.interfaces import SITE_OWNER_PASSWORD

from collective.gitresource.testing import GITRESOURCE_ACCEPTANCE_TESTING


class TestGitFromPlone(unittest.TestCase):

    layer = GITRESOURCE_ACCEPTANCE_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.repo = Repo.init(tempfile.mkdtemp())

    def test_clone_from_plone(self):
        uri = 'http://{0:s}:{1:s}/{2:s}/++test++repo/'.format(
            os.environ.get('ZSERVER_HOST', 'localhost'),
            os.environ.get('ZSERVER_PORT', '55001'),
            PLONE_SITE_ID
        )

        client, host_path = get_transport_and_path(uri)
        client.opener.addheaders.append((
            'Authorization', 'Basic {0:s}'.format(
                '{0:s}:{1:s}'.format(
                    SITE_OWNER_NAME, SITE_OWNER_PASSWORD
                ).encode('base64').strip()
            )
        ))

        remote_refs = client.fetch(
            uri, self.repo,
            determine_wants=self.repo.object_store.determine_wants_all
        )
        self.repo["HEAD"] = remote_refs["HEAD"]
        self.repo._build_tree()

        self.assertIn('.git', os.listdir(self.repo.path))
        self.assertIn('foo', os.listdir(self.repo.path))
        self.assertIn('bar', os.listdir(self.repo.path))
        self.assertIn('sub', os.listdir(self.repo.path))
        self.assertIn('foo', os.listdir(os.path.join(self.repo.path, 'sub')))
        self.assertIn('bar', os.listdir(os.path.join(self.repo.path, 'sub')))

        with open(os.path.join(self.repo.path, 'foo'), 'r') as fp:
            self.assertEqual(fp.read(), 'monty')

        with open(os.path.join(self.repo.path, 'bar'), 'r') as fp:
            self.assertEqual(fp.read(), 'python')

        with open(os.path.join(self.repo.path, 'sub', 'foo'), 'r') as fp:
            self.assertEqual(fp.read(), 'sub_monty')

        with open(os.path.join(self.repo.path, 'sub', 'bar'), 'r') as fp:
            self.assertEqual(fp.read(), 'sub_python')

    def tearDown(self):
        shutil.rmtree(self.repo.path)
