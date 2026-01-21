<template>
  <div class="p-16">
    <n-card title="EEG 数据预处理" :bordered="false">
      <n-grid :x-gap="24" :y-gap="24" :cols="2">
        <n-gi>
          <n-space vertical :size="24">
            <n-spin :show="loading.eegFiles">
              <n-card title="第一步：选择原始文件" :bordered="false" class="card-wrapper">
                <n-form-item label="选择要进行预处理的EEG文件">
                  <n-select
                    v-model:value="selectedEegFileId"
                    placeholder="请选择一个状态为'Completed'的EEG文件"
                    :options="eegFileOptions"
                    filterable
                    clearable
                    @update:value="handleFileSelectionChange"
                  />
                </n-form-item>
              </n-card>
            </n-spin>

            <n-spin :show="loading.apply">
              <n-card title="第二步：设置预处理参数" class="card-wrapper">
                <n-form
                  ref="preprocessFormRef"
                  :model="preprocessFormModel"
                  :rules="preprocessFormRules"
                  :disabled="!selectedEegFileId"
                  label-placement="left"
                  label-width="auto"
                >
                  <n-form-item label="管道名称" path="pipeline_name">
                    <n-input v-model:value="preprocessFormModel.pipeline_name" placeholder="为这次处理起一个名字" />
                  </n-form-item>
                  <n-form-item label="蒙太奇 (Montage)" path="montage">
                    <n-select
                      v-model:value="preprocessFormModel.montage"
                      placeholder="选择电极帽标准"
                      :options="montageOptions"
                    />
                  </n-form-item>
                  <n-form-item label="坏导 (Bad Channels)" path="bad_chs">
                    <n-dynamic-tags v-model:value="preprocessFormModel.bad_chs" />
                  </n-form-item>
                  <n-form-item label="EEG参考" path="eeg_reference">
                    <n-input v-model:value="preprocessFormModel.eeg_reference" placeholder="例如: average, TP9, TP10" />
                  </n-form-item>
                  <n-form-item label="陷波频率 (Hz)" path="notch_freq">
                    <n-input-number
                      v-model:value="preprocessFormModel.notch_freq"
                      :min="0"
                      clearable
                      placeholder="可选, 如 50 或 60"
                      class="w-full"
                    />
                  </n-form-item>
                  <n-form-item label="高通频率 (Hz)" path="highpass_freq">
                    <n-input-number
                      v-model:value="preprocessFormModel.highpass_freq"
                      :min="0"
                      clearable
                      placeholder="可选, 如 0.5 或 1"
                      class="w-full"
                    />
                  </n-form-item>
                  <n-form-item label="低通频率 (Hz)" path="lowpass_freq">
                    <n-input-number
                      v-model:value="preprocessFormModel.lowpass_freq"
                      :min="0"
                      clearable
                      placeholder="可选, 如 40 或 100"
                      class="w-full"
                    />
                  </n-form-item>
                  <n-form-item label="重采样频率 (Hz)" path="resample_sfreq">
                    <n-input-number
                      v-model:value="preprocessFormModel.resample_sfreq"
                      :min="0"
                      clearable
                      placeholder="可选, 如 250 或 500"
                      class="w-full"
                    />
                  </n-form-item>
                  <n-form-item label="保存预处理文件" path="save_file">
                    <n-switch v-model:value="preprocessFormModel.save_file" />
                  </n-form-item>
                </n-form>
                <n-button
                  type="primary"
                  block
                  :disabled="!selectedEegFileId"
                  :loading="loading.apply"
                  @click="handleApplyPreprocessing"
                >
                  应用并执行预处理
                </n-button>
              </n-card>
            </n-spin>
          </n-space>
        </n-gi>

        <n-gi class="flex flex-col">
          <n-card
            title="第三步：查看已保存的处理结果"
            class="card-wrapper flex-1 flex flex-col"
            :content-style="{ display: 'flex', flexDirection: 'column', flexGrow: 1 }"
          >
            <n-space vertical :size="12" class="pb-12px">
              <n-input
                v-model:value="tableState.search"
                placeholder="按管道名称或原始文件名搜索"
                clearable
                @update:value="fetchCompletedSteps"
              />
            </n-space>
            <n-data-table
              class="flex-1"
              flex-height
              :columns="tableColumns"
              :data="tableState.data"
              :pagination="tableState.pagination"
              :loading="loading.table"
              :remote="true"
              @update:page="handlePageChange"
              @update:sorter="handleSorterChange"
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
  useMessage,
  useNotification,
  useDialog,
  NButton,
  NSpace,
  NTooltip,
  type SelectOption,
  type FormInst,
  type FormRules,
  type DataTableColumns,
  type PaginationProps
} from 'naive-ui';
import { request } from '@/service/request';
import { formatDateTime } from '@/utils/common';
import { Icon } from '@iconify/vue';

