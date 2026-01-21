<template>
  <div class="p-16">
    <n-card title="小波去噪 (ATAR)" :bordered="false">
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
                  />
                </n-form-item>
              </n-card>
            </n-spin>

            <!-- Step 2: Set Parameters and Denoise -->
            <n-spin :show="loading.denoise">
              <n-card title="第二步：设置ATAR参数并执行去噪" class="card-wrapper">
                <n-form
                  ref="denoiseFormRef"
                  :model="denoiseFormModel"
                  :rules="denoiseFormRules"
                  :disabled="!selectedStepId"
                  label-placement="left"
                  label-width="auto"
                >
                  <n-form-item label="小波基函数" path="wavelet_name">
                    <n-select v-model:value="denoiseFormModel.wavelet_name" :options="waveletOptions" />
                  </n-form-item>
                  <n-form-item label="窗口大小" path="window_size">
                    <n-input-number v-model:value="denoiseFormModel.window_size" class="w-full" />
                  </n-form-item>
                  <n-form-item label="阈值模式" path="optimal_mode">
                    <n-select v-model:value="denoiseFormModel.optimal_mode" :options="optimalModeOptions" />
                  </n-form-item>
                  <n-form-item label="调节参数 (beta)" path="beta">
                    <n-input-number v-model:value="denoiseFormModel.beta" :step="0.1" class="w-full" />
                  </n-form-item>
                  <n-form-item label="阈值下界 (k1)" path="k1">
                    <n-input-number v-model:value="denoiseFormModel.k1" class="w-full" />
                  </n-form-item>
                  <n-form-item label="阈值上界 (k2)" path="k2">
                    <n-input-number v-model:value="denoiseFormModel.k2" class="w-full" />
                  </n-form-item>
                  <n-form-item label="保存去噪文件">
                    <n-switch v-model:value="denoiseFormModel.save_file" />
                  </n-form-item>
                </n-form>
                <n-button type="primary" block :disabled="!selectedStepId" :loading="loading.denoise" @click="handleDenoise">
                  执行小波去噪
                </n-button>
              </n-card>
            </n-spin>
          </n-space>
        </n-gi>

        <!-- Right Column: Results Table -->
        <n-gi class="flex flex-col">
          <n-card
            title="小波去噪结果列表"
            class="card-wrapper flex-1 flex flex-col"
            :content-style="{ display: 'flex', flexDirection: 'column', flexGrow: 1 }"
          >
            <n-data-table
              class="flex-1"
              flex-height
              :columns="tableColumns"
              :data="tableState.data"
              :loading="loading.table"
              :pagination="pagination"
            />
          </n-card>
        </n-gi>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount, onMounted, reactive } from 'vue';
import {
  useNotification,
  type SelectOption,
  type FormInst,
  type FormRules,
  type DataTableColumns,
  type PaginationProps
} from 'naive-ui';
import { request } from '@/service/request';
import { formatDateTime } from '@/utils/common';

// --- Interfaces and Types ---
interface PreprocessedFile {
  id: number;
  pipeline_name: string;
  original_filename: string;
}

interface WaveletDenoiseResult {
  id: number;
  preprocessing_step_id: number;
  wavelet_name: string;
  window_size: number;
  optimal_mode: string;
  beta: number;
  k1: number;
  k2: number;
  status?: string;
  elapsed_seconds?: number | null;
  create_time: string;
}

// --- Hooks ---
const notification = useNotification();

// --- State ---
const loading = reactive({
  preprocessedFiles: false,
  denoise: false,
  table: false
});

const selectedStepId = ref<number | null>(null);
const preprocessedFileOptions = ref<SelectOption[]>([]);

const denoiseFormRef = ref<FormInst | null>(null);
const denoiseFormModel = ref({
  wavelet_name: 'db3',
  window_size: 128,
  optimal_mode: 'soft',
  beta: 0.1,
  k1: 10.0,
  k2: 100.0,
  save_file: true
});

const tableState = reactive({ data: [] as WaveletDenoiseResult[] });
const pagination = reactive<PaginationProps>({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  onChange: (page: number) => {
    pagination.page = page;
    fetchDenoiseResults();
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize;
    pagination.page = 1;
    fetchDenoiseResults();
  }
});

// --- Static Config ---
const denoiseFormRules: FormRules = {
  wavelet_name: { required: true, message: '请选择小波基函数' },
  window_size: { type: 'number', required: true, message: '请输入窗口大小' },
  optimal_mode: { required: true, message: '请选择阈值模式' },
  beta: { type: 'number', required: true, message: '请输入调节参数 beta' },
  k1: { type: 'number', required: true, message: '请输入阈值下界 k1' },
  k2: { type: 'number', required: true, message: '请输入阈值上界 k2' }
};

const waveletOptions = ['db3', 'db4', 'db5', 'sym4', 'sym5', 'coif2', 'coif3'].map(w => ({ label: w, value: w }));
const optimalModeOptions = [
  { label: '软阈值 (soft)', value: 'soft' },
  { label: '消除 (elim)', value: 'elim' },
  { label: '线性衰减 (linAtten)', value: 'linAtten' }
];

