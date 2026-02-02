<template>
  <div class="p-16px space-y-16px">
    <section class="hero">
      <div class="hero__content">
        <div class="hero__tag">Deep Learning Pipeline</div>
        <h1 class="hero__title">{{ t('page.deepLearning.dataset.title') }}</h1>
        <p class="hero__desc">
          管理 EEG 数据集版本、标签、划分与统计，为训练与评估提供统一入口。
        </p>
        <div class="hero__actions">
          <n-button type="primary">导入数据集</n-button>
          <n-button>创建划分</n-button>
          <n-button tertiary>新建标签</n-button>
        </div>
      </div>
      <div class="hero__panel">
        <div class="hero__panel-title">当前版本</div>
        <div class="hero__panel-value">{{ stats?.currentVersion ?? '-' }}</div>
        <div class="hero__panel-meta">最近更新：{{ stats?.updatedAt ?? '-' }}</div>
        <div class="hero__panel-meta">样本数：{{ stats?.sampleCount ?? '-' }}</div>
        <div class="hero__panel-meta">通道数：{{ stats?.channelInfo ?? '-' }}</div>
      </div>
    </section>

    <n-grid cols="1 s:2 l:4" x-gap="16" y-gap="16">
      <n-gi>
        <n-card size="small" class="stat-card">
          <div class="stat-card__label">数据集数</div>
          <div class="stat-card__value">{{ stats?.datasetCount ?? '-' }}</div>
          <div class="stat-card__hint">含 1 个公开基线集</div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small" class="stat-card">
          <div class="stat-card__label">样本总量</div>
          <div class="stat-card__value">{{ stats?.sampleCount ?? '-' }}</div>
          <div class="stat-card__hint">含 Epoch 与原始段</div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small" class="stat-card">
          <div class="stat-card__label">标签数</div>
          <div class="stat-card__value">{{ stats?.labelCount ?? '-' }}</div>
          <div class="stat-card__hint">PD/Normal/DBS-ON/DBS-OFF</div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small" class="stat-card">
          <div class="stat-card__label">划分策略</div>
          <div class="stat-card__value">{{ stats?.split ?? '-' }}</div>
          <div class="stat-card__hint">Train / Val / Test</div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid cols="1 l:3" x-gap="16" y-gap="16">
      <n-gi span="2">
        <n-card title="数据集列表" size="small" class="card">
          <div class="toolbar">
            <n-input
              v-model:value="filters.keyword"
              placeholder="搜索名称 / 标签 / 版本"
              clearable
              class="toolbar__search"
              @update:value="handleSearch"
            />
            <n-select
              v-model:value="filters.status"
              placeholder="状态"
              :options="statusOptions"
              class="toolbar__select"
              clearable
              @update:value="handleFilterChange"
            />
            <n-select
              v-model:value="filters.label"
              placeholder="标签"
              :options="labelOptions"
              class="toolbar__select"
              clearable
              @update:value="handleFilterChange"
            />
          </div>
          <n-data-table
            :columns="columns"
            :data="tableData"
            :pagination="pagination"
            :bordered="false"
            :loading="loading"
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="数据集详情" size="small" class="card">
          <n-empty description="请选择左侧数据集查看详情" />
        </n-card>
        <n-card title="划分预览" size="small" class="card mt-16">
          <n-tabs type="segment">
            <n-tab-pane name="train" tab="Train">
              <n-empty description="暂无 Train 样本预览" />
            </n-tab-pane>
            <n-tab-pane name="val" tab="Val">
              <n-empty description="暂无 Val 样本预览" />
            </n-tab-pane>
            <n-tab-pane name="test" tab="Test">
              <n-empty description="暂无 Test 样本预览" />
            </n-tab-pane>
          </n-tabs>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, ref } from 'vue';
import type { DataTableColumns, PaginationProps } from 'naive-ui';
import { NTag, NSpace, NButton } from 'naive-ui';
import { useI18n } from 'vue-i18n';
import type { DatasetRow, DatasetStats } from '@/service/api';
import { fetchDatasetList, fetchDatasetStats } from '@/service/api';

