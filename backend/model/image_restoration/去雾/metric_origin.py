# from __future__ import print_function
import numpy as np
import cv2
import os
import glob
import tqdm
import time
import math
from PIL import Image

gt_dir = "/home/lym/srdata_path/deblu_dataset/benchmark/GOPRO/sharp_bicubic/X1/"
test_dir = "/home/lym/srdata_path/x4"

def PSNR(img1, img2):
    mse = np.mean((img1 / 255. - img2 / 255.) ** 2)
    if mse == 0:
        return 100
    PIXEL_MAX = 1
    return 20 * math.log10(PIXEL_MAX / math.sqrt(mse))


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




def get_gt_image(path):
	dir, filename = os.path.split(path)
	gt_path = os.path.join(gt_dir,filename)
	gt_img = cv2.cvtColor(cv2.imread(gt_path), cv2.COLOR_BGR2RGB)
	return gt_img



def save_image(result,filename):
	save_img = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
	cv2.imwrite(filename,save_img)



def test_image(image_path):
	img = cv2.imread(image_path)
	img_s = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	gt_img = get_gt_image(image_path)
	psnr = PSNR(gt_img, img_s)
	ssim = calculate_ssim(gt_img, img_s)
	return psnr, ssim


def test( files):
	psnr = 0
	ssim = 0
	for file in tqdm.tqdm(files):
		cur_psnr, cur_ssim = test_image(file)
		psnr += cur_psnr
		ssim += cur_ssim
	print("PSNR = {}".format(psnr / len(files)))
	print("SSIM = {}".format(ssim / len(files)))


# if __name__ == '__main__':
	# des_dir = "/home/lym/srdata_path/deblu_dataset/benchmark/GOPRO/sharp_bicubic/X1"
	# test_dir = "/home/lym/Downloads/可以运行的代码/训练过得desate/DRN-masterOK/experiment_test160_epoch600/experiment/test/results/Set5/x4"
begin = time.time()
filenames = sorted(glob.glob(test_dir, recursive=True))
print(len(filenames))
test(filenames)
final = time.time()
print("time is " , final-begin)
