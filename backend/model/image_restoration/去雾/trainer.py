import torch
import utility
from decimal import Decimal
from tqdm import tqdm
# import visdom
import zen_utils


class Trainer():
    def __init__(self, opt, loader, my_model, my_loss, ckp):
        self.opt = opt
        self.scale = opt.scale
        self.ckp = ckp
        self.loader_train = loader.loader_train
        self.loader_test = loader.loader_test
        self.model = my_model
        self.loss = my_loss
        self.optimizer = utility.make_optimizer(opt, self.model)
        self.scheduler = utility.make_scheduler(opt, self.optimizer)

        self.error_last = 1e8

        # self.visualizer = visdom.Visdom(env='desate_dual')


    def train(self):
        epoch = self.scheduler.last_epoch + 1
        lr = self.scheduler.get_lr()[0]###学习率

        self.ckp.write_log(
            '[Epoch {}]\tLearning rate: {:.2e}'.format(epoch, Decimal(lr))
        )
        self.loss.start_log()
        self.model.train()
        timer_data, timer_model = utility.timer(), utility.timer()
        for batch, ( sharp, blur, _) in enumerate(self.loader_train):
            sharp, blur,= self.prepare(sharp, blur, )
            timer_data.hold()
            timer_model.tic()
            
            self.optimizer.zero_grad()

            # forward
            latent = self.model(blur)
            latent = utility.quantize(latent, self.opt.rgb_range)
            # print(latent)
            # print(sharp)
            # print(blur)
            # compute primary loss
            loss_primary = self.loss(latent, sharp)

            # compute total loss
            loss = loss_primary
            
            if loss.item() < self.opt.skip_threshold * self.error_last:
                loss.backward()                
                self.optimizer.step()

            else:
                print('Skip this batch {}! (Loss: {})'.format(
                    batch + 1, loss.item()
                ))

            timer_model.hold()

            if (batch + 1) % self.opt.print_every == 0:
                self.ckp.write_log('[{}/{}]\t{}\t{:.1f}+{:.1f}s'.format(
                    (batch + 1) * self.opt.batch_size,
                    len(self.loader_train.dataset),
                    self.loss.display_loss(batch),
                    timer_model.release(),
                    timer_data.release()))
            # self.visualizer.image(torch.squeeze(blur[1], dim=0), win='train_sharp')
            # self.visualizer.image(torch.squeeze(latent[2][1], dim=0), win='train_restore')
            # self.visualizer.image(torch.squeeze(sharp[2][1], dim=0), win='train_blur')
            # self.visualizer.image(torch.squeeze(latent_blur[1], dim=0), win='train_latentblur')
            #
            # self.visualizer.image(torch.squeeze(latent2lr[1][1], dim=0), win='trainX2_latent2lr')
            # self.visualizer.image(torch.squeeze(latent[1][1], dim=0), win='trainX2_restore')
            # self.visualizer.image(torch.squeeze(sharp[1][1], dim=0), win='trainX2_sharp')
            #
            # self.visualizer.image(torch.squeeze(latent2lr[0][1], dim=0), win='trainX4_latent2lr')
            # self.visualizer.image(torch.squeeze(latent[0][1], dim=0), win='trainX4_restore')
            # self.visualizer.image(torch.squeeze(sharp[0][1], dim=0), win='trainX4_sharp')

            timer_data.tic()
        # self.visualizer.image(torch.squeeze(sr[2], dim=0), win='train_restore')
        self.loss.end_log(len(self.loader_train))
        self.error_last = self.loss.log[-1, -1]
        self.step()

    def test(self):
        epoch = self.scheduler.last_epoch
        self.ckp.write_log('\nEvaluation:')
        self.ckp.add_log(torch.zeros(1, 1))
        self.model.eval()

        timer_test = utility.timer()
        with torch.no_grad():
            scale = max(self.scale)
            for si, s in enumerate([scale]):
                eval_psnr = 0
                eval_ssim = 0
                tqdm_test = tqdm(self.loader_test, ncols=80)
                for _, (sharp, blur, filename) in enumerate(tqdm_test):
                    filename = filename[0]
                    no_eval = (blur.nelement() == 1)
                    if not no_eval:
                        sharp, blur = self.prepare(sharp, blur)
                    else:
                        _,blur = self.prepare(sharp, blur)

                    latent = self.model(blur)



                    if isinstance(latent, list): latent = latent
                    #
                    latent = utility.quantize(latent, self.opt.rgb_range)

                    if not no_eval:
                        test_result = zen_utils.InverseTensor()(latent)
                        target_img = zen_utils.InverseTensor()(sharp)
                        psnr , ssim = zen_utils.calculate_all(target_img,test_result)

                        eval_psnr += psnr
                        eval_ssim += ssim
                    # save test results
                    if self.opt.save_results:
                        self.ckp.save_results_nopostfix(filename, latent, s)

                self.ckp.log[-1, si] = eval_psnr / len(self.loader_test)
                ssim = eval_ssim/ len(self.loader_test)
                print("ssim: " , ssim )
                best = self.ckp.log.max(0)
                self.ckp.write_log(
                    '[{} x{}]\tPSNR: {:.2f} (Best: {:.2f} @epoch {})'.format(
                        self.opt.data_test, s,
                        self.ckp.log[-1, si],
                        best[0][si],
                        best[1][si] + 1
                    )
                )
        # self.visualizer.image(torch.squeeze(sr[2], dim=0), win='test_restore')
        self.ckp.write_log(
            'Total time: {:.2f}s\n'.format(timer_test.toc()), refresh=True
        )
        if not self.opt.test_only:
            self.ckp.save(self, epoch, is_best=(best[1][0] + 1 == epoch))

    def step(self):
        self.scheduler.step()


    def prepare(self, *args):
        device = torch.device('cpu' if self.opt.cpu else 'cuda')

        if len(args)>1:
            return args[0].to(device), args[-1].to(device)
        return args[0].to(device),

    def terminate(self):
        if self.opt.test_only:
            self.test()
            return True
        else:
            epoch = self.scheduler.last_epoch
            return epoch >= self.opt.epochs
