import torch as nn
import torch
import torch.nn as nn
import mmcv
from thop import profile
from mmcv.cnn import ConvModule
class SELayer(nn.Module):
    """Squeeze-and-Excitation Module.

    Args:
        channels (int): The input (and output) channels of the SE layer.
        ratio (int): Squeeze ratio in SELayer, the intermediate channel will be
            ``int(channels/ratio)``. Default: 16.
        conv_cfg (None or dict): Config dict for convolution layer.
            Default: None, which means using conv2d.
        act_cfg (dict or Sequence[dict]): Config dict for activation layer.
            If act_cfg is a dict, two activation layers will be configured
            by this dict. If act_cfg is a sequence of dicts, the first
            activation layer will be configured by the first dict and the
            second activation layer will be configured by the second dict.
            Default: (dict(type='ReLU'), dict(type='HSigmoid', bias=3.0,
            divisor=6.0)).
    """

    def __init__(self,
                 channels,
                 ratio=16,
                 conv_cfg=None,
                 act_cfg=(dict(type='ReLU'),
                        #   dict(type='HSigmoid', bias=3.0, divisor=6.0),
                          dict(type='Sigmoid')
                          )
                          ):
        super(SELayer, self).__init__()
        if isinstance(act_cfg, dict):
            act_cfg = (act_cfg, act_cfg)
        assert len(act_cfg) == 2
        assert mmcv.is_tuple_of(act_cfg, dict)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.conv1 = ConvModule(
            in_channels=channels,
            # out_channels=make_divisible(channels // ratio, 8),
            out_channels=channels // ratio,
            kernel_size=1,
            stride=1,
            conv_cfg=conv_cfg,
            act_cfg=act_cfg[0])
        self.conv2 = ConvModule(
            # in_channels=make_divisible(channels // ratio, 8),
            in_channels=channels // ratio,
            out_channels=channels,
            kernel_size=1,
            stride=1,
            conv_cfg=conv_cfg,
            act_cfg=act_cfg[1])

    def forward(self, x):
        out = self.global_avgpool(x)
        out = self.conv1(out)
        out = self.conv2(out)
        return out
