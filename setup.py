from setuptools import setup, find_packages

kwargs = {
    'name': 'django-vocabulary',
    'version': '.4',
    'author': 'Jeff Miller',
    'author_email': 'millerjm1@email.chop.edu',
    'description': 'A vocabulary browser for django that displays tree structured data. Includes database back-end and front-end for AudGenDB framework.',
    'license': 'BSD',
    'keywords': 'AudGenDB avocado django vocabulary browser',
    'install_requires': ['django>=1.2','django-avocado>=1.0'],
    'packages': find_packages(exclude=('*.tests', '*.tests.*')),
    'package_data':{'static':['*.js','*.css']},
    'exclude_package_data': {
        '': ['fixtures/*']
    },
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
}

setup(**kwargs)

instructions = """This is a django application, and needs to be placed in the INSTALLED_APPS array in your settings.py file. It also has additional requirements:
1. It has its own static files that must be made available. It looks in the static directory of your django project for plugins/vb/.
2. This application has its own models and expects find those models in a database called "vocabulary" in the database dictionary of your settings file.
3. The urls.py in this application needs to be included in the main urls.py for the project so that the urls.py is found at /plugins/vb/
"""
print instructions