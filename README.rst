Introduction
============

dulwich_-based pure Python GIT-integration for `plone.resource`_.

.. _dulwich: https://pypi.python.org/pypi/dulwich
.. _plone.resource: https://pypi.python.org/pypi/plone.resource


Status
------

Updated 2014-12-01.

- Uses git as memory only local repository (bare).
- Tries to commit + push after each write / save.

  * git+ssh-protocol works with GitHub (requires proper credentials
    been configured for the user running Plone)

  * git+https-protocol support is planned (as a way to set credentials
    using product-config), but does not work with GitHub (dulwich_ tries
    to use API, which GitHub has deprecated)

  * currently commits as the current Plone-user (support to configure
    the user using product-config is planned)

- No pull, but can push to plone (no authentication (!), no cache purge).
- No persistent caching (relying on shared memory between threads and front-end
  caching)
- All files have the time of the last commit as their last modification time
  (correct modification time can be supported if it there's a fast way to
  look it up from the repository data without iterating through all the
  commits)


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
