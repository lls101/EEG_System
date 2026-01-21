import numpy as np
import mne
from mne.time_frequency import tfr_morlet, tfr_multitaper, tfr_stockwell
from scipy import signal
from scipy.stats import entropy
import warnings

def extract_time_frequency_features(epochs, method='morlet', freqs=None):
    """
    提取EEG时频域特征
    
    Parameters:
    -----------
    epochs : mne.Epochs
        预处理后的epoch数据
    method : str
        时频分析方法: 'morlet', 'multitaper', 'stockwell', 'stft'
    freqs : array-like or None
        分析的频率范围，默认为1-40Hz
    
    Returns:
    --------
    features : ndarray, shape (n_epochs, n_features)
        时频特征矩阵
    feature_names : list
        特征名称列表
    """
    
    print(f"提取时频域特征 (方法: {method})...")
    
    epochs_data = epochs.get_data()
    sfreq = epochs.info['sfreq']
    n_epochs, n_channels, n_times = epochs_data.shape
    
    print(f"数据形状: {epochs_data.shape}")
    print(f"采样频率: {sfreq} Hz")
    
    # 设置频率范围
    if freqs is None:
        freqs = np.logspace(np.log10(1), np.log10(40), 30)  # 1-40Hz，30个频率点
    
    # 计算时频表示
    if method == 'morlet':
        tfr = compute_morlet_tfr(epochs, freqs)
    elif method == 'multitaper':
        tfr = compute_multitaper_tfr(epochs, freqs)
    elif method == 'stockwell':
        tfr = compute_stockwell_tfr(epochs, freqs)
    elif method == 'stft':
        tfr = compute_stft_tfr(epochs_data, sfreq, freqs)
    else:
        raise ValueError(f"不支持的方法: {method}")
    
    # 获取时频数据和元信息
    if method != 'stft':
        # 对于MNE的时频方法，检查返回的数据维度
        if hasattr(tfr, 'data'):
            tfr_data = tfr.data
            times = tfr.times
            freqs_used = tfr.freqs
            
            print(f"原始时频数据形状: {tfr_data.shape}")
            # MNE的multitaper等方法可能返回平均的TFR，形状为 (n_channels, n_freqs, n_times)
            # 我们需要为每个epoch构建特征
            if tfr_data.ndim == 3:
                # 对于平均TFR，我们需要重新计算每个epoch的时频表示
                print("检测到平均TFR，重新计算每个epoch的时频表示...")
                tfr_data = np.zeros((n_epochs, n_channels, len(freqs), len(times)))
                
                # 为每个epoch单独计算时频表示
                for i in range(n_epochs):
                    epoch_single = epochs[i:i+1]  # 单个epoch
                    if method == 'morlet':
                        tfr_single = compute_morlet_tfr(epoch_single, freqs)
                    elif method == 'multitaper':
                        tfr_single = compute_multitaper_tfr(epoch_single, freqs)
                    elif method == 'stockwell':
                        tfr_single = compute_stockwell_tfr(epoch_single, freqs)
                    
                    if hasattr(tfr_single, 'data'):
                        tfr_data[i] = tfr_single.data.squeeze()
                    
                print(f"重新计算后时频数据形状: {tfr_data.shape}")
        else:
            raise ValueError(f"TFR对象没有data属性: {type(tfr)}")
    else:
        tfr_data = tfr['data']
        times = tfr['times'] 
        freqs_used = tfr['freqs']
    
    print(f"最终时频数据形状: {tfr_data.shape}")
    print(f"频率范围: {freqs_used[0]:.2f} - {freqs_used[-1]:.2f} Hz")
    print(f"时间范围: {times[0]:.3f} - {times[-1]:.3f} s")
    
    # 定义频段
    bands = {
        'delta': (1, 4),
        'theta': (4, 8),
        'alpha': (8, 12),
        'beta': (12, 30),
        'gamma': (30, 40)
    }
    
    features = []
    feature_names = []
    
    # 1. 频段功率特征
    print("提取频段功率特征...")
    
    for band_name, (f_min, f_max) in bands.items():
        freq_mask = (freqs_used >= f_min) & (freqs_used <= f_max)
        if np.any(freq_mask):
            # 计算每个epoch每个通道在该频段的平均功率
            band_power = np.mean(np.abs(tfr_data[:, :, freq_mask, :]), axis=(2, 3))  # (n_epochs, n_channels)
            
            # 跨通道统计
            features.extend([
                np.mean(band_power, axis=1),  # 平均功率
                np.std(band_power, axis=1),   # 功率标准差
                np.max(band_power, axis=1),   # 最大功率
            ])
            
            feature_names.extend([
                f'{band_name}_mean_power',
                f'{band_name}_std_power', 
                f'{band_name}_max_power'
            ])
    
    # 2. 频段比值特征
    print("提取频段比值特征...")
    
    # Theta/Alpha比值
    theta_mask = (freqs_used >= 4) & (freqs_used <= 8)
    alpha_mask = (freqs_used >= 8) & (freqs_used <= 12)
    
    if np.any(theta_mask) and np.any(alpha_mask):
        theta_power = np.mean(np.abs(tfr_data[:, :, theta_mask, :]), axis=(2, 3))
        alpha_power = np.mean(np.abs(tfr_data[:, :, alpha_mask, :]), axis=(2, 3))
        
        theta_alpha_ratio = np.mean(theta_power, axis=1) / (np.mean(alpha_power, axis=1) + 1e-10)
        features.append(theta_alpha_ratio)
        feature_names.append('theta_alpha_ratio')
    
    # 3. 光谱熵特征
    print("提取光谱熵特征...")
    
    spectral_entropy = []
    for epoch in range(n_epochs):
        epoch_entropy = []
        for ch in range(n_channels):
            # 计算功率谱密度
            psd = np.abs(tfr_data[epoch, ch, :, :]).mean(axis=1)
            psd = psd / psd.sum()  # 归一化
            
            # 计算熵
            ent = entropy(psd + 1e-10)
            epoch_entropy.append(ent)
        
        spectral_entropy.append(np.mean(epoch_entropy))
    
    features.append(np.array(spectral_entropy))
    feature_names.append('spectral_entropy')
    
    # 4. 时间变化特征 (如果数据足够长)
    if len(times) > 10:  # 确保有足够的时间点
        print("提取时间变化特征...")
        
        # 分时间窗口分析theta/alpha比值变化
        n_time_windows = 3
        time_window_size = len(times) // n_time_windows
        
        for window_idx in range(n_time_windows):
            start_idx = window_idx * time_window_size
            end_idx = min((window_idx + 1) * time_window_size, len(times))
            
            # 提取该时间窗口的数据
            window_tfr = tfr_data[:, :, :, start_idx:end_idx]
            
            # 计算theta/alpha比值在该时间窗口
            if np.any(theta_mask) and np.any(alpha_mask):
                theta_power = np.mean(np.abs(window_tfr[:, :, theta_mask, :]), axis=(2, 3))
                alpha_power = np.mean(np.abs(window_tfr[:, :, alpha_mask, :]), axis=(2, 3))
                
                theta_alpha_ratio = np.mean(theta_power, axis=1) / (np.mean(alpha_power, axis=1) + 1e-10)
                features.append(theta_alpha_ratio)
                feature_names.append(f'theta_alpha_ratio_t{window_idx+1}')
    
    # 转换为numpy数组
    features_array = np.column_stack(features)
    
    print(f"提取的时频特征数量: {len(feature_names)}")
    print(f"特征矩阵形状: {features_array.shape}")
    
    return features_array, feature_names


