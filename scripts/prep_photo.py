#!/usr/bin/env python3
"""Prepare a high-contrast, white-background portrait for ASCII rendering."""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

try:
    from rembg import remove
except (ImportError, OSError):
    remove = None

ROOT = Path(__file__).resolve().parent.parent


def isolate(image):
    rgb = np.array(image.convert("RGB"))
    if remove is not None:
        cutout = remove(image.convert("RGBA"))
        return np.array(cutout.convert("RGB")), np.array(cutout.getchannel("A"))

    height, width = rgb.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    background = np.zeros((1, 65), dtype=np.float64)
    foreground = np.zeros((1, 65), dtype=np.float64)
    inset_x, inset_y = max(2, width // 30), max(2, height // 40)
    rectangle = (inset_x, inset_y, width - 2 * inset_x, height - 2 * inset_y)
    cv2.grabCut(rgb, mask, rectangle, background, foreground, 6, cv2.GC_INIT_WITH_RECT)
    alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    return rgb, alpha


def prepare(source, destination):
    rgb, alpha = isolate(Image.open(source))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.04, beta=18)
    matte = cv2.GaussianBlur(alpha.astype(np.float32) / 255, (0, 0), 1.1)
    result = gray * matte + 255 * (1 - matte)
    Image.fromarray(np.clip(result, 0, 255).astype(np.uint8)).save(destination)


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "source-photo.jpg"
    destination = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "source-prepped.png"
    prepare(source, destination)
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
