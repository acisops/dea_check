#!/usr/bin/env python
from setuptools import setup
from dea_check import __version__

entry_points = {'console_scripts': 'dea_check = dea_check.dea_check:main'}

url = 'https://github.com/acisops/dea_check/tarball/{}'.format(__version__)

setup(name='dea_check',
      packages=["dea_check"],
      version=__version__,
      description='ACIS Thermal Model for 1DEAMZT',
      author='John ZuHone',
      author_email='jzuhone@gmail.com',
      url='http://github.com/acisops/dea_check',
      download_url=url,
      include_package_data=True,
      classifiers=[
          'Intended Audience :: Science/Research',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
      ],
      entry_points=entry_points,
      )
