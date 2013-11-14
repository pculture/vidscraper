.. module:: vidscraper.suites

Suite API
=========

Vidscraper defines a simple API for "Suites", classes which provide the
functionality necessary for scraping video information from a specific video
service.

The Suite Registry
++++++++++++++++++

.. autodata:: vidscraper.suites.registry

.. autoclass:: vidscraper.suites.base.SuiteRegistry
	:members:

Built-in Suites
+++++++++++++++

.. autoclass:: vidscraper.suites.BaseSuite
   :members:
