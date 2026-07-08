import app.external.musicbrainz as musicbrainz
import app.external.open_library as open_library
import app.external.tmdb as tmdb


async def _fake_tmdb_search(query, page=1):
    return [
        {
            "id": 155,
            "title": "The Dark Knight",
            "release_date": "2008-07-16",
            "genre_ids": [28, 80, 18],
            "overview": "Batman raises the stakes...",
            "poster_path": "/poster.jpg",
            "popularity": 84.2,
        }
    ]


async def _fake_ol_search(query, limit=20):
    return [
        {
            "key": "/works/OL12345W",
            "title": "Dune",
            "author_name": ["Frank Herbert"],
            "first_publish_year": 1965,
            "subject": ["Science fiction"],
            "cover_i": 12345,
            "edition_count": 200,
        }
    ]


async def _fake_mb_search(query, limit=20):
    return [
        {
            "id": "abc-123-mbid",
            "title": "Bohemian Rhapsody",
            "artist-credit": [{"name": "Queen"}],
            "first-release-date": "1975-10-31",
            "score": 100,
        }
    ]


def _patch_all_providers(monkeypatch):
    monkeypatch.setattr(tmdb, "search_movies", _fake_tmdb_search)
    monkeypatch.setattr(open_library, "search_books", _fake_ol_search)
    monkeypatch.setattr(musicbrainz, "search_recordings", _fake_mb_search)


async def test_search_requires_auth(client):
    resp = await client.get("/search", params={"q": "test"})
    assert resp.status_code == 401


async def test_search_fans_out_to_all_domains(client, auth_headers, monkeypatch):
    _patch_all_providers(monkeypatch)
    resp = await client.get("/search", params={"q": "test"}, headers=auth_headers)
    assert resp.status_code == 200
    titles = {r["title"] for r in resp.json()["results"]}
    assert titles == {"The Dark Knight", "Dune", "Bohemian Rhapsody"}


async def test_search_filtered_by_domain_skips_other_providers(client, auth_headers, monkeypatch):
    monkeypatch.setattr(tmdb, "search_movies", _fake_tmdb_search)

    called = False

    async def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(open_library, "search_books", fail_if_called)
    monkeypatch.setattr(musicbrainz, "search_recordings", fail_if_called)

    resp = await client.get("/search", params={"q": "test", "domain": "movie"}, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1
    assert called is False


async def test_one_provider_failing_does_not_break_search(client, auth_headers, monkeypatch):
    monkeypatch.setattr(tmdb, "search_movies", _fake_tmdb_search)
    monkeypatch.setattr(open_library, "search_books", _fake_ol_search)

    async def broken(*args, **kwargs):
        raise RuntimeError("MusicBrainz is down")

    monkeypatch.setattr(musicbrainz, "search_recordings", broken)

    resp = await client.get("/search", params={"q": "test"}, headers=auth_headers)
    assert resp.status_code == 200
    titles = {r["title"] for r in resp.json()["results"]}
    assert titles == {"The Dark Knight", "Dune"}


async def test_repeat_search_is_served_from_cache(client, auth_headers, monkeypatch):
    call_count = 0

    async def counting_search(query, page=1):
        nonlocal call_count
        call_count += 1
        return []

    monkeypatch.setattr(tmdb, "search_movies", counting_search)
    monkeypatch.setattr(open_library, "search_books", counting_search)
    monkeypatch.setattr(musicbrainz, "search_recordings", counting_search)

    await client.get("/search", params={"q": "cache-me"}, headers=auth_headers)
    await client.get("/search", params={"q": "cache-me"}, headers=auth_headers)
    assert call_count == 3  # one call per provider, only on the first request
