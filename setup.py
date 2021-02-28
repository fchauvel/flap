#!/usr/bin/env python

#
# This file is part of Flap.
#
# Flap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Flap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Flap.  If not, see <http://www.gnu.org/licenses/>.
#

import flap
from setuptools import setup, find_packages


test_dependencies = [
    "virtualenv==15.1.0",
    "green==2.15.0",
    "mock==2.0.0",
    "coverage==4.5.3",
    "codecov==2.0.5",
    "coverage==4.2",
    "mkdocs==0.14.0",
    "mock==1.3.0",
]


setup(name='FLaP',
      version=flap.__version__,
      description='Flat LaTeX Projects',
      author='Franck Chauvel',
      author_email='franck.chauvel@gmail.com',
      license="GPLv3",
      url='https://github.com/fchauvel/flap',
      download_url="https://github.com/fchauvel/flap/tarball/v" +
      flap.__version__,
      packages=find_packages(exclude='tests'),
      test_suite="tests",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Science/Research",
          "Environment :: Console",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Natural Language :: English",
          "Topic :: Text Processing :: Markup :: LaTeX",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
      ],
      install_requires=[
          "PyYAML==5.1",
          "click==6.6",
          "enum34==1.1.6",
      ],
      tests_require=test_dependencies,
      extras_require={
          "test": test_dependencies
      },
      entry_points={
          'console_scripts': [
              'flap = flap.ui:main'
          ]
      }
      )
