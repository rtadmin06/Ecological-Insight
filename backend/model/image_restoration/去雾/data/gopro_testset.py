import os
from data import deblurdata


class Benchmark(deblurdata.deblurData):
    def __init__(self, args, name='test', train=False, benchmark=True):
        super(Benchmark, self).__init__(
            args, name=name, train=train, benchmark=True
        )

    def _set_filesystem(self, data_dir):
        super(Benchmark, self)._set_filesystem(data_dir)
        self.apath = '/home/lym/deblu_dataset/GOPRO/test'
        self.dir_blur = os.path.join(self.apath, 'blur')

        self.dir_sharp = os.path.join(self.apath, 'sharp')


