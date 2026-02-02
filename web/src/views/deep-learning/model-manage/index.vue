<template>
  <div class="p-16px">
    <n-card title="模型管理" class="mb-16px">
      <template #header-extra>
        <n-space>
          <n-button type="primary" @click="handleRegisterModel">
            <template #icon>
              <icon-mdi-plus />
            </template>
            注册模型
          </n-button>
        </n-space>
      </template>

      <!-- 统计卡片 -->
      <n-grid cols="1 s:2 m:4" x-gap="16" y-gap="16" class="mb-24px">
        <n-gi>
          <n-statistic label="已注册模型" :value="modelStats.total">
            <template #prefix>
              <icon-mdi-cube-outline class="text-18px text-primary" />
            </template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="生产模型" :value="modelStats.active" tabular-nums>
            <template #prefix>
              <icon-mdi-check-circle class="text-18px text-success" />
            </template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="草稿模型" :value="modelStats.draft">
            <template #prefix>
              <icon-mdi-pencil class="text-18px text-warning" />
            </template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="平均准确率" :value="modelStats.avgAccuracy" suffix="%">
            <template #prefix>
              <icon-mdi-chart-line class="text-18px text-info" />
            </template>
          </n-statistic>
        </n-gi>
      </n-grid>

      <!-- 搜索和过滤 -->
      <div class="toolbar mb-12px">
        <n-input
          v-model:value="searchKeyword"
          placeholder="搜索模型名称、版本"
          clearable
          @update:value="handleSearch"
        >
          <template #prefix>
            <icon-mdi-magnify />
          </template>
        </n-input>
        <n-select
          v-model:value="statusFilter"
          placeholder="状态筛选"
          :options="statusOptions"
          clearable
          @update:value="handleSearch"
        />
        <n-select
          v-model:value="architectureFilter"
          placeholder="模型架构"
          :options="architectureOptions"
          clearable
          @update:value="handleSearch"
        />
      </div>

      <!-- 模型列表 -->
      <n-data-table
        :columns="columns"
        :data="filteredModels"
        :pagination="pagination"
        :loading="loading"
        :bordered="false"
      />
    </n-card>

    <!-- 模型对比Modal -->
    <n-modal v-model:show="compareModalVisible" preset="card" title="模型对比" style="width: 80%; max-width: 1200px">
      <n-empty v-if="selectedModels.length < 2" description="请至少选择2个模型进行对比" />
      <div v-else>
        <n-grid cols="1 m:2" x-gap="16" y-gap="16">
          <n-gi v-for="model in selectedModels" :key="model.id">
            <n-card :title="model.name" size="small">
              <n-descriptions :column="1" label-placement="left" size="small">
                <n-descriptions-item label="版本">{{ model.version }}</n-descriptions-item>
                <n-descriptions-item label="架构">{{ model.architecture }}</n-descriptions-item>
                <n-descriptions-item label="准确率">{{ model.accuracy }}%</n-descriptions-item>
                <n-descriptions-item label="AUC">{{ model.auc }}</n-descriptions-item>
                <n-descriptions-item label="F1分数">{{ model.f1Score }}</n-descriptions-item>
                <n-descriptions-item label="训练集">{{ model.datasetName }}</n-descriptions-item>
              </n-descriptions>
            </n-card>
          </n-gi>
        </n-grid>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, ref, computed } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { NTag, NSpace, NButton, NSwitch } from 'naive-ui';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// Mock数据类型
interface ModelRow {
  id: string;
  name: string;
  version: string;
  architecture: string;
  accuracy: number;
  auc: number;
  f1Score: number;
  datasetName: string;
  status: 'active' | 'draft' | 'archived';
  isProduction: boolean;
  createdAt: string;
}

// Mock数据
const mockModels = ref<ModelRow[]>([
  {
    id: 'M-001',
    name: 'PD-CNN-Baseline',
    version: 'v1.0.0',
    architecture: '1D-CNN',
    accuracy: 92.4,
    auc: 0.96,
    f1Score: 0.91,
    datasetName: 'PD-EEG Base v0.1',
    status: 'active',
    isProduction: true,
    createdAt: '2026-02-01 10:00'
  },
  {
    id: 'M-002',
    name: 'DBS-Transformer',
    version: 'v0.2.5',
    architecture: 'Transformer',
    accuracy: 88.5,
    auc: 0.93,
    f1Score: 0.87,
    datasetName: 'DBS Stimulation v0.1',
    status: 'active',
    isProduction: false,
    createdAt: '2026-02-01 14:30'
  },
  {
    id: 'M-003',
    name: 'Multi-Task-LSTM',
    version: 'v0.1.0',
    architecture: 'LSTM',
    accuracy: 85.2,
    auc: 0.89,
    f1Score: 0.84,
    datasetName: 'Cross-Subject Mix v0.2',
    status: 'draft',
    isProduction: false,
    createdAt: '2026-01-31 16:20'
  },
  {
    id: 'M-004',
    name: 'ResNet-PD',
    version: 'v1.1.2',
    architecture: 'ResNet1D',
    accuracy: 94.1,
    auc: 0.97,
    f1Score: 0.93,
    datasetName: 'PD-EEG Base v0.1',
    status: 'active',
    isProduction: true,
    createdAt: '2026-01-30 09:15'
  }
]);

