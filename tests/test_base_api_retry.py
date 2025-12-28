import requests

from apis.base_api import BaseMarineAPI


def test_default_session_has_retry_adapter():
    # Create a small subclass to instantiate BaseMarineAPI (abstract)
    class Dummy(BaseMarineAPI):
        def get_taxa(self, *args, **kwargs):
            return []

    d = Dummy("https://example.org/")
    # Check that adapters are mounted for http/https
    assert "https://" in d.session.adapters
    assert "http://" in d.session.adapters
    # The adapter should be a requests.adapters.HTTPAdapter
    assert isinstance(d.session.adapters["https://"], requests.adapters.HTTPAdapter)
