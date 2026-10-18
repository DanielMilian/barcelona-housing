from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed on client IP, not the API key: a rotating fake key must not dodge the limit,
# and requests with a bad key count too (throttles key guessing).
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
