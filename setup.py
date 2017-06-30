from setuptools import setup

setup(name='endpointsauth',
    version='0.2',
    description='A simple authentication utility module for Google App Engine endpoints',
    url='http://github.com/path/to/change',
    author='Pierre Beaujeu',
    author_email='beaujeup@essilor.fr',
    license='MIT',
    packages=['endpointsauth'],      
    install_requires=[
        'httplib2',
        'oauth2client==3.0.0',
        'google-api-python-client',
        'google-endpoints',
    ],
    zip_safe=False)