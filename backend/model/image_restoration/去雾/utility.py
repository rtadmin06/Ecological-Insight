import math
import time
import random
import numpy as np
import torch
import torch.optim as optim
import torch.optim.lr_scheduler as lrs
import cv2

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.device_count() == 1:
        torch.cuda.manual_seed(seed)
    else:
        torch.cuda.manual_seed_all(seed)
    

class timer():
    def __init__(self):
        self.acc = 0
        self.tic()

    def tic(self):
        self.t0 = time.time()

    def toc(self):
        return time.time() - self.t0

    def hold(self):
        self.acc += self.toc()

    def release(self):
        ret = self.acc
        self.acc = 0

        return ret

    def reset(self):
        self.acc = 0


def quantize(img, rgb_range):
    pixel_range = 255 / rgb_range
    return img.mul(pixel_range).clamp(0, 255).round().div(pixel_range)


def calc_psnr(sharp, blur, scale, rgb_range, benchmark=False):
    if sharp.size(-2) > blur.size(-2) or sharp.size(-1) > blur.size(-1):
        print("the dimention of sr image is not equal to hr's! ")
        sharp = sharp[:,:,:blur.size(-2),:blur.size(-1)]
    diff = (sharp - blur).data.div(rgb_range)

    if benchmark:
        shave = scale
        if diff.size(1) > 1:
            convert = diff.new(1, 3, 1, 1)
            convert[0, 0, 0, 0] = 65.738
            convert[0, 1, 0, 0] = 129.057
            convert[0, 2, 0, 0] = 25.064
            diff.mul_(convert).div_(256)
            diff = diff.sum(dim=1, keepdim=True)
    else:
        shave = scale + 6

    valid = diff[:, :, shave:-shave, shave:-shave]
    mse = valid.pow(2).mean()

    return -10 * math.log10(mse)

def ssim(img1, img2):
    C1 = (0.01 * 255)**2
    C2 = (0.03 * 255)**2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]  # valid
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.filter2D(img1**2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2**2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) *
                                                            (sigma1_sq + sigma2_sq + C2))
    return ssim_map.mean()


def calculate_ssim(img1, img2):
    '''calculate SSIM
    the same outputs as MATLAB's
    img1, img2: [0, 255]
    '''
    if not img1.shape == img2.shape:
        raise ValueError('Input images must have the same dimensions.')
    if img1.ndim == 2:
        return ssim(img1, img2)
    elif img1.ndim == 3:
        if img1.shape[2] == 3:
            ssims = []
            for i in range(3):
                ssims.append(ssim(img1, img2))
            return np.array(ssims).mean()
        elif img1.shape[2] == 1:
            return ssim(np.squeeze(img1), np.squeeze(img2))
    else:
        raise ValueError('Wrong input image dimensions.')

def make_optimizer(opt, my_model):
    trainable = filter(lambda x: x.requires_grad, my_model.parameters())
    optimizer_function = optim.Adam
    kwargs = {
        'betas': (opt.beta1, opt.beta2),
        'eps': opt.epsilon
    }
    kwargs['lr'] = opt.lr
    kwargs['weight_decay'] = opt.weight_decay
    
    return optimizer_function(trainable, **kwargs)


def make_cycle_optimizer(opt, my_model):
    trainable = filter(lambda x: x.requires_grad, my_model.parameters())
    optimizer_cycle_function = optim.Adam
    kwargs = {
        'betas': (opt.beta1, opt.beta2),
        'eps': opt.epsilon
    }
    kwargs['lr'] = opt.lr
    kwargs['weight_decay'] = opt.weight_decay

    return optimizer_cycle_function(trainable, **kwargs)

def make_dual_optimizer(opt, dual_models):
    dual_optimizers = []
    for dual_model in dual_models:
        temp_dual_optim = torch.optim.Adam(
            params=dual_model.parameters(),
            lr = opt.lr, 
            betas = (opt.beta1, opt.beta2),
            eps = opt.epsilon,
            weight_decay=opt.weight_decay)
        dual_optimizers.append(temp_dual_optim)
    
    return dual_optimizers


def make_scheduler(opt, my_optimizer):
    scheduler = lrs.CosineAnnealingLR(
        my_optimizer,
        float(opt.epochs),
        eta_min=opt.eta_min
    )

    return scheduler

def make_cycle_scheduler(opt, cycle_optimizer):
    scheduler = lrs.CosineAnnealingLR(
        cycle_optimizer,
        float(opt.epochs),
        eta_min=opt.eta_min
    )

    return scheduler

def make_dual_scheduler(opt, dual_optimizers):
    dual_scheduler = []
    for i in range(len(dual_optimizers)):
        scheduler = lrs.CosineAnnealingLR(
            dual_optimizers[i],
            float(opt.epochs),
            eta_min=opt.eta_min
        )
        dual_scheduler.append(scheduler)

    return dual_scheduler


def init_model(args):
    # Set the templates here
    if args.model.find('DRN-S') >= 0:
        if args.scale == 4:
            args.n_blocks = 30
            args.n_feats = 16
        elif args.scale == 8:
            args.n_blocks = 30
            args.n_feats = 8
        else:
            print('Use defaults n_blocks and n_feats.')
        args.dual = True

    if args.model.find('DRN-L') >= 0:
        if args.scale == 4:
            args.n_blocks = 40
            args.n_feats = 20
        elif args.scale == 8:
            args.n_blocks = 36
            args.n_feats = 10
        else:
            print('Use defaults n_blocks and n_feats.')
        args.dual = True


