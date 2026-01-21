<script setup lang="ts">
import { computed } from 'vue';
import { createReusableTemplate } from '@vueuse/core';

defineOptions({
  name: 'CardData'
});

interface CardData {
  key: string;
  title: string;
  value: number;
  unit: string;
  color: {
    start: string;
    end: string;
  };
  icon: string;
}

interface OverviewCounts {
  uploads: number;
  preprocessing: number;
  features: number;
}

interface OverviewRuntime {
  uptime_seconds: number;
}

const props = defineProps<{
  counts?: OverviewCounts | null;
  runtime?: OverviewRuntime | null;
}>();

const cardData = computed<CardData[]>(() => {
  const uploads = props.counts?.uploads ?? 0;
  const preprocessing = props.counts?.preprocessing ?? 0;
  const features = props.counts?.features ?? 0;
  const uptimeHours = props.runtime?.uptime_seconds
    ? Math.floor(props.runtime.uptime_seconds / 3600)
    : 0;

  return [
    {
      key: 'uploadCount',
      title: '文件上传数量',
      value: uploads,
      unit: '个',
      color: {
        start: '#2563eb',
        end: '#3b82f6'
      },
      icon: 'mdi:file-upload'
    },
    {
      key: 'preprocessingCount',
      title: '预处理数据量',
      value: preprocessing,
      unit: '个',
      color: {
        start: '#10b981',
        end: '#34d399'
      },
      icon: 'mdi:filter-cog'
    },
    {
      key: 'featureCount',
      title: '特征提取数量',
      value: features,
      unit: '个',
      color: {
        start: '#f97316',
        end: '#fb923c'
      },
      icon: 'mdi:chart-bell-curve'
    },
    {
      key: 'uptimeHours',
      title: '系统运行时长',
      value: uptimeHours,
      unit: '小时',
      color: {
        start: '#8b5cf6',
        end: '#a78bfa'
      },
      icon: 'mdi:clock-outline'
    }
  ];
});

interface GradientBgProps {
  gradientColor: string;
}

const [DefineGradientBg, GradientBg] = createReusableTemplate<GradientBgProps>();

function getGradientColor(color: CardData['color']) {
  return `linear-gradient(to bottom right, ${color.start}, ${color.end})`;
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <!-- define component start: GradientBg -->
    <DefineGradientBg v-slot="{ $slots, gradientColor }">
      <div class="rd-8px px-16px pb-4px pt-8px text-white" :style="{ backgroundImage: gradientColor }">
        <component :is="$slots.default" />
      </div>
    </DefineGradientBg>
    <!-- define component end: GradientBg -->

    <NGrid cols="s:1 m:2 l:4" responsive="screen" :x-gap="16" :y-gap="16">
      <NGi v-for="item in cardData" :key="item.key">
        <GradientBg :gradient-color="getGradientColor(item.color)" class="flex-1">
          <h3 class="text-16px">{{ item.title }}</h3>
          <div class="flex justify-between pt-12px">
            <SvgIcon :icon="item.icon" class="text-32px" />
            <CountTo
              :suffix="item.unit"
              :start-value="1"
              :end-value="item.value"
              class="text-30px text-white dark:text-dark"
            />
          </div>
        </GradientBg>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped></style>
