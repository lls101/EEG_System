<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { request } from '@/service/request';
import HeaderBanner from './modules/header-banner.vue';
import CardData from './modules/card-data.vue';
import LineChart from './modules/line-chart.vue';
import PieChart from './modules/pie-chart.vue';
import ProjectNews from './modules/project-news.vue';
import SystemInfo from './modules/system-info.vue';

const appStore = useAppStore();

const gap = computed(() => (appStore.isMobile ? 0 : 16));

interface OverviewData {
  counts: {
    uploads: number;
    preprocessing: number;
    features: number;
  };
  runtime: {
    app_title: string;
    version: string;
    start_time: string;
    uptime_seconds: number;
    pid: number;
    python_version: string;
    platform: string;
  };
}

const overview = ref<OverviewData | null>(null);

async function fetchOverview() {
  try {
    const response = await request<any>({ url: '/system-manage/overview', method: 'get' });
    if (!response.error && response.data) {
      overview.value = response.data;
    }
  } finally {}
}

onMounted(() => {
  fetchOverview();
});
</script>

<template>
  <NSpace vertical :size="16">
    <HeaderBanner />
    <CardData :counts="overview?.counts" :runtime="overview?.runtime" />
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:14">
        <NCard :bordered="false" class="card-wrapper">
          <LineChart />
        </NCard>
      </NGi>
      <NGi span="24 s:24 m:10">
        <NCard :bordered="false" class="card-wrapper">
          <PieChart />
        </NCard>
      </NGi>
    </NGrid>
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:14">
        <ProjectNews />
      </NGi>
      <NGi span="24 s:24 m:10">
        <SystemInfo :runtime="overview?.runtime" />
      </NGi>
    </NGrid>
  </NSpace>
</template>

<style scoped></style>
