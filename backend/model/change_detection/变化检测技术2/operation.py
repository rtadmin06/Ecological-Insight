import cv2
import torch
from PIL import Image
from tqdm import tqdm
import numpy as np
import metrics
import glob
from path import *
from utils import save_pre_result

filename = glob.glob(test_src_t1 + '/*.png')
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
#device_ids = [0, 1]


def train(net, dataloader_train, total_step, criterion_ce, optimizer , lr_scheduler):
    print('Training...')
    model = net.train()
    num = 0
    epoch_loss = 0
    cm_total = np.zeros((2, 2))

    for x1, x2, y in dataloader_train:
        inputs_t1 = x1.to(device)
        inputs_t2 = x2.to(device)
        labels = y.to(device)

        optimizer.zero_grad()
        out_result = model(inputs_t1, inputs_t2)
        out8 = out_result[0]
        out4 = out_result[1]
        out2 = out_result[2]
        pre = out_result[3]
        labels8 = torch.nn.functional.interpolate(labels, scale_factor=1 / 8, mode='bilinear',
                                                  align_corners=False)
        labels4 = torch.nn.functional.interpolate(labels, scale_factor=1 / 4, mode='bilinear',
                                                  align_corners=False)
        labels2 = torch.nn.functional.interpolate(labels, scale_factor=1 / 2, mode='bilinear',
                                                  align_corners=False)
        loss8 = criterion_ce(out8, labels8)
        loss4 = criterion_ce(out4, labels4)
        loss2 = criterion_ce(out2, labels2)
        loss_pre = criterion_ce(pre, labels)
        loss = 0.1 * loss8 + 0.1 * loss4 + 0.1 * loss2 + 0.7 * loss_pre
        #loss = criterion_ce(pre, labels)   # out_ch=1
        # loss = criterion_ce(pre, torch.squeeze(labels.long(), dim=1))   # out_ch=2
        loss.backward()
        epoch_loss += loss.item()
        optimizer.step()
        # lr_scheduler.step()
        # pre = torch.max(pre, 1)[1]  # out_ch=2
        cm = metrics.ConfusionMatrix(2, pre, labels)
        cm_total += cm
        precision, recall, f1, iou, kc = metrics.get_score(cm)

        num += 1

        print('%d/%d, loss:%f, Pre:%f, Rec:%f, F1:%f, IoU:%f, KC:%f' % (num, total_step, loss.item(), precision[1], recall[1], f1[1], iou[1], kc))
    precision_total, recall_total, f1_total, iou_total, kc_total = metrics.get_score_sum(cm_total)

    return epoch_loss, precision_total['precision_1'], recall_total['recall_1'], f1_total['f1_1'], iou_total['iou_1'], kc_total


def validate(net, dataloader_val, epoch):
    print('Validating...')
    model = net.eval()
    num = 0
    cm_total = np.zeros((2, 2))

    for x1, x2, y in tqdm(dataloader_val):
        inputs_t1 = x1.to(device)
        inputs_t2 = x2.to(device)
        labels = y.to(device)
        pre = model(inputs_t1, inputs_t2)
        out_result = model(inputs_t1, inputs_t2)
        #out8 = out_result[0]
        #out4 = out_result[1]
        #out2 = out_result[2]
        pre = out_result[3]
        # pre = torch.max(pre, 1)[1]  # out_ch=2
        cm = metrics.ConfusionMatrix(2, pre, labels)
        cm_total += cm
        num += 1
    precision_total, recall_total, f1_total, iou_total, kc_total = metrics.get_score_sum(cm_total)
    return precision_total['precision_1'], recall_total['recall_1'], f1_total['f1_1'], iou_total['iou_1'], kc_total


def predict(net, dataloader_test):
    print('Testing...')
    model = net.eval()
    # num = 0
    cm_total = np.zeros((2, 2))
    for x1, x2, y,file_name in tqdm(dataloader_test):
        inputs_t1 = x1.to(device)
        inputs_t2 = x2.to(device)
        labels = y.to(device)
        #pre = model(inputs_t1, inputs_t2)
        out_result = model(inputs_t1, inputs_t2)
        #out8 = out_result[0]
        #out4 = out_result[1]
        #out2 = out_result[2]
        pre = out_result[3]
        cm = metrics.ConfusionMatrix(2, pre, labels)
        cm_total += cm
        save_pre_result(pre, file_name, save_path=test_predict)
        # num += 1
    precision_total, recall_total, f1_total, iou_total, kc_total = metrics.get_score_sum(cm_total)
    return precision_total, recall_total, f1_total, iou_total, kc_total
