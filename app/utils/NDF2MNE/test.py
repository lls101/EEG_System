from matplotlib.pyplot import isinteractive
from NDFSysParser import FileNEF, FileNTP,FileNSF,FileNDF,FolderNHF, FolderNSF
from NDFSysUtility import FolderCatergory, NDFUtility
from NDFSysMNE import mneNDF
import mne
from ReadNDF import ReadNDFChannels,ReadOneChannel
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import savemat
from mne.preprocessing import ICA
# 数据导入
# 32导联数据
include_ch = ['Fp1','Fp2','Fz','F3','F4','F7','F8','FC1','FC2','FC5',
'FC6','Cz','C3','C4','T7','T8','CP1','CP2',
'CP5','CP6','Pz','P3','P4','P7','P8','PO3','PO4','Oz','O1','O2']

    # ndfMneObj = mneNDF(file_path) 
    # data = ndfMneObj.read2MneRaw() 

ndfMneObj = mneNDF(r'D:\Document\EEG相关\20240519193301_经颅电_00_静息态1\4') 
data = ndfMneObj.read2MneRaw()

data_sel = data.pick(include_ch)
montage = mne.channels.make_standard_montage("standard_1020")
data_sel.set_montage(montage)

# data_sel.plot(duration=5, n_channels=32, clipping=None)
# data_sel.plot_psd(average=True)
# data_sel.plot_sensors(ch_type='eeg',show_names=True)
# 滤波
data_sel = data_sel.notch_filter(freqs=(50)) #notch filter
data_sel =data_sel.filter(l_freq=0.1,h_freq=49,method='iir') # 0.1-49Hz band pass filter
data_sel =data_sel.set_eeg_reference(ref_channels='average') # 重参考，使用平均参考

# 分段，降采样
data_sel = data_sel.resample(200, npad='auto') #降采样到200Hz


# data_epoch = epochs.get_data() # n_events,n_channels,n_times数组形式
# data_epoch_5 = data_epoch[5,:,:] #选取第5段进行分析51-60s
data_sel_data = data_sel.get_data() #n_channels, n_times格式
data_sel_data = data_sel_data[:,200*5:200*5+240000] #选取20min数据进行分析，去除前5s
# 小波去噪
import spkit
info =mne.create_info(ch_names=include_ch, sfreq=200,ch_types='eeg')
X = data_sel_data.T*1e6 # 矩阵转置 + 单位换算为uv
XR = spkit.eeg.ATAR(X, wv='db3', winsize=200, beta=0.3, IPR=[25,75], OptMode='soft')
XR =XR.T/1e6
data_filter_raw = mne.io.RawArray(XR,info) # 重构为raw格式
montage = mne.channels.make_standard_montage("standard_1020")
data_filter_raw.set_montage(montage)
# data_filter_raw.plot(duration=10,n_channels=30,clipping=None)
# data_filter_raw.plot_psd(average=True) #绘制数据功率谱
# 
epochs = mne.make_fixed_length_epochs(data_filter_raw, duration=10, preload=False) # 共20min 1200s，每10s一段，分为了12段
# epochs.plot(n_epochs=12)
epochs.compute_psd().plot(picks='eeg') #绘制功率谱图，逐导联
# bands = [(4, 8, 'Theta'), (8, 12, 'Alpha'), (12, 30, 'Beta')]
# epochs.plot_psd_topomap(bands=bands, vlim='joint')
data_filter_raw.compute_psd().plot_topomap()


