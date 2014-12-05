# -*- coding: utf-8 -*-
import os
import tempfile
import shutil

from App.config import getConfiguration
from App.config import setConfiguration
from dulwich.repo import Repo
import pkg_resources
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.resource.interfaces import IResourceDirectory
from plone.resource.traversal import ResourceTraverser
from plone.testing import z2
from zope.component import getSiteManager
from zope.interface import Interface
from zope.publisher.interfaces import IRequest
from zope.traversing.interfaces import ITraversable

from collective.gitresource.directory import ResourceDirectory


try:
    pkg_resources.get_distribution('redis_collections')
except pkg_resources.DistributionNotFound:
    HAS_REDIS = False
else:
    from redis import StrictRedis
    from redis_collections import Dict
    HAS_REDIS = True


def TestRepo():
    repo = Repo.init(tempfile.mkdtemp())

    with open(os.path.join(repo.path, 'foo'), 'w') as fp:
        fp.write('monty')
    with open(os.path.join(repo.path, 'bar'), 'w') as fp:
        fp.write('python')

    repo_sub = os.path.join(repo.path, 'sub')
    os.mkdir(repo_sub)

    with open(os.path.join(repo_sub, 'foo'), 'w') as fp:
        fp.write('sub_monty')
    with open(os.path.join(repo_sub, 'bar'), 'w') as fp:
        fp.write('sub_python')

    repo.stage(['foo', 'bar',
                os.path.join('sub', 'foo'),
                os.path.join('sub', 'bar')])
    repo.do_commit(
        'The first commit',
        committer='John Doe <john.doe@example.com>'
    )
    return repo


class TestTraverser(ResourceTraverser):
    name = 'test'


class GitResourceLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):

        # Set product configuration
        cfg = getConfiguration()
        if HAS_REDIS:
            cfg.product_config = {
                'collective.gitresource': {
                    'redis.host': 'localhost',
                    'redis.port': '6379',
                    'redis.db': '0'
                }
            }
        else:
            pass
        setConfiguration(cfg)

        import plone.app.theming
        self.loadZCML(package=plone.app.theming)

        import collective.gitresource
        self.loadZCML(package=collective.gitresource)

#       self.loadZCML(package=collective.gitresource,
#                     name='testing.zcml')
        self['repo'] = TestRepo()

    def setUpPloneSite(self, portal):
        sm = getSiteManager()

        # Register repositories
        directory = ResourceDirectory(
            uri=self['repo'].path, branch='master', directory='',
            resource_type='test', name='repo')
        sm.registerUtility(directory, IResourceDirectory, '++test++repo')

        directory = ResourceDirectory(
            uri=self['repo'].path, branch='master', directory='sub',
            resource_type='test', name='sub-repo')
        sm.registerUtility(directory, IResourceDirectory, '++test++sub-repo')

        # Register traverser
        sm.registerAdapter(
            name='test', factory=TestTraverser,
            required=(Interface, IRequest), provided=ITraversable)

        # Maybe we'll test theme-editor support later...
        self.applyProfile(portal, "plone.app.theming:default")

    def tearDownZope(self, app):
        shutil.rmtree(self['repo'].path)

GITRESOURCE_FIXTURE = GitResourceLayer()

GITRESOURCE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(GITRESOURCE_FIXTURE,),
    name="GitResource:Integration")

GITRESOURCE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(GITRESOURCE_FIXTURE,),
    name="GitResource:Functional")

GITRESOURCE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(GITRESOURCE_FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE,
           z2.ZSERVER_FIXTURE),
    name="GitResource:Acceptance")
