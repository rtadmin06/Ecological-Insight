import os
import glob
#####这是给blur改名
data_dir = "/home/lym/gopro_test/train"
dir_hr = "/home/lym/gopro_test/train/blur/"
# dir_lr = "/home/lym/gopro_test/train/sharp/"
names_hr = sorted(
    glob.glob(os.path.join(dir_hr,'*', '*' + ".png"))  ####dir_hr改成dir_lr
)
print(names_hr)
for f in names_hr:
    filename, _ = os.path.splitext(os.path.basename(f))
    #print(filename)
    dir_name = f.split('/')[-2]
    print(dir_name)
    #filename = filename.split('_')
    print(filename)
    # filename = filename[0] + "_" + filename[1] + "_" + filename[2]
    filename_new =os.path.join(dir_hr, dir_name + "_" + filename + '.png')
    print("filename_new")
    print(filename_new)
    # s = 4
    os.rename(f,filename_new)