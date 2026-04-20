import os
from data import deblurdata


class GOPRO(deblurdata.deblurData):
    def __init__(self, args, name='train', train=True, benchmark=False):
        super(GOPRO, self).__init__(
            args, name=name, train=train, benchmark=benchmark
        )

    def _set_filesystem(self, data_dir):
        super(GOPRO, self)._set_filesystem(data_dir)
        self.dir_blur = os.path.join(self.apath, 'blur')
        self.dir_sharp = os.path.join(self.apath, 'sharp')

