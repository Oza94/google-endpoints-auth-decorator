from setuptools import setup

setup(name='endpointsauth',
    version='0.1',
    description='A simple authentication utility module for Google App Engine endpoints',
    url='http://github.com/path/to/change',
    author='Pierre Beaujeu',
    author_email='beaujeup@essilor.fr',
    license='MIT',
    packages=['endpointsauth'],      
    install_requires=[
        'httplib2',
        'oauth2client==1.5.2',
        'google-api-python-client',
        'google-endpoints',
    ],
    zip_safe=False)