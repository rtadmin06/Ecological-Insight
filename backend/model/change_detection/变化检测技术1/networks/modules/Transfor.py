from networks.modules.help_funcs import Transformer, TransformerDecoder, TwoLayerConv2d
import torch.nn.functional as F
from einops import rearrange
from torch import nn
import torch

class BASE_Transformer(nn.Module):
    """
    Resnet of 8 downsampling + BIT + bitemporal feature Differencing + a small CNN
    """
    def __init__(self, dim, input_nc, output_nc, with_pos,
                 token_len=4, token_trans=True,
                 enc_depth=1, dec_depth=1,
                 dim_head=16, decoder_dim_head=16,
                 tokenizer=True,
                 pool_mode='max', pool_size=2,
                 # backbone='resnet18',
                 decoder_softmax=True, with_decoder_pos=None,
                 with_decoder=True):
        super(BASE_Transformer, self).__init__()
        self.token_len = token_len
        self.conv_a = nn.Conv2d(dim, self.token_len, kernel_size=1,
                                padding=0, bias=False)
        # self.down = is_down
        # if self.down:
        #     self.conv1 = nn.Conv2d(dim, dim // 2, kernel_size=1,
        #                            padding=0, bias=False)
        # else:
        #     self.conv1 = nn.Conv2d(dim, dim * 2, kernel_size=1,
        #                            padding=0, bias=False)
        # self.up =  nn.Upsample(scale_factor=2)
        self.tokenizer = tokenizer
        if not self.tokenizer:
            #  if not use tokenzier，then downsample the feature map into a certain size
            self.pooling_size = pool_size
            self.pool_mode = pool_mode
            self.token_len = self.pooling_size * self.pooling_size

        self.token_trans = token_trans
        self.with_decoder = with_decoder
        #dim = 32
        mlp_dim = dim

        self.with_pos = with_pos
        if with_pos is 'learned':
            self.pos_embedding = nn.Parameter(torch.randn(1, self.token_len, dim))
        decoder_pos_size = 256//4
        self.with_decoder_pos = with_decoder_pos
        if self.with_decoder_pos == 'learned':
            self.pos_embedding_decoder =nn.Parameter(torch.randn(1, dim,
                                                                 decoder_pos_size,
                                                                 decoder_pos_size))
        self.enc_depth = enc_depth
        self.dec_depth = dec_depth
        self.dim_head = dim_head
        self.decoder_dim_head = decoder_dim_head
        self.transformer = Transformer(dim=dim, depth=self.enc_depth, heads=8,
                                       dim_head=self.dim_head,
                                       mlp_dim=mlp_dim, dropout=0)
        self.transformer_decoder = TransformerDecoder(dim=dim, depth=self.dec_depth,
                            heads=8, dim_head=self.decoder_dim_head, mlp_dim=mlp_dim, dropout=0,
                                                      softmax=decoder_softmax)

    def _forward_semantic_tokens(self, x):

        b, c, h, w = x.shape
        #print(x.size())
        spatial_attention = self.conv_a(x)   #1,4,64,64

        spatial_attention = spatial_attention.view([b, self.token_len, -1]).contiguous()  #1,4,4096

        spatial_attention = torch.softmax(spatial_attention, dim=-1)#1,4,4096

        x = x.view([b, c, -1]).contiguous()  #1, 32, 4096

        tokens = torch.einsum('bln,bcn->blc', spatial_attention, x) #1, 4, 32

        return tokens

    def _forward_reshape_tokens(self, x):
        # b,c,h,w = x.shape
        if self.pool_mode is 'max':
            x = F.adaptive_max_pool2d(x, [self.pooling_size, self.pooling_size])
        elif self.pool_mode is 'ave':
            x = F.adaptive_avg_pool2d(x, [self.pooling_size, self.pooling_size])
        else:
            x = x
        tokens = rearrange(x, 'b c h w -> b (h w) c')

        return tokens

    def _forward_transformer(self, x):
        if self.with_pos:
            x += self.pos_embedding
        x = self.transformer(x) #1,8,32

        return x

    def _forward_transformer_decoder(self, x, m):
        b, c, h, w = x.shape

        if self.with_decoder_pos == 'fix':
            x = x + self.pos_embedding_decoder
        elif self.with_decoder_pos == 'learned':
            x = x + self.pos_embedding_decoder

        x = rearrange(x, 'b c h w -> b (h w) c')
        x = self.transformer_decoder(x, m) #1,4096,32

        x = rearrange(x, 'b (h w) c -> b c h w', h=h) #1,32,64,64
        return x

    def _forward_simple_decoder(self, x, m):
        b, c, h, w = x.shape

        b, l, c = m.shape
        m = m.expand([h,w,b,l,c])
        m = rearrange(m, 'h w b l c -> l b c h w')
        m = m.sum(0)
        x = x + m

        return x

    def forward(self, x1):
        # forward backbone resnet
        #x1 = self.forward_single(x1) #1,32,64,64

        #x2 = self.forward_single(x2)#1,32,64,64
        #print(x1.size(),'x1.size')#1, 32, 128, 128


        #  forward tokenzier
        if self.tokenizer:
            token1 = self._forward_semantic_tokens(x1)
            #print(token1.size(),'token1.size')

            #token2 = self._forward_semantic_tokens(x2)
        else:
            token1 = self._forward_reshape_tokens(x1)
            #token2 = self._forward_reshape_tokens(x2)
        # forward transformer encoder
        if self.token_trans:
            #self.tokens_ = torch.cat([token1, token2], dim=1)
            self.tokens = self._forward_transformer(token1)
            #token1, token2 = self.tokens.chunk(2, dim=1)
        # forward transformer decoder
        if self.with_decoder:
            x1 = self._forward_transformer_decoder(x1, token1)
            #x2 = self._forward_transformer_decoder(x2, token2)
        else:
            x1 = self._forward_simple_decoder(x1, token1)
            #x2 = self._forward_simple_decoder(x2, token2)
        # feature differencing
        #x = torch.abs(x1 - x2)

        #x = self.conv1(x1)
        # if not self.if_upsample_2x:
        #     x = self.upsamplex2(x)
        # x = self.upsamplex4(x)
        # forward small cnn
        # x = self.classifier(x)
        # if self.output_sigmoid:
        #     x = self.sigmoid(x)
        return x1