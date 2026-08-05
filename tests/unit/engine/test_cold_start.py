import pytest

from app.engine.cold_start import smooth_likelihood
from app.engine.models import LikelihoodEntry


def test_high_sample_uses_raw_likelihood():
    entry = LikelihoodEntry(likelihood=0.95, sample_size=100)
    assert smooth_likelihood(entry) == pytest.approx(0.95)


def test_low_sample_shrinks_toward_neutral():
    entry = LikelihoodEntry(likelihood=1.0, sample_size=1)
    smoothed = smooth_likelihood(entry)
    assert 0.5 < smoothed < 1.0


def test_missing_entry_defaults_to_neutral():
    assert smooth_likelihood(None) == pytest.approx(0.5)
