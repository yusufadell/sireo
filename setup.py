#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Yusuf Adel",
    author_email='yusufadell.dev@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="A tool keeping track of data, metrics, and files throughout code development, testing, probing, experimentation, and analysis. ",
    entry_points={
        'console_scripts': [
            'sireo=sireo.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='sireo',
    name='sireo',
    packages=find_packages(include=['sireo', 'sireo.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/yusufadell/sireo',
    version='0.1.0',
    zip_safe=False,
)
