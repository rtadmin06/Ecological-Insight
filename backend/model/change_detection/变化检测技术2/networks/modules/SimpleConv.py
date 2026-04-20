import math
import torch
from torch import nn

from networks.modules.SSFC import SSFC
from networks.modules.CMConv import CMConv
from networks.modules.freq import FrequencySelection
from networks.modules.EfficientViM import EfficientViMBlock
class SimpleConv(nn.Module):
    def __init__(self, in_ch, out_ch, kernel_size=1, stride=1, padding=0, ratio=2, aux_k=3, dilation=3):
        super(SimpleConv, self).__init__()
        self.out_ch = out_ch
        native_ch = math.ceil(out_ch / 4)
        aux_ch = native_ch * (ratio - 1)
        # self.flag = in_ch == out_ch
        # native feature maps
        self.native = nn.Sequential(
            nn.Conv2d(in_ch, native_ch, kernel_size, stride, padding=padding, dilation=1, bias=False),
            nn.BatchNorm2d(native_ch),
            nn.ReLU(inplace=True),
        )
        # freq feature maps 
        self.freq = nn.Sequential(
            FrequencySelection(in_channels=native_ch),
            nn.BatchNorm2d(aux_ch),
            nn.ReLU(inplace=True),
        )
        # auxiliary feature maps
        self.aux = nn.Sequential(
            EfficientViMBlock(aux_ch),
            nn.BatchNorm2d(aux_ch),
            nn.ReLU(inplace=True),
        )

        self.cmconv = CMConv(in_ch = native_ch , out_ch=native_ch)
        # self.conv = nn.Conv2d(native_ch * 2 , self.out_ch , kernel_size=1 , stride=1)
        self.att = SSFC(aux_ch)

    def forward(self, x):
        x = self.native(x)
        x1 = self.aux(x)
        x2 = self.freq(x)
        x3 = self.cmconv(x)
        x3 = self.att(x3)
        out = torch.cat([x , x1, x2 , x3], dim=1)
        return out
        # return out[:, :self.out_ch, :, :]

        
        
    
