Introduction
============

dulwich_-based pure Python GIT-integration for `plone.resource`_.

.. _dulwich: https://pypi.python.org/pypi/dulwich
.. _plone.resource: https://pypi.python.org/pypi/plone.resource


Status
------

Updated 2014-11-29.

- Uses git as memory only local repository (bare).
- Read only. Write support is planned as direct commit + push to the remote.
- No pull. Manual pull via Plone control panel planned (incl. cache purges).
- No caching. Relying on Front-end caching at first. Local copy as
  persistent `plone.resource`_ directory would be implementable.
- All files have the time of the last commit as their last modification date.


Example
-------

..  code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:plone="http://namespaces.plone.org/plone"
        i18n_domain="collective.gitresource">

      <include package="collective.gitresource" file="meta.zcml" />

      <plone:git-remote
          uri="git://github.com/collective/diazotheme.frameworks.git"
          branch="master"
          directory="diazotheme/frameworks/bootstrap"
          name="bootstrap-framework"
          type="theme"
          />

      <plone:git-remote
          uri="git://github.com/collective/diazotheme.frameworks.git"
          directory="diazotheme/frameworks/plone"
          name="plone"
          type="theme"
          />

      <plone:git-remote
          uri="git+ssh://git@github.com/collective/diazotheme.bootswatch.git"
          directory="diazotheme/bootswatch/bootswatch"
          name="bootswatch"
          type="theme"
          />

      <plone:git-remote
          uri="git+ssh://git@github.com/collective/diazotheme.bootswatch.git"
          directory="diazotheme/bootswatch/amelia"
          name="amelia"
          type="theme"
          />

      <plone:git-remote
          uri="git+ssh://git@github.com/collective/diazotheme.bootswatch.git"
          directory="diazotheme/bootswatch/amelia-narrow"
          name="amelia-narrow"
          type="theme"
          />

    </configure>
