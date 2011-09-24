from setuptools import setup, find_packages

version = '0.5.0a'

setup(name="vidscraper",
      version=version,
      author='Participatory Culture Foundation',
      license='BSD',
      packages=find_packages(),
      install_requires=['lxml', 'oauth2', 'feedparser'])


