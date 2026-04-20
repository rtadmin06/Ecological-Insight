import os
import glob
#####这是给blur改名
# data_dir = "/home/lym/gopro_test/train"
dir_hr = "/home/lym/deblu_dataset/Kohler/Kohlerzip/groundtruth"
# dir_lr = "/home/lym/gopro_test/train/sharp/"
names_hr = sorted(
    glob.glob(os.path.join(dir_hr,'*', '*' + ".jpg"))  ####dir_hr改成dir_lr
)
print(names_hr)
i = 1
for f in names_hr:
    # filename, _ = os.path.splitext(os.path.basename(f))
    # #print(filename)
    dir_name = f.split('/')[-2]
    # print(dir_name)
    # #filename = filename.split('_')

    # filename = filename[0] + "_" + filename[1] + "_" + filename[2]
    filename_new =os.path.join(dir_hr, dir_name + '_{}.png'.format(i))
    i+=1
    print("filename_new")
    print(filename_new)
    # names_sharp[si].append(os.path.join(
    #     self.dir_sharp, 'X{}/{}{}'.format(
    #         s, filename, self.ext[1]
    #     )
    # )
    # os.rename(f,filename_new)