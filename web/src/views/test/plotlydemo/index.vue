
<template>
  <div class="p-4">
    <h1 class="text-2xl mb-4">我的 Plotly 图表示例</h1>
    <div class="h-96">
      <PlotlyChart :data="chartData" :layout="chartLayout" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import PlotlyChart from '@/components/advanced/PlotlyChart.vue';
import type { Data, Layout } from 'plotly.js';

// 1. 定义图表的 `data`
// Plotly 的 data 是一个数组，可以包含多种类型的 trace
const chartData = ref<Data[]>([
  {
    x: [1, 2, 3, 4, 5],
    y: [10, 15, 13, 17, 20],
    type: 'scatter', // 'scatter', 'bar', 'pie' 等
    mode: 'lines+markers',
    name: 'Trace 1'
  },
  {
    x: [1, 2, 3, 4, 5],
    y: [16, 5, 11, 9, 8],
    type: 'bar',
    name: 'Trace 2'
  }
]);

// 2. 定义图表的 `layout`
// layout 用于控制图表的标题、坐标轴、颜色、尺寸等外观样式
const chartLayout = ref<Partial<Layout>>({
  title: '简单的 Plotly.js 图表',
  xaxis: {
    title: 'X 轴'
  },
  yaxis: {
    title: 'Y 轴'
  },
  // 更多布局选项...
});

// 您可以随时修改 chartData 和 chartLayout 的值，
// 图表将会像 useEcharts 一样自动、响应式地更新。
// 例如：
// setTimeout(() => {
//   chartData.value[0].y = [20, 22, 24, 26, 28];
//   chartLayout.value.title = '数据已更新！';
// }, 3000);

</script>
