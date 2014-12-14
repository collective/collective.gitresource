# -*- coding: utf-8 -*-
import os
import tempfile
import shutil

from App.config import getConfiguration
from App.config import setConfiguration
from dulwich.client import get_transport_and_path
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

from plone.app.testing.interfaces import SITE_OWNER_NAME
from plone.app.testing.interfaces import SITE_OWNER_PASSWORD

from collective.gitresource.directory import ResourceDirectory

try:
    pkg_resources.get_distribution('redis_collections')
except pkg_resources.DistributionNotFound:
    HAS_REDIS = False
else:
    HAS_REDIS = True


def TestRepo():
    checkout = Repo.init(tempfile.mkdtemp())

    with open(os.path.join(checkout.path, 'foo'), 'w') as fp:
        fp.write('monty')
    with open(os.path.join(checkout.path, 'bar'), 'w') as fp:
        fp.write('python')

    sub_path = os.path.join(checkout.path, 'sub')
    os.mkdir(sub_path)

    with open(os.path.join(sub_path, 'foo'), 'w') as fp:
        fp.write('sub_monty')
    with open(os.path.join(sub_path, 'bar'), 'w') as fp:
        fp.write('sub_python')

    checkout.stage(['foo', 'bar',
                    os.path.join('sub', 'foo'),
                    os.path.join('sub', 'bar')])
    checkout.do_commit(
        'The first commit',
        committer='John Doe <john.doe@example.com>'
    )

    bare = Repo.init_bare(tempfile.mkdtemp())
    client, host_path = get_transport_and_path(checkout.path)

    refs = client.fetch(
        host_path, bare,
        determine_wants=bare.object_store.determine_wants_all,
    )
    bare["HEAD"] = refs["HEAD"]
    bare["refs/heads/master"] = refs["refs/heads/master"]

    return bare, checkout


class TestTraverser(ResourceTraverser):
    name = 'test'


class GitResourceLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):

        # Set product configuration
        cfg = getConfiguration()
        cfg.product_config = {
            'collective.gitresource': {
                os.environ.get('ZSERVER_HOST', 'localhost:'):
                '{0:s}:{1:s}'.format(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
            }
        }
        if HAS_REDIS:
            cfg.product_config['collective.gitresource'].update({
                'redis.host': 'localhost',
                'redis.port': '6379',
                'redis.db': '0'
            })
        setConfiguration(cfg)

        import plone.app.theming
        self.loadZCML(package=plone.app.theming)

        import collective.gitresource
        self.loadZCML(package=collective.gitresource)

#       self.loadZCML(package=collective.gitresource,
#                     name='testing.zcml')

    def setUpPloneSite(self, portal):
        # Maybe we'll test theme-editor support later...
        self.applyProfile(portal, "plone.app.theming:default")

    def testSetUp(self):
        sm = getSiteManager()

        # Create repository
        self['repo'], self['checkout'] = TestRepo()

        # Register repositories
        self['directory'] = ResourceDirectory(
            uri=self['repo'].path, branch='master', directory='',
            resource_type='test', name='repo')
        sm.registerUtility(
            self['directory'], IResourceDirectory, '++test++repo')

        self['sub-directory'] = ResourceDirectory(
            uri=self['repo'].path, branch='master', directory='sub',
            resource_type='test', name='sub-repo')
        sm.registerUtility(
            self['sub-directory'], IResourceDirectory, '++test++sub-repo')

        # Register traverser
        sm.registerAdapter(
            name='test', factory=TestTraverser,
            required=(Interface, IRequest), provided=ITraversable)

    def testTearDown(self):
        sm = getSiteManager()

        # Un-register traverser
        sm.unregisterAdapter(
            name='test', factory=TestTraverser,
            required=(Interface, IRequest), provided=ITraversable)

        # Un-register resource registries
        sm.unregisterUtility(
            self['sub-directory'], IResourceDirectory, '++test++sub-repo')
        sm.unregisterUtility(
            self['directory'], IResourceDirectory, '++test++repo')

        # Remove repository
        shutil.rmtree(self['checkout'].path)
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
