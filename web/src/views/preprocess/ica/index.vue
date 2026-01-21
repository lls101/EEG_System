<template>
  <div class="p-16">
    <n-card title="ICA 伪迹去除" :bordered="false">
      <n-grid :x-gap="24" :y-gap="24" :cols="2">
        <!-- Left Column: Controls -->
        <n-gi>
          <n-space vertical :size="24">
            <!-- Step 1: Select Input File -->
            <n-spin :show="loading.preprocessedFiles">
              <n-card title="第一步：选择预处理文件" :bordered="false" class="card-wrapper">
                <n-form-item label="选择一个基础预处理后的文件作为输入">
                  <n-select
                    v-model:value="selectedStepId"
                    placeholder="请选择一个文件"
                    :options="preprocessedFileOptions"
                    filterable
                    clearable
                    @update:value="handleInputFileChange"
                  />
                </n-form-item>
              </n-card>
            </n-spin>

            <!-- Step 2: Fit ICA Model -->
            <n-spin :show="loading.fit">
              <n-card title="第二步：设置参数并拟合ICA模型" class="card-wrapper">
                <n-form
                  ref="fitFormRef"
                  :model="fitFormModel"
                  :rules="fitFormRules"
                  :disabled="!selectedStepId"
                  label-placement="left"
                  label-width="auto"
                >
                  <n-form-item label="ICA方法" path="method">
                    <n-select v-model:value="fitFormModel.method" :options="icaMethodOptions" />
                  </n-form-item>
                  <n-form-item label="成分数/方差" path="n_components">
                    <n-input-number
                      v-model:value="fitFormModel.n_components"
                      placeholder="如 0.99 (方差) 或 15 (个数)"
                      class="w-full"
                    />
                  </n-form-item>
                  <n-form-item label="随机种子" path="random_state">
                    <n-input-number v-model:value="fitFormModel.random_state" class="w-full" />
                  </n-form-item>
                </n-form>
                <n-button type="primary" block :disabled="!selectedStepId" :loading="loading.fit" @click="handleFitIca">
                  拟合ICA模型
                </n-button>
              </n-card>
            </n-spin>

            <!-- Step 3: Inspect and Apply -->
            <n-spin :show="loading.apply">
              <n-card v-if="icaFitResult.ica_analysis_id" title="第三步：选择伪迹成分并应用" class="card-wrapper">
                <n-h4>ICA 成分图谱</n-h4>
                <n-p>请观察以下地形图，勾选您认为是伪迹的成分。</n-p>
                <n-checkbox-group v-model:value="applyParams.exclude_components">
                  <n-grid :y-gap="8" :cols="5">
                    <n-gi v-for="plot in icaFitResult.plots" :key="plot.index">
                      <n-card class="plot-card">
                        <template #cover>
                          <img :src="getFullImageUrl(plot.plot_url)" alt="Component Plot" />
                        </template>
                        <n-checkbox :value="plot.index" :label="`IC ${plot.index}`" />
                      </n-card>
                    </n-gi>
                  </n-grid>
                </n-checkbox-group>
                <n-divider />
                <n-form-item label="保存去噪后的文件">
                  <n-switch v-model:value="applyParams.save_file" />
                </n-form-item>
                <n-button
                  type="primary"
                  block
                  :disabled="!icaFitResult.ica_analysis_id || applyParams.exclude_components.length === 0"
                  :loading="loading.apply"
                  @click="handleApplyIca"
                >
                  应用剔除
                </n-button>
              </n-card>
            </n-spin>
          </n-space>
        </n-gi>

        <!-- Right Column: Results Table -->
        <n-gi class="flex flex-col">
          <n-card
            title="ICA去噪结果列表"
            class="card-wrapper flex-1 flex flex-col"
            :content-style="{ display: 'flex', flexDirection: 'column', flexGrow: 1 }"
          >
            <n-data-table
              class="flex-1"
              flex-height
              :columns="tableColumns"
              :data="tableState.data"
              :loading="loading.table"
            />
          </n-card>
        </n-gi>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, h } from 'vue';
