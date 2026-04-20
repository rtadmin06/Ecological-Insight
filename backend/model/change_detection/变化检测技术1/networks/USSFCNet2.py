import torch.nn as nn
import torch
from thop import profile
from torchsummary import summary

from networks.modules.MSDConv_SSFC import MSDConv_SSFC

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

class Mix(nn.Module):
    def __init__(self, m=-0.80):
        super(Mix, self).__init__()
        w = torch.nn.Parameter(torch.FloatTensor([m]), requires_grad=True)
        w = torch.nn.Parameter(w, requires_grad=True)
        self.w = w
        self.mix_block = nn.Sigmoid()

    def forward(self, fea1, fea2):
        mix_factor = self.mix_block(self.w)
        out = fea1 * mix_factor.expand_as(fea1) + fea2 * (1 - mix_factor.expand_as(fea2))
        return out

class USSFCNet(nn.Module):
    def __init__(self, in_ch, out_ch, ratio=0.5):
        super(USSFCNet, self).__init__()

        self.Maxpool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.mix1 = Mix()

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

        self.Up4 = nn.ConvTranspose2d(int(512 * ratio), int(256 * ratio), 2, stride=2)
        self.Up_conv4 = DoubleConv(int(512 * ratio), int(256 * ratio))

        self.Up3 = nn.ConvTranspose2d(int(256 * ratio), int(128 * ratio), 2, stride=2)
        self.Up_conv3 = DoubleConv(int(256 * ratio), int(128 * ratio))

        self.Up2 = nn.ConvTranspose2d(int(128 * ratio), int(64 * ratio), 2, stride=2)
        self.Up_conv2 = DoubleConv(int(128 * ratio), int(64 * ratio))

        self.Conv_1x1 = nn.Conv2d(int(64 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.la5 = nn.Conv2d(int(512 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.la4 = nn.Conv2d(int(256 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.la3 = nn.Conv2d(int(128 * ratio), out_ch, kernel_size=1, stride=1, padding=0)


    def forward(self, x1, x2):
        # encoding
        # x1, x2 = torch.unsqueeze(x1[0], dim=0), torch.unsqueeze(x1[1], dim=0)
        c1_1 = self.Conv1_1(x1)
        c1_2 = self.Conv1_2(x2)
        x1 = torch.abs(torch.sub(c1_1, c1_2))
        #print(c1_1.size(),'c1_1')
        #print(x1.size(), 'x1')
        # x1 = x1_1+x1_2


        c2_1 = self.Maxpool(c1_1)
        c2_1 = self.Conv2_1(c2_1)
        c2_2 = self.Maxpool(c1_2)
        c2_2 = self.Conv2_2(c2_2)
        x2 = torch.abs(torch.sub(c2_1, c2_2))
        #print(c2_1.size(), 'c2_1')
        #print(x2.size(), 'x2')
        # x2_1 = self.dfm1(c2_1, c2_2)
        # x2 = x2_1+x2_2
        #print(x2.size(), 'x2.size----------')

        c3_1 = self.Maxpool(c2_1)
        c3_1 = self.Conv3_1(c3_1)
        c3_2 = self.Maxpool(c2_2)
        c3_2 = self.Conv3_2(c3_2)
        x3 = torch.abs(torch.sub(c3_1, c3_2))
        #print(c3_1.size(), 'c3_1')
        #print(x3.size(), 'x3')
        # x3_2 = self.dfm2(c3_1, c3_2)
        # x3 = x3_1+x3_2
        #print(x3.size(), 'x3.size----------')


        c4_1 = self.Maxpool(c3_1)
        c4_1 = self.Conv4_1(c4_1)
        c4_2 = self.Maxpool(c3_2)
        c4_2 = self.Conv4_2(c4_2)
        x4 = torch.abs(torch.sub(c4_1, c4_2))
        #print(c4_1.size(), 'c4_1')
        #print(x4.size(), 'x1')
        # x4_2 = self.dfm3(c4_1, c4_2)
        # x4= x4_1+x4_2
        #print(x4.size(), 'x4.size----------')

        c5_1 = self.Maxpool(c4_1)
        c5_1 = self.Conv5_1(c5_1)
        c5_2 = self.Maxpool(c4_2)
        c5_2 = self.Conv5_2(c5_2)
        x5 = torch.abs(torch.sub(c5_1, c5_2))
        #print(c5_1.size(), 'c5_1')
        #print(x5.size(), 'x5')
        # x5_2 = self.dfm4(c5_1, c5_2)
        # x5 = x5_1+x5_2
        #print(x5.size(), 'x5.size----------')

        # decoding

        d5_1 = self.Up5(c5_1)
        d5_1 = self.mix1(c4_1, d5_1)
        d5_2 = self.Up5(c5_2)
        d5_2 = self.mix1(c4_2, d5_2)
        #d5 = self.Up5(x5)
        d5 = torch.abs(torch.sub(d5_1, d5_2))
        #d5 = torch.cat((x4, d5), dim=1)
        d5 = self.mix1(x4, d5)
        #print(d5.size(), 'd5_2')
        #d5 = self.Up_conv5(d5)
        #print(d5.size(), 'd5')
        d51 = self.la5(d5)
        out8 = nn.Sigmoid()(d51)

        #d4 = self.Up4(d5)
        d4_1 = self.Up4(c4_1)
        d4_1 = self.mix1(c3_1, d4_1)
        d4_2 = self.Up4(c4_2)
        d4_2 = self.mix1(c3_2, d4_2)
        d4 = torch.abs(torch.sub(d4_1, d4_2))

        #d4 = torch.cat((x3, d4), dim=1)
        d4 = self.mix1(x3, d4)
        d41 = self.la4(d4)
        out4 = nn.Sigmoid()(d41)

        # d3 = self.Up3(d4)
        d3_1 = self.Up3(c3_1)
        d3_1 = self.mix1(c2_1, d3_1)
        d3_2 = self.Up3(c3_2)
        d3_2 = self.mix1(c2_2, d3_2)
        d3 = torch.abs(torch.sub(d3_1, d3_2))
        # d3 = torch.cat((x2, d3), dim=1)
        # d3 = self.Up_conv3(d3)
        d3 = self.mix1(x2, d3)
        d31 = self.la3(d3)
        out2 = nn.Sigmoid()(d31)

        #d2 = self.Up2(d3)
        d2_1 = self.Up2(c2_1)
        d2_1 = self.mix1(c1_1, d2_1)
        d2_2 = self.Up2(c2_2)
        d2_2 = self.mix1(c1_2, d2_2)
        d2 = torch.abs(torch.sub(d2_1, d2_2))
        # d2 = torch.cat((x1, d2), dim=1)
        # d2 = self.Up_conv2(d2)
        d2 = self.mix1(x1, d2)
        #print(d2.size(),'d2')

        d1 = self.Conv_1x1(d2)
        #print(d1.size(),'d1')
        out = nn.Sigmoid()(d1)

        return out8,out4,out2,out


if __name__ == "__main__":
    A2016 = torch.randn(1, 3, 256, 256)
    A2019 = torch.randn(1, 3, 256, 256)
    lables = torch.randn(1, 3, 256, 256)



    lables8 = torch.nn.functional.interpolate(lables, scale_factor=1/8, mode='bilinear', align_corners=False)
    lables4 = torch.nn.functional.interpolate(lables, scale_factor=1 /4, mode='bilinear', align_corners=False)
    lables2 = torch.nn.functional.interpolate(lables, scale_factor=1 / 2, mode='bilinear', align_corners=False)
    #print(lables8.size(),'lables8')
    model = USSFCNet(3, 3, ratio=0.5)
    out_result = model(A2016, A2019)
    out=out_result[3]
    out8=out_result[0]
    out4 = out_result[1]
    out2 = out_result[2]

    criterion_ce = nn.BCELoss()
    loss = criterion_ce(out,lables)
    loss8 = criterion_ce(out8, lables8)
    loss4 = criterion_ce(out4, lables4)
    loss2 = criterion_ce(out2, lables2)
    #loss4 = criterion_ce(out_result, lables4)
    #loss2 = criterion_ce(out_result, lables2)
   # print(loss8,'loss')
    #print(out_result.size())
    #summary(model, [(3, 256, 256), (3, 256, 256)])
    flops, params = profile(model, inputs=(A2016, A2019))
    #print(flops, params)
