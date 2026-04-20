import torch.nn as nn
import torch
from thop import profile
from torchsummary import summary
from torch.nn import functional as F
from networks.modules.MSDConv_SSFC import MSDConv_SSFC
from mmengine.model import BaseModule, Sequential
from mmcv.cnn.bricks.drop import build_dropout
from mmcv.cnn import Conv2d, ConvModule, build_activation_layer

from mmcv.cnn import build_activation_layer, build_conv_layer, build_norm_layer
from mmengine.model import BaseModule

#from opencd.models.utils.builder import ITERACTION_LAYERS
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


#@ITERACTION_LAYERS.register_module()
class ChannelExchange(BaseModule):
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
class SpatialExchange(BaseModule):
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


#@ITERACTION_LAYERS.register_module()
class Aggregation_distribution(BaseModule):
    # Aggregation_Distribution Layer (AD)
    def __init__(self,
                 channels,
                 num_paths=2,
                 attn_channels=None,
                 act_cfg=dict(type='ReLU'),
                 norm_cfg=dict(type='BN', requires_grad=True)):
        super().__init__()
        self.num_paths = num_paths  # `2` is supported.
        attn_channels = attn_channels or channels // 16
        attn_channels = max(attn_channels, 8)

        self.fc_reduce = nn.Conv2d(channels, attn_channels, kernel_size=1, bias=False)
        self.bn = build_norm_layer(norm_cfg, attn_channels)[1]
        self.act = build_activation_layer(act_cfg)
        self.fc_select = nn.Conv2d(attn_channels, channels * num_paths, kernel_size=1, bias=False)

    def forward(self, x1, x2):
        x = torch.stack([x1, x2], dim=1)
        attn = x.sum(1).mean((2, 3), keepdim=True)
        attn = self.fc_reduce(attn)
        attn = self.bn(attn)
        attn = self.act(attn)
        attn = self.fc_select(attn)
        B, C, H, W = attn.shape
        attn1, attn2 = attn.reshape(B, self.num_paths, C // self.num_paths, H, W).transpose(0, 1)
        attn1 = torch.sigmoid(attn1)
        attn2 = torch.sigmoid(attn2)
        return x1 * attn1, x2 * attn2

class FeatureFusionNeck(BaseModule):
    """Feature Fusion Neck.

    Args:
        policy (str): The operation to fuse features. candidates
            are `concat`, `sum`, `diff` and `Lp_distance`.
        in_channels (Sequence(int)): Input channels.
        channels (int): Channels after modules, before conv_seg.
        out_indices (tuple[int]): Output from which layer.
    """

    def __init__(self,
                 policy,
                 in_channels=None,
                 channels=None,
                 out_indices=(0, 1, 2, 3)):
        super().__init__()
        self.policy = policy
        self.in_channels = in_channels
        self.channels = channels
        self.out_indices = out_indices

    @staticmethod
    def fusion(x1, x2, policy):
        """Specify the form of feature fusion"""

        _fusion_policies = ['concat', 'sum', 'diff', 'abs_diff']
        assert policy in _fusion_policies, 'The fusion policies {} are ' \
                                           'supported'.format(_fusion_policies)

        if policy == 'concat':
            x = torch.cat([x1, x2], dim=1)
        elif policy == 'sum':
            x = x1 + x2
        elif policy == 'diff':
            x = x2 - x1
        elif policy == 'abs_diff':
            x = torch.abs(x1 - x2)

        return x

    def forward(self, x1, x2):
        """Forward function."""

        assert len(x1) == len(x2), "The features x1 and x2 from the" \
                                   "backbone should be of equal length"
        outs = []
        for i in range(len(x1)):
            out = self.fusion(x1[i], x2[i], self.policy)
            outs.append(out)

        outs = [outs[i] for i in self.out_indices]
        return tuple(outs)

class FDAF(BaseModule):
    """Flow Dual-Alignment Fusion Module.

    Args:
        in_channels (int): Input channels of features.
        conv_cfg (dict | None): Config of conv layers.
            Default: None
        norm_cfg (dict | None): Config of norm layers.
            Default: dict(type='BN')
        act_cfg (dict): Config of activation layers.
            Default: dict(type='ReLU')
    """

    def __init__(self,
                 in_channels,
                 conv_cfg=None,
                 norm_cfg=dict(type='IN'),
                 act_cfg=dict(type='GELU')):
        super(FDAF, self).__init__()
        self.in_channels = in_channels
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.act_cfg = act_cfg
        # TODO
        conv_cfg = None
        norm_cfg = dict(type='IN')
        act_cfg = dict(type='GELU')

        kernel_size = 5
        self.flow_make = Sequential(
            nn.Conv2d(in_channels * 2, in_channels * 2, kernel_size=kernel_size, padding=(kernel_size - 1) // 2,
                      bias=True, groups=in_channels * 2),
            nn.InstanceNorm2d(in_channels * 2),
            nn.GELU(),
            nn.Conv2d(in_channels * 2, 4, kernel_size=1, padding=0, bias=False),
        )

    def forward(self, x1, x2, fusion_policy=None):
        """Forward function."""

        output = torch.cat([x1, x2], dim=1)
        flow = self.flow_make(output)
        f1, f2 = torch.chunk(flow, 2, dim=1)
        x1_feat = self.warp(x1, f1) - x2
        x2_feat = self.warp(x2, f2) - x1

        if fusion_policy == None:
            return x1_feat, x2_feat

        output = FeatureFusionNeck.fusion(x1_feat, x2_feat, fusion_policy)
        return output

    @staticmethod
    def warp(x, flow):
        n, c, h, w = x.size()

        norm = torch.tensor([[[[w, h]]]]).type_as(x).to(x.device)
        col = torch.linspace(-1.0, 1.0, h).view(-1, 1).repeat(1, w)
        row = torch.linspace(-1.0, 1.0, w).repeat(h, 1)
        grid = torch.cat((row.unsqueeze(2), col.unsqueeze(2)), 2)
        grid = grid.repeat(n, 1, 1, 1).type_as(x).to(x.device)
        grid = grid + flow.permute(0, 2, 3, 1) / norm

        output = F.grid_sample(x, grid, align_corners=True)
        return output

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

class MixFFN(BaseModule):
    """An implementation of MixFFN of Segformer. \
        Here MixFFN is uesd as projection head of Changer.
    Args:
        embed_dims (int): The feature dimension. Same as
            `MultiheadAttention`. Defaults: 256.
        feedforward_channels (int): The hidden dimension of FFNs.
            Defaults: 1024.
        act_cfg (dict, optional): The activation config for FFNs.
            Default: dict(type='ReLU')
        ffn_drop (float, optional): Probability of an element to be
            zeroed in FFN. Default 0.0.
        dropout_layer (obj:`ConfigDict`): The dropout_layer used
            when adding the shortcut.
        init_cfg (obj:`mmcv.ConfigDict`): The Config for initialization.
            Default: None.
    """

    def __init__(self,
                 embed_dims,
                 feedforward_channels,
                 act_cfg=dict(type='GELU'),
                 ffn_drop=0.,
                 dropout_layer=None,
                 init_cfg=None):
        super(MixFFN, self).__init__(init_cfg)

        self.embed_dims = embed_dims
        self.feedforward_channels = feedforward_channels
        self.act_cfg = act_cfg
        self.activate = build_activation_layer(act_cfg)

        in_channels = embed_dims
        fc1 = Conv2d(
            in_channels=in_channels,
            out_channels=feedforward_channels,
            kernel_size=1,
            stride=1,
            bias=True)
        # 3x3 depth wise conv to provide positional encode information
        pe_conv = Conv2d(
            in_channels=feedforward_channels,
            out_channels=feedforward_channels,
            kernel_size=3,
            stride=1,
            padding=(3 - 1) // 2,
            bias=True,
            groups=feedforward_channels)
        fc2 = Conv2d(
            in_channels=feedforward_channels,
            out_channels=in_channels,
            kernel_size=1,
            stride=1,
            bias=True)
        drop = nn.Dropout(ffn_drop)
        layers = [fc1, pe_conv, self.activate, drop, fc2, drop]
        self.layers = Sequential(*layers)
        self.dropout_layer = build_dropout(
            dropout_layer) if dropout_layer else torch.nn.Identity()

    def forward(self, x, identity=None):
        out = self.layers(x)
        if identity is None:
            identity = x
        return identity + self.dropout_layer(out)

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
    def __init__(self, in_ch, out_ch, ratio=0.5, gaussian=False):
        super(USSFCNet, self).__init__()

        self.Maxpool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.color_filter = FilterLow(recursions=1, stride=1, kernel_size=5, padding=False,
                                      gaussian=gaussian)

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
        self.Conv1 = DoubleConv(int(128 * ratio), int(64 * ratio))
        self.Conv2 = DoubleConv(int(256 * ratio), int(128 * ratio))
        self.Conv3 = DoubleConv(int(512 * ratio), int(256 * ratio))
        self.Conv4 = DoubleConv(int(1024 * ratio), int(512 * ratio))
        self.Conv5 = DoubleConv(int(2048 * ratio), int(1024 * ratio))
        self.Conv_5x5 = nn.Conv2d(int(512 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.Conv_4x4 = nn.Conv2d(int(256 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.Conv_3x3 = nn.Conv2d(int(128 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        

        self.Up5 = nn.ConvTranspose2d(int(1024 * ratio), int(512 * ratio), 2, stride=2)
        self.Up_conv5 = DoubleConv(int(1024 * ratio), int(512 * ratio))

        self.Up4 = nn.ConvTranspose2d(int(512 * ratio), int(256 * ratio), 2, stride=2)
        self.Up_conv4 = DoubleConv(int(512 * ratio), int(256 * ratio))

        self.Up3 = nn.ConvTranspose2d(int(256 * ratio), int(128 * ratio), 2, stride=2)
        self.Up_conv3 = DoubleConv(int(256 * ratio), int(128 * ratio))

        self.Up2 = nn.ConvTranspose2d(int(128 * ratio), int(64 * ratio), 2, stride=2)
        self.Up_conv2 = DoubleConv(int(128 * ratio), int(64 * ratio))

        self.Conv_1x1 = nn.Conv2d(int(64 * ratio), out_ch, kernel_size=1, stride=1, padding=0)
        self.neck_layer1 = FDAF(32 // 2)
        self.neck_layer2 = FDAF(64 // 2)
        self.neck_layer3 = FDAF(128 // 2)
        self.neck_layer4 = FDAF(256 // 2)
        self.neck_layer5 = FDAF(512 // 2)
        self.channelexchange = ChannelExchange()
        self.spatialexchange = SpatialExchange()



    def forward(self, x1, x2):
        # encoding
        # x1, x2 = torch.unsqueeze(x1[0], dim=0), torch.unsqueeze(x1[1], dim=0)
        c1_1 = self.Conv1_1(x1)
        c1_2 = self.Conv1_2(x2)
        #x1 = self.neck_layer1(c1_1,c1_2,'concat') #1, 64, 256, 256
        #x1 = self.Conv1(x1)


        x1 = torch.abs(torch.sub(c1_1, c1_2)) #1, 32, 256, 256
        #print(x1.size(), 'x1')


        c2_1 = self.Maxpool(c1_1)
        c2_1 = self.Conv2_1(c2_1)
        c2_2 = self.Maxpool(c1_2)
        c2_2 = self.Conv2_2(c2_2)
        #x2 = self.neck_layer2(c2_1, c2_2, 'concat')
        #x2 = self.Conv2(x2)
        x2 = torch.abs(torch.sub(c2_1, c2_2))

        #print(x2.size(), 'x2.size----------')

        c3_1 = self.Maxpool(c2_1)
        c3_1 = self.Conv3_1(c3_1)
        c3_2 = self.Maxpool(c2_2)
        c3_2 = self.Conv3_2(c3_2)
        c3_1, c3_2 = self.spatialexchange(c3_1, c3_2)
        #x3 = self.neck_layer3(c3_1, c3_2, 'concat')
        #x3 = self.Conv3(x3)
        x3 = torch.abs(torch.sub(c3_1, c3_2))

        #print(x3.size(), 'x3.size----------')


        c4_1 = self.Maxpool(c3_1)
        c4_1 = self.Conv4_1(c4_1)
        c4_2 = self.Maxpool(c3_2)
        c4_2 = self.Conv4_2(c4_2)
        #x4 = self.neck_layer4(c4_1, c4_2, 'concat')
        #x4 = self.Conv4(x4)
        c4_1, c4_2 = self.channelexchange(c4_1, c4_2)
        x4 = torch.abs(torch.sub(c4_1, c4_2))

        #print(x4.size(), 'x4.size----------')

        c5_1 = self.Maxpool(c4_1)
        c5_1 = self.Conv5_1(c5_1)
        c5_2 = self.Maxpool(c4_2)
        c5_2 = self.Conv5_2(c5_2)
        c5_1, c5_2 = self.channelexchange(c5_1, c5_2)
        #x5 = self.neck_layer5(c5_1, c5_2, 'concat')
        #x5 = self.Conv5(x5)

        x5 = torch.abs(torch.sub(c5_1, c5_2))



        # decoding
        d5 = self.Up5(x5)

        d5 = self.neck_layer5(x4, d5, 'concat')
        d5 = self.Up_conv5(d5)

        d51 = self.Conv_5x5(d5)
        out8 = nn.Sigmoid()(d51)


        d4 = self.Up4(d5)
        d4 = self.neck_layer4(x3, d4, 'concat')
        d4 = self.Up_conv4(d4)

        d41 = self.Conv_4x4(d4)
        out4 = nn.Sigmoid()(d41)

        d3 = self.Up3(d4)
        d3 = self.neck_layer3(x2, d3, 'concat')
        d3 = self.Up_conv3(d3)

        d31 = self.Conv_3x3(d3)
        out2 = nn.Sigmoid()(d31)

        d2 = self.Up2(d3)
        d2 = self.neck_layer2(x1, d2, 'concat')
        d2 = self.Up_conv2(d2)

        d1 = self.Conv_1x1(d2)
        
        out = nn.Sigmoid()(d1)

        return out8, out4, out2, out


if __name__ == "__main__":
    A2016 = torch.randn(1, 3, 256, 256)
    A2019 = torch.randn(1, 3, 256, 256)
    model = USSFCNet(3, 1, ratio=0.5)
    out_result = model(A2016, A2019)
    #print(out_result.size())
    #summary(model, [(3, 256, 256), (3, 256, 256)])
    flops, params = profile(model, inputs=(A2016, A2019))
    #print(flops, params)
