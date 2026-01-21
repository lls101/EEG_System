<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    title="特征统计信息"
    size="huge"
    :bordered="false"
    :segmented="true"
    @close="handleClose"
  >
    <div v-if="statistics">
      <n-space vertical :size="16">
        <n-alert type="info" :bordered="false">
          <template #header>
            <Icon icon="mdi:chart-line" />
            统计说明
          </template>
          以下是前5个特征的详细统计信息，包括均值、标准差、最小值和最大值。
        </n-alert>

        <n-data-table
          :columns="columns"
          :data="tableData"
          :pagination="false"
          :bordered="true"
          :single-line="false"
          size="small"
        />

        <n-space justify="space-between" align="center">
          <n-text depth="3">
            * 仅显示前5个特征的统计信息，完整数据请下载CSV文件查看
          </n-text>
          <n-space>
            <n-button @click="exportStatistics">
              <template #icon>
                <Icon icon="mdi:file-export" />
              </template>
              导出统计
            </n-button>
            <n-button type="primary" @click="handleClose">
              关闭
            </n-button>
          </n-space>
        </n-space>
      </n-space>
    </div>

    <n-empty v-else description="暂无统计数据" />
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import {
  NModal, NSpace, NAlert, NDataTable, NText, NButton, NEmpty, NIcon,
  useNotification
} from 'naive-ui';
import { Icon } from '@iconify/vue';
import type { DataTableColumns } from 'naive-ui';

interface Props {
  show: boolean;
  statistics?: Record<string, any>;
}

interface Emits {
  (e: 'close'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();
const notification = useNotification();

const showModal = ref(false);

// 表格列定义
const columns: DataTableColumns = [
  {
    title: '特征名称',
    key: 'featureName',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '均值',
    key: 'mean',
    width: 120,
    render: (row: any) => formatNumber(row.mean)
  },
  {
    title: '标准差',
    key: 'std',
    width: 120,
    render: (row: any) => formatNumber(row.std)
  },
  {
    title: '最小值',
    key: 'min',
    width: 120,
    render: (row: any) => formatNumber(row.min)
  },
  {
    title: '最大值',
    key: 'max',
    width: 120,
    render: (row: any) => formatNumber(row.max)
  },
  {
    title: '变异系数',
    key: 'cv',
    width: 120,
    render: (row: any) => {
      const cv = Math.abs(row.mean) > 1e-10 ? (row.std / Math.abs(row.mean)) : 0;
      return formatNumber(cv);
    }
  }
];

// 转换统计数据为表格数据
const tableData = computed(() => {
  if (!props.statistics) return [];

  return Object.entries(props.statistics).map(([featureName, stats]: [string, any]) => ({
    featureName,
    mean: stats.mean,
    std: stats.std,
    min: stats.min,
    max: stats.max
  }));
});

// 数字格式化
const formatNumber = (value: number): string => {
  if (Math.abs(value) < 1e-6) {
    return value.toExponential(2);
  } else if (Math.abs(value) < 1e-3) {
    return value.toExponential(3);
  } else if (Math.abs(value) < 1) {
    return value.toFixed(6);
  } else {
    return value.toFixed(4);
  }
};

const handleClose = () => {
  emit('close');
};

const exportStatistics = () => {
  if (!props.statistics) return;

  try {
    // 准备CSV数据
    const headers = ['特征名称', '均值', '标准差', '最小值', '最大值', '变异系数'];
    const rows = tableData.value.map(row => [
      row.featureName,
      row.mean,
      row.std,
      row.min,
      row.max,
      Math.abs(row.mean) > 1e-10 ? (row.std / Math.abs(row.mean)) : 0
    ]);

    // 生成CSV内容
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // 创建下载
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'feature_statistics.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    notification.success({
      title: '导出成功',
      content: '统计信息已导出为CSV文件'
    });
  } catch (error) {
    notification.error({
      title: '导出失败',
      content: '无法导出统计信息'
    });
  }
};

// 监听props变化
watch(() => props.show, (newVal) => {
  showModal.value = newVal;
});

watch(showModal, (newVal) => {
  if (!newVal) {
    handleClose();
  }
});
</script>

<style scoped>
:deep(.n-data-table th) {
  background-color: #fafafa;
}

:deep(.n-data-table td) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}
</style>
