<script setup lang="ts">
import { Icon } from '@iconify/vue';

defineOptions({
  name: 'CreativityBanner'
});
</script>

<template>
  <NCard title="快速访问" :bordered="false" size="small" class="h-full card-wrapper">
    <div class="h-full flex-col gap-16px">
      <div class="flex-1 flex-center">
        <div class="text-center">
          <div class="text-72px mb-16px">🧠</div>
          <h3 class="text-18px font-semibold mb-8px">EEG数据分析</h3>
          <p class="text-#666 text-14px">专业的脑电信号处理平台</p>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-12px">
        <NButton type="primary" size="small" block>
          <template #icon>
            <Icon icon="mdi:brain" />
          </template>
          数据预处理
        </NButton>
        <NButton type="primary" size="small" block>
          <template #icon>
            <Icon icon="mdi:chart-line" />
          </template>
          特征提取
        </NButton>
        <NButton type="primary" size="small" block>
          <template #icon>
            <Icon icon="mdi:filter-cog" />
          </template>
          ICA去噪
        </NButton>
        <NButton type="primary" size="small" block>
          <template #icon>
            <Icon icon="mdi:file-chart" />
          </template>
          分析报告
        </NButton>
      </div>
    </div>
  </NCard>
</template>

<style scoped></style>