// --- 接口和类型定义 ---
interface PreprocessingStep {
  id: number;
  eeg_file_id: number;
  original_filename: string;
  pipeline_name: string;
  montage: string;
  create_time: string;
}

// --- Naive UI Hooks ---
const message = useMessage();
const notification = useNotification();
const dialog = useDialog();

// --- 响应式状态 ---
const loading = reactive({
  eegFiles: false,
  apply: false,
  table: false
});

const selectedEegFileId = ref<number | null>(null);
const eegFileOptions = ref<SelectOption[]>([]);

const preprocessFormRef = ref<FormInst | null>(null);
const initialFormState = {
  pipeline_name: '',
  montage: null,
  bad_chs: [],
  eeg_reference: 'average',
  notch_freq: 50,
  highpass_freq: 1,
  lowpass_freq: 40,
  resample_sfreq: null,
  save_file: true
};
const preprocessFormModel = ref({ ...initialFormState });

const preprocessFormRules: FormRules = {
  pipeline_name: { required: true, message: '请输入管道名称', trigger: 'blur' },
  montage: { required: true, message: '请选择蒙太奇标准', trigger: 'change' },
  eeg_reference: { required: true, message: '请输入参考电极', trigger: 'blur' },
  resample_sfreq: { type: 'number', message: '重采样频率必须是数字', trigger: ['input', 'blur'] }
};

const montageOptions: SelectOption[] = [
  'standard_1005', 'standard_1020', 'standard_a', 'standard_b', 'standard_c', 'standard_d',
  'standard_e', 'standard_f', 'standard_g', 'standard_h', 'standard_i', 'biosemi16',
  'biosemi32', 'biosemi64', 'biosemi128', 'biosemi160', 'biosemi256', 'easycap16',
  'easycap32', 'easycap64', 'easycap128', 'EGI_256', 'GSN-HydroCel-32', 'GSN-HydroCel-64',
  'GSN-HydroCel-128', 'GSN-HydroCel-256', 'artinis-octamon', 'artinis-britemon'
].map(name => ({ label: name, value: name }));

const tableState = reactive({
  data: [] as PreprocessingStep[],
  search: '',
  pagination: {
    page: 1,
    pageSize: 10,
    itemCount: 0,
    showSizePicker: true,
    pageSizes: [10, 20, 50]
  } as PaginationProps,
  sorter: {
    columnKey: 'create_time',
    order: 'descend'
  }
});

const tableColumns: DataTableColumns<PreprocessingStep> = [
  { title: 'ID', key: 'id', sorter: true, width: 80 },
  { title: '管道名称', key: 'pipeline_name', sorter: true },
  { title: '原始文件', key: 'original_filename', sorter: true },
  { title: 'Montage', key: 'montage' },
  {
    title: '创建时间',
    key: 'create_time',
    sorter: true,
    render: row => formatDateTime(row.create_time)
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    align: 'center',
    render(row) {
      const downloadButton = h(
        NButton,
        {
          size: 'small',
          type: 'primary',
          circle: true,
          tertiary: true,
          onClick: () => message.info(`下载文件: ${row.id}`)
        },
        { default: () => h(Icon, { icon: 'mdi:download' }) }
      );

      const deleteButton = h(
        NButton,
        {
          size: 'small',
          type: 'error',
          circle: true,
          tertiary: true,
          onClick: () => handleDeleteStep(row.id)
        },
        { default: () => h(Icon, { icon: 'mdi:delete' }) }
      );

      const downloadTooltip = h(NTooltip, null, {
        trigger: () => downloadButton,
        default: () => '下载'
      });

      const deleteTooltip = h(NTooltip, null, {
        trigger: () => deleteButton,
        default: () => '删除'
      });

      return h(NSpace, { justify: 'center', style: 'gap: 8px;' }, { default: () => [downloadTooltip, deleteTooltip] });
    }
  }
];

