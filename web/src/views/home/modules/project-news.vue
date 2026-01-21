<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

defineOptions({
  name: 'ProjectNews'
});

interface NewsItem {
  id: number;
  content: string;
  time: string;
}

const newses = computed<NewsItem[]>(() => [
  { id: 1, content: '新增上传校验与自动归档，文件管理更稳定', time: '2025-09-15 10:30:22' },
  { id: 2, content: '新增小波去噪算法，支持多种小波基函数', time: '2025-09-14 16:45:18' },
  { id: 3, content: 'ICA算法优化完成，处理速度提升40%', time: '2025-09-13 09:15:33' },
  { id: 4, content: '系统新增时频域特征提取功能', time: '2025-09-12 14:22:07' },
  { id: 5, content: '数据预处理管道重构，支持批量处理', time: '2025-09-11 11:38:55' }
]);
</script>

<template>
  <NCard title="系统动态" :bordered="false" size="small" segmented class="card-wrapper">
    <template #header-extra>
      <a class="text-primary" href="javascript:;">更多动态</a>
    </template>
    <NList>
      <NListItem v-for="item in newses" :key="item.id">
        <template #prefix>
          <div class="size-32px rd-1/2 bg-gradient-to-br from-blue-500 to-purple-600 flex-center">
            <div class="text-white text-12px font-bold">EEG</div>
          </div>
        </template>
        <NThing :title="item.content" :description="item.time" />
      </NListItem>
    </NList>
  </NCard>
</template>

<style scoped></style>
