import os
import re
from setuptools import setup, find_packages


VERSIONFILE = os.path.join('vidscraper', '__init__.py')
VSRE = r"""^__version__ = \(([^\)]+)\)"""


def get_version():
    version_file = open(VERSIONFILE, 'rt').read()
    version = re.search(VSRE, version_file, re.M).group(1)
    version = '.'.join([part.strip() for part in version.split(',')])
    return version


setup(
    name="vidscraper",
    version=get_version(),
    maintainer='Participatory Culture Foundation',
    maintainer_email='dev@mirocommunity.org',
    url='https://github.com/pculture/vidscraper',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/vidscraper'],
    install_requires=[
        'feedparser>=5.1.2',
        'beautifulsoup4>=4.0.2',
        'requests>=1.0.0',
        'lxml>=2.3.4',
    ],
    extras_require={
        'oauth': ['requests-oauth>=0.4.1'],
        'tests': ['unittest2>=0.5.1', 'mock>=0.8.0', 'tox>=1.4.2', 'nose>=1.2.1'],
    },
    test_suite='vidscraper.tests',
    classifiers=(
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Sound/Audio',
    ),
)
