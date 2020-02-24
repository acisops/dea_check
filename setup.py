#!/usr/bin/env python
from setuptools import setup

try:
      from testr.setup_helper import cmdclass
except ImportError:
      cmdclass = {}

entry_points = {'console_scripts': 'dea_check = dea_check.dea_check:main'}

setup(name='dea_check',
      packages=["dea_check"],
      use_scm_version=True,
      setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],
      description='ACIS Thermal Model for 1DEAMZT',
      author='John ZuHone',
      author_email='jzuhone@gmail.com',
      url='http://github.com/acisops/dea_check',
      include_package_data=True,
      entry_points=entry_points,
      zip_safe=False,
      tests_require=["pytest"],
      cmdclass=cmdclass,
      )
