from setuptools import setup

setup(name='datasethoster',
      version='0.1',
      description='Super simple data set hoster',
      url='https://github.com/metabrainz/data-set-hoster',
      author='Robert Kaye',
      author_email='rob@metabrainz.org',
      license='CC0',
      packages=['datasethoster'],
      install_requires=[
          'Flask==1.1.2',
      ],
      zip_safe=False)
