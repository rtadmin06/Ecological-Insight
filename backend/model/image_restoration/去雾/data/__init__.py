from importlib import import_module
from torch.utils.data import DataLoader
import random
from torch.utils.data.sampler import SubsetRandomSampler

class Data:
    def __init__(self, args):
        self.loader_train = None
        if not args.test_only:
            module_train = import_module('data.' + args.data_train.lower())
            # print(module_train)
            trainset = getattr(module_train, "GOPRO")(args)  #######从一个py文件中 返回是整个GOPRO的属性值，也就是一个类
            #print(trainset.images_blur)
            self.loader_train = DataLoader(
                trainset,
                batch_size=args.batch_size,
                num_workers=args.n_threads,
                shuffle=True,
                pin_memory=not args.cpu
            )

        if args.data_test in ['gopro_testset', 'B100', 'Urban100', 'Manga109']:  #这里是通用数据集
            module_test = import_module('data.gopro_testset')
            testset = getattr(module_test, 'Benchmark')(args, name=args.data_test, train=False)
        else:
            module_test = import_module('data.' +  args.data_test.lower())    ###特定数据集
            testset = getattr(module_test, args.data_test)(args, train=False)

        num = 2200
        index = list(range(num))
        random.shuffle(index)
        valid_sampler = SubsetRandomSampler(index[:100])
        self.loader_test = DataLoader(
            testset,
            batch_size=1,    ################ pay attention please batch size =1
            num_workers=1,
            shuffle=False,
            pin_memory=not args.cpu,
            sampler = valid_sampler
        )

