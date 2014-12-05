# -*- coding: utf-8 -*-
import unittest
from collective.gitresource.testing import GITRESOURCE_FUNCTIONAL_TESTING


class TestResourceDirectory(unittest.TestCase):

    layer = GITRESOURCE_FUNCTIONAL_TESTING

    def test_traverse(self):
        portal = self.layer['portal']

        foo = portal.restrictedTraverse('++test++repo/foo')
        self.assertEqual(foo.bytes.getvalue(), 'monty')

        bar = portal.restrictedTraverse('++test++repo/bar')
        self.assertEqual(bar.bytes.getvalue(), 'python')
