import pandas as pd
import responses

from apis import SHARKAPI


@responses.activate
def test_get_datasets_success():
    api = SHARKAPI()
    url = api.base_url.rstrip("/") + "/datasets"
    sample = [{"id": "PHYTO", "name": "Phytoplankton"}]
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_datasets()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["id"] == "PHYTO"


@responses.activate
def test_get_datasets_fallback():
    api = SHARKAPI()
    url = api.base_url.rstrip("/") + "/datasets"
    responses.add(responses.GET, url, status=500)

    df = api.get_datasets()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    # When the API fails, fallback data should be used and metadata attached
    assert df.attrs.get("api_fallback") is True
    assert df.attrs.get("api_error") is not None


@responses.activate
def test_search_data_error_sets_api_error_attr():
    api = SHARKAPI()
    url = api.base_url.rstrip("/") + "/data"
    responses.add(responses.GET, url, status=500)

    df = api.search_data(limit=1)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert df.attrs.get("api_error") is not None


@responses.activate
def test_download_dataset_writes_file(tmp_path):
    api = SHARKAPI()
    dataset = "PHYTO"
    url = api.base_url.rstrip("/") + f"/datasets/{dataset}/download"
    content = b"Test,CSV,Content\n1,2,3"
    responses.add(
        responses.GET,
        url,
        body=content,
        status=200,
        content_type="application/octet-stream",
    )

    out = tmp_path / "out.dat"
    ok = api.download_dataset(dataset, str(out))
    assert ok is True
    assert out.exists()
    assert out.read_bytes() == content


@responses.activate
def test_search_data_returns_dataframe():
    api = SHARKAPI()
    url = api.base_url.rstrip("/") + "/data"
    sample = [{"value": 1}, {"value": 2}]
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.search_data(limit=2)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
