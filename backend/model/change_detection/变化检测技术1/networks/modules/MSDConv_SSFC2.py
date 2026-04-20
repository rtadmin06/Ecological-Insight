import math
import torch
from torch import nn

from networks.modules.SSFC import SSFC
from networks.modules.CMConv import CMConv
from networks.modules.Transfor import BASE_Transformer

class MSDConv_SSFC(nn.Module):
    def __init__(self, in_ch, out_ch, kernel_size=1, stride=1, padding=0, ratio=2, aux_k=3, dilation=3):
        super(MSDConv_SSFC, self).__init__()
        self.out_ch = out_ch
        native_ch = math.ceil(out_ch / ratio)
        aux_ch = native_ch * (ratio - 1)

        # native feature maps
        # local feature
        self.native = nn.Sequential(
            nn.Conv2d(in_ch, native_ch, kernel_size, stride, padding=padding, dilation=1, bias=False),
            nn.BatchNorm2d(native_ch),
            nn.ReLU(inplace=True),
        )

        # auxiliary feature maps
        self.aux = nn.Sequential(
            CMConv(native_ch, aux_ch, aux_k, 1, padding=1, groups=int(native_ch / 4), dilation=dilation,
                   bias=False),
            nn.BatchNorm2d(aux_ch),
            nn.ReLU(inplace=True),
        )

        self.att = SSFC(aux_ch)
        self.transformer = BASE_Transformer(dim=aux_ch, input_nc=3, output_nc=2,token_len=4,
                             with_pos='learned', enc_depth=1, dec_depth=4)


    def forward(self, x):
        x1 = self.native(x)  #用于cnn分支和transformer分支
        #print(x.size(),'x')
        x2_1 = self.transformer(x1)
        x2_2 = self.aux(x1)
        x2 = torch.cat([x2_1, x2_2], dim=1)
        # x2 = self.att(self.aux(x1))
        x2 = self.att(x2)
        out = torch.cat([x1, x2], dim=1)
        # out_cnn = out[:, :self.out_ch, :, :]
        #print(out_cnn.size(),'out_cnn.size')
        # out_transformer = self.transformer(x)
        #print(out_transformer.size(),'out_transformer')
        # out_final = out_transformer + out_cnn
        # return out[:, :self.out_ch, :, :]
        return out[:, :self.out_ch, :, :]

class MSDConv_SSFC1(nn.Module):
    def __init__(self, in_ch, out_ch, kernel_size=1, stride=1, padding=0, ratio=2, aux_k=3, dilation=3):
        super(MSDConv_SSFC1, self).__init__()
        self.out_ch = out_ch
        native_ch = math.ceil(out_ch / ratio)
        aux_ch = native_ch * (ratio - 1)

        # native feature maps
        # local feature
        self.native = nn.Sequential(
            nn.Conv2d(in_ch, native_ch, kernel_size, stride, padding=padding, dilation=1, bias=False),
            nn.BatchNorm2d(native_ch),
            nn.ReLU(inplace=True),
        )

        # auxiliary feature maps
        self.aux = nn.Sequential(
            CMConv(native_ch, aux_ch, aux_k, 1, padding=1, groups=int(native_ch / 4), dilation=dilation,
                   bias=False),
            nn.BatchNorm2d(aux_ch),
            nn.ReLU(inplace=True),
        )

        self.att = SSFC(aux_ch)
        self.transformer = BASE_Transformer(dim=in_ch, input_nc=3, output_nc=2,token_len=8,
                             with_pos='learned', enc_depth=1, dec_depth=4,is_down=True)


    def forward(self, x):
        x1 = self.native(x)
        #print(x.size(),'x')
        # x2 = self.att(self.aux(x1))
        x2 = self.att(self.transformer(x))
        out = torch.cat([x1, x2], dim=1)
        #print(out.size(),'out')
        # out_cnn = out[:, :self.out_ch, :, :]
        #print(out_cnn.size(),'out_cnn.size')
        #out_transformer = self.transformer(x)
        #print(out_transformer.size(),'out_transformer')
        #out_final = out_transformer + out_cnn
        return out[:, :self.out_ch, :, :]
        # return out_final

class TransConv(nn.Module):
    def __init__(self, in_ch, out_ch, kernel_size=1, stride=1, padding=0, ratio=2, aux_k=3, dilation=3):
        super(TransConv, self).__init__()
        self.out_ch = out_ch
        native_ch = math.ceil(out_ch / ratio)
        # native_ch = out_ch
        aux_ch = native_ch * (ratio - 1)

        # native feature maps
        # local feature
        self.native = nn.Sequential(
            nn.Conv2d(in_ch, native_ch, kernel_size, stride, padding=padding, dilation=1, bias=False),
            nn.BatchNorm2d(native_ch),
            nn.ReLU(inplace=True),
        )

        # auxiliary feature maps
        # self.aux = nn.Sequential(
        #     CMConv(native_ch, aux_ch, aux_k, 1, padding=1, groups=int(native_ch / 4), dilation=dilation,
        #            bias=False),
        #     nn.BatchNorm2d(aux_ch),
        #     nn.ReLU(inplace=True),
        # )

        self.att = SSFC(aux_ch)
        self.transformer = BASE_Transformer(dim=in_ch, input_nc=3, output_nc=2,token_len=4,
                             with_pos='learned', enc_depth=1, dec_depth=4)


    def forward(self, x):
        x1 = self.native(x)
        x2 = self.att(self.transformer(x))
        out = torch.cat([x1, x2], dim=1)
        # out_cnn = out[:, :self.out_ch, :, :]
        #print(out_cnn.size(),'out_cnn.size')
        #out_transformer = self.transformer(x)
        #print(out_transformer.size(),'out_transformer')
        #out_final = out_transformer + out_cnn
        return out[:, :self.out_ch, :, :]