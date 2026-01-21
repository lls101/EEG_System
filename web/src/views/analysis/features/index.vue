<template>
  <div class="p-16">
    <n-card title="EEG特征提取" :bordered="false">
      <n-grid :x-gap="24" :y-gap="24" :cols="2">
        <!-- 左列：参数设置 -->
        <n-gi>
          <n-space vertical :size="24">
            <!-- 第一步：选择数据源 -->
            <n-card title="第一步：选择数据源" :bordered="false" class="card-wrapper">
              <n-form
                ref="dataSourceFormRef"
                :model="dataSourceForm"
                :rules="dataSourceRules"
                label-placement="left"
                label-width="auto"
              >
                <n-form-item label="数据源类型" path="source_type">
                  <n-select
                    v-model:value="dataSourceForm.source_type"
                    placeholder="选择数据源类型"
                    :options="sourceTypeOptions"
                    @update:value="handleSourceTypeChange"
                  />
                </n-form-item>

                <n-form-item label="选择数据" path="source_id">
                  <n-select
                    v-model:value="dataSourceForm.source_id"
                    placeholder="选择具体的数据文件"
                    :options="sourceDataOptions"
                    :loading="loading.sourceData"
                    :disabled="!dataSourceForm.source_type"
                    filterable
                    clearable
                    @update:value="handleSourceDataChange"
                  />
                </n-form-item>
              </n-form>
            </n-card>

            <!-- 第二步：特征提取参数 -->
            <n-card title="第二步：特征提取参数" :bordered="false" class="card-wrapper">
              <n-form
                ref="featuresFormRef"
                :model="featuresForm"
                :rules="featuresRules"
                label-placement="left"
                label-width="auto"
                :disabled="!dataSourceForm.source_id"
              >
                <n-form-item label="特征域" path="domain">
                  <n-select
                    v-model:value="featuresForm.domain"
                    placeholder="选择特征域类型"
                    :options="domainOptions"
                    @update:value="handleDomainChange"
                  />
                </n-form-item>

                <n-form-item label="方法" path="method" v-if="showMethodOption">
                  <n-select
                    v-model:value="featuresForm.method"
                    placeholder="选择计算方法"
                    :options="methodOptions"
                  />
                </n-form-item>

                <n-form-item label="Epoch时长 (秒)" path="epoch_duration">
                  <n-input-number
                    v-model:value="featuresForm.epoch_duration"
                    :min="0.5"
                    :max="10"
                    :step="0.5"
                    placeholder="建议2-4秒"
                    class="w-full"
                  />
                </n-form-item>
              </n-form>

              <n-space justify="center" class="mt-6">
                <n-button
                  type="primary"
                  size="large"
                  :disabled="!canExtract"
                  :loading="loading.extract"
                  @click="handleExtractFeatures"
                >
                  开始特征提取
                </n-button>
              </n-space>
            </n-card>
          </n-space>
        </n-gi>

        <!-- 右列：结果展示 -->
        <n-gi>
          <n-space vertical :size="24">
            <!-- 数据源信息 -->
            <n-card title="数据源信息" :bordered="false" class="card-wrapper" v-if="selectedSourceInfo">
              <n-descriptions :column="1" label-placement="left">
                <n-descriptions-item label="数据源类型">
                  <n-tag :type="getSourceTypeTagType(selectedSourceInfo.type)">
                    {{ getSourceTypeLabel(selectedSourceInfo.type) }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="ID">{{ selectedSourceInfo.id }}</n-descriptions-item>
                <n-descriptions-item label="方法" v-if="selectedSourceInfo.method">
                  {{ selectedSourceInfo.method }}
                </n-descriptions-item>
                <n-descriptions-item label="移除成分" v-if="selectedSourceInfo.components_removed !== undefined">
                  {{ selectedSourceInfo.components_removed }} 个
                </n-descriptions-item>
                <n-descriptions-item label="小波类型" v-if="selectedSourceInfo.wavelet">
                  {{ selectedSourceInfo.wavelet }}
                </n-descriptions-item>
              </n-descriptions>
            </n-card>

            <!-- 特征提取结果 -->
            <n-card title="特征提取结果" :bordered="false" class="card-wrapper" v-if="extractionResult">
              <n-result status="success" title="特征提取完成">
                <template #footer>
                  <n-space vertical>
                    <n-descriptions :column="2" label-placement="left">
                      <n-descriptions-item label="特征数量">
                        {{ extractionResult.feature_count }}
                      </n-descriptions-item>
                      <n-descriptions-item label="Epoch数量">
                        {{ extractionResult.epoch_count }}
                      </n-descriptions-item>
                      <n-descriptions-item label="通道数量">
                        {{ extractionResult.channels.length }}
                      </n-descriptions-item>
                      <n-descriptions-item label="特征域">
                        <n-tag>{{ getDomainLabel(extractionResult.features_summary.domain) }}</n-tag>
                      </n-descriptions-item>
                    </n-descriptions>

                    <n-space justify="center">
                      <n-button type="primary" @click="handleDownload" :loading="loading.download">
                        <template #icon>
                          <Icon icon="mdi:download" />
                        </template>
                        下载CSV文件
                      </n-button>
                      <n-button @click="showStatistics = true">
                        查看统计信息
                      </n-button>
                    </n-space>
                  </n-space>
                </template>
              </n-result>
            </n-card>

            <!-- 处理进度 -->
            <n-card title="处理状态" :bordered="false" class="card-wrapper" v-if="loading.extract">
              <n-space vertical align="center">
                <n-spin size="large" />
                <n-text>正在进行特征提取，请稍候...</n-text>
                <n-progress
                  type="line"
                  :percentage="progressPercentage"
                  :show-indicator="false"
                />
              </n-space>
            </n-card>
          </n-space>
        </n-gi>
      </n-grid>
    </n-card>

    <!-- 统计信息模态框 -->
    <StatisticsModal
      :show="showStatistics"
      :statistics="extractionResult?.features_summary.feature_statistics"
      @close="showStatistics = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import {
  NCard, NGrid, NGi, NSpace, NForm, NFormItem, NSelect, NInputNumber,
  NButton, NDescriptions, NDescriptionsItem, NTag, NResult, NProgress,
  NSpin, NText, NIcon, useNotification, useDialog
} from 'naive-ui';
import { Icon } from '@iconify/vue';
import { request } from '@/service/request';
import StatisticsModal from './components/StatisticsModal.vue';

