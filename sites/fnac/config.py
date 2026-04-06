"""Fnac.fr constants."""

import os

SITE_ID = "fnac"
SUPPORTS_API = True

BASE_URL = "https://www.fnac.com"
BASKET_ADD_URL = f"{BASE_URL}/basket/add"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

REFERENTIAL_FR = "1"
DEFAULT_OFFER = "00000000-0000-0000-0000-000000000000"

# Per-account cookies: set FNAC_COOKIE_LABEL to the registry ``cookie_label`` (often same as account label).
COOKIE_LABEL = os.environ.get("FNAC_COOKIE_LABEL", "fnac")

# Manual login entry (path may change — see sites.fnac.endpoints.LOGON_PAGE).
FNAC_LOGIN_URL = os.environ.get(
    "FNAC_LOGIN_URL",
    "https://secure.fnac.com/interaction/connection",
)
