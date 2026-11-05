"""Slightly deepen existing bamboo textures without changing shape or bindings."""
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[1]
A = R / 'mods/ink-chrome/art'
for source in sorted(A.glob('bamboo-v9-*.png')):
    pixels = np.array(Image.open(source).convert('RGBA'))
    # Three percent ink tint: about five RGB steps darker, same alpha and grain.
    pixels[:, :, :3] = np.round(pixels[:, :, :3]*.97 + np.array([70,83,72])*.03).astype('uint8')
    Image.fromarray(pixels).save(A / source.name.replace('bamboo-v9-', 'bamboo-v17-'))
print('Generated subtly deeper bamboo-v17 textures from v9 originals')
