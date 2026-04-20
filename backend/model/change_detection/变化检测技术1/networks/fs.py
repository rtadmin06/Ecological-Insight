import torch.nn as nn
import torch
from thop import profile
from torchsummary import summary
import torch.nn.functional as F
from networks.modules.MSDConv_SSFC import MSDConv_SSFC
from networks.modules.layers import *
import cv2 as cv

class GaussianFilter(nn.Module):
    def __init__(self, kernel_size=5, stride=1, padding=4):
        super(GaussianFilter, self).__init__()
        # initialize guassian kernel
        mean = (kernel_size - 1) / 2.0
        variance = (kernel_size / 6.0) ** 2.0
        # Create a x, y coordinate grid of shape (kernel_size, kernel_size, 2)
        x_coord = torch.arange(kernel_size)
        x_grid = x_coord.repeat(kernel_size).view(kernel_size, kernel_size)
        y_grid = x_grid.t()
        xy_grid = torch.stack([x_grid, y_grid], dim=-1).float()

        # Calculate the 2-dimensional gaussian kernel
        gaussian_kernel = torch.exp(-torch.sum((xy_grid - mean) ** 2., dim=-1) / (2 * variance))

        # Make sure sum of values in gaussian kernel equals 1.
        gaussian_kernel = gaussian_kernel / torch.sum(gaussian_kernel)

        # Reshape to 2d depthwise convolutional weight
        gaussian_kernel = gaussian_kernel.view(1, 1, kernel_size, kernel_size)
        gaussian_kernel = gaussian_kernel.repeat(3, 1, 1, 1)

        # create gaussian filter as convolutional layer
        self.gaussian_filter = nn.Conv2d(3, 3, kernel_size, stride=stride, padding=padding, groups=3, bias=False)
        self.gaussian_filter.weight.data = gaussian_kernel
        self.gaussian_filter.weight.requires_grad = False

    def forward(self, x):
        return self.gaussian_filter(x)


class FilterLow(nn.Module):
    def __init__(self, recursions=1, kernel_size=5, stride=1, padding=True, include_pad=True, gaussian=False):
        super(FilterLow, self).__init__()
        if padding:
            pad = int((kernel_size - 1) / 2)
        else:
            pad = 0
        if gaussian:
            self.filter = GaussianFilter(kernel_size=kernel_size, stride=stride, padding=pad)
        else:
            self.filter = nn.AvgPool2d(kernel_size=kernel_size, stride=stride, padding=pad, count_include_pad=include_pad)
        self.recursions = recursions

    def forward(self, img):
        for i in range(self.recursions):
            img = self.filter(img)
        return img


class FilterHigh(nn.Module):
    def __init__(self, recursions=1, kernel_size=5, stride=1, include_pad=True, normalize=True, gaussian=False):
        super(FilterHigh, self).__init__()
        self.filter_low = FilterLow(recursions=1, kernel_size=kernel_size, stride=stride, include_pad=include_pad,
                                    gaussian=gaussian)
        self.recursions = recursions
        self.normalize = normalize

    def forward(self, img):
        if self.recursions > 1:
            for i in range(self.recursions - 1):
                img = self.filter_low(img)
        img = img - self.filter_low(img)
        if self.normalize:
            return 0.5 + img * 0.5
        else:
            return img

class First_DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(First_DoubleConv, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, input):
        return self.conv(input)


class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(DoubleConv, self).__init__()
        self.Conv = nn.Sequential(
            MSDConv_SSFC(in_ch, out_ch, dilation=3),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            MSDConv_SSFC(out_ch, out_ch, dilation=3),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, input):
        return self.Conv(input)

class Loss111(nn.Module):
    def __int__(self):
        super(Loss111, self).__init__()
        self.Color_filter = FilterLow(recursions=1, stride=1, kernel_size=5, padding=False, gaussian=False)

    def forward(self, x):
        return self.Color_filter(x)

