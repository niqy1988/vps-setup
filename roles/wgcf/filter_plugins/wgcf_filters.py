import base64
from urllib.parse import urlparse, parse_qs

def url_query(url):
    return parse_qs(urlparse(url).query)

def decode_wgcf_reserved(client_id):
    return [x for x in base64.b64decode(client_id)]

class FilterModule(object):
    def filters(self):
        return {
            'url_query': url_query,
            'decode_wgcf_reserved': decode_wgcf_reserved,
        }