def compute_morlet_tfr(epochs, freqs):
    """使用Morlet小波计算时频表示"""
    n_cycles = freqs / 2.
    return tfr_morlet(epochs, freqs=freqs, n_cycles=n_cycles,
                      use_fft=True, return_itc=False, decim=3,
                      n_jobs=1, verbose=False)


def compute_multitaper_tfr(epochs, freqs):
    """使用多锥度方法计算时频表示"""
    n_cycles = freqs / 2.
    time_bandwidth = 2.0
    return tfr_multitaper(epochs, freqs=freqs, n_cycles=n_cycles,
                          time_bandwidth=time_bandwidth, use_fft=True, 
                          return_itc=False, decim=3, n_jobs=1, verbose=False)


def compute_stockwell_tfr(epochs, freqs):
    """使用S变换计算时频表示"""
    return tfr_stockwell(epochs, fmin=freqs[0], fmax=freqs[-1], 
                         n_fft=None, width=1.0, decim=3, n_jobs=1,
                         return_itc=False, verbose=False)


def compute_stft_tfr(epochs_data, sfreq, freqs):
    """使用短时傅里叶变换计算时频表示"""
    n_epochs, n_channels, n_times = epochs_data.shape
    
    # STFT参数
    nperseg = int(sfreq * 0.25)  # 250ms窗口
    noverlap = nperseg // 2      # 50%重叠
    
    # 初始化结果数组
    stft_results = []
    times_stft = None
    
    for epoch in range(n_epochs):
        epoch_stft = []
        for ch in range(n_channels):
            # 计算STFT
            f, t, Zxx = signal.stft(epochs_data[epoch, ch, :], 
                                    fs=sfreq, nperseg=nperseg, 
                                    noverlap=noverlap)
            
            if times_stft is None:
                times_stft = t
            
            # 插值到目标频率
            freqs_interp = np.interp(freqs, f, np.abs(Zxx))
            epoch_stft.append(freqs_interp)
        
        stft_results.append(epoch_stft)
    
    # 转换为numpy数组
    stft_data = np.array(stft_results)  # (n_epochs, n_channels, n_freqs, n_times)
    
    return {
        'data': stft_data,
        'times': times_stft,
        'freqs': freqs
    }