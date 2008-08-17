##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Setup for zope.server package

$Id$
"""

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name='zope.server',
      version = '3.4.4dev',
      license='ZPL 2.1',
      description='Zope server (Web and FTP)',
      author='Zope Corporation and Contributors',
      author_email='zope-dev@zope.org',
       long_description=(
        read('README.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
      keywords=('zope3 server http ftp'),
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Zope Public License',
          'Programming Language :: Python',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Topic :: Internet :: WWW/HTTP',
          'Framework :: Zope3'],
      url='http://cheeseshop.python.org/pypi/zope.server',
      packages=find_packages('src'),
      package_dir = {'': 'src'},

      namespace_packages=['zope',],

      tests_require = ['zope.testing',
                       'zope.i18n',
                       'zope.component'],
      install_requires = ['setuptools',
                          'zope.interface',
                          'zope.publisher',
                          'zope.security',
                          'zope.deprecation',
                          'ZODB3'],
      include_package_data = True,

      zip_safe = False,
      )
