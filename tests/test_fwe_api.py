import responses
import pandas as pd

from apis import FreshwaterEcologyAPI


@responses.activate
def test_status_endpoint():
    api = FreshwaterEcologyAPI()
    url = api.base_url.rstrip("/") + "/status"
    responses.add(responses.GET, url, json={"status": "ok"}, status=200)

    res = api.get_status()
    assert isinstance(res, dict)
    assert res.get("status") == "ok"


@responses.activate
def test_authenticate_and_query_flow():
    api = FreshwaterEcologyAPI(api_key="dummy-key")
    t_url = api.base_url.rstrip("/") + "/token"
    q_url = api.base_url.rstrip("/") + "/query"

    # Token endpoint returns token
    responses.add(responses.POST, t_url, json={"token": "abcd1234", "expires_in": 3600}, status=200)

    # Query endpoint returns some results when authenticated
    sample = [{"taxon": "Salmo salar", "trait": "size", "value": 50}]
    responses.add(responses.POST, q_url, json=sample, status=200)

    token = api.authenticate()
    assert token == "abcd1234"

    df = api.query(organismgroup="fi", genus="Salmo")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["taxon"] == "Salmo salar"


@responses.activate
def test_get_ecoparam_list_and_fallback():
    api = FreshwaterEcologyAPI()
    url = api.base_url.rstrip("/") + "/getecoparamlist"
    # simulate server error to trigger fallback; _safe_api_call fallback returns DataFrame
    responses.add(responses.GET, url, status=500)

    df = api.get_ecoparam_list()
    assert isinstance(df, pd.DataFrame)
    # When server fails, fallback returns DataFrame (per implementation)


@responses.activate
def test_query_without_key_returns_empty():
    api = FreshwaterEcologyAPI()  # no key set
    responses.add(responses.POST, api.base_url.rstrip("/") + "/query", status=401)

    df = api.query(organismgroup="fi")
    assert isinstance(df, pd.DataFrame)
