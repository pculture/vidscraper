from setuptools import setup, find_packages

version = '0.6-a'

setup(
    name="vidscraper",
    version=version,
    author='Participatory Culture Foundation',
    license='BSD',
    packages=find_packages(),
    install_requires=[
        'lxml',
        'oauth2',
        'feedparser',
        'BeautifulSoup==3.2.0',
        'requests',
    ],
    test_suite='vidscraper.tests',
    classifiers=(
        'Development Status :: 3 - Alpha',
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