// 接口定义
interface DataSourceForm {
  source_type: string;
  source_id: number | null;
}

interface FeaturesForm {
  domain: string;
  method: string | null;
  epoch_duration: number;
}

interface ExtractionResult {
  success: boolean;
  message: string;
  feature_count: number;
  epoch_count: number;
  channels: string[];
  source_type: string;
  source_id: number;
  features_summary: {
    domain: string;
    total_features: number;
    feature_statistics: Record<string, any>;
  };
  download_url: string;
}

interface SourceOption {
  label: string;
  value: number;
  type?: string;
  method?: string;
  components_removed?: number;
  wavelet?: string;
  threshold_mode?: string;
}

const notification = useNotification();
const dialog = useDialog();

// 表单数据
const dataSourceForm = ref<DataSourceForm>({
  source_type: '',
  source_id: null
});

const featuresForm = ref<FeaturesForm>({
  domain: 'time',
  method: null,
  epoch_duration: 2.0
});

// 加载状态
const loading = ref({
  sourceData: false,
  extract: false,
  download: false
});

// 数据
const sourceDataOptions = ref<SourceOption[]>([]);
const selectedSourceInfo = ref<any>(null);
const extractionResult = ref<ExtractionResult | null>(null);
const showStatistics = ref(false);
const progressPercentage = ref(0);