class USSFCNet(nn.Module):
    def __init__(self, in_ch, out_ch, ratio=0.5,gaussian=False):
        super(USSFCNet, self).__init__()
        self.color_filter = FilterLow(recursions=1, stride=1, kernel_size=5, padding=False,
                                      gaussian=gaussian)
        self.Maxpool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.Conv1_1 = First_DoubleConv(in_ch, int(64 * ratio))
        self.Conv1_2 = First_DoubleConv(in_ch, int(64 * ratio))
        self.Conv2_1 = DoubleConv(int(64 * ratio), int(128 * ratio))
        self.Conv2_2 = DoubleConv(int(64 * ratio), int(128 * ratio))
        self.Conv3_1 = DoubleConv(int(128 * ratio), int(256 * ratio))
        self.Conv3_2 = DoubleConv(int(128 * ratio), int(256 * ratio))
        self.Conv4_1 = DoubleConv(int(256 * ratio), int(512 * ratio))
        self.Conv4_2 = DoubleConv(int(256 * ratio), int(512 * ratio))
        self.Conv5_1 = DoubleConv(int(512 * ratio), int(1024 * ratio))
        self.Conv5_2 = DoubleConv(int(512 * ratio), int(1024 * ratio))

        self.Up5 = nn.ConvTranspose2d(int(1024 * ratio), int(512 * ratio), 2, stride=2)
        self.Up_conv5 = DoubleConv(int(1024 * ratio), int(512 * ratio))
        self.Conv_5x5 = nn.Conv2d(int(512 * ratio), out_ch, kernel_size=1, stride=1, padding=0)

        self.Up4 = nn.ConvTranspose2d(int(512 * ratio), int(256 * ratio), 2, stride=2)
        self.Up_conv4 = DoubleConv(int(512 * ratio), int(256 * ratio))
        self.Conv_4x4 = nn.Conv2d(int(256 * ratio), out_ch, kernel_size=1, stride=1, padding=0)

        self.Up3 = nn.ConvTranspose2d(int(256 * ratio), int(128 * ratio), 2, stride=2)
        self.Up_conv3 = DoubleConv(int(256 * ratio), int(128 * ratio))
        self.Conv_3x3 = nn.Conv2d(int(128 * ratio), out_ch, kernel_size=1, stride=1, padding=0)

        self.Up2 = nn.ConvTranspose2d(int(128 * ratio), int(64 * ratio), 2, stride=2)
        self.Up_conv2 = DoubleConv(int(128 * ratio), int(64 * ratio))
        self.Conv_1x1 = nn.Conv2d(int(64 * ratio), out_ch, kernel_size=1, stride=1, padding=0)

    def forward(self, x1, x2):
        # encoding

        c1_1 = self.Conv1_1(x1)
        c1_2 = self.Conv1_2(x2)

        x1 = torch.abs(torch.sub(c1_1, c1_2))

        # print(xh1.size(), 'xh1')

        c2_1 = self.Maxpool(c1_1)
        c2_1 = self.Conv2_1(c2_1)
        c2_2 = self.Maxpool(c1_2)
        c2_2 = self.Conv2_2(c2_2)
        x2 = torch.abs(torch.sub(c2_1, c2_2))

        c3_1 = self.Maxpool(c2_1)
        c3_1 = self.Conv3_1(c3_1)
        c3_2 = self.Maxpool(c2_2)
        c3_2 = self.Conv3_2(c3_2)
        x3 = torch.abs(torch.sub(c3_1, c3_2))

        c4_1 = self.Maxpool(c3_1)
        c4_1 = self.Conv4_1(c4_1)
        c4_2 = self.Maxpool(c3_2)
        c4_2 = self.Conv4_2(c4_2)

        x4 = torch.abs(torch.sub(c4_1, c4_2))

        c5_1 = self.Maxpool(c4_1)
        c5_1 = self.Conv5_1(c5_1)
        c5_2 = self.Maxpool(c4_2)
        c5_2 = self.Conv5_2(c5_2)
        x5 = torch.abs(torch.sub(c5_1, c5_2))

        d5 = self.Up5(x5)

        d5 = torch.cat((x4, d5), dim=1)
        d5 = self.Up_conv5(d5)

        d51 = self.Conv_5x5(d5)
        out8 = nn.Sigmoid()(d51)

        d4 = self.Up4(d5)
        d4 = torch.cat((x3, d4), dim=1)
        d4 = self.Up_conv4(d4)
        d41 = self.Conv_4x4(d4)
        out4 = nn.Sigmoid()(d41)

        d3 = self.Up3(d4)
        d3 = torch.cat((x2, d3), dim=1)
        d3 = self.Up_conv3(d3)
        d31 = self.Conv_3x3(d3)
        out2 = nn.Sigmoid()(d31)

        d2 = self.Up2(d3)
        d2 = torch.cat((x1, d2), dim=1)
        d2 = self.Up_conv2(d2)
        d1 = self.Conv_1x1(d2)

        out = nn.Sigmoid()(d1)




        return out8, out4, out2, out


if __name__ == "__main__":
    A2016 = torch.randn(8, 3, 256, 256)
    A2019 = torch.randn(8, 3, 256, 256)
    labels = torch.randn(8, 1, 256, 256)
    pixel_loss = nn.L1Loss()
    model = USSFCNet(3, 1, ratio=0.5)
    #model1 = Loss()
    loss = model.color_filter
    #print(loss.size)()
    out_result = model(A2016, A2019)


    # print(lables8.size(),'lables8')
    #model = USSFCNet(3, 3, ratio=0.5)
    #out_result = model(A2016, A2019)
    out = out_result[3]
    #print(out.size())
    out8 = out_result[0]
    out4 = out_result[1]
    out2 = out_result[2]
    loss1 = loss(out)
    loss2 = loss(labels)

    pixelloss = pixel_loss(loss1, loss2)
    print(pixelloss)
    criterion_ce = nn.BCELoss()

    loss = criterion_ce(out, labels)

    # loss4 = criterion_ce(out_result, lables4)
    # loss2 = criterion_ce(out_result, lables2)
    # print(loss8,'loss')
    # print(out_result.size())
    # summary(model, [(3, 256, 256), (3, 256, 256)])
    flops, params = profile(model, inputs=(A2016, A2019))

