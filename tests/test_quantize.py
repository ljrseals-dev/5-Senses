import numpy as np
import pytest

from body_of_secrets.compression.quantize import quantize_cdf


@pytest.mark.parametrize("total", [256, 512, 4096])
@pytest.mark.parametrize("alpha", [0.01, 0.1, 1.0])
def test_dirichlet_distributions_preserve_total_and_minimum(total, alpha):
    for seed in range(300):
        probs = np.random.default_rng(seed).dirichlet(np.full(256, alpha))
        freqs, cdf = quantize_cdf(probs, total=total)
        assert int(freqs.sum()) == total
        assert np.all(freqs >= 1)
        assert cdf[0] == 0
        assert cdf[-1] == total
        np.testing.assert_array_equal(np.diff(cdf), freqs)


def test_one_hot_distribution_reserves_one_count_per_other_symbol():
    probs = np.zeros(256)
    probs[42] = 1.0
    freqs, cdf = quantize_cdf(probs)
    assert int(freqs.sum()) == 4096
    assert freqs[42] == 3841
    assert np.all(np.delete(freqs, 42) == 1)
    assert cdf[-1] == 4096


def test_zero_distribution_becomes_uniform():
    freqs, cdf = quantize_cdf(np.zeros(256))
    assert int(freqs.sum()) == 4096
    assert np.all(freqs == 16)
    assert cdf[-1] == 4096


def test_invalid_total_below_minimum_budget_is_rejected():
    with pytest.raises(ValueError):
        quantize_cdf(np.ones(256), total=255)


def test_non_finite_probabilities_are_rejected():
    with pytest.raises(ValueError):
        quantize_cdf([0.5, float("nan")])


@pytest.mark.parametrize(
    "probs",
    [[], np.ones((2, 2)), [-0.1, 1.1], [0.5, float("inf")], [0.5, -float("inf")]],
)
def test_invalid_probability_shapes_and_values_are_rejected(probs):
    with pytest.raises(ValueError):
        quantize_cdf(probs)


def test_two_symbol_input_is_valid_with_default_total():
    freqs, cdf = quantize_cdf([0.25, 0.75])
    assert freqs.tolist() == [1024, 3072]
    assert cdf.tolist() == [0, 1024, 4096]


def test_float32_probabilities_are_supported():
    probs = np.asarray([0.1, 0.2, 0.7], dtype=np.float32)
    freqs, cdf = quantize_cdf(probs)
    assert int(freqs.sum()) == 4096
    assert np.all(freqs >= 1)
    assert cdf[-1] == 4096


def test_ties_are_resolved_by_lowest_symbol_index():
    freqs, _ = quantize_cdf(np.ones(250), total=4096)
    assert np.all(freqs[:154] == 17)
    assert np.all(freqs[154:] == 16)


def test_calls_are_deterministic():
    probs = np.random.default_rng(123).dirichlet(np.ones(256))
    first = quantize_cdf(probs)
    second = quantize_cdf(probs)
    np.testing.assert_array_equal(first[0], second[0])
    np.testing.assert_array_equal(first[1], second[1])


@pytest.mark.parametrize("bad_total", [0, -1, 4.5, True])
def test_total_must_be_an_integer(bad_total):
    with pytest.raises(ValueError):
        quantize_cdf([0.5, 0.5], total=bad_total)


@pytest.mark.parametrize("bad_min_freq", [0, -1, 1.5, False])
def test_min_freq_must_be_a_positive_integer(bad_min_freq):
    with pytest.raises(ValueError):
        quantize_cdf([0.5, 0.5], min_freq=bad_min_freq)


def test_large_finite_weights_do_not_overflow_normalization():
    freqs, cdf = quantize_cdf([1e308, 1e308, 1e307])
    assert int(freqs.sum()) == 4096
    assert cdf[-1] == 4096
