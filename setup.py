from setuptools import setup, find_packages

version = '0.5'

setup(
    name="vidscraper",
    version=version,
    maintainer='Participatory Culture Foundation',
    maintainer_email='dev@mirocommunity.org',
    url='https://github.com/pculture/vidscraper',
    license='BSD',
    packages=find_packages(),
    install_requires=[
        'lxml',
        'oauth2',
        'feedparser>5.1',
        'BeautifulSoup==3.2.0'
    ],
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


