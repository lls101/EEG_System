# EEG特征提取前端页面

## 页面位置
`/analysis/features`

## 功能介绍

EEG特征提取页面提供了一个完整的Web界面，用于从不同数据源提取EEG特征。

### 主要功能

1. **数据源选择**
   - 基础预处理数据
   - ICA清理后数据
   - 小波去噪后数据

2. **特征提取配置**
   - 时域特征
   - 频域特征（Multitaper, Welch）
   - 时频域特征（Morlet小波, Multitaper, Stockwell变换, STFT）

3. **结果展示**
   - 特征统计信息
   - CSV文件下载
   - 详细统计数据查看

## 使用步骤

1. **选择数据源**
   - 从下拉列表中选择数据源类型
   - 选择具体的数据文件

2. **配置参数**
   - 选择特征域类型
   - 根据需要选择计算方法
   - 设置Epoch时长（建议2-4秒）

3. **执行提取**
   - 点击"开始特征提取"按钮
   - 等待处理完成

4. **查看结果**
   - 查看提取的特征数量和Epoch信息
   - 下载CSV文件
   - 查看详细统计信息

## 技术实现

- **前端框架**: Vue 3 + TypeScript
- **UI组件**: Naive UI
- **路由**: 自动生成路由系统
- **API**: RESTful API与后端通信

## 文件结构

```
web/src/views/analysis/features/
├── index.vue                    # 主页面
└── components/
    └── StatisticsModal.vue      # 统计信息模态框
```

## API端点

- `GET /api/v1/features/domains` - 获取支持的特征域
- `POST /api/v1/features/extract` - 执行特征提取
- `GET /api/v1/features/download/{filename}` - 下载结果文件
- `GET /api/v1/preprocess/steps` - 获取预处理步骤
- `GET /api/v1/preprocess/ica/all` - 获取ICA分析结果
- `GET /api/v1/preprocess/wavelet/all` - 获取小波去噪结果

## 特征输出

生成的CSV文件包含：
- `epoch`: Epoch编号
- `channel_count`: 通道数量
- 各种特征值（依据选择的域类型）

### 时域特征
- 均值、标准差、最大值、最小值等统计量
- 各通道的时域特征聚合

### 频域特征
- Delta, Theta, Alpha, Beta, Gamma各频段功率
- 功率谱密度相关特征

### 时频域特征
- 时频功率特征
- 频段比值（如Theta/Alpha）
- 光谱熵
- 时间变化特征

## 注意事项

1. 确保选择的数据源已完成相应的预处理
2. Epoch时长会影响特征的时间分辨率
3. 不同方法的计算时间可能有差异
4. 下载功能无需身份验证，便于文件共享
