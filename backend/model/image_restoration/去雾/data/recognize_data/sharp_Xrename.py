import os
import glob

import shutil
#####这是给blur改名
# data_dir = "/home/lym/gopro_test/train"
# dir_hr = "/home/lym/gopro_test/train/blur/"
dir_sharp = "/home/lym/gopro_test/train/sharp/"
names_sharp = sorted(
    glob.glob(os.path.join(dir_sharp,'*', '*' + ".png"))  ####dir_hr改成dir_lr
)
print(names_sharp)
for f in names_sharp:
    filename, _ = os.path.splitext(os.path.basename(f))

    dir_name = f.split('/')[-2]
    # print(dir_name)

    # print(filename)
    if not os.path.exists(os.path.join(dir_sharp,"X4")):
        os.mkdir(os.path.join(dir_sharp,"X4"))
    if not os.path.exists(os.path.join(dir_sharp, "X2")):
        os.mkdir(os.path.join(dir_sharp, "X2"))
    if not os.path.exists(os.path.join(dir_sharp, "X1")):
        os.mkdir(os.path.join(dir_sharp, "X1"))
    x4_filename_new =os.path.join(dir_sharp,"X4", dir_name + "_" + filename + '.png')
    x2_filename_new = os.path.join(dir_sharp, "X2", dir_name + "_" + filename + '.png')
    x1_filename_new = os.path.join(dir_sharp, "X1", dir_name + "_" + filename + '.png')
    print(x4_filename_new)
    shutil.copyfile(f,x4_filename_new)
    shutil.copyfile(f, x1_filename_new)
    shutil.copyfile(f, x2_filename_new)
    # print(filename_new)
    #
    # os.rename(f,filename_new)