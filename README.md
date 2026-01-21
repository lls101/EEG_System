<!-- markdownlint-disable MD033 MD041 -->

<p align="center">
  <img src="web/public/favicon.svg" width="120" height="120" alt="EEG Analysis System">
</p>

<h1 align="center">EEG Signal Analysis System</h1>

<p align="center">
  基于 FastAPI + Vue3 的脑电信号分析与帕金森病检测系统
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue.js-3.x-4FC08D?logo=vue.js&logoColor=white" alt="Vue3">
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/MNE--Python-0A9EDC" alt="MNE-Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

---

## 项目简介

本系统是一个专业的 **EEG（脑电图）信号处理与分析平台**，集成了数据管理、信号预处理、特征提取和深度学习模型推理等功能。系统基于 [FastSoyAdmin](https://github.com/sleep1223/fast-soy-admin) 框架开发，主要面向神经科学研究和临床应用场景，特别是 **帕金森病（PD）的辅助检测**。

## 技术栈

<table>
<tr><th>层级</th><th>技术</th></tr>
<tr><td><b>后端框架</b></td><td>FastAPI / Tortoise ORM / Pydantic</td></tr>
<tr><td><b>信号处理</b></td><td>MNE-Python / NumPy / SciPy</td></tr>
<tr><td><b>深度学习</b></td><td>PyTorch</td></tr>
<tr><td><b>前端框架</b></td><td>Vue 3 / TypeScript / Vite 5</td></tr>
<tr><td><b>UI 组件</b></td><td>Naive UI / UnoCSS</td></tr>
<tr><td><b>数据可视化</b></td><td>Plotly.js / ECharts</td></tr>
<tr><td><b>状态管理</b></td><td>Pinia</td></tr>
<tr><td><b>数据库</b></td><td>SQLite / Redis（缓存）</td></tr>
</table>

## 核心功能

### 1. EEG 文件管理

支持多种 EEG 数据格式的上传、解析与管理：

| 格式 | 说明 |
|------|------|
| EDF / EDF+ | European Data Format |
| BDF | BioSemi Data Format |
| FIF | MNE-Python 原生格式 |
| SET / FDT | EEGLAB 格式 |
| VHDR | Brain Vision 格式 |
| NDF | 日本光电 Nihon Kohden 格式 |

- 自动格式识别与元数据提取
- 通道信息、采样率、时长等参数展示
- 文件状态追踪（原始/已预处理/已分析）

### 2. 信号预处理

#### 2.1 基础预处理
- **电极定位 (Montage)**：支持 10-20、Biosemi、EasyCap 等标准电极系统
- **坏导检测**：自动识别与手动标记异常通道
- **滤波处理**：
  - 陷波滤波（50/60 Hz 工频干扰）
  - 高通滤波（去除基线漂移）
  - 低通滤波（去除高频噪声）
- **重参考**：平均参考、REST、自定义参考电极
- **重采样**：调整采样频率

#### 2.2 ICA 独立成分分析
- **算法支持**：FastICA / Infomax / Extended Infomax / PICARD
- **成分可视化**：脑地形图、时间序列、功率谱
- **伪迹去除**：眼电、肌电、心电等伪迹识别与剔除

#### 2.3 小波去噪
- **ATAR 算法**：自适应阈值伪迹去除
- **小波基选择**：Daubechies、Symlet、Coiflet 等
- **阈值模式**：软阈值 / 硬阈值
- **异步处理**：支持后台任务执行

### 3. 特征提取

从预处理后的 EEG 信号中提取多域特征：

| 特征域 | 提取方法 |
|--------|----------|
| **时域** | 均值、方差、标准差、RMS、峰度、偏度、过零率、Hjorth 参数、样本熵、排列熵 |
| **频域** | Welch 功率谱密度、Multitaper 功率谱、各频段（δ/θ/α/β/γ）能量占比 |
| **时频域** | Morlet 小波变换、STFT 短时傅里叶变换、Stockwell 变换 |

- 可配置分段时长（epoch duration）
- 特征结果导出为 CSV 格式

### 4. 帕金森病检测

基于深度学习的 PD 状态分类系统：

- **模型架构**：多层 1D-CNN 卷积神经网络
- **检测目标**：DBS（脑深部电刺激）开/关状态
- **输出结果**：
  - 分段（epoch）级别预测
  - 置信度评分
  - 整体统计（ON/OFF 比例、平均概率）
- **模型管理**：支持动态加载自定义训练模型

### 5. 系统管理

- **用户管理**：注册、登录、信息维护
- **角色权限**：细粒度 RBAC 权限控制
- **菜单配置**：动态路由与菜单管理
- **日志审计**：API 调用日志记录
- **系统监控**：运行状态、文件统计

## 项目结构

```
fast-soy-admin/
├── app/                              # 后端应用
│   ├── api/v1/                       # API 路由层
│   │   ├── route/                    # 业务路由
│   │   │   ├── features.py           # 特征提取 API
│   │   │   └── pd_detection.py       # PD 检测 API
│   │   ├── preprocess/               # 预处理 API
│   │   └── system_manage/            # 系统管理 API
│   │
│   ├── controllers/                  # 控制器层
│   │   ├── eeg_controller.py         # EEG 文件处理
│   │   ├── preprocessing_controller.py
│   │   ├── ica_controller.py         # ICA 分析
│   │   ├── wavelet_controller.py     # 小波去噪
│   │   ├── features_controller.py    # 特征提取
│   │   └── pd_detection.py           # PD 检测
│   │
│   ├── core/                         # 核心算法
│   │   ├── features/                 # 特征提取算法实现
│   │   └── pd_detection.py           # 检测模型推理
│   │
│   ├── models/                       # 数据库模型 (Tortoise ORM)
│   │   ├── system/                   # 系统相关模型
│   │   └── preprocess/               # 预处理相关模型
│   │
│   ├── schemas/                      # Pydantic 数据模式
│   ├── dl_models/                    # 深度学习模型文件 (.pt)
│   └── utils/                        # 工具函数
│       └── NDF2MNE/                  # NDF 格式转换工具
│
├── web/                              # 前端应用
│   └── src/
│       ├── views/
│       │   ├── eegfile/              # 文件管理页面
│       │   ├── preprocess/           # 预处理页面
│       │   │   ├── basic/            # 基础预处理
│       │   │   ├── ica/              # ICA 分析
│       │   │   └── wavelet/          # 小波去噪
│       │   ├── analysis/             # 数据分析页面
│       │   │   └── features/         # 特征提取
│       │   ├── apply-model/          # 模型应用页面
│       │   └── manage/               # 系统管理页面
│       ├── components/               # 公共组件
│       │   └── advanced/
│       │       └── PlotlyChart.vue   # Plotly 图表组件
│       ├── hooks/                    # 组合式函数
│       └── locales/                  # 国际化配置
│
├── eeg_data/                         # EEG 数据存储目录
├── run.py                            # 后端启动入口
├── pyproject.toml                    # Python 项目配置
└── docker-compose.yml                # Docker 部署配置
```

## 使用流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │     │              │     │              │
│   上传文件   │ ──▶ │   预处理     │ ──▶ │  ICA/去噪   │ ──▶ │   特征提取   │ ──▶ │   模型分析   │
│              │     │              │     │              │     │              │     │              │
│  EDF/BDF/FIF │     │ 滤波/参考/   │     │  伪迹识别   │     │ 时域/频域/   │     │  PD 状态     │
│  SET/NDF...  │     │ 重采样       │     │  成分剔除   │     │ 时频域特征   │     │  分类检测    │
│              │     │              │     │              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- pnpm 8+
- Redis（可选，用于缓存）

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd fast-soy-admin

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f
```

### 方式二：手动部署

**后端**

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
# 或使用 pdm
pdm install

# 启动后端
python run.py
```

**前端**

```bash
cd web

# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 生产构建
pnpm build
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:9527 |
| 后端 API | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |
| ReDoc 文档 | http://localhost:8000/redoc |

## 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 123456 |

## 相关资源

- [FastSoyAdmin](https://github.com/sleep1223/fast-soy-admin) - 基础框架
- [MNE-Python](https://mne.tools/) - EEG 信号处理库
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Naive UI](https://www.naiveui.com/) - UI 组件库

## 开源协议

本项目基于 [MIT](./LICENSE) 协议开源。