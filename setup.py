from setuptools import setup, find_packages

version = '0.6-a'

setup(
    name="vidscraper",
    version=version,
    maintainer='Participatory Culture Foundation',
    maintainer_email='dev@mirocommunity.org',
    url='https://github.com/pculture/vidscraper',
    license='BSD',
    packages=find_packages(),
    scripts=['bin/vidscraper-cmd'],
    install_requires=[
        'lxml>=2.3.4',
        'oauth2>=1.5.211',
        'feedparser>=5.1.1',
        'beautifulsoup4>=4.0.2',
        'requests>=0.10.8',
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


