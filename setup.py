##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
# This package is developed by the Zope Toolkit project, documented here:
# https://zopetoolkit.readthedocs.io/
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Setup for zope.server package
"""
import os

from setuptools import find_packages
from setuptools import setup


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


tests_require = [
    'zope.testrunner',
    'zope.testing',
    'zope.i18n',
    'zope.component',
    'Paste',
]


setup(
    name='zope.server',
    version='5.1.dev0',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.dev',
    description='Zope Server (Web and FTP)',
    long_description=(
        read('README.rst')
        + '\n\n' +
        read('CHANGES.rst')
    ),
    license='ZPL 2.1',
    keywords=('zope3 server http ftp'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: Zope :: 3',
    ],
    url='https://github.com/zopefoundation/zope.server',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zope'],
    tests_require=tests_require,
    install_requires=[
        'setuptools',
        'zope.interface',
        'zope.publisher',
        'zope.security',
    ],
    extras_require=dict(test=tests_require),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.7",
    entry_points="""
        [paste.server_runner]
        main = zope.server.http.wsgihttpserver:run_paste
    """,
)
