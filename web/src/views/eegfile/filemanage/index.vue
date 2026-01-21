<template>
  <div class="p-16">
    <n-card title="EEG 文件管理">
      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        remote
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>

    <EegDetailsModal
      :show="showDetailsModal"
      :loading="detailsLoading"
      :details="selectedFile"
      @close="showDetailsModal = false"
    />

    
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, ref } from 'vue';
// 导入新组件
import EegDetailsModal from './components/EegDetailsModal.vue';
import { NButton, NSpace, NTooltip, useDialog, useNotification, NTag } from 'naive-ui';
import type { DataTableColumns, PaginationProps } from 'naive-ui';
import { request } from '@/service/request';

type EEGFile = {
  id: number;
  original_filename: string;
  eeg_format: string;
  status: string;
  subject_id: string | null;
  created_at: string;
  updated_at: string;
  nchan: number | null;
  sfreq: number | null;
  // ... and any other fields you want to have typed from the backend
};

const dialog = useDialog();
const notification = useNotification();

const loading = ref(false);
const tableData = ref<EEGFile[]>([]);
const pagination = ref<PaginationProps>({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
});

// 使用一个统一的 ref 来存储当前操作的文件
const selectedFile = ref<EEGFile | null>(null);

// 详情模态框状态
const showDetailsModal = ref(false);
const detailsLoading = ref(false);



const handleViewDetails = async (row: EEGFile) => {
  selectedFile.value = row;
  showDetailsModal.value = true;
  detailsLoading.value = true;
  try {
    const res = await request<any>({ url: `/preprocess/eeg/${row.id}`, method: 'get' });
    // 更新选中文件的数据，以防数据不是最新的
    selectedFile.value = res.data;
  } catch (error: any) {
    notification.error({ title: '获取详情失败', content: error.message, duration: 3000 });
    showDetailsModal.value = false;
  } finally {
    detailsLoading.value = false;
  }
};



const createColumns = (): DataTableColumns<EEGFile> => {
  return [
    { title: 'ID', key: 'id', width: 80 },
    { title: '原始文件名', key: 'original_filename', resizable: true, ellipsis: { tooltip: true } },
    { title: '通道数', key: 'nchan', width: 100 },
    { title: '采样率(Hz)', key: 'sfreq', width: 120 },
    { title: '状态', key: 'status', width: 120 },
    { title: '被试ID', key: 'subject_id', width: 120 },
    {
      title: '创建时间',
      key: 'created_at',
      width: 200,
      render: row => new Date(row.created_at).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render(row) {
        return h(
          NSpace,
          {},
          {
            default: () => [
              h(
                NButton,
                { size: 'small', type: 'primary', onClick: () => handleViewDetails(row) },
                { default: () => '详情' }
              ),
              h(
                NButton,
                { size: 'small', type: 'error', onClick: () => handleDelete(row) },
                { default: () => '删除' }
              )
            ]
          }
        );
      }
    }
  ];
};

const columns = createColumns();

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await request<any>({
      url: '/preprocess/eeg/',
      method: 'get',
      params: {
        page: pagination.value.page,
        page_size: pagination.value.pageSize
      }
    });
    tableData.value = res.data || [];
    pagination.value.itemCount = res.total || 0;
  } catch (error: any) {
    notification.error({ title: '数据加载失败', content: error.message, duration: 3000 });
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  pagination.value.page = page;
  fetchData();
};

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize;
  pagination.value.page = 1;
  fetchData();
};

const handleDelete = (row: EEGFile) => {
  dialog.warning({
    title: '确认删除',
    content: `删除操作不可逆，确定要删除文件 "${row.original_filename}" 吗？`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request({ url: `/preprocess/eeg/${row.id}`, method: 'delete' });
        notification.success({ title: '删除成功', duration: 3000 });
        fetchData();
      } catch (error: any) {
        notification.error({ title: '删除失败', content: error.message, duration: 3000 });
      }
    }
  });
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped></style>