// 选项配置
const sourceTypeOptions = [
  { label: '基础预处理', value: 'preprocessing' },
  { label: 'ICA清理数据', value: 'ica' },
  { label: '小波去噪数据', value: 'wavelet' }
];

const domainOptions = [
  { label: '时域特征', value: 'time' },
  { label: '频域特征', value: 'frequency' },
  { label: '时频域特征', value: 'time_frequency' }
];

// 计算属性
const showMethodOption = computed(() => {
  return featuresForm.value.domain === 'frequency' || featuresForm.value.domain === 'time_frequency';
});

const methodOptions = computed(() => {
  if (featuresForm.value.domain === 'frequency') {
    return [
      { label: 'Multitaper', value: 'multitaper' },
      { label: 'Welch', value: 'welch' }
    ];
  } else if (featuresForm.value.domain === 'time_frequency') {
    return [
      { label: 'Morlet小波', value: 'morlet' },
      { label: 'Multitaper', value: 'multitaper' },
      { label: 'Stockwell变换', value: 'stockwell' },
      { label: '短时傅里叶变换', value: 'stft' }
    ];
  }
  return [];
});

const canExtract = computed(() => {
  return dataSourceForm.value.source_id && featuresForm.value.domain;
});

// 表单验证规则
const dataSourceRules = {
  source_type: { required: true, message: '请选择数据源类型' },
  source_id: { required: true, message: '请选择具体数据', type: 'number' }
};

const featuresRules = {
  domain: { required: true, message: '请选择特征域' },
  epoch_duration: { required: true, message: '请设置Epoch时长', type: 'number' }
};

// 工具函数
const getSourceTypeLabel = (type: string) => {
  const map = {
    preprocessing: '基础预处理',
    ica: 'ICA清理',
    wavelet: '小波去噪'
  };
  return map[type] || type;
};

const getSourceTypeTagType = (type: string) => {
  const map = {
    preprocessing: 'info',
    ica: 'success',
    wavelet: 'warning'
  };
  return map[type] || 'default';
};

const getDomainLabel = (domain: string) => {
  const map = {
    time: '时域',
    frequency: '频域',
    time_frequency: '时频域'
  };
  return map[domain] || domain;
};

// 事件处理
const handleSourceTypeChange = async () => {
  dataSourceForm.value.source_id = null;
  selectedSourceInfo.value = null;
  extractionResult.value = null;

  if (dataSourceForm.value.source_type) {
    await loadSourceData();
  }
};

const handleSourceDataChange = () => {
  if (dataSourceForm.value.source_id) {
    const selectedOption = sourceDataOptions.value.find(
      option => option.value === dataSourceForm.value.source_id
    );
    if (selectedOption) {
      selectedSourceInfo.value = {
        type: dataSourceForm.value.source_type,
        id: dataSourceForm.value.source_id,
        method: selectedOption.method,
        components_removed: selectedOption.components_removed,
        wavelet: selectedOption.wavelet,
        threshold_mode: selectedOption.threshold_mode
      };
    }
  }
  extractionResult.value = null;
};

const handleDomainChange = () => {
  featuresForm.value.method = null;
  extractionResult.value = null;
};