class _FrequencyMix(nn.Module):
    '''
    Frequency Mixing module
    '''

    def __init__(self,
                 in_channels,
                 k_list=[2],
                 # freq_list=[2, 3, 5, 7, 9, 11],
                 fs_feat='feat',
                 lp_type='freq_channel_att',
                 act='sigmoid',
                 channel_res=True,
                 spatial='conv',
                 spatial_group=1,
                 compress_ratio=16,
                 ):
        super().__init__()
        k_list.sort()
        # print()
        self.k_list = k_list
        # self.freq_list = freq_list
        self.lp_list = nn.ModuleList()
        self.freq_weight_conv_list = nn.ModuleList()
        self.fs_feat = fs_feat
        self.lp_type = lp_type
        self.in_channels = in_channels
        self.channel_res = channel_res
        if spatial_group > 64: spatial_group = in_channels
        self.spatial_group = spatial_group
        if spatial == 'conv':
            self.freq_weight_conv = nn.Conv2d(in_channels=in_channels,
                                              out_channels=(len(k_list) + 1) * self.spatial_group,
                                              stride=1,
                                              kernel_size=3, padding=1, bias=True)
            # self.freq_weight_conv.weight.data.zero_()
            # self.freq_weight_conv.bias.data.zero_()
        elif spatial == 'cbam':
            self.freq_weight_conv = SpatialGate(out=len(k_list) + 1)
        else:
            raise NotImplementedError

        if self.lp_type == 'avgpool':
            for k in k_list:
                self.lp_list.append(nn.Sequential(
                    nn.ReflectionPad2d(padding=k // 2),
                    # nn.ZeroPad2d(padding= k // 2),
                    nn.AvgPool2d(kernel_size=k, padding=0, stride=1)
                ))
        elif self.lp_type == 'freq':
            pass
        elif self.lp_type in ('freq_channel_att', 'freq_channel_att_reduce_high'):
            # self.channel_att= nn.ModuleList()
            # for i in
            self.channel_att_low = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Conv2d(self.in_channels, self.in_channels // compress_ratio, kernel_size=1, padding=0, bias=True),
                nn.ReLU(inplace=True),
                nn.Conv2d(self.in_channels // compress_ratio, self.in_channels, kernel_size=1, padding=0, bias=True),
                nn.Sigmoid()
            )
            # self.channel_att_low[3].weight.data.zero_()
            # self.channel_att_low[3].bias.data.zero_()

            self.channel_att_high = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Conv2d(self.in_channels, self.in_channels // compress_ratio, kernel_size=1, padding=0, bias=True),
                nn.ReLU(inplace=True),
                nn.Conv2d(self.in_channels // compress_ratio, self.in_channels, kernel_size=1, padding=0, bias=True),
                nn.Sigmoid()
            )
            # self.channel_att_high[3].weight.data.zero_()
            # self.channel_att_high[3].bias.data.zero_()
            # self.channel_att.weight.data.zero_()
        elif self.lp_type in ('freq_eca',):
            # self.channel_att_list = nn.ModuleList()
            # for i in
            self.channel_att = nn.ModuleList(
                [eca_layer(self.in_channels, k_size=9) for _ in range(len(k_list) + 1)]
            )
        elif self.lp_type in ('freq_channel_se',):
            # self.channel_att_list = nn.ModuleList()
            # for i in
            self.channel_att = SELayer(self.in_channels, ratio=16)
        else:
            raise NotImplementedError

        self.act = act
        # self.freq_weight_conv_list.append(nn.Conv2d(self.deform_groups * 3 * self.kernel_size[0] * self.kernel_size[1], 1, kernel_size=1, padding=0, bias=True))
        self.freq_thres = 0.25 * 1.4

    def forward(self, x):
        freq_weight = self.freq_weight_conv(x)

        if self.act == 'sigmoid':
            freq_weight = freq_weight.sigmoid()
        elif self.act == 'softmax':
            freq_weight = freq_weight.softmax(dim=1) * freq_weight.shape[1]
        else:
            raise NotImplementedError
        x_fft = torch.fft.fftshift(torch.fft.fft2(x))
        low_mask = torch.zeros_like(x_fft, device=x_fft.device)
        high_mask = torch.ones_like(x_fft, device=x_fft.device)
        # mask[:,:,int(x.size()[2]/4):int(x.size()[2]/4*3),int(x.size()[3]/4):int(x.size()[3]/4*3)] = 1.0
        _, _, h, w = x.shape
        low_mask[:, :, round(h / 2 - h * self.freq_thres):round(h / 2 + h * self.freq_thres),
        round(w / 2 - w * self.freq_thres):round(w / 2 + w * self.freq_thres)] = 1.0
        high_mask[:, :, round(h / 2 - h * self.freq_thres):round(h / 2 + h * self.freq_thres),
        round(w / 2 - w * self.freq_thres):round(w / 2 + w * self.freq_thres)] = 0.0

        low_part = torch.fft.ifft2(torch.fft.ifftshift(x_fft * low_mask)).real
        high_part = x - low_part
        low_x_fft = x_fft * low_mask
        high_x_fft = x_fft * high_mask
        low_c_att = torch.sqrt(
            self.channel_att_low(low_x_fft.real) ** 2 + self.channel_att_low(low_x_fft.imag) ** 2 + 1e-8)
        high_c_att = torch.sqrt(
            self.channel_att_high(high_x_fft.real) ** 2 + self.channel_att_high(high_x_fft.imag) ** 2 + 1e-8)
        low_part = low_part * freq_weight[:, 0:1, ] * low_c_att
        high_part = high_part * freq_weight[:, 1:2, ] * high_c_att
        # low_part = low_part * freq_weight[:, 0:1,] * self.channel_att_low((x_fft * low_mask).abs())
        # high_part = high_part * freq_weight[:, 1:2,] * self.channel_att_high((x_fft * high_mask).abs())
        res = low_part + high_part
        if self.channel_res: res += x
        return res

if __name__ == '__main__':
    import os

    os.environ['CUDA_VISIBLE_DEVICES'] = '1'
    size = 64
    N = size*size

    input = torch.rand(1, 64, size, size).cuda()  # 输入 B C H W
    model = _FrequencyMix(64).cuda()
    out = model(input)

    # flops, params = profile(model, inputs=(input, size, size,))
    flops, params = profile(model, inputs=(input,))
    print('flops: %.4f G, params: %.4f M' % (flops / 1e9, params / 1000000.0))
    # output = model(input)
    print(out.size())
