import os
import pytest
import pandas as pd

from apis import FreshwaterEcologyAPI


@pytest.mark.skipif(
    not os.getenv("FWE_API_KEY"),
    reason="Integration test for FreshwaterEcology API requires FWE_API_KEY environment variable",
)
def test_fwe_live_flow():
    """Integration test that runs only when FWE_API_KEY is provided as an env var.

    This test will perform the following against the live API:
    - check status
    - authenticate (exchange API key for token)
    - run a simple query (organismgroup=fi, genus=Salmo, limit=5)

    NOTE: This test does NOT store the API key in the repository. Set FWE_API_KEY locally
    (or export it in your CI) before running integration tests.
    """
    key = os.getenv("FWE_API_KEY")
    api = FreshwaterEcologyAPI(api_key=key)

    status = api.get_status()
    assert isinstance(status, dict)

    token = api.authenticate()
    # token should be a string when auth succeeds
    assert token is None or isinstance(token, str)

    # perform a query and verify we get a DataFrame back (may be empty)
    df = api.query(organismgroup="fi", genus="Salmo", limit=5)
    assert isinstance(df, pd.DataFrame)
    # If API returns data, expect at least the taxon field
    if not df.empty:
        assert "taxon" in df.columns or "scientificName" in df.columns
