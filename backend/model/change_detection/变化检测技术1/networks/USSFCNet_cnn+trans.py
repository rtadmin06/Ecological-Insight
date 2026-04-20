import torch.nn as nn
import torch
from thop import profile
import paddle
from torchsummary import summary
import torch.nn.functional as F
from networks.modules.MSDConv_SSFC import MSDConv_SSFC
from networks.modules.layers import *
from modules.mix import MixFormer,MixingAttention
class BasicConv(nn.Module):
    def __init__(self, in_channel, out_channel, kernel_size, stride, bias=True, norm=False, relu=True, transpose=False):
        super(BasicConv, self).__init__()
        if bias and norm:
            bias = False

        padding = kernel_size // 2
        layers = list()
        if transpose:
            padding = kernel_size // 2 - 1
            layers.append(nn.ConvTranspose2d(in_channel, out_channel,
                          kernel_size, padding=padding, stride=stride, bias=bias, output_padding=stride-1))
        else:
            layers.append(
                nn.Conv2d(in_channel, out_channel, kernel_size, padding=padding, stride=stride, bias=bias))
        if norm:
            layers.append(nn.BatchNorm2d(out_channel))
        if relu:
            layers.append(nn.ReLU(inplace=True))
        self.main = nn.Sequential(*layers)

    def forward(self, x):
        return self.main(x)
class Branch(nn.Module):
    def __init__(self, in_channel, out_channel):
        super(Branch, self).__init__()
        self.c1_1 = BasicConv(in_channel, out_channel,
                              kernel_size=3, stride=1, relu=True)
        self.c1_2 = BasicConv(out_channel, out_channel,
                              kernel_size=3, stride=1, relu=True)
        self.c1_3 = BasicConv(out_channel, out_channel,
                              kernel_size=3, stride=1, relu=True)

    def forward(self, x):
        x1 = self.c1_1(x)
        x2 = self.c1_2(x1)
        x3 = self.c1_3(x2)
        return x3 + x2 + x1


class DFM(nn.Module):
    def __init__(self, in_channel, out_channel):
        super(DFM, self).__init__()

        self.branch1 = Branch(in_channel, out_channel)
        self.branch2 = Branch(in_channel, out_channel)
        self.conv1 = BasicConv(out_channel, out_channel,
                              kernel_size=3, stride=1, relu=True)
        self.conv2 = BasicConv(out_channel, out_channel,
                              kernel_size=3, stride=1, relu=True)

    def forward(self, f1, f2):
        x1 = self.branch1(f1)
        x2 = self.branch1(f2)
        x3 = self.branch2(f1)
        x4 = self.branch2(f2)
        x = torch.abs(x1 - x2)
        c1 = self.conv1(x)
        y = x3 + x4
        c2 = self.conv2(y)
        return c1 + c2


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


class USSFCNet(nn.Module):
    def __init__(self, in_ch, out_ch, ratio=0.5):
        super(USSFCNet, self).__init__()


        self.Conv_1x1 = nn.Conv2d(384, 16, kernel_size=3, stride=1, padding=1)

        self.mix1=MixFormer()
        self.mix2 = MixFormer()
    def forward(self, x1, x2):
        # encoding
        #batch=8
        # x1, x2 = torch.unsqueeze(x1[0], dim=0), torch.unsqueeze(x1[1], dim=0)
        c1_1 = self.mix1(x1)

        c1_2 = self.mix2(x2)
        #x1=self.dfm(c1_1,c1_2)
        x1 = paddle.abs(paddle.subtract(c1_1, c1_2))
        #print(x1.shape, 'c1_1')
        #MixFormer()

        #d1 = self.Conv_1x1(x1)
        #x1 =self.Conv_1x1(x1)
        #out = nn.Sigmoid()(d1)
        #print(x1)

        return x1


if __name__ == "__main__":
    A2016 = paddle.randn([1, 3, 256, 256])
    #A2016 = torch.randn(1, 3, 256, 256)
    # print (type(A2016))
    A2019 = paddle.randn([1, 3, 256, 256])
    model = USSFCNet(3, 1, ratio=0.5)
    out_result = model(A2016, A2019)
    #print(out_result.size())
    #summary(model, [(3, 256, 256), (3, 256, 256)])
    flops, params = profile(model, inputs=(A2016, A2019))
    #print(flops, params)
