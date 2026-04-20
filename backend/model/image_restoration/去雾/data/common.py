import random
import numpy as np
import skimage.color as sc
import torch
# import visdom

# visualizer = visdom.Visdom(env='dual')
def get_patch(*args, patch_size=96, scale=[2], multi_scale=False):

    th, tw = args[-1].shape[:2] # target images size
#th tw 720*1280
    tp = patch_size  # patch size of target hr image
    #  option li 384
    ip = [patch_size // s for s in scale] # patch size of lr images
#tw-tp= 1280-384 =900  th-tp= 720-384=340

    # tx and ty are the top  and left coordinate of the patch 
    tx = random.randrange(0, tw - tp + 1)
    ty = random.randrange(0, th - tp + 1)
    # tx= 900 ; ty=340   tx -   [1,2,4]
    tx, ty = tx- tx % scale[0], ty - ty % scale[0]

    sharp = args[0][ty:ty + tp, tx:tx + tp, :]


    blur = args[-1][ty:ty + tp, tx:tx + tp, :]

    return [sharp, blur]

def set_channel(*args, n_channels=3):
    def _set_channel(img):
        if img.ndim == 2:
            img = np.expand_dims(img, axis=2)

        c = img.shape[2]
        if n_channels == 1 and c == 3:
            img = np.expand_dims(sc.rgb2ycbcr(img)[:, :, 0], 2)
        elif n_channels == 3 and c == 1:
            img = np.concatenate([img] * n_channels, 2)

        return img

    return _set_channel(args[0]), _set_channel(args[1])


def np2Tensor(*args, rgb_range=255):
    def _np2Tensor(img):
        np_transpose = np.ascontiguousarray(img.transpose((2, 0, 1)))
        tensor = torch.from_numpy(np_transpose).float()
        tensor.mul_(rgb_range / 255)

        # visualizer.image(torch.squeeze(tensor,dim=2),win='patch_tensor')
        return tensor

    return _np2Tensor(args[0]), _np2Tensor(args[1])


def augment(*args, hflip=True, rot=True):
    hflip = hflip and random.random() < 0.5
    vflip = rot and random.random() < 0.5
    rot90 = rot and random.random() < 0.5

    def _augment(img):
        if hflip: img = img[:, ::-1, :]
        if vflip: img = img[::-1, :, :]
        if rot90: img = img.transpose(1, 0, 2)
        
        return img

    return _augment(args[0]), _augment(args[-1])

