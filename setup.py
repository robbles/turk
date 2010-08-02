__author__="Rob O'Dwyer"
__date__ ="$Mar 09, 2010 5:34:40 PM$"

from setuptools import setup,find_packages

setup (
    name = 'Turk',
    version = '0.1.1',
    packages = find_packages(),
    zip_safe = False,

    install_requires=['twisted', 'pyserial', 'PyYAML', 'wokkel'],

    author = 'Rob O\'Dwyer',
    author_email = 'odwyerrob@gmail.com',

    summary = 'Turk - the framework for interfacing applications and devices with the web',
    url = 'http://github.com/robbles/turk',
    license = 'MIT',
    description = 'A framework for interfacing applications and devices with the web',
    long_description = open('README').read(),
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Topic :: Internet',
        'Topic :: Home Automation',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],

    entry_points = {
        'console_scripts': [
            'turkctl = turk.turkctl:main',
        ],
        'gui_scripts': []
    }

)

