from urllib.parse import urlparse
from flask import request

def is_safe_next_url(target):
    if not target: return False
    ref=urlparse(request.host_url); test=urlparse(target if '://' in target else request.host_url.rstrip('/')+'/'+target.lstrip('/'))
    return test.scheme in {'http','https'} and test.netloc == ref.netloc
