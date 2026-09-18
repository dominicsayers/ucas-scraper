from v3.utils.fetcher.http_verb import HttpVerb


def test_get_value() -> None:
    assert HttpVerb.GET.value == "get"


def test_post_value() -> None:
    assert HttpVerb.POST.value == "post"
