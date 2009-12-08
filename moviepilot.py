# Released into the Public Domain by tav <tav@espians.com>

"""
MoviePilot API

"""

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        raise RuntimeError("Cannot find a valid JSON implementation.")

from urllib import urlopen, urlencode

class MoviePilotResource(dict):
    """Return a dict which provides item access via the .attribute notation."""

    __cmp__ = dict.__cmp__
    __contains__ = dict.__contains__
    __delitem__ = dict.__delitem__
    __eq__ = dict.__eq__
    __ge__ = dict.__ge__
    __getitem__ = dict.__getitem__
    __gt__ = dict.__gt__
    __hash__ = dict.__hash__
    __iter__ = dict.__iter__
    __le__ = dict.__le__
    __len__ = dict.__len__
    __lt__ = dict.__lt__
    __ne__ = dict.__ne__
    __repr__ = dict.__repr__
    __str__ = dict.__str__

    clear = dict.clear
    copy = dict.copy
    fromkeys = dict.fromkeys
    get = dict.get
    has_key = dict.has_key
    items = dict.items
    iteritems = dict.iteritems
    iterkeys = dict.iterkeys
    itervalues = dict.itervalues
    keys = dict.keys
    pop = dict.pop
    popitem = dict.popitem
    setdefault = dict.setdefault
    update = dict.update
    values = dict.values

    def __getattr__(self, key):
        if key in self:
            return self.__getitem__(key)
        try:
            return self.__dict__.__getitem__(key)
        except KeyError:
            raise AttributeError(
                "%r has no attribute %r" % (self.__class__.__name__, key)
                )

    def __setattr__(self, key, value):
        if key not in dict.__dict__: # maybe not the best way?
            return self.__setitem__(key, value)
        return self.__dict__.__setitem__(key, value)

class DownloadError(Exception):
    """Download Error."""

def urlfetch_default(url):
    return urlopen(url).read()

try:
    from google.appengine.api import urlfetch
except ImportError:
    def urlfetch_ae(url):
        raise RuntimeError("Couldn't import App Engine's urlfetch.")
else:
    def urlfetch_ae(url):
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return result.content
        raise DownloadError(result.status_code)

def attrify(data):
    """Turn a standard JSON hash dataset into a recursive MoviePilotResource dict."""

    retval = MoviePilotResource()
    for key, value in data.items():
        if isinstance(value, dict):
            retval[key] = attrify(value)
        elif isinstance(value, list):
            retval[key] = attrify_seq(value)
        else:
            retval[key] = value
    return retval

def attrify_seq(seq):

    nval = []
    for val in seq:
        if isinstance(val, dict):
            nval.append(attrify(val))
        elif isinstance(val, list):
            nval.append(attrify_seq(val))
        else:
            nval.append(val)
    return nval


class MoviePilot(object):
    """MoviePilot API."""

    def __init__(
        self, api_key, base_url='http://uk.moviepilot.com', appengine=False
        ):

        self._base_url = base_url
        self._base_len = len(self._base_url + '/movies/')
        self._api_key = api_key

        if appengine:
            if callable(appengine):
                self._urlfetch = appengine
            else:
                self._urlfetch = urlfetch_ae
        else:
            self._urlfetch = urlfetch_default

    def call(self, path, params=None):
        if params:
            params = params.copy()
        else:
            params = {}
        params['api_key'] = self._api_key
        url = "%s/%s.json?%s" % (self._base_url, path, urlencode(params))
        data = self._urlfetch(url)
        return attrify(json.loads(data))
    
    def get(self, id, service=None, casts=False, related=False):
        if isinstance(id, MoviePilotResource):
            if not hasattr(id, 'restful_url'):
                raise ValueError("The given id is not a valid Movie reference.")
            id = id.restful_url[self._base_len:]
        else:
            if service:
                service = service.lower()
                if service == 'imdb':
                    id = int(id)
                id = '%s-id-%s' % (service, id)
        if casts:
            return self.call("movies/%s/casts" % id)
        if related:
            return self.call("movies/%s/neighbourhood" % id)
        return self.call("movies/%s" % id)

    def search(self, term, type='movies'):
        return self.call("searches/%s" % type, {"q": term})




# m = MoviePilot('your-api-key', base_url='http://www.moviepilot.de')
# m = MoviePilot('your-api-key')
# matrix = m.search('matrix')

# print matrix.movies[1].display_title

# s = m.search('Robert de niro', 'people')

# print s.people[0].date_of_birth

# id = matrix.movies[1].alternative_identifiers.imdb
# s = m.get(id, 'imdb', casts=True)

# s = m.get(matrix.movies[1], 'imdb', casts=True)

# r = m.get(matrix.movies[1], related=True)

# for i in r.item_neighbours:
    #if hasattr(i, 'display_title'):
#    print i.neighbour_movie.display_title
#    print i.distance

# print r.item_neighbours[0].keys()
