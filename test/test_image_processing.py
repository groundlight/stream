import numpy as np
import pytest

from stream.image_processing import crop_frame, parse_crop_string


def test_crop_frame():
    # Create test image
    test_img = np.zeros((100, 200, 3), dtype=np.uint8)

    # Test full crop
    cropped = crop_frame(test_img, (0, 0, 1, 1))
    assert cropped.shape == (100, 200, 3)

    # Test quarter crop from top left
    cropped = crop_frame(test_img, (0, 0, 0.5, 0.5))
    assert cropped.shape == (50, 100, 3)

    # Test quarter crop from center
    cropped = crop_frame(test_img, (0.25, 0.25, 0.5, 0.5))
    assert cropped.shape == (50, 100, 3)


def test_parse_crop_string():
    # Test valid crops
    assert parse_crop_string("0,0,1,1") == (0, 0, 1, 1)
    assert parse_crop_string("0.25,0.25,0.5,0.5") == (0.25, 0.25, 0.5, 0.5)

    # Test invalid formats
    with pytest.raises(ValueError):
        parse_crop_string("0,0,1")  # Too few values

    with pytest.raises(ValueError):
        parse_crop_string("0,0,1,1,1")  # Too many values

    with pytest.raises(ValueError):
        parse_crop_string("not,valid,numbers,here")  # Invalid numbers

    # Test invalid ranges
    with pytest.raises(ValueError):
        parse_crop_string("-0.1,0,1,1")  # Negative value

    with pytest.raises(ValueError):
        parse_crop_string("0,0,1.1,1")  # Value > 1

    with pytest.raises(ValueError):
        parse_crop_string("0.7,0,0.4,1")  # x + width > 1

    with pytest.raises(ValueError):
        parse_crop_string("0,0.7,1,0.4")  # y + height > 1

    with pytest.raises(ValueError):
        parse_crop_string("0,0,0,1")  # Zero width

    with pytest.raises(ValueError):
        parse_crop_string("0,0,1,0")  # Zero height
