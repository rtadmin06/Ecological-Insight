import math
import torch

img = torch.tensor([123, 111 ,112, 255])

pixel_range = 255 / 255
img = img.mul(pixel_range).clamp(0, 255).round().div(pixel_range)
print(img)