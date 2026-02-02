<template>
  <div class="p-16px">
    <n-card :title="t('page.deepLearning.inference.title')">
      <n-empty :description="t('common.lookForward')" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>
