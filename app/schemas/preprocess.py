from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Dict, Any

# MNE支持众多标准电极帽，我们这里列出一些常用的作为枚举
# 这将给前端提供一个明确的选项列表，并提供后端类型安全
class MontageOptions(str, Enum):
    STANDARD_1020 = "standard_1020"
    STANDARD_1005 = "standard_1005"
    BIOSEMI64 = "biosemi64"
    BIOSEMI32 = "biosemi32"
    EGI_256 = "egi_256"
    GSN_HYDROCEL_128 = "gsn-hydrocel-128"

class SetMontageRequest(BaseModel):
    montage_name: MontageOptions = Field(..., description="要应用的电极位置标准名称")

class ChannelSelectionRequest(BaseModel):
    # 可以按类型选择，也可以按名称，但最终传给后端的都是要保留的通道名称列表
    channels_to_keep: List[str] = Field([], description="按名称指定要保留的通道列表")
    channel_types_to_keep: List[str] = Field([], description="按类型指定要保留的通道列表 (例如 ['eeg', 'eog'])")

class ChannelInfo(BaseModel):
    name: str
    type: str

class ChannelInfoResponse(BaseModel):
    by_type: Dict[str, List[str]]
    all_channels: List[ChannelInfo]

class ElectrodePosition(BaseModel):
    ch_name: str
    x: float
    y: float
    z: float

class SetMontageResponse(BaseModel):
    message: str
    channel_positions: List[ElectrodePosition]

class ChannelSelectionResponse(BaseModel):
    message: str
    n_channels_before: int
    n_channels_after: int
    channels_kept: List[str]