import mne
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis

def extract_frequency_features_mne110(epochs, method='multitaper'):
    """
    适用于MNE 1.10版本的频域特征提取函数
    
    Parameters:
    -----------
    epochs : mne.Epochs
        预处理后的epoch数据
    method : str
        PSD计算方法，'multitaper' 或 'welch'
    
    Returns:
    --------
    features : ndarray
        频域特征矩阵 (n_epochs, n_features)
    feature_names : list
        特征名称列表
    """
    
    print(f"使用MNE版本: {mne.__version__}")
    
    # 使用epochs对象的compute_psd方法（MNE 1.10推荐方式）
    if method == 'multitaper':
        psd = epochs.compute_psd(
            method='multitaper', 
            fmin=1, 
            fmax=40, 
            bandwidth=2.0,
            low_bias=True,
            verbose=False
        )
    elif method == 'welch':
        psd = epochs.compute_psd(
            method='welch', 
            fmin=1, 
            fmax=40,
            n_fft=None,  # 使用默认值
            n_overlap=0,
            verbose=False
        )
    else:
        raise ValueError("method must be 'multitaper' or 'welch'")
    
    # 获取PSD数据和频率
    psds = psd.get_data()  # shape: (n_epochs, n_channels, n_freqs)
    freqs = psd.freqs
    
    print(f"PSD数据形状: {psds.shape}")
    print(f"频率范围: {freqs[0]:.2f} - {freqs[-1]:.2f} Hz")
    
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
    
    # 1. 绝对功率特征
    print("提取绝对功率特征...")
    for band_name, (fmin, fmax) in bands.items():
        freq_mask = (freqs >= fmin) & (freqs <= fmax)
        if not np.any(freq_mask):
            print(f"警告: 频段 {band_name} ({fmin}-{fmax} Hz) 没有对应的频率点")
            continue
            
        band_power = psds[:, :, freq_mask].mean(axis=2)  # 对频率维度求平均
        
        # 跨电极的统计特征
        mean_power = band_power.mean(axis=1)  # 平均功率
        max_power = band_power.max(axis=1)    # 最大功率
        std_power = band_power.std(axis=1)    # 功率标准差
        
        features.extend([mean_power, max_power, std_power])
        feature_names.extend([f'{band_name}_mean_power', 
                             f'{band_name}_max_power', 
                             f'{band_name}_std_power'])
    
    # 2. 相对功率特征
    print("提取相对功率特征...")
    total_power = psds.sum(axis=2)  # 总功率
    for band_name, (fmin, fmax) in bands.items():
        freq_mask = (freqs >= fmin) & (freqs <= fmax)
        if not np.any(freq_mask):
            continue
            
        band_power = psds[:, :, freq_mask].mean(axis=2)
        relative_power = (band_power / (total_power + 1e-10)).mean(axis=1)  # 防止除零
        
        features.append(relative_power)
        feature_names.append(f'{band_name}_relative_power')
    
    # 3. 峰值频率特征
    print("提取峰值频率特征...")
    for band_name, (fmin, fmax) in bands.items():
        freq_mask = (freqs >= fmin) & (freqs <= fmax)
        if not np.any(freq_mask):
            continue
            
        band_psds = psds[:, :, freq_mask]
        band_freqs = freqs[freq_mask]
        
        # 找到每个epoch每个通道的峰值频率
        peak_indices = np.argmax(band_psds, axis=2)
        peak_freqs = band_freqs[peak_indices]
        
        # 跨电极平均
        mean_peak_freq = peak_freqs.mean(axis=1)
        std_peak_freq = peak_freqs.std(axis=1)
        
        features.extend([mean_peak_freq, std_peak_freq])
        feature_names.extend([f'{band_name}_mean_peak_freq', 
                             f'{band_name}_std_peak_freq'])
    
    # 4. 频段功率比值特征
    print("提取频段比值特征...")
    band_powers = {}
    for band_name, (fmin, fmax) in bands.items():
        freq_mask = (freqs >= fmin) & (freqs <= fmax)
        if np.any(freq_mask):
            band_powers[band_name] = psds[:, :, freq_mask].mean(axis=2).mean(axis=1)
    
    # 常用的比值特征
    ratios = [
        ('theta', 'alpha', 'theta_alpha_ratio'),
        ('alpha', 'beta', 'alpha_beta_ratio'), 
        ('theta', 'beta', 'theta_beta_ratio'),
        ('alpha', 'delta', 'alpha_delta_ratio'),
        ('beta', 'gamma', 'beta_gamma_ratio')
    ]
    
    for num_band, den_band, ratio_name in ratios:
        if num_band in band_powers and den_band in band_powers:
            ratio = band_powers[num_band] / (band_powers[den_band] + 1e-10)
            features.append(ratio)
            feature_names.append(ratio_name)
    
    # 5. 频谱统计特征
    print("提取频谱统计特征...")
    # 频谱中心频率（质心）
    freq_weights = freqs[np.newaxis, np.newaxis, :]
    spectral_centroid = np.sum(psds * freq_weights, axis=2) / (np.sum(psds, axis=2) + 1e-10)
    features.append(spectral_centroid.mean(axis=1))
    feature_names.append('spectral_centroid')
    
    # 频谱带宽
    centroid_expanded = spectral_centroid[:, :, np.newaxis]
    freq_diff_squared = (freq_weights - centroid_expanded) ** 2
    spectral_bandwidth = np.sqrt(np.sum(psds * freq_diff_squared, axis=2) / (np.sum(psds, axis=2) + 1e-10))
    features.append(spectral_bandwidth.mean(axis=1))
    feature_names.append('spectral_bandwidth')
    
    # 合并所有特征
    features_array = np.column_stack(features)
    
    print(f"成功提取了 {features_array.shape[1]} 个频域特征")
    print(f"特征矩阵形状: {features_array.shape}")
    
    return features_array, feature_names


def simple_frequency_features(epochs, method='welch'):
    """
    简化版的频域特征提取（适用于MNE 1.10）
    
    Parameters:
    -----------
    epochs : mne.Epochs
        预处理后的epoch数据
    method : str
        PSD计算方法
        
    Returns:
    --------
    features : ndarray
        频域特征矩阵 (n_epochs, n_features)
    """
    
    # 计算PSD
    psd = epochs.compute_psd(method=method, fmin=1, fmax=40, verbose=False)
    psds = psd.get_data()
    freqs = psd.freqs
    
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
    
    # 提取每个频段的平均功率
    for band_name, (fmin, fmax) in bands.items():
        freq_mask = (freqs >= fmin) & (freqs <= fmax)
        if np.any(freq_mask):
            # 绝对功率
            band_power = psds[:, :, freq_mask].mean(axis=2).mean(axis=1)
            features.append(band_power)
            feature_names.append(f'{band_name}_power')
    
    # 计算功率比值
    if len(features) >= 3:  # 确保有足够的频段
        theta_power = features[1]  # theta
        alpha_power = features[2]  # alpha
        beta_power = features[3] if len(features) > 3 else features[2]  # beta or alpha
        
        # theta/alpha 比值
        theta_alpha_ratio = theta_power / (alpha_power + 1e-10)
        features.append(theta_alpha_ratio)
        feature_names.append('theta_alpha_ratio')
    
    return np.column_stack(features), feature_names