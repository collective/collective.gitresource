# -*- coding: utf-8 -*-
import tempfile
import unittest
import shutil

from collective.gitresource.testing import GITRESOURCE_ACCEPTANCE_TESTING


class TestGit(unittest.TestCase):

    layer = GITRESOURCE_ACCEPTANCE_TESTING

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_checkout(self):
        pass
