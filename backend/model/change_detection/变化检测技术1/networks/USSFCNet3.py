import torch.nn as nn
import torch
from thop import profile
from torchsummary import summary

from networks.modules.MSDConv_SSFC import MSDConv_SSFC
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
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

        self.Maxpool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dfm = DFM(32,32)
        self.dfm1=DFM(64,64)
        self.dfm2 = DFM(128, 128)
        self.dfm3= DFM(256, 256)
        self.dfm4 = DFM(512, 512)

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


    def forward(self, x1, x2):
        # encoding
        # x1, x2 = torch.unsqueeze(x1[0], dim=0), torch.unsqueeze(x1[1], dim=0)
        c1_1 = self.Conv1_1(x1)
        c1_2 = self.Conv1_2(x2)
        x1=self.dfm(c1_1,c1_2)
        x1_1 = torch.abs(torch.sub(c1_1, c1_2))
        x1 = x1+ x1_1
        #print(x11.size(),'x11')
        input10=x1.narrow(0,1,1)
        rnn = nn.GRU(256, 256, 2).to(device)
        
        #print(input10.size(),'input10')
        input1 = torch.squeeze(input10, 0)
        #print(input.size(),'input')
        output, hn = rnn(input1)
        #print(output.size(),'output.size')
        #print(output.size(),'output')
        x1 = torch.unsqueeze(output, 0)

        x1_1=self.Conv2_1(x1)
        x1_1=self.Maxpool(x1_1)
        #print(x1_1.size(),'x1_1')
        #input10=x1_1.narrow(0,1,1)
        c2_1 = self.Maxpool(c1_1)
        c2_1 = self.Conv2_1(c2_1)
        c2_2 = self.Maxpool(c1_2)
        c2_2 = self.Conv2_2(c2_2)
        x21 = torch.abs(torch.sub(c2_1, c2_2))
        x22 = self.dfm1(c2_1, c2_2)
        x2=x21+x22
        rnn = nn.GRU(128, 128, 64).to(device)
        input20=x2.narrow(0,1,1)
        input2 = torch.squeeze(input20, 0)
        h0=torch.squeeze(x1_1, 0)
        output2, hn = rnn(input2,h0)
        #print(output2.size(),'output2')
        x2 = torch.unsqueeze(output2, 0)
        x2_1 = self.Conv3_1(x2)
        x2_1 = self.Maxpool(x2_1)

        c3_1 = self.Maxpool(c2_1)
        c3_1 = self.Conv3_1(c3_1)
        c3_2 = self.Maxpool(c2_2)
        c3_2 = self.Conv3_2(c3_2)
        x31 = torch.abs(torch.sub(c3_1, c3_2))
        x32 = self.dfm2(c3_1, c3_2)
        x3=x31+x32
        rnn = nn.GRU(64, 64, 128).to(device)
        input30=x3.narrow(0,1,1)
        input3 = torch.squeeze(input30, 0)
        h2 = torch.squeeze(x2_1, 0)
        output3, hn = rnn(input3, h2)
        x3 = torch.unsqueeze(output3, 0)
        #print(output3.size(), 'x3.size----------')
        x3_1 = self.Conv4_1(x3)
        x3_1 = self.Maxpool(x3_1)

        c4_1 = self.Maxpool(c3_1)
        c4_1 = self.Conv4_1(c4_1)
        c4_2 = self.Maxpool(c3_2)
        c4_2 = self.Conv4_2(c4_2)
        x41 = self.dfm3(c4_1, c4_2)
        x42 = torch.abs(torch.sub(c4_1, c4_2))
        x4=x41+x42
        rnn = nn.GRU(32, 32, 256).to(device)
        input40=x4.narrow(0,1,1)
        input4 = torch.squeeze(input40, 0)
        h3 = torch.squeeze(x3_1, 0)
        output4, hn = rnn(input4, h3)
        x4 = torch.unsqueeze(output4, 0)
        #print(output4.size(), 'x4.size----------')
        #x4 = self.dfm3(c4_1, c4_2)
        #print(x4.size(), 'x4.size----------')
        x4_1 = self.Conv5_1(x4)
        x4_1 = self.Maxpool(x4_1)

        c5_1 = self.Maxpool(c4_1)
        c5_1 = self.Conv5_1(c5_1)
        c5_2 = self.Maxpool(c4_2)
        c5_2 = self.Conv5_2(c5_2)
        x51 = torch.abs(torch.sub(c5_1, c5_2))
        x52 = self.dfm4(c5_1, c5_2)
        x5=x51+x52
        #print(x5.size(), 'x5.size----------')
        rnn = nn.GRU(16, 16, 512).to(device)
        input50=x5.narrow(0,1,1)
        input5 = torch.squeeze(input50, 0)
        h4 = torch.squeeze(x4_1, 0)
        output5, hn = rnn(input5, h4)
        x5 = torch.unsqueeze(output5, 0)
        print(x5.size(), 'x4.size----------')
        # decoding
        d5 = self.Up5(x5)
        d5 = torch.cat((x4, d5), dim=1)
        d5 = self.Up_conv5(d5)

        d4 = self.Up4(d5)
        d4 = torch.cat((x3, d4), dim=1)
        d4 = self.Up_conv4(d4)

        d3 = self.Up3(d4)
        d3 = torch.cat((x2, d3), dim=1)
        d3 = self.Up_conv3(d3)

        d2 = self.Up2(d3)
        d2 = torch.cat((x1, d2), dim=1)
        d2 = self.Up_conv2(d2)

        d1 = self.Conv_1x1(d2)
        out = nn.Sigmoid()(d1)

        return out


if __name__ == "__main__":
    A2016 = torch.randn(1, 3, 256, 256)
    A2019 = torch.randn(1, 3, 256, 256)
    model = USSFCNet(3, 1, ratio=0.5)
    out_result = model(A2016, A2019)
    #print(out_result.size())
    #summary(model, [(3, 256, 256), (3, 256, 256)])
    flops, params = profile(model, inputs=(A2016, A2019))
    #print(flops, params)
