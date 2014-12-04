Introduction
============

dulwich_-based pure Python GIT-integration for `plone.resource`_.

.. _dulwich: https://pypi.python.org/pypi/dulwich
.. _plone.resource: https://pypi.python.org/pypi/plone.resource


Status
------

Updated 2014-12-04.

- Uses git as memory only local repository (bare)

- Optional "use Redis instead of memory" for sharing data between instances:

  .. code:: ini

     [instance]
     eggs +=
         ...
         collective.gitresource [redis]

  .. code:: xml

     <product-config collective.gitresource>
         redis.host localhost
         redis.port 6379
         ...
     </product-config>

  Warning: At least the HEAD of the remote repository is still always
  fetched on start. This might be fixed, once there's an UI for manually
  pulling changes from remote repo.

- Tries to commit + push after each write / save.

  * git+ssh-protocol works with GitHub (requires proper credentials
    been configured for the user running Plone)

  * git+https-protocol might work, but does not work with GitHub (dulwich_
    tries to use API, which GitHub has deprecated)

    .. code:: xml

       <product-config collective.gitresource>
           https://path/to/repo username:password
       </product-config>

  * currently commits as the current Plone-user (support to configure
    the user using product-config is planned)

- No pull, but you can **push** to plone (and also clone and pull from plone)

  Push url is just ``++resourcetype++myresource``,
  e.g. ``http://localhost:8080/Plone/++theme++mytheme/``.

  Warning: Git-interface is currently public and there's no authentication.
  This should be fixed to support HTTP Basic Auth (but did not manage to
  get git send the credentials yet)

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
