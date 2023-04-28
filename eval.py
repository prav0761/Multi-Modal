# -*- coding: utf-8 -*-
"""eval.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1j2oQqe2ylAHExlv84TUb8ylw0gY79x-R
"""

import argparse
import torch
import numpy as np
import torchvision
from torchvision import transforms
from PIL import Image
import requests
import time
import numpy as np
import io
from io import BytesIO
import matplotlib.pyplot as plt
import torchvision.models as models
from torch.autograd import Variable
import torch.nn.functional as F
import torchvision.transforms as transforms
import torchvision.datasets as datasets
from torch.utils.data import DataLoader
import os
from torch.utils.data import Dataset
import torch.nn.init as init
from torch.nn.utils.rnn import pad_sequence
import random
from tqdm import tqdm
import json
from torch.optim.lr_scheduler import CosineAnnealingLR
import threading
import warnings
warnings.filterwarnings('ignore')
import torchvision.models as models
import torch.nn as nn
from pytorch_pretrained_bert import OpenAIGPTTokenizer, OpenAIGPTModel
from nltk.corpus import wordnet
from caption_transforms import SimCLRData_Caption_Transform
from image_transforms import SimCLRData_image_Transform
from dataset import FlickrDataset,Flickr30kDataset
from models import ResNetSimCLR,OpenAI_SIMCLR,Image_fine_tune_model ,Text_fine_tune_model
from utils import layerwise_trainable_parameters,count_trainable_parameters,get_gpu_memory,recall_score_calculate
from utils import get_all_recall_scores,get_img_txt_embed
from metrics import inter_ContrastiveLoss, intra_ContrastiveLoss,cosine_sim , finetune_ContrastiveLoss
from metrics import LARS,Optimizer_simclr
from logger import Logger ,Fine_Tune_Logger
from train_fns import train, test , fine_tune_train ,fine_tune_val
from args import args_c , args_finetune
def main(image, text):
    torch.cuda.empty_cache()
    torch.manual_seed(1234)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    flickr30k_images_dir_path='/work/08629/pradhakr/maverick2/cv_project/flickr30k-images'
    flickr30k_tokens_dir_path='/work/08629/pradhakr/maverick2/cv_project/flickr30k_captions/results_20130124.token'
    caption_index_1=0
    caption_index_2=1

    dataset = Flickr30kDataset(flickr30k_images_dir_path, 
                               flickr30k_tokens_dir_path,
                               caption_index_1=caption_index_1,
                               caption_index_2=caption_index_2,
                              image_transform=None,
                                  evaluate=True)
    indices = list(range(len(dataset)))
    train_indices = indices[:29783]
    val_indices = indices[29783:30783]
    test_indices = indices[30783:]
    train_set = torch.utils.data.Subset(dataset, train_indices)
    val_set = torch.utils.data.Subset(dataset, val_indices)
    test_set = torch.utils.data.Subset(dataset, test_indices)
    batch_size=128
    train_loader = DataLoader(train_set, 
                             batch_size=batch_size, 
                             shuffle=True, 
                             num_workers=4, 
                             pin_memory=True)
    val_loader = DataLoader(val_set, 
                             batch_size=batch_size, 
                             shuffle=False, 
                             num_workers=4, 
                             pin_memory=True)
    test_loader = DataLoader(test_set, 
                             batch_size=batch_size, 
                             shuffle=False, 
                             num_workers=4, 
                             pin_memory=True)
    images, txt1, txt2, txt3, txt4, txt5, index1 = zip(*[(val_set[i][0], val_set[i][1], val_set[i][2],
                                                          val_set[i][3], val_set[i][4], val_set[i][5], torch.tensor(i)) 
                                                         for i in range(len(val_set))])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_finetune_img=Image_fine_tune_model(weights_file=None, output_dim=1024).to(device)
    model_finetune_text=Text_fine_tune_model(weights_file=None ,output_dim=1024).to(device)
    # Load the image and text fine-tuned models
    image_weights_file = f'/work/08629/pradhakr/maverick2/cv_project/flickr30k_finetune_results/image_model_finetune{image}_30k.pth'
    text_weights_file = f'/work/08629/pradhakr/maverick2/cv_project/flickr30k_finetune_results/text_model_finetune{text}_30k.pth'

    model_finetune_img.load_state_dict(torch.load(image_weights_file))
    model_finetune_text.load_state_dict(torch.load(text_weights_file))
    # Call the fine-tune validation function
    image_embed ,text_embeds=get_img_txt_embed(images,txt1,txt2,txt3,txt4,
                                                  txt5,model_finetune_img,model_finetune_text,device)
    r_1_it,r_5_it,r_10_it,r_1_ti,r_5_ti,r_10_ti=get_all_recall_scores(image_embed,text_embeds)
    print('recall@1_it = {:.4f}, recall@5_it = {:.4f}, recall@10_it = {:.4f}'
          .format(r_1_it, r_5_it, r_10_it))
    print('recall@1_ti = {:.4f}, recall@5_ti = {:.4f}, recall@10_ti = {:.4f}'
          .format(r_1_ti, r_5_ti, r_10_ti))
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fine-tune image and text models')
    parser.add_argument('--image', type=str, required=True,
                        help='Path to the image fine-tuned model weights file')
    parser.add_argument('--text', type=str, required=True,
                        help='Path to the text weights file')
    args = parser.parse_args()
    main(args.image, args.text)
    

