#!/usr/bin/env python
from distutils.core import setup

setup(
    name='django_helpful',
    version="0.3.1",
    author='Raphael Kimmig',
    author_email='raphael.kimmig@ampad.de',
    url = 'https://github.com/RaphaelKimmig/django_helpful',

    description = 'Helpful stuff for django development',

    license = 'BSD',
    packages=['django_helpful', 'django_helpful.templatetags'],
    requires = ['django (>=1.2)'],
    extras_require = {
        'views':  ["django-extra-views", "django-crispy-forms"]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
    ],
)
