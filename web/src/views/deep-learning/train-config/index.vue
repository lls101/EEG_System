<template>
  <div class="p-16px">
    <n-grid cols="1 l:3" x-gap="16" y-gap="16">
      <n-gi span="2">
        <n-card title="新建训练任务" size="small">
          <n-form
            ref="formRef"
            :model="model"
            :rules="rules"
            label-placement="left"
            label-width="120"
            require-mark-placement="right-hanging"
          >
            <n-form-item label="任务名称" path="name">
              <n-input v-model:value="model.name" placeholder="请输入任务名称（如：CNN_Baseline_v1）" />
            </n-form-item>

            <n-form-item label="数据集" path="datasetId">
              <n-select
                v-model:value="model.datasetId"
                placeholder="请选择训练数据集"
                :options="datasetOptions"
                :loading="loadingDatasets"
              />
            </n-form-item>

            <n-divider title-placement="left">模型架构</n-divider>

            <n-form-item label="模型类型" path="modelType">
              <n-radio-group v-model:value="model.modelType" name="modelTypeGroup">
                <n-space>
                  <n-radio-button
                    v-for="type in modelTypes"
                    :key="type.value"
                    :value="type.value"
                    :label="type.label"
                  />
                </n-space>
              </n-radio-group>
            </n-form-item>

            <n-form-item label="模型描述">
              <div class="text-gray-400 text-12px">
                {{ currentModelDesc }}
              </div>
            </n-form-item>

            <n-divider title-placement="left">超参数配置</n-divider>

            <n-grid cols="1 s:2" x-gap="24">
              <n-gi>
                <n-form-item label="训练轮次 (Epochs)" path="epochs">
                  <n-input-number v-model:value="model.epochs" :min="1" :max="1000" class="w-full" />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="批次大小 (Batch)" path="batchSize">
                  <n-select
                    v-model:value="model.batchSize"
                    :options="batchSizeOptions"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="学习率 (LR)" path="learningRate">
                  <n-input-number
                    v-model:value="model.learningRate"
                    :step="0.0001"
                    :min="0.00001"
                    :max="0.1"
                    class="w-full"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="优化器" path="optimizer">
                  <n-select
                    v-model:value="model.optimizer"
                    :options="optimizerOptions"
                  />
                </n-form-item>
              </n-gi>
            </n-grid>

            <div class="flex justify-end mt-4">
              <n-button type="primary" size="large" :loading="submitting" @click="handleValidateButtonClick">
                <template #icon>
                  <div class="i-mdi:rocket-launch" />
                </template>
                提交训练任务
              </n-button>
            </div>
          </n-form>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card title="配置指南" size="small" class="mb-4">
          <n-collapse>
            <n-collapse-item title="如何选择模型架构？" name="1">
              <p class="text-13px text-gray-500">
                <b>1D-CNN</b>: 适合捕捉局部特征，训练速度快，是 EEG 分类的基准模型。<br/><br/>
                <b>Transformer</b>: 擅长捕捉长距离依赖关系，但需要更多数据和显存。<br/><br/>
                <b>LSTM</b>: 经典的循环神经网络，适合处理时序数据。
              </p>
            </n-collapse-item>
            <n-collapse-item title="推荐参数设置" name="2">
              <ul class="text-13px text-gray-500 list-disc pl-4">
                <li>Epochs: 初次尝试建议 50-100</li>
                <li>Batch Size: 显存允许情况下越大越好，通常 32 或 64</li>
                <li>Learning Rate: 默认 0.001，若震荡则降低</li>
              </ul>
            </n-collapse-item>
          </n-collapse>
        </n-card>

        <n-card title="最近使用的配置" size="small">
          <n-empty description="暂无历史配置" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useMessage } from 'naive-ui';
import type { FormInst } from 'naive-ui';
import { useRouter } from 'vue-router';
import { fetchDatasetList, submitTrainingTask } from '@/service/api';
import type { TrainingConfig } from '@/service/api';

const message = useMessage();
const router = useRouter();
const formRef = ref<FormInst | null>(null);
const submitting = ref(false);

const model = ref<TrainingConfig>({
  name: '',
  datasetId: '',
  modelType: '1D-CNN',
  epochs: 100,
  batchSize: 32,
  learningRate: 0.001,
  optimizer: 'adam',
  lossFunction: 'cross_entropy'
});

const rules = {
  name: { required: true, message: '请输入任务名称', trigger: 'blur' },
  datasetId: { required: true, message: '请选择数据集', trigger: ['blur', 'change'] },
  modelType: { required: true, message: '请选择模型类型', trigger: 'change' },
  epochs: { type: 'number', required: true, message: '请输入轮次', trigger: ['blur', 'change'] },
  batchSize: { type: 'number', required: true, message: '请选择批次大小', trigger: ['blur', 'change'] },
  learningRate: { type: 'number', required: true, message: '请输入学习率', trigger: ['blur', 'change'] }
};

const modelTypes = [
  { label: '1D-CNN', value: '1D-CNN', desc: '包含 3 层卷积层和 2 层全连接层的标准卷积网络，适合快速验证。' },
  { label: 'Transformer', value: 'Transformer', desc: '基于 Self-Attention 机制，适合捕捉 EEG 信号中的全局时空依赖。' },
  { label: 'ResNet1D', value: 'ResNet1D', desc: '深层残差网络，能够训练更深的模型，适合大规模数据集。' },
  { label: 'LSTM', value: 'LSTM', desc: '长短期记忆网络，经典的时序处理模型。' }
];

const batchSizeOptions = [16, 32, 64, 128, 256].map(v => ({ label: String(v), value: v }));
const optimizerOptions = [
  { label: 'Adam', value: 'adam' },
  { label: 'SGD', value: 'sgd' },
  { label: 'RMSprop', value: 'rmsprop' }
];

const datasetOptions = ref<{ label: string; value: string }[]>([]);
const loadingDatasets = ref(false);

const currentModelDesc = computed(() => {
  const t = modelTypes.find(item => item.value === model.modelType);
  return t ? t.desc : '';
});

async function loadDatasets() {
  loadingDatasets.value = true;
  try {
    const { records } = await fetchDatasetList({ pageSize: 100, status: 'active' });
    datasetOptions.value = records.map(d => ({
      label: `${d.name} (${d.version}) - ${d.samples} samples`,
      value: d.id
    }));
  } finally {
    loadingDatasets.value = false;
  }
}

async function handleValidateButtonClick(e: MouseEvent) {
  e.preventDefault();
  formRef.value?.validate(async errors => {
    if (!errors) {
      submitting.value = true;
      try {
        await submitTrainingTask(model.value);
        message.success('训练任务提交成功！');
        router.push({ name: 'deep-learning_train-tasks' });
      } catch (error) {
        message.error('提交失败');
      } finally {
        submitting.value = false;
      }
    } else {
      message.error('请检查表单填写');
    }
  });
}

onMounted(() => {
  loadDatasets();
});
</script>