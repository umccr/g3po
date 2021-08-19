import logging
import os

from gen3.auth import Gen3Auth
from gen3.index import Gen3Index

from g3po import GEN3_URL

logger = logging.getLogger(__name__)


def build_auth(cred=None):
    auth = Gen3Auth()
    if cred is not None:
        assert os.path.exists(cred), f"{cred} not found"
        auth = Gen3Auth(GEN3_URL, refresh_file=cred)
    return auth


def build_public_indexer():
    return Gen3Index(GEN3_URL)


def build_auth_indexer(cred=None):
    auth = build_auth(cred)
    return Gen3Index(GEN3_URL, auth_provider=auth)
