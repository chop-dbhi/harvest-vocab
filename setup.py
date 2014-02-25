from setuptools import setup, find_packages

kwargs = {
    # Packages
    'packages': find_packages(exclude=[
        'tests',
        '*.tests',
        '*.tests.*',
        'tests.*'
    ]),
    'include_package_data': True,

    # Dependencies
    'install_requires': [
        'serrano>=2.1.0,<2.4',
    ],

    # Test dependencies
    'tests_require': [
        'coverage',
    ],

    'test_suite': 'test_suite',

    # Metadata
    'name': 'harvest-vocab',
    'version': __import__('vocab').get_version(),
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'A Harvest Stack app for modeling hierarchical data',
    'license': 'BSD',
    'keywords': 'django harvest avocado cilantro vocabulary hierarchical',
    'url': 'https://github.com/cbmi/harvest-vocab/',
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Topic :: Internet :: WWW/HTTP',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Healthcare Industry',
    ],
}

setup(**kwargs)
