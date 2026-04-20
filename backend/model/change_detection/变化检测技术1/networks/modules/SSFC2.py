import torch
import torch.nn as nn
import numpy as np
from mmengine.model import BaseModule, Sequential

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

    def forward(self, x1):
        N, c, h, w = x1.shape

        exchange_map = torch.arange(c) % self.p == 0
        exchange_mask_channel = exchange_map.unsqueeze(0).expand((N, -1))
        exchange_mask_spatial = torch.arange(w) % self.p == 0
        out_x1, out_x2 = torch.zeros_like(x1), torch.zeros_like(x1)
        out_x1= torch.zeros_like(x1)
        out_x1[~exchange_mask_channel, ...] = x1[~exchange_mask_channel, ...]
        out_x2[~exchange_mask_spatial, ...] = x1[~exchange_mask_spatial, ...]
        out_x1[..., exchange_mask_channel] = x1[..., exchange_mask_channel]
        out_x2[..., exchange_mask_spatial] = x1[..., exchange_mask_spatial]
        return out_x1, out_x2


class SSFC(torch.nn.Module):
    def __init__(self, in_ch):
        super(SSFC, self).__init__()

        # self.proj = nn.Conv2d(in_ch, in_ch, kernel_size=1)  # generate k by conv
        self.change=ChannelExchange()

    def forward(self, x):
        _, _, h, w = x.size()
        out1, out2 =self.change(x)

        q = x.mean(dim=[2, 3], keepdim=True)
        # k = self.proj(x)
        k = x
        square = (k - q).pow(2)
        sigma = square.sum(dim=[2, 3], keepdim=True) / (h * w)
        att_score = square / (2 * sigma + np.finfo(np.float32).eps) + 0.5
        att_weight = nn.Sigmoid()(att_score)
        # print(sigma)

        return x * att_weight+out1*att_weight+out2*att_weight

