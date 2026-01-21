
<template>
  <div ref="domRef" class="w-full h-full"></div>
</template>

<script setup lang="ts">
import { watch } from 'vue';
import type { Config, Data, Layout } from 'plotly.js-dist-min';
import { usePlotly } from '@/hooks/common/plotly';

const props = defineProps<{
  data: Data[];
  layout?: Partial<Layout>;
  config?: Partial<Config>;
}>();

const { domRef, react } = usePlotly(
  () => props.data,
  () => props.layout ?? {},
  () => props.config ?? { responsive: true }
);

watch(
  () => [props.data, props.layout, props.config],
  () => {
    react();
  },
  { deep: true }
);
</script>