import {
  useNotification,
  useDialog,
  NButton,
  NSpace,
  NTooltip,
  type SelectOption,
  type FormInst,
  type FormRules,
  type DataTableColumns
} from 'naive-ui';
import { request } from '@/service/request';
import { formatDateTime } from '@/utils/common';
import { Icon } from '@iconify/vue';

// --- Interfaces and Types ---
interface PreprocessedFile {
  id: number;
  pipeline_name: string;
  original_filename: string;
}

interface IcaPlot {
  index: number;
  plot_url: string;
}

interface IcaFitResult {
  ica_analysis_id: number | null;
  plots: IcaPlot[];
}

// --- Hooks ---
const notification = useNotification();
const dialog = useDialog();

// --- State ---
const loading = reactive({
  preprocessedFiles: false,
  fit: false,
  apply: false,
  table: false
});

const selectedStepId = ref<number | null>(null);
const preprocessedFileOptions = ref<SelectOption[]>([]);

const fitFormRef = ref<FormInst | null>(null);
const fitFormModel = ref({
  method: 'fastica',
  n_components: 0.99,
  random_state: 42
});

const icaFitResult = reactive<IcaFitResult>({ ica_analysis_id: null, plots: [] });
const applyParams = ref({ exclude_components: [], save_file: true });

const tableState = reactive({ data: [] });

// --- Static Config ---
const fitFormRules: FormRules = {
  method: { required: true, message: '请选择ICA方法' },
  n_components: { type: 'number', required: true, message: '请输入成分数或方差' }
};

const icaMethodOptions = ['fastica', 'infomax', 'picard'].map(m => ({ label: m, value: m }));

const tableColumns: DataTableColumns<any> = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '源文件ID', key: 'preprocessing_step_id' },
  { title: '剔除成分', key: 'exclude_components', render: row => JSON.stringify(row.exclude_components) },
  { title: '创建时间', key: 'create_time', render: row => formatDateTime(row.create_time) }
];

// --- Functions ---
function getFullImageUrl(plotUrl: string) {
  // The backend now serves the eeg_data directory at the /eeg_data endpoint
  const baseUrl = 'http://127.0.0.1:8001/eeg_data';
  return `${baseUrl}/${plotUrl}`;
}

async function fetchPreprocessedFiles() {
  loading.preprocessedFiles = true;
  try {
    const { data } = await request<any>({ url: '/preprocess/preprocessing/steps/completed', method: 'get' });
    console.log(data);
    preprocessedFileOptions.value = (data.records || []).map((file: PreprocessedFile) => ({
      label: `${file.pipeline_name} (Source: ${file.original_filename})`,
      value: file.id
    }));
  } catch (error: any) {
    notification.error({ title: '获取预处理文件失败', content: error.message });
  } finally {
    loading.preprocessedFiles = false;
  }
}

async function fetchIcaAnalyses(stepId: number) {
  if (!stepId) {
    tableState.data = [];
    return;
  }

  loading.table = true;
  try {
    console.log('[前端] 获取ICA分析记录，stepId:', stepId);
    const response = await request<any>({
      url: `/preprocess/ica/analyses/${stepId}`,
      method: 'get'
    });

    console.log('[前端] ICA分析记录响应:', response);

    // 处理响应数据格式
    if (response.error === null && response.data) {
      tableState.data = response.data || [];
      console.log('[前端] 设置表格数据:', tableState.data);
    } else {
      console.error('[前端] 获取ICA分析记录失败:', response.error);
      tableState.data = [];
    }
  } catch (error: any) {
    console.error('[前端] 获取ICA分析记录异常:', error);
    notification.error({ title: '获取ICA分析记录失败', content: error.message });
    tableState.data = [];
  } finally {
    loading.table = false;
  }
}

