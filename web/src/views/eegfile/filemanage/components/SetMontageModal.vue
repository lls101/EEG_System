<template>
  <n-modal
    :show="show"
    preset="card"
    style="width: 600px"
    title="设置电极位置 (Montage)"
    @update:show="closeModal"
  >
    <n-spin :show="loading">
      <div v-if="eegFile">
        <p class="mb-16">
          正在为文件
          <n-text strong>"{{ eegFile.original_filename }}"</n-text>
          设置电极位置。
        </p>
        <n-select
          v-model:value="selectedMontage"
          :options="montageOptions"
          placeholder="请选择一个标准的电极帽"
        />
        <n-space justify="end" class="mt-16">
          <n-button @click="closeModal">取消</n-button>
          <n-button type="primary" :disabled="!selectedMontage" @click="handleSave">
            应用并保存
          </n-button>
        </n-space>
      </div>
    </n-spin>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { NModal, NSpin, NSelect, NButton, NSpace, NText, useNotification } from 'naive-ui';
import { request } from '@/service/request';

// 和后端 schemas/preprocess.py 中的 MontageOptions 枚举保持一致
const montageOptions = [
  { label: 'Standard 10-20', value: 'standard_1020' },
  { label: 'Standard 10-05', value: 'standard_1005' },
  { label: 'BioSemi 64', value: 'biosemi64' },
  { label: 'BioSemi 32', value: 'biosemi32' },
  { label: 'EGI 256', value: 'egi_256' },
  { label: 'GSN HydroCel 128', value: 'gsn-hydrocel-128' }
];

// 定义组件接收的 props
interface EEGFile {
  id: number;
  original_filename: string;
  montage: string | null;
  [key: string]: any;
}

interface Props {
  show: boolean;
  eegFile: EEGFile | null;
}

const props = defineProps<Props>();

// 定义组件可以触发的事件
const emit = defineEmits(['close', 'refresh']);

const notification = useNotification();
const loading = ref(false);
const selectedMontage = ref<string | null>(null);

// 监听 props.eegFile 的变化，当模态框打开并传入新的文件时，自动填充已保存的选项
watch(
  () => props.eegFile,
  newFile => {
    if (newFile) {
      selectedMontage.value = newFile.montage   
  }
);

const closeModal = () => {
  emit('close');
};

const handleSave = async () => {
  if (!props.eegFile || !selectedMontage.value) return;

  loading.value = true;
  try {
    await request({
      url: `/preprocess/base_checks/${props.eegFile.id}/set_montage`,
      method: 'post',
      data: {
        montage_name: selectedMontage.value
      }
    });
    notification.success({ title: '电极位置设置成功', duration: 3000 });
    emit('refresh'); // 通知父组件刷新列表
    closeModal(); // 关闭模态框
  } catch (error: any) {
    notification.error({ title: '操作失败', content: error.message, duration: 3000 });
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.mt-16 {
  margin-top: 16px;
}
.mb-16 {
  margin-bottom: 16px;
}
</style>