const loadSourceData = async () => {
  if (!dataSourceForm.value.source_type) return;

  loading.value.sourceData = true;
  try {
    let endpoint = '';

    switch (dataSourceForm.value.source_type) {
      case 'preprocessing':
        endpoint = '/preprocess/preprocessing/steps/completed';
        break;
      case 'ica':
        endpoint = '/preprocess/ica/all';
        break;
      case 'wavelet':
        endpoint = '/preprocess/wavelet/all';
        break;
    }

    const response = await request({ method: 'GET', url: endpoint });

    if (response.error) {
      throw new Error(response.error.message || 'API request failed');
    }

    let dataArray: any[] = [];

    // Handle different response formats from the backend
    if (response.data && Array.isArray(response.data)) {
        // Direct array response
        dataArray = response.data;
    } else if (response.data && response.data.records && Array.isArray(response.data.records)) {
        // Paginated response like { records: [...], total, ... }
        dataArray = response.data.records;
    } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
        // Wrapped response like { code, msg, data: [...] }
        dataArray = response.data.data;
    } else {
        notification.error({
            title: '数据格式错误',
            content: '无法从API响应中找到有效的数据列表。'
        });
        sourceDataOptions.value = [];
        return;
    }

    sourceDataOptions.value = dataArray.map((item: any) => ({
      label: dataSourceForm.value.source_type === 'preprocessing'
        ? `${item.pipeline_name} (ID: ${item.id})`
        : `分析 ${item.id} - ${item.method || item.wavelet_name || ''}`,
      value: item.id,
      method: item.method || item.ica_method,
      components_removed: item.exclude_components?.length,
      wavelet: item.wavelet_name,
      threshold_mode: item.threshold_mode
    }));

  } catch (error: any) {
    notification.error({
      title: '加载失败',
      content: error.message || '无法加载数据源列表'
    });
  } finally {
    loading.value.sourceData = false;
  }
};

const handleExtractFeatures = async () => {
  loading.value.extract = true;
  progressPercentage.value = 0;

  // 模拟进度
  const progressInterval = setInterval(() => {
    if (progressPercentage.value < 90) {
      progressPercentage.value += Math.random() * 10;
    }
  }, 1000);

  try {
    const requestData = {
      source_type: dataSourceForm.value.source_type,
      source_id: dataSourceForm.value.source_id,
      domain: featuresForm.value.domain,
      epoch_duration: featuresForm.value.epoch_duration,
      ...(featuresForm.value.method && { method: featuresForm.value.method })
    };

    const response = await request({
      method: 'POST',
      url: '/features/extract',
      data: requestData
    });

    if (response.error) {
      throw new Error(response.error.message || 'Feature extraction failed');
    }

    if (response.data && response.data.success) {
      extractionResult.value = response.data;
      progressPercentage.value = 100;

      notification.success({
        title: '特征提取成功',
        content: `成功提取 ${response.data.feature_count} 个特征，共 ${response.data.epoch_count} 个epochs`
      });
    } else {
      throw new Error(response.data?.message || '特征提取失败');
    }
  } catch (error: any) {
    notification.error({
      title: '特征提取失败',
      content: error.message || '未知错误'
    });
  } finally {
    clearInterval(progressInterval);
    loading.value.extract = false;
  }
};

const handleDownload = async () => {
  if (!extractionResult.value?.download_url) return;

  loading.value.download = true;
  try {
    // 处理URL，避免重复的/api/v1路径
    let downloadUrl = extractionResult.value.download_url;
    // 如果download_url已经包含/api/v1，需要去掉，因为request服务的baseURL已经包含了/api/v1
    if (downloadUrl.startsWith('/api/v1/')) {
      downloadUrl = downloadUrl.substring(7); // 去掉前面的'/api/v1'
    }

    // 通过request服务下载文件，避免跨域问题
    const response = await request({
      method: 'GET',
      url: downloadUrl,
      responseType: 'blob'
    });

    if (response.error) {
      throw new Error('文件下载失败');
    }

    // 创建blob URL并下载
    const blob = response.data;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `features_${extractionResult.value.features_summary.domain}_${extractionResult.value.source_type}_${extractionResult.value.source_id}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // 清理blob URL
    window.URL.revokeObjectURL(url);

    notification.success({
      title: '下载开始',
      content: '特征文件正在下载中...'
    });
  } catch (error) {
    notification.error({
      title: '下载失败',
      content: '无法下载特征文件'
    });
  } finally {
    loading.value.download = false;
  }
};

// 清除方法选择当域改变时
watch(() => featuresForm.value.domain, () => {
  featuresForm.value.method = null;
});

onMounted(() => {
  // 页面加载时可以加载一些初始数据
});
</script>

<style scoped>
.card-wrapper {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.mt-6 {
  margin-top: 1.5rem;
}
</style>
