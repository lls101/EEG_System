<template>
  <div class="flex-col-stretch gap-16px p-16px">
    <!-- Header with Stats -->
    <n-grid :x-gap="16" :y-gap="16" :item-responsive="true">
      <n-grid-item span="24 s:12 m:6">
        <n-card :bordered="false" class="rounded-12px shadow-sm">
          <n-statistic label="正在运行任务" :value="runningTasksCount">
            <template #prefix>
              <icon-line-md:loading-loop class="text-primary text-24px" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item span="24 s:12 m:6">
        <n-card :bordered="false" class="rounded-12px shadow-sm">
          <n-statistic label="当前 Epoch" :value="monitorData?.currentEpoch || 0">
            <template #suffix>
              <span class="text-14px text-gray-400">/ {{ monitorData?.totalEpochs || 0 }}</span>
            </template>
            <template #prefix>
              <icon-carbon:cycle class="text-info text-24px" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item span="24 s:12 m:6">
        <n-card :bordered="false" class="rounded-12px shadow-sm">
          <n-statistic label="当前准确率" :value="latestAccuracy" :precision="4">
            <template #prefix>
              <icon-carbon:bullseye class="text-success text-24px" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item span="24 s:12 m:6">
        <n-card :bordered="false" class="rounded-12px shadow-sm">
          <n-statistic label="当前 Loss" :value="latestLoss" :precision="4">
            <template #prefix>
              <icon-carbon:chart-line-smooth class="text-error text-24px" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-card :bordered="false" class="rounded-12px shadow-sm" title="训练实时监控">
      <template #header-extra>
        <div class="flex-center gap-12px">
          <n-select
            v-model:value="selectedTaskId"
            :options="taskOptions"
            placeholder="选择监控任务"
            class="w-200px"
            @update:value="handleTaskChange"
          />
          <n-button type="primary" ghost @click="initData">
            <template #icon>
              <icon-carbon:refresh />
            </template>
            刷新
          </n-button>
        </div>
      </template>

      <n-grid :x-gap="16" :y-gap="16" :item-responsive="true">
        <n-grid-item span="24 m:12">
          <n-card title="Loss 曲线" :bordered="false" size="small">
            <div ref="lossChartRef" class="h-360px w-full"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item span="24 m:12">
          <n-card title="Accuracy 曲线" :bordered="false" size="small">
            <div ref="accChartRef" class="h-360px w-full"></div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-divider />

      <div class="flex-col gap-12px">
        <div class="flex-between">
          <span class="font-bold">训练进度: {{ monitorData?.taskName }}</span>
          <n-tag :type="statusTagType">{{ monitorData?.status }}</n-tag>
        </div>
        <n-progress
          type="line"
          :percentage="progressPercentage"
          :indicator-placement="'inside'"
          processing
          :color="progressColor"
        />
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import { useElementSize } from '@vueuse/core';
import { fetchTrainingMonitorData, fetchTrainingTasks } from '@/service/api/deep-learning';
import type { TrainingMonitorData, TrainingTaskRow } from '@/service/api/deep-learning';

const runningTasksCount = ref(1);
const selectedTaskId = ref<string>('');
const taskOptions = ref<{ label: string; value: string }[]>([]);
const monitorData = ref<TrainingMonitorData | null>(null);

const lossChartRef = ref<HTMLElement | null>(null);
const accChartRef = ref<HTMLElement | null>(null);
let lossChart: echarts.ECharts | null = null;
let accChart: echarts.ECharts | null = null;

const { width: lossWidth } = useElementSize(lossChartRef);
const { width: accWidth } = useElementSize(accChartRef);

watch([lossWidth, accWidth], () => {
  lossChart?.resize();
  accChart?.resize();
});

const latestAccuracy = computed(() => {
  if (!monitorData.value?.metrics.length) return 0;
  return monitorData.value.metrics[monitorData.value.metrics.length - 1].accuracy;
});

const latestLoss = computed(() => {
  if (!monitorData.value?.metrics.length) return 0;
  return monitorData.value.metrics[monitorData.value.metrics.length - 1].loss;
});

const progressPercentage = computed(() => {
  if (!monitorData.value) return 0;
  return Math.round((monitorData.value.currentEpoch / monitorData.value.totalEpochs) * 100);
});

const statusTagType = computed(() => {
  switch (monitorData.value?.status) {
    case 'running': return 'info';
    case 'success': return 'success';
    case 'failed': return 'error';
    default: return 'default';
  }
});

const progressColor = computed(() => {
  if (monitorData.value?.status === 'failed') return '#f87171';
  if (monitorData.value?.status === 'success') return '#4ade80';
  return '#3b82f6';
});

async function initTasks() {
  const tasks = await fetchTrainingTasks();
  taskOptions.value = tasks.map((t: TrainingTaskRow) => ({
    label: t.name,
    value: t.id
  }));
  
  const running = tasks.find(t => t.status === 'running');
  if (running) {
    selectedTaskId.value = running.id;
    runningTasksCount.value = tasks.filter(t => t.status === 'running').length;
  } else if (tasks.length > 0) {
    selectedTaskId.value = tasks[0].id;
  }
}

async function initData() {
  if (!selectedTaskId.value) return;
  
  const data = await fetchTrainingMonitorData(selectedTaskId.value);
  monitorData.value = data;
  
  renderCharts();
}

function handleTaskChange() {
  initData();
}

function renderCharts() {
  if (!monitorData.value) return;
  
  const epochs = monitorData.value.metrics.map(m => m.epoch);
  const trainLoss = monitorData.value.metrics.map(m => m.loss);
  const valLoss = monitorData.value.metrics.map(m => m.val_loss);
  const trainAcc = monitorData.value.metrics.map(m => m.accuracy);
  const valAcc = monitorData.value.metrics.map(m => m.val_accuracy);

  if (!lossChart && lossChartRef.value) {
    lossChart = echarts.init(lossChartRef.value);
  }
  
  lossChart?.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['Train Loss', 'Val Loss'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: epochs, name: 'Epoch' },
    yAxis: { type: 'value', name: 'Loss' },
    series: [
      {
        name: 'Train Loss',
        type: 'line',
        data: trainLoss,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#3b82f6' }
      },
      {
        name: 'Val Loss',
        type: 'line',
        data: valLoss,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#f87171', type: 'dashed' }
      }
    ]
  });

  if (!accChart && accChartRef.value) {
    accChart = echarts.init(accChartRef.value);
  }
  
  accChart?.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['Train Acc', 'Val Acc'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: epochs, name: 'Epoch' },
    yAxis: { type: 'value', name: 'Accuracy', min: 0, max: 1 },
    series: [
      {
        name: 'Train Acc',
        type: 'line',
        data: trainAcc,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#10b981' }
      },
      {
        name: 'Val Acc',
        type: 'line',
        data: valAcc,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#f59e0b', type: 'dashed' }
      }
    ]
  });
}

onMounted(async () => {
  await initTasks();
  await initData();
});
</script>

<style scoped></style>
