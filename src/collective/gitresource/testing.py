# -*- coding: utf-8 -*-
from App.config import getConfiguration
from App.config import setConfiguration
import pkg_resources
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

try:
    pkg_resources.get_distribution('redis_collections')
except pkg_resources.DistributionNotFound:
    HAS_REDIS = False
else:
    from redis import StrictRedis
    from redis_collections import Dict
    HAS_REDIS = True


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
        self.loadZCML(package=collective.gitresource,
                      name='testing.zcml')

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, "plone.app.theming:default")

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
