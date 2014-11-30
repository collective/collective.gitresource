# -*- coding: utf-8 -*-
from plone.resource.interfaces import IResourceDirectory
from plone.resource.zcml import IResourceDirectoryDirective
from zope.component.zcml import handler
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface
from zope.schema import URI, ASCIILine
from zope.schema import TextLine

from collective.gitresource.directory import ResourceDirectory


class IGitRemoteResourceDirectoryDirective(Interface):
    """Register resource directories with the global registry.
    """

    uri = URI(
        title=u'Repository URI',
        description=u'Valid GIT repository URI',
        required=True
    )

    branch = ASCIILine(
        title=u'Branch',
        description=u'Repository branch (defaults to master)',
        required=False
    )

    directory = TextLine(
        title=u'Directory path',
        description=u'Optional path relative to the repository root',
        required=False
    )

    name = ASCIILine(
        title=u'Name',
        description=u'Unique name for the resource directory',
        required=True
    )

    type = IResourceDirectoryDirective['type']


# noinspection PyShadowingBuiltins
def registerGitRemoteResourceDirectory(_context, uri, branch='master',
                                       directory='', name=None, type=None):
    """
    Register a new resource directory.

    The actual ZCA registrations are deferred so that conflicts can be resolved
    via zope.configuration's discriminator machinery.
    """

    if name is None and _context.package:
        name = _context.package.__name__

    if type:
        identifier = '++%s++%s' % (type, name or '')
    else:
        if _context.package:
            raise ConfigurationError('Resource directories in distributions '
                                     'must have a specified resource type.')
        identifier = name or ''

    directory = ResourceDirectory(uri, branch, directory, name)

    _context.action(
        discriminator=('plone:git-remote', identifier),
        callable=handler,
        args=('registerUtility', directory, IResourceDirectory, identifier),
    )
