export type DatasetStatus = 'active' | 'archived' | 'draft';

export type DatasetRow = {
  id: string;
  name: string;
  version: string;
  labels: string[];
  samples: number;
  createdAt: string;
  status: DatasetStatus;
};

export type DatasetListParams = {
  page?: number;
  pageSize?: number;
  keyword?: string;
  status?: DatasetStatus | null;
  label?: string | null;
};

export type DatasetListResult = {
  records: DatasetRow[];
  total: number;
};

export type DatasetStats = {
  datasetCount: number;
  sampleCount: number;
  labelCount: number;
  split: string;
  currentVersion: string;
  updatedAt: string;
  channelInfo: string;
};

const mockDatasets: DatasetRow[] = [
  {
    id: 'DS-001',
    name: 'PD-EEG Base',
    version: 'v0.1',
    labels: ['PD', 'Normal'],
    samples: 8240,
    createdAt: '2026-01-28 21:10',
    status: 'active'
  },
  {
    id: 'DS-002',
    name: 'DBS Stimulation',
    version: 'v0.1',
    labels: ['DBS-ON', 'DBS-OFF'],
    samples: 3120,
    createdAt: '2026-01-29 09:45',
    status: 'draft'
  },
  {
    id: 'DS-003',
    name: 'Cross-Subject Mix',
    version: 'v0.2',
    labels: ['PD', 'Normal', 'DBS-ON', 'DBS-OFF'],
    samples: 1120,
    createdAt: '2026-01-30 16:30',
    status: 'archived'
  },
  {
    id: 'DS-004',
    name: 'Medication Challenge',
    version: 'v0.1',
    labels: ['PD', 'Normal'],
    samples: 960,
    createdAt: '2026-01-31 11:05',
    status: 'active'
  }
];

const mockStats: DatasetStats = {
  datasetCount: mockDatasets.length,
  sampleCount: mockDatasets.reduce((sum, item) => sum + item.samples, 0),
  labelCount: 6,
  split: '70 / 20 / 10',
  currentVersion: 'PD-EEG v0.1',
  updatedAt: '2026-02-01',
  channelInfo: '32 / 64'
};

function delay<T>(value: T, ms = 350): Promise<T> {
  return new Promise(resolve => {
    setTimeout(() => resolve(value), ms);
  });
}

export async function fetchDatasetStats(): Promise<DatasetStats> {
  return delay(mockStats, 200);
}

export async function fetchDatasetList(params: DatasetListParams = {}): Promise<DatasetListResult> {
  const {
    page = 1,
    pageSize = 10,
    keyword = '',
    status = null,
    label = null
  } = params;

  const normalizedKeyword = keyword.trim().toLowerCase();

  let result = mockDatasets.filter(item => {
    const matchKeyword = normalizedKeyword
      ? `${item.id} ${item.name} ${item.version}`.toLowerCase().includes(normalizedKeyword)
      : true;
    const matchStatus = status ? item.status === status : true;
    const matchLabel = label ? item.labels.includes(label) : true;

    return matchKeyword && matchStatus && matchLabel;
  });

  const total = result.length;
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  result = result.slice(start, end);

  return delay({ records: result, total });
}

// --- Training Configuration & Tasks Types ---

export type ModelArchitecture = '1D-CNN' | 'Transformer' | 'LSTM' | 'ResNet1D';

export type TrainingConfig = {
  id?: string;
  name: string;
  datasetId: string;
  modelType: ModelArchitecture;
  epochs: number;
  batchSize: number;
  learningRate: number;
  optimizer: 'adam' | 'sgd' | 'rmsprop';
  lossFunction: 'cross_entropy' | 'focal_loss';
  description?: string;
};

export type TrainingTaskStatus = 'pending' | 'running' | 'success' | 'failed' | 'stopped';

export type TrainingTaskRow = {
  id: string;
  name: string;
  datasetName: string;
  modelType: ModelArchitecture;
  status: TrainingTaskStatus;
  progress: number; // 0-100
  accuracy?: number;
  loss?: number;
  startTime: string;
  duration?: string;
};

// --- Mock Data for Tasks ---

const mockTasks: TrainingTaskRow[] = [
  {
    id: 'TASK-001',
    name: 'CNN Baseline',
    datasetName: 'PD-EEG Base v0.1',
    modelType: '1D-CNN',
    status: 'success',
    progress: 100,
    accuracy: 0.924,
    loss: 0.15,
    startTime: '2026-02-01 10:00',
    duration: '45m 12s'
  },
  {
    id: 'TASK-002',
    name: 'Transformer Exp',
    datasetName: 'PD-EEG Base v0.1',
    modelType: 'Transformer',
    status: 'failed',
    progress: 45,
    accuracy: 0.65,
    loss: 0.8,
    startTime: '2026-02-01 11:30',
    duration: '12m 05s'
  },
  {
    id: 'TASK-003',
    name: 'ResNet Deep',
    datasetName: 'Medication Challenge v0.1',
    modelType: 'ResNet1D',
    status: 'running',
    progress: 68,
    accuracy: 0.88,
    loss: 0.22,
    startTime: '2026-02-01 14:15',
    duration: 'Running...'
  },
  {
    id: 'TASK-004',
    name: 'LSTM Sequence',
    datasetName: 'DBS Stimulation v0.1',
    modelType: 'LSTM',
    status: 'pending',
    progress: 0,
    startTime: '2026-02-01 15:00'
  }
];

export async function fetchTrainingTasks(): Promise<TrainingTaskRow[]> {
  return delay(mockTasks);
}

export async function submitTrainingTask(config: TrainingConfig): Promise<boolean> {
  console.log('Submitting task with config:', config);
  return delay(true, 800);
}

export async function stopTrainingTask(taskId: string): Promise<boolean> {
  console.log('Stopping task:', taskId);
  return delay(true, 500);
}

// --- Training Monitor Metrics ---

export type TrainingMetricPoint = {
  epoch: number;
  loss: number;
  accuracy: number;
  val_loss: number;
  val_accuracy: number;
};

export type TrainingMonitorData = {
  taskId: string;
  taskName: string;
  status: TrainingTaskStatus;
  currentEpoch: number;
  totalEpochs: number;
  metrics: TrainingMetricPoint[];
};

export async function fetchTrainingMonitorData(taskId: string): Promise<TrainingMonitorData> {
  const task = mockTasks.find(t => t.id === taskId) || mockTasks[2]; // Default to running task
  
  const totalEpochs = 100;
  const currentEpoch = task.status === 'success' ? 100 : (task.status === 'running' ? 68 : 0);
  
  const metrics: TrainingMetricPoint[] = [];
  
  // Generate some semi-realistic curve data
  for (let i = 1; i <= currentEpoch; i++) {
    const baseLoss = Math.exp(-i / 20) * 0.8 + 0.1;
    const noise = (Math.random() - 0.5) * 0.05;
    
    metrics.push({
      epoch: i,
      loss: Math.max(0.05, baseLoss + noise),
      accuracy: Math.min(0.98, 0.6 + (1 - Math.exp(-i / 30)) * 0.35 + noise),
      val_loss: Math.max(0.08, baseLoss * 1.1 + noise * 1.5),
      val_accuracy: Math.min(0.96, 0.55 + (1 - Math.exp(-i / 35)) * 0.35 + noise * 0.8)
    });
  }

  return delay({
    taskId: task.id,
    taskName: task.name,
    status: task.status,
    currentEpoch,
    totalEpochs,
    metrics
  }, 400);
}
