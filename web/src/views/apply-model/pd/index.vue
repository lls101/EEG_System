<template>
  <div class="p-16">
    <n-card title="PD刺激检测" :bordered="false">
      <n-grid :x-gap="24" :y-gap="24" :cols="2">
        <!-- 左列：文件上传和检测 -->
        <n-gi>
          <n-space vertical :size="24">
            <!-- 文件上传区域 -->
            <n-card title="上传 EEG Epochs 文件" :bordered="false" class="card-wrapper">
              <n-space vertical :size="16">
                <n-upload
                  ref="uploadRef"
                  :file-list="fileList"
                  :max="1"
                  accept=".fif,.fif.gz"
                  :show-file-list="true"
                  :on-change="handleFileChange"
                  :on-remove="handleFileRemove"
                  :custom-request="customRequest"
                  :disabled="uploading"
                >
                  <n-upload-dragger>
                    <div style="margin-bottom: 12px">
                      <n-icon size="48" :depth="3">
                        <Icon icon="mdi:cloud-upload-outline" />
                      </n-icon>
                    </div>
                    <n-text style="font-size: 16px">
                      点击或者拖动文件到该区域来上传
                    </n-text>
                    <n-p depth="3" style="margin: 8px 0 0 0">
                      支持 .fif 和 .fif.gz 格式的 MNE Epochs 文件
                    </n-p>
                  </n-upload-dragger>
                </n-upload>

                <n-button
                  type="primary"
                  size="large"
                  :loading="uploading"
                  :disabled="!selectedFile || !modelInfo?.model_loaded"
                  @click="handleUpload"
                  block
                >
                  {{ !modelInfo?.model_loaded ? '请先加载模型' : '开始检测' }}
                </n-button>

                <!-- 模型未加载提示 -->
                <n-alert v-if="!modelInfo?.model_loaded && !loading.modelInfo" type="warning" title="模型未加载">
                  请先在下方选择并加载一个PD检测模型
                </n-alert>

                <!-- 进度提示 -->
                <n-alert v-if="uploading" type="info" title="检测中">
                  正在分析 EEG 数据，请稍候...
                </n-alert>
              </n-space>
            </n-card>

            <!-- 模型选择 -->
            <n-card title="模型选择" :bordered="false" class="card-wrapper">
              <n-space vertical :size="16">
                <n-select
                  v-model:value="selectedModelName"
                  placeholder="选择PD检测模型"
                  :options="modelOptions"
                  :loading="loading.models"
                  @update:value="handleModelChange"
                  filterable
                >
                  <template #option="{ node, option }">
                    <n-space align="center" justify="space-between">
                      <span>{{ option.label }}</span>
                      <n-space>
                        <n-tag size="small" :type="option.is_valid ? 'success' : 'error'">
                          {{ option.is_valid ? '可用' : '错误' }}
                        </n-tag>
                        <n-text depth="3" style="font-size: 12px">
                          {{ option.size_mb }} MB
                        </n-text>
                      </n-space>
                    </n-space>
                  </template>
                </n-select>

                <n-button
                  type="primary"
                  :loading="loading.loadModel"
                  :disabled="!selectedModelName"
                  @click="handleLoadModel"
                  size="medium"
                >
                  加载模型
                </n-button>
              </n-space>
            </n-card>

            <!-- 模型信息 -->
            <n-card title="模型信息" :bordered="false" class="card-wrapper">
              <n-spin :show="loading.modelInfo">
                <div v-if="modelInfo && modelInfo.model_loaded">
                  <n-descriptions :column="1" label-placement="left">
                    <n-descriptions-item label="模型状态">
                      <n-tag type="success">已加载</n-tag>
                    </n-descriptions-item>
                    <n-descriptions-item label="模型路径">
                      <n-text style="font-family: monospace; font-size: 12px">
                        {{ modelInfo.model_path }}
                      </n-text>
                    </n-descriptions-item>
                    <n-descriptions-item label="设备">{{ modelInfo.device }}</n-descriptions-item>
                    <n-descriptions-item label="输入通道">{{ modelInfo.input_channels }}</n-descriptions-item>
                    <n-descriptions-item label="参数数量">{{ formatNumber(modelInfo.total_parameters) }}</n-descriptions-item>
                    <n-descriptions-item label="模型大小">{{ modelInfo.model_size_mb?.toFixed(2) }} MB</n-descriptions-item>
                  </n-descriptions>
                </div>
                <n-empty v-else-if="modelInfo && !modelInfo.model_loaded" description="模型未加载，请选择并加载模型" />
                <n-empty v-else description="正在获取模型信息..." />
              </n-spin>
            </n-card>
          </n-space>
        </n-gi>

        <!-- 右列：检测结果 -->
        <n-gi>
          <n-space vertical :size="24">
            <!-- 检测结果 -->
            <n-card title="检测结果" :bordered="false" class="card-wrapper">
              <n-spin :show="uploading">
                <div v-if="detectionResult">
                  <!-- 总体结果 -->
                  <n-space vertical :size="16">
                    <n-result
                      :status="detectionResult.overall_prediction === 'ON' ? 'success' : 'warning'"
                      :title="detectionResult.overall_prediction === 'ON' ? '检测到刺激状态 (ON)' : '未检测到刺激状态 (OFF)'"
                    >
                      <template #footer>
                        <n-space vertical :size="8">
                          <n-progress
                            type="circle"
                            :percentage="Math.round(detectionResult.confidence * 100)"
                            :color="detectionResult.confidence > 0.8 ? '#18a058' : detectionResult.confidence > 0.6 ? '#f0a020' : '#d03050'"
                          >
                            置信度
                          </n-progress>
                        </n-space>
                      </template>
                    </n-result>

                    <!-- 详细统计 -->
                    <n-descriptions :column="2" label-placement="left" bordered>
                      <n-descriptions-item label="总 Epochs">{{ detectionResult.total_epochs }}</n-descriptions-item>
                      <n-descriptions-item label="平均概率">{{ (detectionResult.average_probability * 100).toFixed(1) }}%</n-descriptions-item>
                      <n-descriptions-item label="ON Epochs">
                        <n-tag type="success">{{ detectionResult.on_epochs }}</n-tag>
                      </n-descriptions-item>
                      <n-descriptions-item label="OFF Epochs">
                        <n-tag type="warning">{{ detectionResult.off_epochs }}</n-tag>
                      </n-descriptions-item>
                    </n-descriptions>

                    <!-- Epochs 预测分布图表 -->
                    <n-divider>Epochs 预测分布</n-divider>
                    <div ref="chartRef" style="height: 300px"></div>
                  </n-space>
                </div>
                <n-empty v-else description="尚未进行检测" />
              </n-spin>
            </n-card>
          </n-space>
        </n-gi>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import type { UploadFileInfo, UploadCustomRequestOptions } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { request } from '@/service/request';
