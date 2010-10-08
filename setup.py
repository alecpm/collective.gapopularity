from setuptools import setup, find_packages

version = '1.0a1'

setup(name='collective.gapopularity',
      version=version,
      description="Adds a popularity count to Plone objects.",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGES.txt").read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='Plone Google Analytics popularity statistics',
      author='Matt Yoder',
      author_email='mattyoder@groundwire.org',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'collective.googleanalytics',
          'plone.indexer',
          'setuptools',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
