from setuptools import setup, find_packages

version = '0.0.1'

setup(name="vidscraper",
      version=version,
      author='Participatory Culture Foundation',
      license='BSD',
      packages=find_packages(),
      install_requires=['lxml', 'oauth2', 'feedparser'])


