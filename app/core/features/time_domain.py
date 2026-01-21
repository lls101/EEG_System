import numpy as np
from scipy import stats
from scipy.signal import find_peaks
import warnings

def extract_time_domain_features(epochs):
    """
    从EEG数据提取时域特征
    
    Parameters:
    -----------
    epochs_data : ndarray, shape (n_epochs, n_channels, n_times)
        EEG epoch数据，可以是epochs.get_data()的结果
    sfreq : float
        采样频率 (Hz)
    
    Returns:
    --------
    features : ndarray, shape (n_epochs, n_features)
        时域特征矩阵
    feature_names : list
        特征名称列表
    """
    epochs_data = epochs.get_data()
    sfreq = epochs.info['sfreq']


    n_epochs, n_channels, n_times = epochs_data.shape
    print(f"提取时域特征...")
    print(f"数据形状: {epochs_data.shape}")
    print(f"采样频率: {sfreq} Hz")
    
    features = []
    feature_names = []
    
    # 1. 基本统计特征
    print("提取基本统计特征...")
    
    # 均值 (Mean)
    mean_values = epochs_data.mean(axis=2).mean(axis=1)  # 跨时间和通道
    features.append(mean_values)
    feature_names.append('mean_amplitude')
    
    # 标准差 (Standard Deviation)
    std_values = epochs_data.std(axis=2).mean(axis=1)
    features.append(std_values)
    feature_names.append('std_amplitude')
    
    # 方差 (Variance)
    var_values = epochs_data.var(axis=2).mean(axis=1)
    features.append(var_values)
    feature_names.append('variance_amplitude')
    
    # 最大值和最小值
    max_values = epochs_data.max(axis=2).mean(axis=1)
    min_values = epochs_data.min(axis=2).mean(axis=1)
    features.extend([max_values, min_values])
    feature_names.extend(['max_amplitude', 'min_amplitude'])
    
    # 峰峰值 (Peak-to-Peak)
    ptp_values = (epochs_data.max(axis=2) - epochs_data.min(axis=2)).mean(axis=1)
    features.append(ptp_values)
    feature_names.append('peak_to_peak')
    
    # 均方根 (Root Mean Square, RMS)
    rms_values = np.sqrt(np.mean(epochs_data**2, axis=2)).mean(axis=1)
    features.append(rms_values)
    feature_names.append('rms_amplitude')
    
    # 2. 形状特征
    print("提取形状特征...")
    
    # 偏度 (Skewness) - 信号分布的不对称性
    skewness_values = []
    for epoch in range(n_epochs):
        epoch_skew = []
        for ch in range(n_channels):
            skew_val = stats.skew(epochs_data[epoch, ch, :])
            epoch_skew.append(skew_val if not np.isnan(skew_val) else 0)
        skewness_values.append(np.mean(epoch_skew))
    features.append(np.array(skewness_values))
    feature_names.append('skewness')
    
    # 峰度 (Kurtosis) - 信号分布的尖锐程度
    kurtosis_values = []
    for epoch in range(n_epochs):
        epoch_kurt = []
        for ch in range(n_channels):
            kurt_val = stats.kurtosis(epochs_data[epoch, ch, :])
            epoch_kurt.append(kurt_val if not np.isnan(kurt_val) else 0)
        kurtosis_values.append(np.mean(epoch_kurt))
    features.append(np.array(kurtosis_values))
    feature_names.append('kurtosis')
    
    # 3. 变化率特征
    print("提取变化率特征...")
    
    # 一阶差分的均值和标准差 (反映信号变化的快慢)
    diff1 = np.diff(epochs_data, axis=2)
    diff1_mean = diff1.mean(axis=2).mean(axis=1)
    diff1_std = diff1.std(axis=2).mean(axis=1)
    features.extend([diff1_mean, diff1_std])
    feature_names.extend(['diff1_mean', 'diff1_std'])
    
    # 二阶差分的均值和标准差 (反映信号曲率变化)
    diff2 = np.diff(epochs_data, n=2, axis=2)
    diff2_mean = diff2.mean(axis=2).mean(axis=1)
    diff2_std = diff2.std(axis=2).mean(axis=1)
    features.extend([diff2_mean, diff2_std])
    feature_names.extend(['diff2_mean', 'diff2_std'])
    
    # 4. 能量特征
    print("提取能量特征...")
    
    # 总能量 (Total Energy)
    total_energy = np.sum(epochs_data**2, axis=2).mean(axis=1)
    features.append(total_energy)
    feature_names.append('total_energy')
    
    # 平均功率
    avg_power = total_energy / n_times
    features.append(avg_power)
    feature_names.append('average_power')
    
    # 信号功率的标准差 (功率变异性)
    power_per_channel = np.sum(epochs_data**2, axis=2)  # (n_epochs, n_channels)
    power_std = power_per_channel.std(axis=1)
    features.append(power_std)
    feature_names.append('power_std')
    
    # 5. 复杂性特征
    print("提取复杂性特征...")
    
    # 零交叉率 (Zero Crossing Rate)
    zcr_values = []
    for epoch in range(n_epochs):
        epoch_zcr = []
        for ch in range(n_channels):
            signal = epochs_data[epoch, ch, :]
            # 移除直流分量
            signal_centered = signal - np.mean(signal)
            zero_crossings = np.sum(np.diff(np.sign(signal_centered)) != 0)
            zcr = zero_crossings / (2 * len(signal_centered))
            epoch_zcr.append(zcr)
        zcr_values.append(np.mean(epoch_zcr))
    features.append(np.array(zcr_values))
    feature_names.append('zero_crossing_rate')
    
    # 平均绝对偏差 (Mean Absolute Deviation)
    mad_values = []
    for epoch in range(n_epochs):
        epoch_mad = []
        for ch in range(n_channels):
            signal = epochs_data[epoch, ch, :]
            mad = np.mean(np.abs(signal - np.mean(signal)))
            epoch_mad.append(mad)
        mad_values.append(np.mean(epoch_mad))
    features.append(np.array(mad_values))
    feature_names.append('mean_absolute_deviation')
    
    # 6. 峰值检测特征
    print("提取峰值特征...")
    
    # 峰值数量和平均峰值间隔
    peak_counts = []
    peak_intervals = []
    
    for epoch in range(n_epochs):
        epoch_peak_count = []
        epoch_peak_interval = []
        
        for ch in range(n_channels):
            signal = epochs_data[epoch, ch, :]
            # 寻找峰值，设置最小距离为采样频率的1/20 (避免噪声)
            min_distance = int(sfreq / 20)  
            peaks, _ = find_peaks(signal, distance=min_distance)
            
            epoch_peak_count.append(len(peaks))
            
            if len(peaks) > 1:
                intervals = np.diff(peaks) / sfreq  # 转换为秒
                epoch_peak_interval.append(np.mean(intervals))
            else:
                epoch_peak_interval.append(0)
        
        peak_counts.append(np.mean(epoch_peak_count))
        peak_intervals.append(np.mean(epoch_peak_interval))
    
    features.extend([np.array(peak_counts), np.array(peak_intervals)])
    feature_names.extend(['peak_count', 'mean_peak_interval'])
    
    # 7. 分位数特征
    print("提取分位数特征...")
    
    # 25%、50%、75%分位数
    q25 = np.percentile(epochs_data, 25, axis=2).mean(axis=1)
    q50 = np.percentile(epochs_data, 50, axis=2).mean(axis=1)  # 中位数
    q75 = np.percentile(epochs_data, 75, axis=2).mean(axis=1)
    
    features.extend([q25, q50, q75])
    feature_names.extend(['percentile_25', 'percentile_50', 'percentile_75'])
    
    # 四分位距 (Interquartile Range)
    iqr = q75 - q25
    features.append(iqr)
    feature_names.append('interquartile_range')
    
    # 8. Hjorth参数
    print("提取Hjorth参数...")
    
    # Hjorth Activity (方差)
    hjorth_activity = np.var(epochs_data, axis=2).mean(axis=1)
    features.append(hjorth_activity)
    feature_names.append('hjorth_activity')
    
    # Hjorth Mobility (一阶导数的标准差/原信号标准差)
    hjorth_mobility = []
    for epoch in range(n_epochs):
        epoch_mobility = []
        for ch in range(n_channels):
            signal = epochs_data[epoch, ch, :]
            diff_signal = np.diff(signal)
            
            var_signal = np.var(signal)
            var_diff = np.var(diff_signal)
            
            if var_signal > 0:
                mobility = np.sqrt(var_diff / var_signal)
            else:
                mobility = 0
            epoch_mobility.append(mobility)
        hjorth_mobility.append(np.mean(epoch_mobility))
    
    features.append(np.array(hjorth_mobility))
    feature_names.append('hjorth_mobility')
    
    # Hjorth Complexity (二阶导数复杂度/一阶导数复杂度)
    hjorth_complexity = []
    for epoch in range(n_epochs):
        epoch_complexity = []
        for ch in range(n_channels):
            signal = epochs_data[epoch, ch, :]
            diff1_signal = np.diff(signal)
            diff2_signal = np.diff(diff1_signal)
            
            var_signal = np.var(signal)
            var_diff1 = np.var(diff1_signal)
            var_diff2 = np.var(diff2_signal)
            
            if var_signal > 0 and var_diff1 > 0:
                mobility_signal = np.sqrt(var_diff1 / var_signal)
                mobility_diff1 = np.sqrt(var_diff2 / var_diff1)
                complexity = mobility_diff1 / mobility_signal
            else:
                complexity = 0
            epoch_complexity.append(complexity)
        hjorth_complexity.append(np.mean(epoch_complexity))
    
    features.append(np.array(hjorth_complexity))
    feature_names.append('hjorth_complexity')
    
    # 9. 波形长度特征
    print("提取波形特征...")
    
    # 波形长度 (Waveform Length) - 信号总变化量
    waveform_length = []
    for epoch in range(n_epochs):
        epoch_wl = []
        for ch in range(n_channels):
            signal = epochs_data[epoch, ch, :]
            wl = np.sum(np.abs(np.diff(signal)))
            epoch_wl.append(wl)
        waveform_length.append(np.mean(epoch_wl))
    
    features.append(np.array(waveform_length))
    feature_names.append('waveform_length')
    
    # 标准化波形长度
    normalized_wl = np.array(waveform_length) / n_times
    features.append(normalized_wl)
    feature_names.append('normalized_waveform_length')
    
    # 合并所有特征
    features_array = np.column_stack(features)
    
    print(f"\n时域特征提取完成!")
    print(f"总共提取了 {features_array.shape[1]} 个时域特征")
    print(f"特征矩阵形状: {features_array.shape}")
    
    return features_array, feature_names
