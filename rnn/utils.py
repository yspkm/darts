import torch
import torch.nn as nn
import torch.nn.functional as F
import os, shutil
import numpy as np
from torch.autograd import Variable


def repackage_hidden(h):
    if isinstance(h, torch.Tensor):
        return h.detach()
    elif isinstance(h, tuple):
        return tuple(repackage_hidden(v) for v in h)
    elif isinstance(h, list):
        # Assuming h is a list of tensors
        return [repackage_hidden(v) for v in h]
    else:
        raise TypeError(f"Unsupported type for hidden state: {type(h)}")

def batchify(data, bsz, args):
    nbatch = data.size(0) // bsz
    data = data.narrow(0, 0, nbatch * bsz)
    data = data.view(bsz, -1).t().contiguous()
    print(data.size())
    if args.cuda:
        data = data.cuda()
    return data


def get_batch(source, i, args, seq_len=None, evaluation=False):
    seq_len = min(seq_len if seq_len else args.bptt, len(source) - 1 - i)
    data = Variable(source[i:i+seq_len], volatile=evaluation)
    target = Variable(source[i+1:i+1+seq_len])
    return data, target


def create_exp_dir(path, scripts_to_save=None):
    if not os.path.exists(path):
        os.mkdir(path)

    print('Experiment dir : {}'.format(path))
    if scripts_to_save is not None:
        os.mkdir(os.path.join(path, 'scripts'))
        for script in scripts_to_save:
            dst_file = os.path.join(path, 'scripts', os.path.basename(script))
            shutil.copyfile(script, dst_file)


def save_checkpoint(model, optimizer, epoch, path, finetune=False):
    if finetune:
        torch.save(model, os.path.join(path, 'finetune_model.pt'))
        torch.save(optimizer.state_dict(), os.path.join(path, 'finetune_optimizer.pt'))
    else:
        torch.save(model, os.path.join(path, 'model.pt'))
        torch.save(optimizer.state_dict(), os.path.join(path, 'optimizer.pt'))
    torch.save({'epoch': epoch+1}, os.path.join(path, 'misc.pt'))


def embedded_dropout(embed, words, dropout=0.1, scale=None):
    if dropout:
        mask = embed.weight.data.new().resize_((embed.weight.size(0), 1)).bernoulli_(1 - dropout).expand_as(embed.weight) / (1 - dropout)
        masked_embed_weight = mask * embed.weight
    else:
        masked_embed_weight = embed.weight

    if scale:
        masked_embed_weight = scale.expand_as(masked_embed_weight) * masked_embed_weight

    # Use F.embedding to apply the embedding
    padding_idx = embed.padding_idx if embed.padding_idx is not None else -1
    X = F.embedding(words, masked_embed_weight, padding_idx, embed.max_norm, embed.norm_type, embed.scale_grad_by_freq, embed.sparse)

    return X


class LockedDropout(nn.Module):
    def __init__(self):
        super(LockedDropout, self).__init__()

    def forward(self, x, dropout=0.5):
        if not self.training or not dropout:
            return x
        m = x.data.new(1, x.size(1), x.size(2)).bernoulli_(1 - dropout)
        mask = Variable(m.div_(1 - dropout), requires_grad=False)
        mask = mask.expand_as(x)
        return mask * x


def mask2d(B, D, keep_prob, cuda=True):
    m = torch.floor(torch.rand(B, D) + keep_prob) / keep_prob
    m = Variable(m, requires_grad=False)
    if cuda:
        m = m.cuda()
    return m