import { $t } from '@/locales';

interface ModelInfo {
  model_loaded: boolean;
  model_path: string;
  device: string;
  input_channels: number;
  model_type: string;
  total_parameters?: number;
  trainable_parameters?: number;
  model_size_mb?: number;
}

interface AvailableModel {
  name: string;
  path: string;
  size_mb: number;
  is_valid: boolean;
  error_message?: string;
}

interface DetectionResult {
  overall_prediction: 'ON' | 'OFF';
  confidence: number;
  average_probability: number;
  total_epochs: number;
  on_epochs: number;
  off_epochs: number;
  epoch_predictions: number[];
  epoch_probabilities: number[];
}

interface ApiResponse {
  success: boolean;
  result: DetectionResult;
}

// 响应式数据
const fileList = ref<UploadFileInfo[]>([]);
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const detectionResult = ref<DetectionResult | null>(null);
const modelInfo = ref<ModelInfo | null>(null);
const chartRef = ref<HTMLElement>();

// 模型选择相关
const availableModels = ref<AvailableModel[]>([]);
const selectedModelName = ref<string>('');
const modelOptions = ref<Array<{label: string, value: string, size_mb: number, is_valid: boolean}>>([]);

const loading = ref({
  modelInfo: true,
  models: false,
  loadModel: false
});

// 格式化数字
const formatNumber = (num?: number) => {
  if (!num) return '0';
  return num.toLocaleString();
};

// 文件上传处理
const handleFileChange = (options: { fileList: UploadFileInfo[] }) => {
  fileList.value = options.fileList;
  if (options.fileList.length > 0) {
    const file = options.fileList[0].file;
    if (file) {
      selectedFile.value = file;
    }
  }
};

const handleFileRemove = () => {
  selectedFile.value = null;
  detectionResult.value = null;
};

// 自定义上传请求
const customRequest = (options: UploadCustomRequestOptions) => {
  // 阻止默认上传行为，我们手动处理
  return {};
};

