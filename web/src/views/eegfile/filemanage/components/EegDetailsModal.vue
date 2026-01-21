<template>
  <n-modal
    :show="show"
    preset="card"
    style="width: 800px"
    title="EEG 文件详情"
    @update:show="closeModal"
  >
    <n-spin :show="loading">
      <n-descriptions v-if="details" label-placement="left" bordered :column="2">
        <n-descriptions-item label="ID">{{ details.id }}</n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="details.status === 'Completed' ? 'success' : 'default'">{{ details.status }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="原始文件名">{{ details.original_filename }}</n-descriptions-item>
        <n-descriptions-item label="文件大小">{{ details.file_size ? `${(details.file_size / 1024).toFixed(2)} KB` : 'N/A' }}</n-descriptions-item>
        <n-descriptions-item label="EEG 格式" :span="2">{{ details.eeg_format }}</n-descriptions-item>
        <n-descriptions-item label="存储路径" :span="2">{{ details.storage_path }}</n-descriptions-item>
        <n-descriptions-item label="被试ID">{{ details.subject_id || 'N/A' }}</n-descriptions-item>
        <n-descriptions-item label="通道数">{{ details.nchan }}</n-descriptions-item>
        <n-descriptions-item label="采样率">{{ details.sfreq }} Hz</n-descriptions-item>
        <n-descriptions-item label="工频">{{ details.line_freq !== null ? `${details.line_freq} Hz` : 'N/A' }}</n-descriptions-item>
        <n-descriptions-item label="高通滤波">{{ details.highpass }} Hz</n-descriptions-item>
        <n-descriptions-item label="低通滤波">{{ details.lowpass }} Hz</n-descriptions-item>
        <n-descriptions-item label="创建时间">{{ new Date(details.created_at).toLocaleString() }}</n-descriptions-item>
        <n-descriptions-item label="更新时间">{{ new Date(details.updated_at).toLocaleString() }}</n-descriptions-item>
        <n-descriptions-item label="备注" :span="2">{{ details.notes || '无' }}</n-descriptions-item>
        <n-descriptions-item label="通道名称" :span="2">
          <n-space>
            <n-tag v-for="ch in details.ch_names" :key="ch" type="info" size="small">
              {{ ch }}
            </n-tag>
          </n-space>
        </n-descriptions-item>
      </n-descriptions>
      <n-empty v-else description="没有可显示的详细信息" />
    </n-spin>
  </n-modal>
</template>

<script setup lang="ts">
import { NModal, NSpin, NDescriptions, NDescriptionsItem, NTag, NEmpty } from 'naive-ui';

// 定义组件接收的 props
interface EEGFileDetails {
  id: number;
  original_filename: string;
  subject_id: string | null;
  file_size: number | null;
  storage_path: string;
  eeg_format: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  nchan: number | null;
  sfreq: number | null;
  line_freq: number | null;
  highpass: number | null;
  lowpass: number | null;
  ch_names: string[] | null;
}

interface Props {
  show: boolean;
  loading: boolean;
  details: EEGFileDetails | null;
}

defineProps<Props>();

// 定义组件可以触发的事件
const emit = defineEmits(['close']);

const closeModal = () => {
  emit('close');
};
</script>

<style scoped>
.m-4 {
  margin: 4px;
}
</style>
