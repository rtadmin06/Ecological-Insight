import torch.nn as nn
import torch
from thop import profile
from torchsummary import summary
import torch.nn.functional as F
from networks.modules.MSDConv_SSFC import MSDConv_SSFC
from networks.modules.layers import *
from networks.modules.dcn_v2 import DCN

class MarginMaximization(nn.Module):
    def __init__(self, num_filters=128):
        super().__init__()
        self.offset = nn.Sequential(nn.Conv2d(num_filters*2, num_filters, kernel_size=1, stride=1, padding=0, bias=False),
                                    nn.BatchNorm2d(num_filters))
        self.dcpack_L2 = DCN(num_filters, num_filters, 3, stride=1, padding=1, dilation=1, deformable_groups=8,
                                extra_offset_mask=True)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, fea1, fea2):

        offset = self.offset(torch.cat([fea1, fea2], dim=1))
        fea_mm = self.relu(self.dcpack_L2([fea2, offset], None))
        fea = torch.cat([fea1, fea_mm], dim=1)

        return fea

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
        self.margin = MarginMaximization()

    def forward(self, x1, x2):
        # encoding
        #batch=8
        # x1, x2 = torch.unsqueeze(x1[0], dim=0), torch.unsqueeze(x1[1], dim=0)
        c1_1 = self.Conv1_1(x1)
        c1_2 = self.Conv1_2(x2)
        x1 = torch.abs(torch.sub(c1_1, c1_2))
        c2_1 = self.Maxpool(c1_1)
        #print(c2_1.size(),'c2_1')#8, 32, 128, 128
        c2_1 = self.Conv2_1(c2_1)
        #print(c2_1.size(),'c2_1')#8, 64, 128, 128
        c2_2 = self.Maxpool(c1_2)
        #print(c2_2.size(), 'c2_1-conv')
        c2_2 = self.Conv2_2(c2_2)
        #print(c2_2.size(), 'c2_2')#8, 32, 128, 128
        x2 = torch.abs(torch.sub(c2_1, c2_2))

        c3_1 = self.Maxpool(c2_1)

        c3_1 = self.Conv3_1(c3_1)


        c3_2 = self.Maxpool(c2_2)

        c3_2 = self.Conv3_2(c3_2)
        #print(c3_2.size(), 'c3_2')#[8, 32, 64, 64]
        x3 = torch.abs(torch.sub(c3_1, c3_2))

        c4_1 = self.Maxpool(c3_1)

        c4_1 = self.Conv4_1(c4_1)
        #print(c4_1.size(), 'c4_1')#8, 256, 32, 32
        c4_2 = self.Maxpool(c3_2)

        c4_2 = self.Conv4_2(c4_2)
        #print(c4_2.size(), 'c4_2')
        x4 = torch.abs(torch.sub(c4_1, c4_2))

        c5_1 = self.Maxpool(c4_1)
        c5_1 = self.Conv5_1(c5_1)

        c5_2 = self.Maxpool(c4_2)

        c5_2 = self.Conv5_2(c5_2)
        #print(c5_2.size(), 'c5_2')#8, 512, 16, 16
        x5 = torch.abs(torch.sub(c5_1, c5_2))

        d5 = self.Up5(x5)

        # d5 = torch.cat((x4, d5), dim=1)
        d5 = self.margin(x4, d5)
        d5 = self.Up_conv5(d5)

        d51 = self.Conv_5x5(d5)
        out8 = nn.Sigmoid()(d51)

        d4 = self.Up4(d5)
        # d4 = torch.cat((x3, d4), dim=1)
        d4 = self.margin(x3, d4)
        d4 = self.Up_conv4(d4)
        d41 = self.Conv_4x4(d4)
        out4 = nn.Sigmoid()(d41)

        d3 = self.Up3(d4)
        # d3 = torch.cat((x2, d3), dim=1)
        d3 = self.margin(x2, d3)
        d3 = self.Up_conv3(d3)
        d31 = self.Conv_3x3(d3)
        out2 = nn.Sigmoid()(d31)

        d2 = self.Up2(d3)
        # d2 = torch.cat((x1, d2), dim=1)
        d2 = self.margin(x1, d2)
        d2 = self.Up_conv2(d2)
        d2 = self.Conv11(d2)
        #print(d2.size(), 'd2')
        d1 = self.Conv_1x1(d2)

        out = nn.Sigmoid()(d1)

        return out8, out4, out2, out


if __name__ == "__main__":
    A2016 = torch.randn(8, 3, 256, 256)
    A2019 = torch.randn(8, 3, 256, 256)
    model = USSFCNet(3, 1, ratio=0.5)
    out_result = model(A2016, A2019)
    print(out_result.size())
    #summary(model, [(3, 256, 256), (3, 256, 256)])
    flops, params = profile(model, inputs=(A2016, A2019))
    print(flops, params)