const { t } = useI18n();

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Draft', value: 'draft' },
  { label: 'Archived', value: 'archived' }
];

const labelOptions = [
  { label: 'PD', value: 'PD' },
  { label: 'Normal', value: 'Normal' },
  { label: 'DBS-ON', value: 'DBS-ON' },
  { label: 'DBS-OFF', value: 'DBS-OFF' }
];

const tableData = ref<DatasetRow[]>([]);
const stats = ref<DatasetStats | null>(null);
const loading = ref(false);

const filters = ref({
  keyword: '',
  status: null as DatasetRow['status'] | null,
  label: null as string | null
});

const pagination = ref<PaginationProps>({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
});

const columns: DataTableColumns<DatasetRow> = [
  { title: 'ID', key: 'id', width: 90 },
  { title: '名称', key: 'name', minWidth: 180 },
  { title: '版本', key: 'version', width: 90 },
  {
    title: '标签',
    key: 'labels',
    minWidth: 180,
    render: row =>
      h(
        NSpace,
        { size: 6 },
        {
          default: () =>
            row.labels.map(label =>
              h(
                NTag,
                { size: 'small', type: label === 'PD' ? 'warning' : 'info' },
                { default: () => label }
              )
            )
        }
      )
  },
  { title: '样本数', key: 'samples', width: 120 },
  { title: '创建时间', key: 'createdAt', minWidth: 160 },
  {
    title: '状态',
    key: 'status',
    width: 110,
    render: row =>
      h(
        NTag,
        { size: 'small', type: row.status === 'active' ? 'success' : row.status === 'draft' ? 'warning' : 'default' },
        { default: () => row.status }
      )
  },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    render: () =>
      h(
        NSpace,
        {},
        {
          default: () => [
            h(NButton, { size: 'small', tertiary: true }, { default: () => '详情' }),
            h(NButton, { size: 'small', tertiary: true }, { default: () => '设置' })
          ]
        }
      )
  }
];

const loadStats = async () => {
  stats.value = await fetchDatasetStats();
};

const loadTable = async () => {
  loading.value = true;
  try {
    const result = await fetchDatasetList({
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      keyword: filters.value.keyword,
      status: filters.value.status,
      label: filters.value.label
    });
    tableData.value = result.records;
    pagination.value.itemCount = result.total;
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.value.page = 1;
  loadTable();
};

const handleFilterChange = () => {
  pagination.value.page = 1;
  loadTable();
};

const handlePageChange = (page: number) => {
  pagination.value.page = page;
  loadTable();
};

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize;
  pagination.value.page = 1;
  loadTable();
};

onMounted(() => {
  loadStats();
  loadTable();
});
</script>

<style scoped>
.hero {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, #0b1f2a, #173b4d);
  color: #f5f7fb;
}

.hero__tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 12px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.hero__title {
  margin: 12px 0 8px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.4px;
}

.hero__desc {
  margin: 0 0 16px;
  color: rgba(245, 247, 251, 0.75);
  max-width: 520px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero__panel {
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
}

.hero__panel-title {
  font-size: 12px;
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

.hero__panel-value {
  font-size: 22px;
  font-weight: 600;
  margin: 8px 0 6px;
}

.hero__panel-meta {
  font-size: 13px;
  opacity: 0.7;
  line-height: 1.6;
}

.stat-card__label {
  font-size: 13px;
  color: rgba(19, 25, 35, 0.6);
}

.stat-card__value {
  font-size: 22px;
  font-weight: 600;
  margin-top: 6px;
}

.stat-card__hint {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(19, 25, 35, 0.45);
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 160px 160px;
  gap: 12px;
  margin-bottom: 12px;
}

.toolbar__search {
  min-width: 220px;
}

.toolbar__select {
  min-width: 140px;
}

.card :deep(.n-card__content) {
  padding-top: 12px;
}

.mt-16 {
  margin-top: 16px;
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
