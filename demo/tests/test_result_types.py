import pytest


def test_passed():
    assert True


def test_failed():
    assert False


# TODO: have this added to demo
# def test_error():
#    raise NotImplementedError()


@pytest.mark.skip
def test_skipped():
    pass


@pytest.mark.xfail
def test_expected_failures():
    assert False


@pytest.mark.xfail
def test_unexpected_passes():
    assert True


@pytest.mark.flaky(reruns=1)
def test_rerun():
    assert False
