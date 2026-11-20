"""Tests for classical neural components."""

from body_of_secrets.neural import HopfieldNetwork, MLP, demo_hopfield, demo_xor


def test_hopfield_store_and_recall():
    patterns = [
        [1, 1, 1, 1, -1, -1, -1, -1],
        [1, -1, 1, -1, 1, -1, 1, -1],
    ]
    net = HopfieldNetwork(n_units=8)
    net.store(patterns)

    # Perfect cue
    recalled = net.recall(patterns[0])
    assert net.overlap(recalled, patterns[0]) > 0.9

    # Mildly corrupted cue
    cue = patterns[0][:]
    cue[0] = -cue[0]
    recalled = net.recall(cue)
    assert net.overlap(recalled, patterns[0]) > 0.5


def test_hopfield_demo():
    result = demo_hopfield()
    assert "Hopfield" in result
    assert "overlap" in result


def test_mlp_xor():
    mlp = MLP(n_input=2, n_hidden=4, n_output=1, learning_rate=0.5)
    data = [
        ([0.0, 0.0], [0.0]),
        ([0.0, 1.0], [1.0]),
        ([1.0, 0.0], [1.0]),
        ([1.0, 1.0], [0.0]),
    ]
    history = mlp.train(data, epochs=400)
    # Should learn something useful
    assert history[-1] < history[0]
    pred = mlp.predict([0.0, 1.0])[0]
    assert 0.0 <= pred <= 1.0


def test_mlp_demo():
    result = demo_xor()
    assert "MLP" in result
    assert "XOR" in result
