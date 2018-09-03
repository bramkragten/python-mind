#!/usr/bin/env python
# -*- coding:utf-8 -*-

import io

from setuptools import setup


version = '0.0.2'


setup(name='python-mind',
      version=version,
      description='Python API for talking to '
                  'MIND Mobility Connected Cars',
      long_description=io.open('README.rst', encoding='UTF-8').read(),
      keywords='MIND Mobility PON Mijn Volkswagen Mijn Skoda Mijn Seat Audi Car Assistant Mijn Volkswagen Bedrijfswagens',
      author='Bram Kragten',
      author_email='mail@bramkragten.nl',
      url='https://github.com/bramkragten/python-mind/',
      packages=['mind'],
      install_requires=['requests>=1.0.0',
                        'requests_oauthlib>=0.7.0']
      )
