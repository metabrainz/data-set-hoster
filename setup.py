from setuptools import setup

setup(name='datasethoster',
      version='0.1',
      description='Super simple data set hoster',
      url='https://github.com/metabrainz/data-set-hoster',
      author='Robert Kaye',
      author_email='rob@metabrainz.org',
      license='GPL2',
      packages=['datasethoster'],
      package_dir={'datasethoster': 'datasethoster'},
      package_data={'datasethoster': ['template/*.html']},
      include_package_data=True,
      install_requires=[
          'Flask>=1.1.2', 'six', 'sentry-sdk[flask]>=0.19.3'
      ],
      zip_safe=False)
