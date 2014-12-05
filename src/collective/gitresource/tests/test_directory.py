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

        sub_foo = portal.restrictedTraverse('++test++repo/sub/foo')
        self.assertEqual(sub_foo.bytes.getvalue(), 'sub_monty')

        sub_bar = portal.restrictedTraverse('++test++repo/sub/bar')
        self.assertEqual(sub_bar.bytes.getvalue(), 'sub_python')

        sub_foo = portal.restrictedTraverse('++test++sub-repo/foo')
        self.assertEqual(sub_foo.bytes.getvalue(), 'sub_monty')

        sub_bar = portal.restrictedTraverse('++test++sub-repo/bar')
        self.assertEqual(sub_bar.bytes.getvalue(), 'sub_python')
