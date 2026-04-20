import os
import glob
from data import common
import numpy as np
import imageio
import torch.utils.data as data


class deblurData(data.Dataset):
    def __init__(self, args, name='', train=True, benchmark=False):
        self.args = args
        self.name = name
        self.train = train
        self.split = 'train' if train else 'test'
        self.do_eval = True
        self.benchmark = benchmark
        self.scale = args.scale.copy()
        self.scale.reverse()
        
        self._set_filesystem(args.data_dir)
        self._get_imgs_path(args)
        self._set_dataset_length()
    
    def __getitem__(self, idx):
        sharp, blur, filename = self._load_file(idx)

        sharp, blur = self.get_patch(sharp, blur)

        sharp, blur  = common.set_channel(sharp, blur, n_channels=self.args.n_colors)
        
        sharp_tensor, blur_tensor = common.np2Tensor(
            sharp, blur, rgb_range=self.args.rgb_range
        )

        return sharp_tensor, blur_tensor, filename

    def __len__(self):
        return self.dataset_length

    def _get_imgs_path(self, args):
        list_blur, list_sharp = self._scan()
        self.images_blur, self.images_sharp = list_blur, list_sharp

    def _set_dataset_length(self):
        if self.train:
            self.dataset_length = self.args.test_every * self.args.batch_size
            repeat = self.dataset_length // len(self.images_blur)
            self.random_border = len(self.images_blur) * repeat
        else:
            self.dataset_length = len(self.images_blur)

    def _scan(self):
        names_blur = sorted(
            glob.glob(os.path.join(self.dir_blur, '*', '*' + self.ext[0]))
        )
        names_sharp = sorted(
            glob.glob(os.path.join(self.dir_sharp, '*', '*' + self.ext[0]))
        )
        # print(names_sharp[300])
        # print(names_blur[300])
        return names_blur, names_sharp

    def _set_filesystem(self, data_dir):
        self.apath = os.path.join(data_dir, self.name)
        self.dir_blur = os.path.join(self.apath, 'blur')
        self.dir_sharp = os.path.join(self.apath, 'sharp')
        self.ext = ('.png', '.png')

    def _get_index(self, idx):
        if self.train:
            if idx < self.random_border:
                return idx % len(self.images_blur)
            else:
                return np.random.randint(len(self.images_blur))
        else:
            return idx

    def _load_file(self, idx):
        idx = self._get_index(idx)
        f_blur = self.images_blur[idx]
        f_sharp = self.images_sharp[idx]

        filename, _ = os.path.splitext(os.path.basename(f_blur))

        blur = imageio.imread(f_blur)
        sharp = imageio.imread(f_sharp)
        return sharp, blur, filename

    def get_patch(self, sharp, blur):
        scale = self.scale
        multi_scale = len(self.scale) > 1
        if self.train:
            sharp, blur = common.get_patch(
                sharp,
                blur,
                patch_size=self.args.patch_size,
                scale=scale,
                multi_scale=multi_scale
            )
            if not self.args.no_augment:
                sharp, blur = common.augment(sharp, blur)
        else:
            if isinstance(sharp, list):
                print("求关注")
                ih, iw = sharp.shape[:2]
            else:
                ih, iw = sharp.shape[:2]
            blur = blur[0:ih * scale[0], 0:iw * scale[0]]
            
        return sharp, blur