async function handleFitIca() {
  if (!selectedStepId.value) return;
  await fitFormRef.value?.validate();
  loading.fit = true;
  try {
    console.log('[前端] 开始发送 ICA 拟合请求');
    console.log('[前端] 选择的步骤ID:', selectedStepId.value);
    console.log('[前端] 请求参数:', fitFormModel.value);

    // 接收标准的 API 响应格式
    const response = await request<any>({
      url: `/preprocess/ica/fit/${selectedStepId.value}`,
      method: 'post',
      data: fitFormModel.value,
      timeout: 10 * 60 * 1000
    });

    console.log('[前端] 收到服务器响应:', response);
    console.log('[前端] 错误状态:', response.error);
    console.log('[前端] 响应数据:', response.data);

    // 检查响应是否成功 - FlatResponseData 格式：error 为 null 表示成功
    if (response.error !== null) {
      console.error('[前端] 请求有错误，视为失败:', response.error);
      throw new Error(response.error?.message || 'ICA拟合失败');
    }

    // 从 data 字段中提取实际数据
    const { data } = response;
    console.log('[前端] 提取的数据对象:', data);

    // 验证数据结构
    if (!data || typeof data.ica_analysis_id !== 'number' || !Array.isArray(data.plots)) {
      console.error('[前端] 数据结构验证失败');
      console.error('[前端] data 存在性:', !!data);
      console.error('[前端] ica_analysis_id 类型:', typeof data?.ica_analysis_id);
      console.error('[前端] plots 是否为数组:', Array.isArray(data?.plots));
      throw new Error('服务器返回的数据格式不正确');
    }

    console.log('[前端] 数据结构验证通过');
    console.log('[前端] ICA分析ID:', data.ica_analysis_id);
    console.log('[前端] 图片数组:', data.plots);

    // 设置 ICA 拟合结果
    icaFitResult.ica_analysis_id = data.ica_analysis_id;
    icaFitResult.plots = data.plots; // 直接使用 plots 数组，因为它已经包含 index 和 plot_url

    console.log('[前端] ICA拟合结果设置完成');
    notification.success({
      title: 'ICA拟合成功',
      content: `成功生成 ${data.plots.length} 个ICA成分，请检查下方组件图并选择伪迹。`
    });

    // 刷新ICA分析记录列表
    if (selectedStepId.value) {
      fetchIcaAnalyses(selectedStepId.value);
    }
  } catch (error: any) {
    console.error('[前端] ICA拟合错误:', error);
    console.error('[前端] 错误堆栈:', error.stack);
    notification.error({
      title: 'ICA拟合失败',
      content: error.message || '请求失败，请检查网络连接'
    });
  } finally {
    loading.fit = false;
  }
}

async function handleApplyIca() {
  if (!icaFitResult.ica_analysis_id) return;
  loading.apply = true;
  try {
    await request<any>({
      url: `/preprocess/ica/apply/${icaFitResult.ica_analysis_id}`,
      method: 'post',
      data: applyParams.value
    });
    notification.success({ title: 'ICA应用成功', content: '伪迹已剔除，结果已保存。' });
    // Reset and refresh
    icaFitResult.ica_analysis_id = null;
    icaFitResult.plots = [];
    applyParams.value = { exclude_components: [], save_file: true };
    // 刷新ICA分析记录列表
    if (selectedStepId.value) {
      fetchIcaAnalyses(selectedStepId.value);
    }
  } catch (error: any) {
    notification.error({ title: 'ICA应用失败', content: error.message });
  } finally {
    loading.apply = false;
  }
}

function handleInputFileChange() {
  icaFitResult.ica_analysis_id = null;
  icaFitResult.plots = [];

  // 当用户选择文件时，获取对应的ICA分析记录
  if (selectedStepId.value) {
    fetchIcaAnalyses(selectedStepId.value);
  } else {
    tableState.data = [];
  }
}

onMounted(() => {
  fetchPreprocessedFiles();
});
</script>

<style scoped>
.w-full {
  width: 100%;
}
.card-wrapper {
  border-radius: 8px;
  box-shadow: 0 1px 2px -2px rgba(0, 0, 0, 0.08), 0 3px 6px 0 rgba(0, 0, 0, 0.06), 0 5px 12px 4px rgba(0, 0, 0, 0.04);
}
.plot-card {
  text-align: center;
}
.flex-col {
  display: flex;
  flex-direction: column;
}
.flex-1 {
  flex: 1 1 0%;
}
</style>
