"""
EEG CNN模型用于PD刺激检测
基于PyTorch实现的CNN模型，用于检测PD患者的刺激状态
"""

import torch
import torch.nn as nn
import numpy as np
import mne
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class EEGCNNModel(nn.Module):
    def __init__(self, input_channels=32):
        super(EEGCNNModel, self).__init__()
        
        self.conv_block1 = nn.Sequential(
            nn.Conv1d(in_channels=input_channels, out_channels=16, kernel_size=15, stride=1, padding='same'),
            nn.BatchNorm1d(16),
            nn.LeakyReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.Dropout(0.3)
        )
        
        self.conv_block2 = nn.Sequential(
            nn.Conv1d(in_channels=16, out_channels=32, kernel_size=31, stride=1, padding='same'),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.Dropout(0.3)
        )
        
        self.conv_block3 = nn.Sequential(
            nn.Conv1d(in_channels=32, out_channels=64, kernel_size=63, stride=1, padding='same'),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.Dropout(0.3)
        )
        
        self.classifier_head = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(start_dim=1),
            nn.Dropout(0.5),
            nn.Linear(64, 1)  # 二分类，输出1个logit
        )

    def forward(self, x):
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        x = self.conv_block3(x)
        x = self.classifier_head(x)
        return x


class PDStimulationDetector:
    """
    PD刺激检测器类
    封装模型加载、预处理和预测功能
    """
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.channel_scalers = None
        self.model_path = model_path
        
        # 如果没有指定模型路径，使用默认路径
        if not self.model_path:
            # 搜索 app/dl_models/pd 目录下的模型文件
            project_root = Path(__file__).resolve().parent.parent.parent
            pd_models_dir = project_root / 'app' / 'dl_models' / 'pd'
            
            chosen = None
            if pd_models_dir.exists() and pd_models_dir.is_dir():
                # 找到第一个 .pth 或 .pt 文件作为默认模型
                pths = sorted([p for p in pd_models_dir.glob('*.pth')])
                pts = sorted([p for p in pd_models_dir.glob('*.pt')])
                candidates_files = pths + pts
                if candidates_files:
                    chosen = candidates_files[0]

            if chosen is None:
                # 没有找到模型文件，设置一个默认路径供参考
                self.model_path = pd_models_dir / 'default_model.pth'
                logger.warning(f"没有在 {pd_models_dir} 中找到模型文件，请将PD模型放到该目录")
            else:
                self.model_path = chosen
        
        # 自动加载模型（仅在路径存在时）
        try:
            if self.model_path and Path(self.model_path).exists():
                self.load_model()
            else:
                logger.warning(f"模型文件不存在，未加载: {self.model_path}")
        except Exception:
            # load_model 会记录错误并抛出；这里捕获避免初始化失败时中断整个应用
            logger.exception("尝试加载模型时发生异常")
    
    def load_model(self, model_path: Optional[str] = None):
        """加载训练好的模型"""
        if model_path:
            self.model_path = model_path
            
        if not self.model_path:
            raise ValueError("未指定模型路径")
            
        try:
            model_path_obj = Path(self.model_path)
            if not model_path_obj.exists():
                raise FileNotFoundError(f"模型文件不存在: {self.model_path}")

            # 先尝试直接 load（可能是完整模型对象或 state_dict）
            try:
                loaded_obj = torch.load(str(model_path_obj), map_location=self.device)
            except Exception as e_load:
                # 如果是 PyTorch 2.6+ 的 weights-only 安全限制导致的错误，尝试在信任文件的前提下用完整加载
                err_msg = str(e_load)
                logger.warning(f"首次 torch.load 失败，尝试用完整加载策略：{err_msg}")
                try:
                    # 首选直接调用 weights_only=False（PyTorch 2.6+）
                    loaded_obj = torch.load(str(model_path_obj), map_location=self.device, weights_only=False)
                except TypeError:
                    # 旧版本 torch.load 可能不支持 weights_only 参数，继续尝试不带该参数
                    try:
                        # 使用 safe_globals 上下文允许反序列化 EEGCNNModel（仅在你信任模型时）
                        try:
                            from torch.serialization import safe_globals
                        except Exception:
                            safe_globals = None

                        if safe_globals is not None:
                            with safe_globals([EEGCNNModel]):
                                loaded_obj = torch.load(str(model_path_obj), map_location=self.device)
                        else:
                            # 作为最后手段，尝试直接加载（风险由调用方承担）
                            loaded_obj = torch.load(str(model_path_obj), map_location=self.device)
                    except Exception:
                        logger.exception("在尝试完整加载模型时发生错误")
                        raise
                except Exception:
                    # 若直接指定 weights_only=False 也失败，尝试在 safe_globals 上下文中加载（更安全）
                    try:
                        from torch.serialization import safe_globals
                        with safe_globals([EEGCNNModel]):
                            loaded_obj = torch.load(str(model_path_obj), map_location=self.device, weights_only=False)
                    except Exception:
                        logger.exception("在尝试使用 safe_globals 加载模型时发生错误")
                        raise

            # 情况1: 保存的是整个模型对象 (torch.save(model))
            if isinstance(loaded_obj, nn.Module):
                self.model = loaded_obj

            # 情况2: 保存的是字典（通常为 state_dict 或 包含 state_dict 的封装）
            elif isinstance(loaded_obj, dict):
                # 常见的key名：'state_dict', 'model_state_dict'，或直接就是 state_dict 映射
                if 'state_dict' in loaded_obj and isinstance(loaded_obj['state_dict'], dict):
                    state = loaded_obj['state_dict']
                elif 'model_state_dict' in loaded_obj and isinstance(loaded_obj['model_state_dict'], dict):
                    state = loaded_obj['model_state_dict']
                else:
                    # 假设该 dict 本身就是 state_dict 映射
                    state = loaded_obj

                # 如果 checkpoint 中包含 channel_scalers, 保存以便推理时使用
                if isinstance(loaded_obj, dict) and 'channel_scalers' in loaded_obj:
                    self.channel_scalers = loaded_obj['channel_scalers']

                # 创建模型实例并加载 state_dict
                self.model = EEGCNNModel(input_channels=32)
                try:
                    self.model.load_state_dict(state)
                except RuntimeError as e:
                    # 更友好的错误信息，用于权重 shape/缺失键的问题
                    logger.error(f"加载 state_dict 失败: {e}")
                    raise

            else:
                raise ValueError("无法识别的模型文件格式，需为 nn.Module 或 state_dict dict")

            # 将模型移动到设备并切换为评估模式
            self.model.to(self.device)
            self.model.eval()

            logger.info(f"模型已成功加载: {self.model_path} -> {self.device}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            self.model = None
            raise
    
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.model is not None
    
    def preprocess_epochs(self, epochs_file_path: str) -> torch.Tensor:
        """
        预处理epochs文件
        
        Args:
            epochs_file_path: epochs文件路径(.fif格式)
            
        Returns:
            处理后的张量数据，形状为 (N, C, L)
        """
        try:
            # 读取epochs文件
            epochs = mne.read_epochs(epochs_file_path, preload=True, verbose=False)
            
            if len(epochs) == 0:
                raise ValueError("Epochs文件中没有有效的数据")
            
            # 获取数据并转换单位为微伏 (与训练时保持一致)
            epochs_data = epochs.get_data() * 1e6  # 从V转换为uV
            
            # 检查通道数
            if epochs_data.shape[1] != 32:
                raise ValueError(f"期望32个通道，但得到{epochs_data.shape[1]}个通道")
            
            # 转换维度: (N, C, L) -> (N, L, C)，为了标准化
            epochs_data = np.moveaxis(epochs_data, 1, 2)
            
            # 标准化处理 (优先使用训练时保存的 channel_scalers)
            if self.channel_scalers is not None:
                try:
                    # channel_scalers 格式应为 [{'mean': m, 'std': s}, ...]
                    data_scaled = np.zeros_like(epochs_data)
                    for ch in range(epochs_data.shape[2]):
                        mean = float(self.channel_scalers[ch].get('mean', 0.0))
                        std = float(self.channel_scalers[ch].get('std', 1.0))
                        if std == 0:
                            std = 1.0
                        data_scaled[:, :, ch] = (epochs_data[:, :, ch] - mean) / std
                    epochs_data_scaled = data_scaled
                except Exception as e:
                    logger.warning(f"应用保存的 channel_scalers 失败，回退到 z-score 标准化: {e}")
                    epochs_data_scaled = self._standardize_data(epochs_data)
            else:
                epochs_data_scaled = self._standardize_data(epochs_data)
            
            # 转换为PyTorch张量并调整维度: (N, L, C) -> (N, C, L)
            tensor_data = torch.FloatTensor(epochs_data_scaled).permute(0, 2, 1)
            
            return tensor_data.to(self.device)
            
        except Exception as e:
            logger.error(f"预处理epochs文件失败: {str(e)}")
            raise
    
    def _standardize_data(self, data: np.ndarray) -> np.ndarray:
        """
        标准化数据 (按通道进行z-score标准化)
        与训练时的标准化方式保持一致
        
        Args:
            data: 形状为 (N, L, C) 的数据
            
        Returns:
            标准化后的数据
        """
        data_scaled = np.zeros_like(data)
        
        # 对每个通道分别进行标准化
        for channel in range(data.shape[2]):
            channel_data = data[:, :, channel]
            mean = np.mean(channel_data)
            std = np.std(channel_data)
            
            # 防止除以零
            if std == 0:
                std = 1
                logger.warning(f"通道 {channel} 的标准差为0，使用1代替")
            
            data_scaled[:, :, channel] = (channel_data - mean) / std
        
        return data_scaled
    
    def predict(self, epochs_file_path: str) -> Dict[str, Any]:
        """
        预测epochs文件的刺激状态
        
        Args:
            epochs_file_path: epochs文件路径
            
        Returns:
            预测结果字典，包含：
            - overall_prediction: 总体预测 ("ON" 或 "OFF")
            - confidence: 置信度 (0-1)
            - average_probability: 平均概率
            - total_epochs: 总epoch数
            - on_epochs: 预测为ON的epoch数
            - off_epochs: 预测为OFF的epoch数
            - epoch_predictions: 每个epoch的预测结果列表
            - epoch_probabilities: 每个epoch的概率列表
        """
        if not self.is_model_loaded():
            raise ValueError("模型尚未加载，请先调用load_model()或检查模型文件是否存在")
        
        try:
            # 预处理数据
            input_tensor = self.preprocess_epochs(epochs_file_path)
            
            # 确保模型已加载
            if self.model is None:
                raise ValueError("模型未正确加载")
            
            # 模型预测
            with torch.no_grad():
                logits = self.model(input_tensor)
                probabilities = torch.sigmoid(logits)  # 转换为概率
                predictions = (probabilities > 0.5).float()  # 二分类阈值
            
            # 转换回CPU并计算统计信息
            probs_cpu = probabilities.cpu().numpy().flatten()
            preds_cpu = predictions.cpu().numpy().flatten().astype(int)
            
            # 计算各epoch的预测结果
            num_epochs = len(probs_cpu)
            on_count = int(np.sum(preds_cpu))
            off_count = num_epochs - on_count
            
            # 总体预测（基于多数投票）
            overall_prediction = "ON" if on_count > off_count else "OFF"
            confidence = max(on_count, off_count) / num_epochs
            
            # 平均概率
            avg_probability = float(np.mean(probs_cpu))
            
            result = {
                "overall_prediction": overall_prediction,
                "confidence": float(confidence),
                "average_probability": avg_probability,
                "total_epochs": num_epochs,
                "on_epochs": on_count,
                "off_epochs": off_count,
                "epoch_predictions": preds_cpu.tolist(),
                "epoch_probabilities": probs_cpu.tolist()
            }
            
            logger.info(
                f"预测完成 - 文件: {Path(epochs_file_path).name}, "
                f"结果: {overall_prediction}, 置信度: {confidence:.2%}, "
                f"总epochs: {num_epochs}, ON: {on_count}, OFF: {off_count}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            "model_loaded": self.is_model_loaded(),
            "model_path": str(self.model_path),
            "device": self.device,
            "input_channels": 32,
            "model_type": "EEGCNNModel"
        }
        
        if self.is_model_loaded() and self.model is not None:
            # 计算模型参数数量
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            
            info.update({
                "total_parameters": total_params,
                "trainable_parameters": trainable_params,
                "model_size_mb": total_params * 4 / (1024 * 1024)  # 假设float32
            })
        
        return info
    
    @staticmethod
    def get_available_models() -> List[Dict[str, Any]]:
        """获取可用的PD模型列表"""
        project_root = Path(__file__).resolve().parent.parent.parent
        pd_models_dir = project_root / 'app' / 'dl_models' / 'pd'
        
        models = []
        if pd_models_dir.exists() and pd_models_dir.is_dir():
            # 搜索所有 .pth 和 .pt 文件
            model_files = list(pd_models_dir.glob('*.pth')) + list(pd_models_dir.glob('*.pt'))
            
            for model_file in sorted(model_files):
                try:
                    # 获取文件信息
                    file_size = model_file.stat().st_size
                    file_size_mb = file_size / (1024 * 1024)
                    
                    # 尝试快速检查模型是否可以加载（只检查格式，不实际加载）
                    is_valid = True
                    error_message = None
                    
                    try:
                        # 快速检查文件是否为有效的PyTorch文件
                        torch.load(str(model_file), map_location='cpu', weights_only=True)
                    except Exception as e:
                        # 如果weights_only加载失败，尝试完整加载检查
                        try:
                            torch.load(str(model_file), map_location='cpu', weights_only=False)
                        except Exception as e2:
                            is_valid = False
                            error_message = f"模型文件格式错误: {str(e2)[:100]}"
                    
                    models.append({
                        "name": model_file.name,
                        "path": str(model_file),
                        "size_mb": round(file_size_mb, 2),
                        "is_valid": is_valid,
                        "error_message": error_message
                    })
                    
                except Exception as e:
                    models.append({
                        "name": model_file.name,
                        "path": str(model_file),
                        "size_mb": 0,
                        "is_valid": False,
                        "error_message": f"读取文件信息失败: {str(e)}"
                    })
        
        return models


# 创建全局检测器实例
pd_detector = PDStimulationDetector()