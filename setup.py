#!/usr/bin/env python

from setuptools import setup

setup(name="BZRFlag",
      version="1.0",
      description="BZRFlag: BZFlag with Robotic Tanks!",
      long_description="See README",
      license="GNU GPL",
      author="BYU AML Lab",
      author_email="kseppi@byu.edu",
      url="http://code.google.com/p/bzrflag/",
      packages=['bzrflag'],
      include_package_data = True,
      package_data = {'': ['*.png', '*.txt', '*.ttf']},
      test_suite="tests",
      data_files=[('data', ['data/std_ground.png'])],
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: POSIX :: Linux',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Natural Language :: English',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering :: Artificial Intelligence'],
     )
