<script setup lang="ts">
import { computed } from 'vue';
import { formatDateTime } from '@/utils/common';

defineOptions({
  name: 'SystemInfo'
});

interface RuntimeInfo {
  app_title: string;
  version: string;
  start_time: string;
  uptime_seconds: number;
  pid: number;
  python_version: string;
  platform: string;
}

const props = defineProps<{
  runtime?: RuntimeInfo | null;
}>();

const uptimeText = computed(() => {
  const seconds = props.runtime?.uptime_seconds ?? 0;
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}天 ${hours}小时 ${minutes}分钟`;
  if (hours > 0) return `${hours}小时 ${minutes}分钟`;
  return `${minutes}分钟`;
});

const startTimeText = computed(() => {
  return props.runtime?.start_time ? formatDateTime(props.runtime.start_time) : '-';
});
</script>

<template>
  <NCard title="系统运行信息" :bordered="false" class="card-wrapper">
    <NDescriptions label-placement="left" :column="1" size="small">
      <NDescriptionsItem label="系统名称">{{ runtime?.app_title || '-' }}</NDescriptionsItem>
      <NDescriptionsItem label="版本">{{ runtime?.version || '-' }}</NDescriptionsItem>
      <NDescriptionsItem label="启动时间">{{ startTimeText }}</NDescriptionsItem>
      <NDescriptionsItem label="运行时长">{{ uptimeText }}</NDescriptionsItem>
      <NDescriptionsItem label="进程ID">{{ runtime?.pid ?? '-' }}</NDescriptionsItem>
      <NDescriptionsItem label="Python">{{ runtime?.python_version || '-' }}</NDescriptionsItem>
      <NDescriptionsItem label="平台">{{ runtime?.platform || '-' }}</NDescriptionsItem>
    </NDescriptions>
  </NCard>
</template>

<style scoped></style>