const modelStats = computed(() => ({
  total: mockModels.value.length,
  active: mockModels.value.filter(m => m.status === 'active').length,
  draft: mockModels.value.filter(m => m.status === 'draft').length,
  avgAccuracy: (mockModels.value.reduce((sum, m) => sum + m.accuracy, 0) / mockModels.value.length).toFixed(1)
}));

const searchKeyword = ref('');
const statusFilter = ref<string | null>(null);
const architectureFilter = ref<string | null>(null);
const loading = ref(false);
const compareModalVisible = ref(false);
const selectedModels = ref<ModelRow[]>([]);

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Draft', value: 'draft' },
  { label: 'Archived', value: 'archived' }
];

const architectureOptions = [
  { label: '1D-CNN', value: '1D-CNN' },
  { label: 'Transformer', value: 'Transformer' },
  { label: 'LSTM', value: 'LSTM' },
  { label: 'ResNet1D', value: 'ResNet1D' }
];

const filteredModels = computed(() => {
  let result = mockModels.value;

  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase();
    result = result.filter(m => m.name.toLowerCase().includes(kw) || m.version.toLowerCase().includes(kw));
  }

  if (statusFilter.value) {
    result = result.filter(m => m.status === statusFilter.value);
  }

  if (architectureFilter.value) {
    result = result.filter(m => m.architecture === architectureFilter.value);
  }

  return result;
});

const columns: DataTableColumns<ModelRow> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '模型名称',
    key: 'name',
    minWidth: 160
  },
  {
    title: '版本',
    key: 'version',
    width: 100
  },
  {
    title: '架构',
    key: 'architecture',
    width: 120,
    render: row =>
      h(NTag, { size: 'small', type: 'info' }, { default: () => row.architecture })
  },
  {
    title: '准确率',
    key: 'accuracy',
    width: 100,
    render: row => `${row.accuracy}%`
  },
  {
    title: 'AUC',
    key: 'auc',
    width: 90
  },
  {
    title: 'F1分数',
    key: 'f1Score',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row =>
      h(
        NTag,
        { size: 'small', type: row.status === 'active' ? 'success' : row.status === 'draft' ? 'warning' : 'default' },
        { default: () => row.status }
      )
  },
  {
    title: '生产环境',
    key: 'isProduction',
    width: 120,
    render: row =>
      h(NSwitch, {
        value: row.isProduction,
        size: 'small',
        onUpdateValue: (value: boolean) => handleToggleProduction(row.id, value)
      })
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    fixed: 'right',
    render: row =>
      h(
        NSpace,
        { size: 6 },
        {
          default: () => [
            h(NButton, { size: 'small', tertiary: true, onClick: () => handleViewDetail(row) }, { default: () => '详情' }),
            h(NButton, { size: 'small', tertiary: true, type: 'info', onClick: () => handleCompare(row) }, { default: () => '对比' }),
            h(NButton, { size: 'small', tertiary: true, type: 'primary', onClick: () => handleDownload(row) }, { default: () => '下载' })
          ]
        }
      )
  }
];

const pagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    pagination.value.page = page;
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize;
    pagination.value.page = 1;
  }
});

function handleSearch() {
  pagination.value.page = 1;
}

function handleRegisterModel() {
  window.$message?.info('注册模型功能开发中');
}

function handleToggleProduction(id: string, value: boolean) {
  const model = mockModels.value.find(m => m.id === id);
  if (model) {
    model.isProduction = value;
    window.$message?.success(`模型 ${model.name} 已${value ? '设置为生产环境' : '从生产环境移除'}`);
  }
}

function handleViewDetail(row: ModelRow) {
  window.$message?.info(`查看模型详情: ${row.name}`);
}

function handleCompare(row: ModelRow) {
  if (selectedModels.value.find(m => m.id === row.id)) {
    selectedModels.value = selectedModels.value.filter(m => m.id !== row.id);
  } else {
    selectedModels.value.push(row);
  }

  if (selectedModels.value.length >= 2) {
    compareModalVisible.value = true;
  }
}

function handleDownload(row: ModelRow) {
  window.$message?.success(`开始下载模型: ${row.name} ${row.version}`);
}

onMounted(() => {
  // 模拟加载
  loading.value = true;
  setTimeout(() => {
    loading.value = false;
  }, 300);
});
</script>

<style scoped>
.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px 180px;
  gap: 12px;
}

@media (max-width: 900px) {
  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
