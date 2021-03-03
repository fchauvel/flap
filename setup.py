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
    "green==3.2.5",
    "coverage==5.5",
    "mock==4.0.3",
]


def fetch_readme():
    with open('README.md') as f:
        return f.read()


setup(name='FLaP',
      version=flap.__version__,
      description='Flat LaTeX Projects',
      long_description=fetch_readme(),
      long_description_content_type='text/markdown',
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
          "PyYAML==5.4.1",
          "click==7.1.2",
          "enum34==1.1.10",
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
