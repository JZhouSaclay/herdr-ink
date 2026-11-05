"""Lift the shared landscape onto the brighter neutral v2 paper."""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'mods/ink-chrome/art'
a=np.asarray(Image.open(ART/'landscape-v1.png').convert('RGB'),dtype=float)
a=a*.94+np.array([252,252,249])*.06
Image.fromarray(np.clip(a,0,255).astype('uint8')).save(ART/'landscape-v2.png')
print(ART/'landscape-v2.png')
