#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mbiiez',
    version='1.0.0',
    description='Movie Battles II Enhanced Server Management',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='MBIIEZ Team',
    url='https://github.com/yourusername/mbiiez',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'psutil>=5.9.0',
        'prettytable>=3.0.0',
        'six>=1.16.0',
        'tailer>=0.4',
        'urllib3>=1.26.0',
    ],
    extras_require={
        'web': [
            'flask>=2.0.0',
            'flask-socketio>=5.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'mbii=mbiiez.client:run',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: System :: Monitoring',
    ],
)