const tableColumns: DataTableColumns<WaveletDenoiseResult> = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '源文件ID', key: 'preprocessing_step_id' },
  { title: '小波基', key: 'wavelet_name' },
  { title: '窗口大小', key: 'window_size' },
  { title: '阈值模式', key: 'optimal_mode' },
  { title: 'Beta', key: 'beta' },
  { title: '状态', key: 'status', width: 120 },
  {
    title: '耗时(s)',
    key: 'elapsed_seconds',
    width: 120,
    render: row => (typeof row.elapsed_seconds === 'number' ? row.elapsed_seconds.toFixed(1) : '-')
  },
  { title: '创建时间', key: 'create_time', render: row => formatDateTime(row.create_time) }
];

const pollingTimer = ref<ReturnType<typeof setInterval> | null>(null);
const pollingTaskId = ref<number | null>(null);
const pollingIntervalMs = 5000;

function stopWaveletPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value);
    pollingTimer.value = null;
  }
  pollingTaskId.value = null;
}

async function pollWaveletTaskStatus() {
  if (!pollingTaskId.value) return;

  const response = await request<any>({
    url: `/preprocess/wavelet/tasks/${pollingTaskId.value}`,
    method: 'get'
  });

  if (response.error || !response.data) return;

  const status = response.data.status;
  if (status === 'Completed') {
    stopWaveletPolling();
    notification.success({ title: '小波去噪完成', content: '可以在结果列表中查看。' });
    fetchDenoiseResults();
  } else if (status === 'Failed' || status === 'Cancelled') {
    stopWaveletPolling();
    notification.error({ title: '小波去噪失败', content: `任务状态: ${status}` });
  }
}

function startWaveletPolling(taskId: number) {
  stopWaveletPolling();
  pollingTaskId.value = taskId;
  pollingTimer.value = setInterval(pollWaveletTaskStatus, pollingIntervalMs);
  pollWaveletTaskStatus();
}

// --- Functions ---
async function fetchPreprocessedFiles() {
  loading.preprocessedFiles = true;
  try {
    const { data } = await request<any>({ url: '/preprocess/preprocessing/steps/completed', method: 'get' });
    preprocessedFileOptions.value = (data?.records || []).map((file: PreprocessedFile) => ({
      label: `${file.pipeline_name} (ID: ${file.id}, Source: ${file.original_filename})`,
      value: file.id
    }));
  } catch (error: any) {
    notification.error({ title: '获取预处理文件失败', content: error.message });
  } finally {
    loading.preprocessedFiles = false;
  }
}

async function fetchDenoiseResults() {
  loading.table = true;
  try {
    const { data } = await request<any>({
      url: '/preprocess/wavelet/all',
      method: 'get',
      params: {
        page: pagination.page,
        page_size: pagination.pageSize
      }
    });
    tableState.data = data?.records || [];
    pagination.itemCount = data?.total || 0;
  } catch (error: any) {
    notification.error({ title: '获取去噪结果失败', content: error.message });
  } finally {
    loading.table = false;
  }
}

async function handleDenoise() {
  if (!selectedStepId.value) return;
  await denoiseFormRef.value?.validate();
  loading.denoise = true;
  try {
    // 步骤1: 创建小波去噪任务
    console.log('[前端] 创建小波去噪任务，stepId:', selectedStepId.value);
    const createResponse = await request<any>({
      url: `/preprocess/wavelet/tasks/${selectedStepId.value}`,
      method: 'post',
      data: denoiseFormModel.value
    });

    console.log('[前端] 任务创建响应:', createResponse);

    // 检查响应格式并提取任务ID
    let taskId;
    if (createResponse.error === null && createResponse.data) {
      taskId = createResponse.data.id;
      console.log('[前端] 获取到任务ID:', taskId);
    } else {
      throw new Error('创建任务失败：' + (createResponse.error?.message || '响应格式错误'));
    }

    // 步骤2: 立即启动任务
    console.log('[前端] 启动小波去噪任务，taskId:', taskId);
    const startResponse = await request<any>({
      url: `/preprocess/wavelet/tasks/${taskId}/start`,
      method: 'post'
    });

    console.log('[前端] 任务启动响应:', startResponse);

    if (startResponse.error === null) {
      notification.success({
        title: '小波去噪任务已启动',
        content: '任务正在后台运行，请稍后查看结果列表。'
      });
      startWaveletPolling(taskId);
      fetchDenoiseResults(); // 刷新列表
    } else {
      throw new Error('启动任务失败：' + (startResponse.error?.message || '未知错误'));
    }

  } catch (error: any) {
    console.error('[前端] 小波去噪失败:', error);
    notification.error({ title: '小波去噪失败', content: error.message || '请求失败' });
  } finally {
    loading.denoise = false;
  }
}

onMounted(() => {
  fetchPreprocessedFiles();
  fetchDenoiseResults();
});

onBeforeUnmount(() => {
  stopWaveletPolling();
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
.flex-col {
  display: flex;
  flex-direction: column;
}
.flex-1 {
  flex: 1 1 0%;
}
</style>
