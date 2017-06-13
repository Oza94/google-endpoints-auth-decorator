"""Google Cloud Endpoints Authenticator

Provide an utility class to easily handle some common authorization
cases when using Google Cloud Endpoints on App Engine for Python
within a Google Apps environment.

This class can check for 4 levels of authorization :
- None : the request is not authorized at all
- Google : the request is authorized using a Google account that
does not belongs to the provided Google Apps domain
- Domain : the request is authorized using a Google Apps account
that belongs to provided Google Apps domain
- Administrator : the request is authorized using a Google Apps account
that is a member of a provided administrator Google Groups

Example :
    authenticator = EndpointsAuthenticator('client_id@gserviceaccount.com',
        '/path/to/private.pem',
        'CUSTOMER_ID',
        'superadmin@acme.com',
        'administrators@groups.acme.com',
        cache=memcache,
        cache_prefix='auth')

    # later in your API definition
    @endpoints.api(name='myapi', version='v1')
    class MyApi(remote.Service):
        @endpoints.method(
            message_types.VoidMessage,
            message_types.VoidMessage,
            path='foo/bar',
            http_method='GET',
            name='foobar')
        # here is the import bit of code
        @authenticator.ensure(auth_level=AuthLevel.ADMINISTRATOR)
        def foobar(self, request):
            # does nothing
            return message_types.VoidMessage()


"""

from enum import Enum
import httplib2
import json
from googleapiclient.discovery import build
from googleapiclient.http import HttpError
from oauth2client.client import SignedJwtAssertionCredentials
import endpoints
import logging

def read_key(keypath):
    """simply read a pem file and returns content"""
    f = file(keypath, 'rb')
    key = f.read()
    f.close()

    return key

DOMAINS_SCOPE = 'https://www.googleapis.com/auth/admin.directory.domain.readonly'
GROUPS_SCOPE = 'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
SCOPES = '%s %s' % (DOMAINS_SCOPE, GROUPS_SCOPE)

DOMAINS_CACHE_DURATION = 3600 # 60-minutes
GROUPS_CACHE_DURATION = 300 # 5-minutes

class AuthLevel(Enum):
    NONE = 0
    GOOGLE = 1
    DOMAIN = 2
    ADMINISTRATOR = 3

class EndpointsAuthenticator:
    def __init__(self, client_id, key_path, customer_id, super_admin_account, admin_group, dangerous_token_key=None,
        dangerous_tokens=[], cache=None, cache_prefix='auth'):
        self.client_id = client_id
        self.key_path = key_path
        self.cache = cache
        self.cache_prefix = cache_prefix
        self.super_admin_account = super_admin_account
        self.admin_group = admin_group
        self.dangerous_token_key = dangerous_token_key
        self.dangerous_tokens = dangerous_tokens
        self.customer_id = customer_id
        self.service = None

    def get_service(self):
        if self.service is None:
            key_content = read_key(self.key_path)
            credentials = SignedJwtAssertionCredentials(self.client_id, key_content, SCOPES,
                sub=self.super_admin_account)

            # initialize and authorize http client
            http = httplib2.Http(cache=self.cache)
            http = credentials.authorize(http)

            self.service = build('admin', 'directory_v1', http=http)

        return self.service

    def ensure(self, auth_level=AuthLevel.NONE):

        def ensure_decorator(func):
            def func_wrapper(*args, **kwargs):
                self.assert_current_user(auth_level, getattr(args[1], self.dangerous_token_key))
                return func(*args, **kwargs)
            # copy docstring since its required by endpoints
            func_wrapper.__doc__ = func.__doc__
            return func_wrapper
        return ensure_decorator

    def assert_current_user(self, auth_level=AuthLevel.NONE, access_token=None):
        logging.info('[assert_current_user] %s required' % auth_level)
        if auth_level == AuthLevel.NONE:
            return

        if access_token is not None and access_token in self.dangerous_tokens:
            logging.info('[assert_current_user] user authorized using access_token "%s"' % access_token)
            return

        current_user = endpoints.get_current_user()

        if current_user is None:
            logging.info('[assert_current_user] current_user is None, raising 401')
            raise endpoints.UnauthorizedException('Invalid or None token.')
        else:
            logging.info('[assert_current_user] user authorized as %s' % current_user.email())

        email = current_user.email()
        domain = email.split('@')[-1]

        if auth_level == AuthLevel.DOMAIN:
            domains = self.get_domains()

            if domain not in domains:
                logging.info('[assert_current_user] (OK) %s does NOT belongs to the domain, raising 403' % domain)
                raise endpoints.ForbiddenException('Please authorize using a domain account.')
            else:
                logging.info('[assert_current_user] (OK) %s belongs to the domain' % domain)

        if auth_level == AuthLevel.ADMINISTRATOR:
            if self.is_administrator(email) == False:
                logging.info('[assert_current_user] (KO) %s does NOT belong to the admin group %s, raising 403' % (email, self.admin_group))
                raise endpoints.ForbiddenException('Please use an administrator account (%s)' % self.admin_group)
            else:
                logging.info('[assert_current_user] (OK) %s belongs to the admin group %s' % (email, self.admin_group))

    def is_administrator(self, user_email):
        is_administrator = False

        if self.cache is not None:
            cache_key = '%s:admin:%s' % (self.cache_prefix, user_email)
            cached = self.cache.get(cache_key)

            if cached is not None:
                is_administrator = json.loads(cached)
            else:
                is_administrator = self.test_membership(self.admin_group, user_email)
                self.cache.set(cache_key, json.dumps(is_administrator), GROUPS_CACHE_DURATION)
        else: is_administrator = self.test_membership(self.admin_group, user_email)

        return is_administrator


    def test_membership(self, group_email, user_email):
        return True if self.fetch_membership(group_email, user_email) is not None else False

    def fetch_membership(self, group_email, user_email):
        service = self.get_service()

        try:
            return service.members().get(groupKey=group_email, memberKey=user_email).execute()
        except HttpError:
            return None

    def get_domains(self):
        domains = None

        if self.cache is not None:
            cache_key = '%s:domains' % self.cache_prefix
            cached = self.cache.get(cache_key)

            if cached is not None:
                domains = json.loads(cached)
            else:
                domains = self.fetch_domains()
                self.cache.add(cache_key, json.dumps(domains), DOMAINS_CACHE_DURATION)
        else: domains = self.fetch_domains()

        return domains

    def fetch_domains(self):
        service = self.get_service()
        domains_feed = service.domains().list(customer=self.customer_id).execute()
        domains = []

        # filter out invalid domains
        for domain_entry in domains_feed.get('domains'):
            if domain_entry.get('verified') == True:
                domains.append(domain_entry.get('domainName'))

        return domains

