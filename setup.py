from setuptools import setup, find_packages

kwargs = {
    'name': 'django-vocab',
    'version': '.4',
    'author': 'Jeff Miller',
    'author_email': 'millerjm1@email.chop.edu',
    'description': 'A vocabulary browser for django that displays tree structured data. Includes database back-end and front-end for AudGenDB framework.',
    'license': 'BSD',
    'keywords': 'AudGenDB avocado django vocabulary browser',
    'packages': find_packages(exclude=('*.tests', '*.tests.*')),
    'package_data':{'vocabulary':['static/js/*.js','static/css/*.css','static/img/*.*','static/img/icons/*.*']},
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
3. The urls.py in this application needs to be included in the main urls.py for the project so that the urls.py is found at /plugins/vb/
"""
print instructions
