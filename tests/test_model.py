import os
import pytest
from PIL import Image
from picseek.model import get_model, reset_model, MockCLIPModel


@pytest.fixture(autouse=True)
def use_mock_model(monkeypatch):
    """All model tests use mock to avoid loading 700MB model."""
    monkeypatch.setenv("PICSEEK_MOCK_MODEL", "1")
    reset_model()
    yield
    reset_model()


def test_mock_model_loads():
    model = get_model()
    assert isinstance(model, MockCLIPModel)
    assert model.model is not None
    assert model.processor is not None


def test_encode_image_returns_512d_vector(tmp_path):
    img = Image.new("RGB", (64, 64), color="red")
    img_path = str(tmp_path / "red.png")
    img.save(img_path)
    model = get_model()
    vec = model.encode_image(img_path)
    assert len(vec) == 512
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 0.01


def test_encode_text_returns_512d_vector():
    model = get_model()
    vec = model.encode_text("一只猫")
    assert len(vec) == 512
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 0.01


def test_encode_batch_images(tmp_path):
    paths = []
    for color in ["red", "green", "blue"]:
        img = Image.new("RGB", (64, 64), color=color)
        p = str(tmp_path / f"{color}.png")
        img.save(p)
        paths.append(p)
    model = get_model()
    vecs = model.encode_images(paths)
    assert len(vecs) == 3
    assert all(len(v) == 512 for v in vecs)


def test_different_inputs_produce_different_vectors():
    model = get_model()
    vec1 = model.encode_text("猫")
    vec2 = model.encode_text("狗")
    assert vec1 != vec2


def test_same_input_produces_same_vector():
    model = get_model()
    vec1 = model.encode_text("猫")
    vec2 = model.encode_text("猫")
    assert vec1 == vec2
