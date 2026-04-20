import cv2
import os
import glob

def downx2():
    x2_dir_sharp = "/home/lym/gopro_test/train/sharp/X2"
    names_sharp = sorted(
        glob.glob(os.path.join(x2_dir_sharp, '*' + ".png"))  ####dir_hr改成dir_lr
    )
    print(names_sharp)
    for f in names_sharp:
        print(f)
        img_src = cv2.imread(f)
        img_result = cv2.pyrDown(img_src)
        print(img_result.shape)
        cv2.imwrite(f,img_result)

def downx4():
    x4_dir_sharp = "/home/lym/gopro_test/train/sharp/X4"
    names_sharp = sorted(
        glob.glob(os.path.join(x4_dir_sharp, '*' + ".png"))  ####dir_hr改成dir_lr
    )
    print(names_sharp)
    for f in names_sharp:
        print(f)
        img_src = cv2.imread(f)
        img = cv2.pyrDown(img_src)
        img_result = cv2.pyrDown(img)
        print(img_result.shape)
        cv2.imwrite(f,img_result)


downx2()
downx4()