// 执行上传和检测
const handleUpload = async () => {
  if (!selectedFile.value) {
    window.$message?.error('请选择要上传的文件');
    return;
  }

  uploading.value = true;
  detectionResult.value = null;

  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);

    const response = await request({
      method: 'POST',
      url: '/route/pd_detection/upload',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    if (response.error) {
      throw new Error(response.error.message || 'API request failed');
    }

    if (response.data?.success && response.data?.result) {
      detectionResult.value = response.data.result;
      window.$message?.success('检测完成！');

      // 渲染图表
      await nextTick();
      renderChart();
    } else {
      throw new Error('检测失败：响应格式错误');
    }
  } catch (error) {
    console.error('检测失败:', error);
    window.$message?.error(`检测失败: ${error instanceof Error ? error.message : '未知错误'}`);
  } finally {
    uploading.value = false;
  }
};

// 获取可用模型列表
const fetchAvailableModels = async () => {
  loading.value.models = true;
  try {
    const response = await request({
      method: 'GET',
      url: '/route/pd_detection/models'
    });

    if (response.error) {
      throw new Error(response.error.message || 'API request failed');
    }

    availableModels.value = response.data || [];
    modelOptions.value = availableModels.value.map(model => ({
      label: model.name,
      value: model.name,
      size_mb: model.size_mb,
      is_valid: model.is_valid
    }));

  } catch (error) {
    console.error('获取模型列表失败:', error);
    window.$message?.error('获取模型列表失败');
  } finally {
    loading.value.models = false;
  }
};

// 处理模型选择变化
const handleModelChange = (modelName: string) => {
  selectedModelName.value = modelName;
};

// 加载选中的模型
const handleLoadModel = async () => {
  if (!selectedModelName.value) return;

  loading.value.loadModel = true;
  try {
    const response = await request({
      method: 'POST',
      url: '/route/pd_detection/load_model',
      data: { model_name: selectedModelName.value }
    });

    if (response.error) {
      throw new Error(response.error.message || 'API request failed');
    }

    window.$message?.success(`模型 ${selectedModelName.value} 加载成功`);

    // 重新获取模型信息
    await fetchModelInfo();

  } catch (error) {
    console.error('加载模型失败:', error);
    window.$message?.error(`加载模型失败: ${error instanceof Error ? error.message : '未知错误'}`);
  } finally {
    loading.value.loadModel = false;
  }
};

// 获取模型信息
const fetchModelInfo = async () => {
  loading.value.modelInfo = true;
  try {
    const response = await request({
      method: 'GET',
      url: '/route/pd_detection/model_info'
    });

    if (response.error) {
      throw new Error(response.error.message || 'API request failed');
    }

    modelInfo.value = response.data;
  } catch (error) {
    console.error('获取模型信息失败:', error);
    // 如果是首次加载且没有模型，不显示错误消息
    // 只有在用户主动操作后失败才显示错误
    modelInfo.value = null;
  } finally {
    loading.value.modelInfo = false;
  }
};

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || !detectionResult.value) return;

  // 使用简单的可视化，显示每个 epoch 的预测概率
  const container = chartRef.value;
  container.innerHTML = '';

  const { epoch_probabilities, epoch_predictions } = detectionResult.value;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  if (!ctx) return;

  canvas.width = container.clientWidth;
  canvas.height = 300;
  container.appendChild(canvas);

  // 绘制概率分布
  const width = canvas.width;
  const height = canvas.height;
  const padding = 40;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;

  // 清空画布
  ctx.clearRect(0, 0, width, height);

  // 绘制坐标轴
  ctx.strokeStyle = '#666';
  ctx.lineWidth = 1;

  // Y轴
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.stroke();

  // X轴
  ctx.beginPath();
  ctx.moveTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  // 绘制数据点
  const stepX = chartWidth / epoch_probabilities.length;

  ctx.fillStyle = '#18a058';
  epoch_probabilities.forEach((prob, index) => {
    const x = padding + index * stepX;
    const y = height - padding - (prob * chartHeight);
    const isOn = epoch_predictions[index] === 1;

    ctx.fillStyle = isOn ? '#18a058' : '#f0a020';
    ctx.fillRect(x - 1, y, 2, height - padding - y);
  });

  // 添加标签
  ctx.fillStyle = '#333';
  ctx.font = '12px sans-serif';
  ctx.fillText('Epoch Index', width / 2 - 30, height - 10);

  ctx.save();
  ctx.translate(15, height / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Probability', -30, 0);
  ctx.restore();
};

// 组件挂载时获取模型信息和模型列表
onMounted(() => {
  fetchAvailableModels();
  fetchModelInfo();
});
</script>

<style scoped>
.card-wrapper {
  height: 100%;
}

.p-16 {
  padding: 16px;
}
</style>
