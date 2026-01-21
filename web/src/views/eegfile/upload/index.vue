<template>
  <div class="p-16">
    <n-card title="EEG 文件上传">
      <n-space vertical :size="24">
        <n-form ref="formRef" :model="model" :rules="rules" label-placement="left" label-width="auto">
          <n-form-item label="EEG 格式" path="eeg_format">
            <n-select
              v-model:value="model.eeg_format"
              placeholder="请选择 EEG 格式"
              :options="formatOptions"
            />
          </n-form-item>
          <n-form-item label="被试ID" path="subject_id">
            <n-input v-model:value="model.subject_id" placeholder="请输入被试ID (可选)" />
          </n-form-item>
          <n-form-item label="备注" path="notes">
            <n-input
              v-model:value="model.notes"
              type="textarea"
              placeholder="请输入备注信息 (可选)"
            />
          </n-form-item>
        </n-form>

        <n-upload
          ref="uploadRef"
          multiple
          action="/preprocess/eeg/upload"
          :custom-request="customRequest"
          :max="1"
          :default-upload="false"
          @before-upload="handleBeforeUpload"
          @change="handleFileChange"
        >
          <n-button>
            <template #icon>
              <icon-mdi-upload />
            </template>
            选择文件
          </n-button>
        </n-upload>

        <n-space>
          <n-button type="primary" :disabled="!fileListLength" @click="handleUploadClick"> 开始上传 </n-button>
        </n-space>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import {
  type FormInst,
  type UploadInst,
  type UploadFileInfo,
  type FormRules,
  type SelectOption
} from 'naive-ui';
import { request } from '@/service/request';
import { useAuthStore } from '@/store/modules/auth';

const formRef = ref<FormInst | null>(null);
const uploadRef = ref<UploadInst | null>(null);
const authStore = useAuthStore();
const fileListLength = ref(0);

import { useMessage } from 'naive-ui';
const message = useMessage();

const model = ref({
  eeg_format: null,
  subject_id: null,
  notes: null
});

const formatOptions: SelectOption[] = [
  { label: 'European Data Format (.edf)', value: 'European Data Format (.edf)' },
  { label: 'BioSemi Data Format (.bdf)', value: 'BioSemi Data Format (.bdf)' },
  { label: 'Brain Vision Format (.vhdr, .vmrk, .eeg)', value: 'Brain Vision Format (.vhdr, .vmrk, .eeg)' },
  { label: 'EEGLAB Format (.set)', value: 'EEGLAB Format (.set)' },
  { label: 'MNE Functional Image Format (.fif)', value: 'MNE Functional Image Format (.fif)' },
  { label: 'Brain Imaging Data Structure', value: 'Brain Imaging Data Structure' },
  { label: 'HDF5-based Formats (.hdf5)', value: 'HDF5-based Formats (.hdf5)' },
  { label: 'Nihon Kohden Format (.ndf)', value: 'Nihon Kohden Format (.ndf)' }
];

const rules: FormRules = {
  eeg_format: { required: true, message: '请选择 EEG 格式', trigger: 'change' }
};

const handleFileChange = (data: { fileList: UploadFileInfo[] }) => {
  fileListLength.value = data.fileList.length;
};

const handleBeforeUpload = (data: { file: UploadFileInfo; fileList: UploadFileInfo[] }) => {
  if (model.value.eeg_format === 'Nihon Kohden Format (.ndf)' && !data.file.file?.name.endsWith('.zip')) {
    message.error('NDF 格式需要上传 .zip 压缩包');
    return false;
  }
  return true;
};

const handleUploadClick = async () => {
  if (!fileListLength.value) {
    message.error('请先选择一个文件');
    return;
  }

  let errorCount = 0;
  await formRef.value?.validate(errors => {
    if (errors) {
      errorCount = errors.length;
    }
  });

  if (errorCount > 0) {
    message.error('请先完成必填项');
    return;
  }

  uploadRef.value?.submit();
};

const customRequest = ({ file, onFinish, onError, onProgress }: any) => {
  const formData = new FormData();
  formData.append('file', file.file as File);
  if (model.value.eeg_format) {
    formData.append('eeg_format', model.value.eeg_format);
  }
  if (model.value.subject_id) {
    formData.append('subject_id', model.value.subject_id);
  }
  if (model.value.notes) {
    formData.append('notes', model.value.notes);
  }

  request({
    url: '/preprocess/eeg/upload',
    method: 'post',
    data: formData,
    onUploadProgress: ({ loaded, total }) => {
      onProgress({ percent: Math.ceil((loaded / total) * 100) });
    }
  })
    .then((res: any) => {
      const payload = res?.data ?? res;
      if (res?.error || !payload) {
        const backendMsg = res?.error?.response?.data?.msg;
        window.$notification?.error({
          title: '上传失败',
          content: backendMsg || '服务端未返回文件处理结果，请查看后端日志确认处理是否失败。',
          duration: 8000
        });
        onError();
        return;
      }
      res = payload;
      window.$notification?.success({
        title: '上传成功',
        content: `文件 '${res.original_filename ?? '未知'}' 已处理完成。`,
        meta: `状态: ${res.status ?? '未知'} | 通道数: ${res.nchan ?? '未知'}`,
        duration: 5000
      });
      onFinish();
      // Reset form and file list
      formRef.value?.restoreValidation();
      model.value = {
        eeg_format: null,
        subject_id: null,
        notes: null
      };
      uploadRef.value?.clear();
    })
    .catch((err: any) => {
      window.$notification?.error({
        title: '上传失败',
        content: '请求失败。请检查您的网络连接，或确认您选择的本地文件是否仍然存在且可访问。',
        meta: `详细错误: ${err.message}`,
        duration: 8000
      });
      onError();
    });
};

</script>

<style scoped></style>
