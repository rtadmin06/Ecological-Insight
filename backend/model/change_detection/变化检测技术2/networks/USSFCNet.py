import torch.nn as nn
import torch
from thop import profile
from torchsummary import summary
from torch.nn import functional as F
from networks.modules.MSDConv_SSFC import MSDConv_SSFC
# from networks.modules.MSDConv_SSFC import MSDConv_SSFC, MSDConv_SSFC2, TransConv

# from networks.modules.Transfor import BASE_Transformer
# from mmengine.model import BaseModule, Sequential
# from mmcv.cnn.bricks.drop import build_dropout
# from mmcv.cnn import Conv2d, ConvModule, build_activation_layer

# from mmcv.cnn import build_activation_layer, build_conv_layer, build_norm_layer
# from mmengine.model import BaseModule

# from opencd.models.utils.builder import ITERACTION_LAYERS

from torch.nn.parameter import Parameter


class Eca_layer(nn.Module):
    """Constructs a ECA module.
    Args:
        channel: Number of channels of the input feature map
        k_size: Adaptive selection of kernel size
    """

    def __init__(self, k_size=3):
        super(Eca_layer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k_size, padding=(k_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # x: input features with shape [b, c, h, w]
        b, c, h, w = x.size()

        # feature descriptor on the global spatial information
        y = self.avg_pool(x)

        # Two different branches of ECA module
        y = self.conv(y.squeeze(-1).transpose(-1, -2)).transpose(-1, -2).unsqueeze(-1)

        # Multi-scale information fusion
        y = self.sigmoid(y)

        return x * y.expand_as(x)


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
            MSDConv_SSFC(in_ch, out_ch, dilation=4),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            MSDConv_SSFC(out_ch, out_ch, dilation=4),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, input):
        return self.Conv(input)

class DoubleConv1(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(DoubleConv1, self).__init__()
        self.Conv = nn.Sequential(
            MSDConv_SSFC2(in_ch, out_ch, dilation=4),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            MSDConv_SSFC2(out_ch, out_ch, dilation=4),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, input):
        return self.Conv(input)

class Trans_Conv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(Trans_Conv, self).__init__()
        self.Conv = nn.Sequential(
            TransConv(in_ch, out_ch, dilation=3),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
            # MSDConv_SSFC(out_ch, out_ch, dilation=3),
            # nn.BatchNorm2d(out_ch),
            # nn.ReLU(inplace=True)
        )

    def forward(self, input):
        return self.Conv(input)
class ChannelExchange(nn.Module):
    """
    channel exchange
    Args:
        p (float, optional): p of the features will be exchanged.
            Defaults to 1/2.
    """

    def __init__(self, p=1 / 2):
        super().__init__()
        assert p >= 0 and p <= 1
        self.p = int(1 / p)

    def forward(self, x1, x2):
        N, c, h, w = x1.shape

        exchange_map = torch.arange(c) % self.p == 0
        exchange_mask = exchange_map.unsqueeze(0).expand((N, -1))

        out_x1, out_x2 = torch.zeros_like(x1), torch.zeros_like(x2)
        out_x1[~exchange_mask, ...] = x1[~exchange_mask, ...]
        out_x2[~exchange_mask, ...] = x2[~exchange_mask, ...]
        out_x1[exchange_mask, ...] = x2[exchange_mask, ...]
        out_x2[exchange_mask, ...] = x1[exchange_mask, ...]

        return out_x1, out_x2


#@ITERACTION_LAYERS.register_module()
class SpatialExchange(nn.Module):
    """
    spatial exchange
    Args:
        p (float, optional): p of the features will be exchanged.
            Defaults to 1/2.
    """

    def __init__(self, p=1 / 2):
        super().__init__()
        assert p >= 0 and p <= 1
        self.p = int(1 / p)

    def forward(self, x1, x2):
        N, c, h, w = x1.shape
        exchange_mask = torch.arange(w) % self.p == 0

        out_x1, out_x2 = torch.zeros_like(x1), torch.zeros_like(x2)
        out_x1[..., ~exchange_mask] = x1[..., ~exchange_mask]
        out_x2[..., ~exchange_mask] = x2[..., ~exchange_mask]
        out_x1[..., exchange_mask] = x2[..., exchange_mask]
        out_x2[..., exchange_mask] = x1[..., exchange_mask]

        return out_x1, out_x2

class USSFCNet(nn.Module):
    def __init__(self, in_ch, out_ch, ratio=0.5, gaussian=False):
        super(USSFCNet, self).__init__()

        self.Maxpool = nn.MaxPool2d(kernel_size=2, stride=2)

        self.Conv1_1 = First_DoubleConv(in_ch, int(64 * ratio))
        self.Conv1_2 = First_DoubleConv(in_ch, int(64 * ratio))
        self.Conv2_1 = DoubleConv1(int(64 * ratio), int(128 * ratio))
        self.Conv2_2 = DoubleConv1(int(64 * ratio), int(128 * ratio))
        self.Conv3_1 = DoubleConv1(int(128 * ratio), int(256 * ratio))
        self.Conv3_2 = DoubleConv1(int(128 * ratio), int(256 * ratio))
        self.Conv4_1 = DoubleConv1(int(256 * ratio), int(512 * ratio))
        self.Conv4_2 = DoubleConv1(int(256 * ratio), int(512 * ratio))
        self.Conv5_1 = DoubleConv1(int(512 * ratio), int(1024 * ratio))
        self.Conv5_2 = DoubleConv1(int(512 * ratio), int(1024 * ratio))
        self.Conv1 = DoubleConv1(int(128 * ratio), int(64 * ratio))
        self.Conv2 = DoubleConv1(int(256 * ratio), int(128 * ratio))
        self.Conv3 = DoubleConv1(int(512 * ratio), int(256 * ratio))
        self.Conv4 = DoubleConv1(int(1024 * ratio), int(512 * ratio))
        self.Conv5 = DoubleConv1(int(2048 * ratio), int(1024 * ratio))
        self.Conv_5x5 = nn.Conv2d(int(512 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.Conv_4x4 = nn.Conv2d(int(256 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.Conv_3x3 = nn.Conv2d(int(128 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        # self.BASE = BASE_Transformer(dim=32, input_nc=3, output_nc=2,token_len=8,
        #                      with_pos='learned', enc_depth=1, dec_depth=4)
        self.TranConv1 = Trans_Conv(32, 32)
        self.TranConv2 = Trans_Conv(64, 64)
        self.TranConv3 = Trans_Conv(128, 128)
        self.TranConv4 = Trans_Conv(256, 256)
        self.TranConv5 = Trans_Conv(512, 512)

        self.Up5 = nn.ConvTranspose2d(int(1024 * ratio), int(512 * ratio), 2, stride=2)
        self.Up_conv5 = DoubleConv(int(1024 * ratio), int(512 * ratio))

        self.Up4 = nn.ConvTranspose2d(int(512 * ratio), int(256 * ratio), 2, stride=2)
        self.Up_conv4 = DoubleConv(int(512 * ratio), int(256 * ratio))

        self.Up3 = nn.ConvTranspose2d(int(256 * ratio), int(128 * ratio), 2, stride=2)
        self.Up_conv3 = DoubleConv(int(256 * ratio), int(128 * ratio))

        self.Up2 = nn.ConvTranspose2d(int(128 * ratio), int(64 * ratio), 2, stride=2)
        self.Up_conv2 = DoubleConv(int(128 * ratio), int(64 * ratio))

        self.Conv_1x1 = nn.Conv2d(int(64 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.channelexchange = ChannelExchange()
        self.spatialexchange = SpatialExchange()
        self.eca = Eca_layer()

    def forward(self, x1, x2):
        # encoding
        # x1, x2 = torch.unsqueeze(x1[0], dim=0), torch.unsqueeze(x1[1], dim=0)
        c1_1 = self.Conv1_1(x1)
        c1_2 = self.Conv1_2(x2)
        c1_1, c1_2 = self.spatialexchange(c1_1, c1_2)
        c1_1 = self.eca(c1_1)
        c1_2 = self.eca(c1_2)
        c1_1, c1_2 = self.channelexchange(c1_1, c1_2)

        #x1 = self.neck_layer1(c1_1,c1_2,'concat') #1, 64, 256, 256
        #x1 = self.Conv1(x1)


        x1 = torch.abs(torch.sub(c1_1, c1_2)) #1, 32, 256, 256
        # x1 = self.TranConv1(x1)

        # print(x1.size(), 'x1')


        c2_1 = self.Maxpool(c1_1)
        c2_1 = self.Conv2_1(c2_1)
        c2_2 = self.Maxpool(c1_2)
        c2_2 = self.Conv2_2(c2_2)
        c2_1, c2_2 = self.spatialexchange(c2_1, c2_2)
        c2_1 = self.eca(c2_1)
        c2_2 = self.eca(c2_2)
        c2_1, c2_2 = self.channelexchange(c2_1, c2_2)
        #x2 = self.neck_layer2(c2_1, c2_2, 'concat')
        #x2 = self.Conv2(x2)
        x2 = torch.abs(torch.sub(c2_1, c2_2))
        # x2 = self.TranConv2(x2)

        # print(x2.size(), 'x2.size----------')

        c3_1 = self.Maxpool(c2_1)
        c3_1 = self.Conv3_1(c3_1)
        c3_2 = self.Maxpool(c2_2)
        c3_2 = self.Conv3_2(c3_2)
        c3_1, c3_2 = self.spatialexchange(c3_1, c3_2)
        c3_1 = self.eca(c3_1)
        c3_2 = self.eca(c3_2)
        c3_1, c3_2 = self.channelexchange(c3_1, c3_2)
        #c3_1, c3_2 = self.spatialexchange(c3_1, c3_2)
        #x3 = self.neck_layer3(c3_1, c3_2, 'concat')
        #x3 = self.Conv3(x3)
        x3 = torch.abs(torch.sub(c3_1, c3_2))
        # x3 = self.TranConv3(x3)

        # print(x3.size(), 'x3.size----------')


        c4_1 = self.Maxpool(c3_1)
        c4_1 = self.Conv4_1(c4_1)
        c4_2 = self.Maxpool(c3_2)
        c4_2 = self.Conv4_2(c4_2)
        c4_1, c4_2 = self.spatialexchange(c4_1, c4_2)
        c4_1 = self.eca(c4_1)
        c4_2 = self.eca(c4_2)
        c4_1, c4_2 = self.channelexchange(c4_1, c4_2)
        #x4 = self.neck_layer4(c4_1, c4_2, 'concat')
        #x4 = self.Conv4(x4)
        #c4_1, c4_2 = self.channelexchange(c4_1, c4_2)
        x4 = torch.abs(torch.sub(c4_1, c4_2))
        # x4 = self.TranConv4(x4)

        # print(x4.size(), 'x4.size----------')

        c5_1 = self.Maxpool(c4_1)
        c5_1 = self.Conv5_1(c5_1)
        c5_2 = self.Maxpool(c4_2)
        c5_2 = self.Conv5_2(c5_2)
        c5_1, c5_2 = self.spatialexchange(c5_1, c5_2)
        c5_1 = self.eca(c5_1)
        c5_2 = self.eca(c5_2)
        c5_1, c5_2 = self.channelexchange(c5_1, c5_2)
        #x5 = self.neck_layer5(c5_1, c5_2, 'concat')
        #x5 = self.Conv5(x5)

        x5 = torch.abs(torch.sub(c5_1, c5_2))
        # x5 = self.TranConv5(x5)



        # decoding
        d5 = self.Up5(x5)
        # print(d5.size(),'d5')
        # d5 = self.TranConv4(d5)
        # print(d5.size(), 'd51')

        d5 = torch.cat((x4, d5), dim=1)
        d5 = self.Up_conv5(d5)

        d51 = self.Conv_5x5(d5)
        out8 = nn.Sigmoid()(d51)


        d4 = self.Up4(d5)
        # d4 = self.TranConv3(d4)
        d4 = torch.cat((x3, d4), dim=1)
        d4 = self.Up_conv4(d4)

        d41 = self.Conv_4x4(d4)
        out4 = nn.Sigmoid()(d41)

        d3 = self.Up3(d4)
        # d3 = self.TranConv2(d3)
        d3 = torch.cat((x2, d3), dim=1)
        d3 = self.Up_conv3(d3)

        d31 = self.Conv_3x3(d3)
        out2 = nn.Sigmoid()(d31)

        d2 = self.Up2(d3)
        # d2 = self.TranConv1(d2)
        d2 = torch.cat((x1, d2), dim=1)
        d2 = self.Up_conv2(d2)

        d1 = self.Conv_1x1(d2)
        
        out = nn.Sigmoid()(d1)

        return out8, out4, out2, out
        # return out


if __name__ == "__main__":
    A2016 = torch.randn(1, 3, 256, 256)
    A2019 = torch.randn(1, 3, 256, 256)
    model = USSFCNet(3, 1, ratio=0.5)
    out_result = model(A2016, A2019)
    #print(out_result)
    #summary(model, [(3, 256, 256), (3, 256, 256)])
    flops, params = profile(model, inputs=(A2016, A2019))
    print(flops, params) #16547934976.0 10708231.0
