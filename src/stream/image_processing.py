import logging
import os
from logging.config import dictConfig

import cv2
import yaml

fname = os.path.join(os.path.dirname(__file__), "logging.yaml")
dictConfig(yaml.safe_load(open(fname)))
logger = logging.getLogger(name="groundlight.stream")


def resize_if_needed(frame: cv2.Mat, width: int, height: int) -> cv2.Mat:
    """Resize image frame while maintaining aspect ratio

    Args:
        frame: OpenCV image array
        width: Target width in pixels (0 to scale based on height)
        height: Target height in pixels (0 to scale based on width)
    """
    if (width == 0) & (height == 0):  # No resize needed
        return frame

    image_height, image_width, _ = frame.shape
    if width > 0:
        target_width = width
    else:
        height_proportion = height / image_height
        target_width = int(image_width * height_proportion)

    if height > 0:
        target_height = height
    else:
        width_proportion = width / image_width
        target_height = int(image_height * width_proportion)

    logger.warning(f"resizing from {frame.shape=} to {target_width=}x{target_height=}")
    frame = cv2.resize(frame, dsize=(target_width, target_height))
    return frame


def crop_frame(frame: cv2.Mat, crop_region: tuple[float, float, float, float]) -> cv2.Mat:
    """Crop image frame to specified region

    Args:
        frame: OpenCV image array
        crop_region: Tuple of (x, y, width, height) as fractions from 0-1

    Returns:
        Cropped image array
    """
    (img_height, img_width, _) = frame.shape
    x1 = int(img_width * crop_region[0])
    y1 = int(img_height * crop_region[1])
    x2 = x1 + int(img_width * crop_region[2])
    y2 = y1 + int(img_height * crop_region[3])

    out = frame[y1:y2, x1:x2, :]
    return out


def parse_crop_string(crop_string: str) -> tuple[float, float, float, float]:
    """Parse crop region string into normalized coordinates

    Args:
        crop_string: String like "0.25,0.25,0.5,0.5" specifying x,y,width,height

    Returns:
        Tuple of (x, y, width, height) as floats from 0-1

    Raises:
        ValueError: If crop parameters are invalid
    """
    parts = crop_string.split(",")
    if len(parts) != 4:
        raise ValueError("Expected crop to be list of four floating point numbers.")
    numbers = tuple([float(n) for n in parts])

    for n in numbers:
        if (n < 0) or (n > 1):
            raise ValueError("All numbers must be between 0 and 1, showing relative position in image")

    if numbers[0] + numbers[2] > 1.0:
        raise ValueError("Invalid crop: x+w is greater than 1.")
    if numbers[1] + numbers[3] > 1.0:
        raise ValueError("Invalid crop: y+h is greater than 1.")

    if numbers[2] * numbers[3] == 0:
        raise ValueError("Width and Height must both be >0")

    return numbers
