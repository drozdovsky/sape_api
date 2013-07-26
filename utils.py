# coding: utf-8
"""
SAPE API v.1
------------

Simple Python API to SAPE's XML-RPC interface

Michael Drozdovsky, 2013
drozdovsky.com
"""
import weakref
import xmlrpclib


# TODO: Extract to another file
class CookieTransport(xmlrpclib.SafeTransport):
    """
    Overides request add cookies from previous request.
    """
    def __init__(self):
        xmlrpclib.Transport.__init__(self)
        self.cookie = None

    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request
        h = self.make_connection(host)

        if verbose:
            h.set_debuglevel(1)

        try:
            self.send_request(h, handler, request_body)
            self.send_host(h, host)
            self.send_user_agent(h)

            if self.cookie is not None:
                h.putheader("Cookie", self.cookie)

            self.send_content(h, request_body)

            response = h.getresponse(buffering=True)
            if response.status == 200:
                self.cookie = response.getheader('Set-Cookie') or self.cookie
                self.verbose = verbose

                return self.parse_response(response)
        except Exception:
            # All unexpected errors leave connection in
            # a strange state, so we clear it.
            self.close()
            raise

        #discard any response data and raise exception
        if (response.getheader("content-length", 0)):
            response.read()
        raise xmlrpclib.ProtocolError(
            host + handler,
            response.status, response.reason,
            response.msg,
        )
#######


class SapeBaseInstance(object):
    """
    Class for base SAPE API instance
    """
    def __init__(self, sape_api):
        self.api = sape_api()
        self.single_properties = []

    def sape_call(self, method_name, *params):
        """
        Call sape method with required params
        """
        method = getattr(self.api, method_name)
        return method(*params)

    def __getattr__(self, name):
        """
        Simple attribute getter
        """
        ret = self.single_properties.get(name)
        if not ret:
            raise AttributeError('No attribute named "%s" found!' % name)
        return ret


class SapePage(SapeBaseInstance):
    """
    Holds information about one site
    page
    """
    def __init__(self, sape_api):
        self.api = sape_api()

    def activate(self):
        pass

    def exclude(self):
        pass

    def purge(self):
        pass


class SapeSite(SapeBaseInstance):
    """
    Holds information about one site
    """
    STATUS = ('NEW', 'IND', 'OK', 'IND_NOW', '')
    def __init__(self, sape_api, site_info):
        super(SapeUser, self).__init__(sape_api)
        self.single_properties = site_info
        print site_info

    def update(self):
        # update site parameters
        pass

    @property
    def regions(self):
        # get site regions
        pass

    @property
    def pages(self):
        # site pages
        pass

    @property
    def links(self):
        # get site links
        pass

class SapeUser(SapeBaseInstance):
    """
    Holds main information about SAPE user account,
    such as:
    - login
    - email
    """
    def __init__(self, sape_api):
        super(SapeUser, self).__init__(sape_api)

        self.id = self.api.user_id
        self.single_properties = self.sape_call('sape.get_user')

    @property
    def balance(self):
        """
        Get user's balance
        """
        value = self.sape_call('sape.get_balance')
        value_real = self.sape_call('sape.get_balance_real')

        return value, value_real

    @property
    def balance_locks(self):
        """
        Get balance locks
        """
        return self.sape_call('sape.get_balance_locks')

    def get_bills(self, year, month=None, day=None, user_id=False):
        """
        Get user bills
        """
        return self.sape_call('sape.get_bills', year, month, day, user_id)

    def get_sites(self):
        """
        Get user sites
        """
        sites = self.sape_call('sape.get_sites')
        ret = [SapeSite(site) for site in sites]

        return ret


class SapeAPI(xmlrpclib.ServerProxy):
    """
    Main class for SAPE API
    """

    SAPE_URL = 'http://api.sape.ru/xmlrpc/'

    def __init__(self, login, password, uri=SAPE_URL, *args, **kwargs):
        kwargs['transport'] = CookieTransport()
        kwargs['allow_none'] = True
        xmlrpclib.ServerProxy.__init__(self, uri, *args, **kwargs)

        # authorize to SAPE with provided login and password
        self.user_id = self.sape.login(login, password, False)

    @property
    def user(self):
        """
        Gets sape user associated with account
        """
        return SapeUser(weakref.ref(self))

