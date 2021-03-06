from setuptools import setup, find_packages

setup(
    name='collective.gitresource',
    version='1.0.0',
    description="",
    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGES.rst').read()),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python',
    ],
    keywords='',
    author='Asko Soukka',
    author_email='asko.soukka@iki.fi',
    url='https://github.com/collective/collective.gitresource/',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['collective'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'plone.resource',
        'dulwich',
    ],
    extras_require={'redis': [
        'redis',
        'redis_collections',
        'collective.monkeypatcher'
    ], 'test': [
        'plone.app.testing',
        'plone.app.theming',
        'plone.app.robotframework',
    ]},
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """
)
