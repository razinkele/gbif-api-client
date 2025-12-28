import pandas as pd
import responses

from apis import PlanktonToolboxAPI


@responses.activate
def test_get_plankton_taxa_fallback_to_mock():
    api = PlanktonToolboxAPI()
    url = api.base_url.rstrip("/") + "/taxa"

    # Simulate that endpoint returns error; method should fallback to mock data
    responses.add(responses.GET, url, status=500)

    df = api.get_plankton_toolbox_taxa()
    assert isinstance(df, pd.DataFrame)
    # Should return mock data
    assert not df.empty


def test_read_ptbx_csv(tmp_path):
    api = PlanktonToolboxAPI()
    csv = tmp_path / "sample.tsv"
    csv.write_text("name\tbiovolume\nX\t100")

    df = api.read_ptbx(str(csv))
    assert not df.empty
    assert "name" in df.columns
