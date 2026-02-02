<template>
  <div class="p-16px">
    <n-card title="训练任务列表" class="h-full shadow-sm">
      <template #header-extra>
        <n-space>
          <n-button strong secondary circle type="info" @click="loadTasks">
            <template #icon>
              <div class="i-mdi:refresh" :class="{ 'animate-spin': loading }" />
            </template>
          </n-button>
          <n-button type="primary" @click="$router.push({ name: 'deep-learning_train-config' })">
            <template #icon>
              <div class="i-mdi:plus" />
            </template>
            新建任务
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, onUnmounted, ref } from 'vue';
import { NButton, NProgress, NSpace, NTag, useMessage } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { useRouter } from 'vue-router';
import { fetchTrainingTasks, stopTrainingTask } from '@/service/api';
import type { TrainingTaskRow } from '@/service/api';

const message = useMessage();
const router = useRouter();
const loading = ref(false);
const tasks = ref<TrainingTaskRow[]>([]);
let timer: number | null = null;

const pagination = { pageSize: 10 };

const statusMap: Record<string, { type: 'default' | 'info' | 'success' | 'warning' | 'error'; label: string }> = {
  pending: { type: 'warning', label: '等待中' },
  running: { type: 'info', label: '训练中' },
  success: { type: 'success', label: '已完成' },
  failed: { type: 'error', label: '失败' },
  stopped: { type: 'default', label: '已停止' }
};

const columns: DataTableColumns<TrainingTaskRow> = [
  { title: 'ID', key: 'id', width: 100 },
  { title: '任务名称', key: 'name', minWidth: 150, ellipsis: { tooltip: true } },
  { title: '数据集', key: 'datasetName', minWidth: 150, ellipsis: { tooltip: true } },
  { 
    title: '模型', 
    key: 'modelType', 
    width: 120,
    render: row => h(NTag, { size: 'small', type: 'info', bordered: false }, { default: () => row.modelType })
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row => {
      const s = statusMap[row.status] || { type: 'default', label: row.status };
      return h(NTag, { type: s.type, size: 'small' }, { default: () => s.label });
    }
  },
  {
    title: '进度',
    key: 'progress',
    width: 180,
    render: row => {
      if (row.status === 'pending') return h('span', { class: 'text-gray-400 text-12px' }, '等待调度...');
      return h(
        NProgress,
        {
          type: 'line',
          percentage: row.progress,
          processing: row.status === 'running',
          status: row.status === 'failed' ? 'error' : row.status === 'success' ? 'success' : 'default',
          indicatorPlacement: 'inside'
        }
      );
    }
  },
  {
    title: 'Metrics (Acc / Loss)',
    key: 'metrics',
    width: 160,
    render: row => {
      if (row.status === 'pending') return '-';
      return h('div', { class: 'text-12px' }, [
        h('div', `Acc: ${(row.accuracy ? (row.accuracy * 100).toFixed(1) + '%' : '-')}`),
        h('div', { class: 'text-gray-400' }, `Loss: ${row.loss ?? '-'}`)
      ]);
    }
  },
  { title: '开始时间', key: 'startTime', width: 160 },
  { title: '耗时', key: 'duration', width: 100 },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render: row => {
      const actions = [];
      
      // 监控/详情按钮
      actions.push(
        h(
          NButton,
          {
            size: 'small',
            tertiary: true,
            type: 'primary',
            onClick: () => handleViewMonitor(row)
          },
          { default: () => (row.status === 'running' ? '监控' : '详情') }
        )
      );

      // 停止按钮（仅运行时）
      if (row.status === 'running' || row.status === 'pending') {
        actions.push(
          h(
            NButton,
            {
              size: 'small',
              tertiary: true,
              type: 'error',
              class: 'ml-2',
              onClick: () => handleStop(row)
            },
            { default: () => '停止' }
          )
        );
      }

      return h('div', actions);
    }
  }
];

const loadTasks = async () => {
  try {
    tasks.value = await fetchTrainingTasks();
  } finally {
    loading.value = false;
  }
};

const handleViewMonitor = (row: TrainingTaskRow) => {
  // message.info(`跳转到任务 ${row.id} 的监控页面`);
  // router.push...
};

const handleStop = async (row: TrainingTaskRow) => {
  try {
    await stopTrainingTask(row.id);
    message.warning('已发送停止指令');
    loadTasks();
  } catch (e) {
    message.error('操作失败');
  }
};

onMounted(() => {
  loadTasks();
  // 简单轮询模拟实时更新
  timer = window.setInterval(() => {
    loadTasks(); // 实际项目中应该静默刷新，不显示 loading 状态
  }, 5000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>