// --- API 调用函数 ---

/** 获取所有可用的EEG文件列表 */
async function fetchEegFiles() {
  loading.eegFiles = true;
  try {
    const res = await request<any>({
      url: '/preprocess/eeg/',
      method: 'get',
      params: { page: 1, page_size: 100 }
    });
    eegFileOptions.value = (res.data ?? [])
      .filter((file: any) => file.status === 'Completed')
      .map((file: any) => ({
        label: `${file.original_filename} (ID: ${file.id}, Subject: ${file.subject_id || 'N/A'})`,
        value: file.id
      }));
  } catch (error: any) {
    message.error(`获取EEG文件列表失败: ${error.message}`);
  } finally {
    loading.eegFiles = false;
  }
}

/** 获取已完成的预处理文件列表 */
async function fetchCompletedSteps() {
  loading.table = true;
  try {
    const params: any = {
      page: tableState.pagination.page,
      page_size: tableState.pagination.pageSize
    };

    if (!selectedEegFileId.value) {
      params.search = tableState.search || undefined;
    }

    if (tableState.sorter && tableState.sorter.order) {
      params.sort_by = tableState.sorter.columnKey;
      params.sort_order = tableState.sorter.order === 'ascend' ? 'asc' : 'desc';
    }

    const url = selectedEegFileId.value
      ? `/preprocess/preprocessing/${selectedEegFileId.value}/steps`
      : '/preprocess/preprocessing/steps/completed';

    const res = await request<any>({ url, method: 'get', params });

    tableState.data = res.data.records || [];
    tableState.pagination.itemCount = res.data.total || 0;
  } catch (error: any) {
    message.error(`获取预处理列表失败: ${error.message}`);
    tableState.data = [];
    tableState.pagination.itemCount = 0;
  } finally {
    loading.table = false;
  }
}

/** 提交预处理任务 */
async function handleApplyPreprocessing() {
  if (!selectedEegFileId.value) return;

  try {
    await preprocessFormRef.value?.validate();
    loading.apply = true;

    const { data: newData } = await request<any>({
      url: `/preprocess/preprocessing/${selectedEegFileId.value}`,
      method: 'post',
      data: preprocessFormModel.value,
      timeout: 5 * 60 * 1000
    });

    notification.success({
      title: '预处理应用成功',
      content: `管道 '${newData.pipeline_name}' 已成功创建。`,
      meta: `新记录ID: ${newData.id}`,
      duration: 5000
    });

    preprocessFormModel.value = { ...initialFormState };
    await fetchCompletedSteps();
  } catch (validationError) {
    // 表单验证失败
  } finally {
    loading.apply = false;
  }
}

/** 删除指定的预处理步骤 */
async function handleDeleteStep(stepId: number) {
  dialog.warning({
    title: '确认删除',
    content: `您确定要删除ID为 ${stepId} 的预处理记录及其文件吗？此操作不可逆。`,
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request<any>({
          url: `/preprocess/steps/${stepId}`,
          method: 'delete'
        });
        notification.success({
          title: '删除成功',
          content: `记录ID ${stepId} 已被删除。`,
          duration: 3000
        });
        await fetchCompletedSteps(); // Refresh the table
      } catch (error: any) {
        notification.error({
          title: '删除失败',
          content: error.message,
          duration: 5000
        });
      }
    }
  });
}

// --- 事件处理 ---
function handlePageChange(currentPage: number) {
  tableState.pagination.page = currentPage;
  fetchCompletedSteps();
}

function handleSorterChange(sorter: any) {
  tableState.sorter = sorter;
  fetchCompletedSteps();
}

function handleFileSelectionChange(value: number | null) {
  selectedEegFileId.value = value;
  tableState.pagination.page = 1;
  tableState.search = '';
  fetchCompletedSteps();
}

// --- 生命周期钩子 ---
onMounted(() => {
  fetchEegFiles();
  fetchCompletedSteps();
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
.pb-12px {
  padding-bottom: 12px;
}
</style>

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
.pb-12px {
  padding-bottom: 12px;
}
</style>
