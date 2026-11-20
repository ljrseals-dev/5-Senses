"""Tests for n-gram language model."""

from body_of_secrets.language import NGramModel


def test_train_and_generate():
    model = NGramModel(n=3, level="word")
    texts = [
        "the cat sat on the mat",
        "the dog sat on the log",
        "the cat sat on the log",
    ]
    model.train(texts)
    assert len(model.vocab) > 0
    generated = model.generate(length=10, seed="the cat")
    assert isinstance(generated, str)
    assert len(generated) > 0


def test_continuations():
    model = NGramModel(n=2, level="word")
    model.train(["the cat sat", "the dog ran", "the cat ran"])
    conts = model.most_likely_continuations("the", k=3)
    assert len(conts) > 0
    tokens = [t for t, _ in conts]
    assert "cat" in tokens or "dog" in tokens


def test_perplexity():
    model = NGramModel(n=2, level="word")
    model.train(["a b c a b c a b c"])
    ppl = model.perplexity("a b c")
    assert ppl > 0
