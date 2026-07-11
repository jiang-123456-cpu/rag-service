<!-- src/views/DashboardHome.vue -->
<template>
  <div class="dashboard-home">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card" v-for="stat in stats" :key="stat.title">
        <div class="stat-content">
          <div class="stat-title">{{ stat.title }}</div>
          <div class="stat-count">{{ stat.count }}</div>
          <div class="stat-unit">{{ stat.unit }}</div>
        </div>
        <div class="stat-icon" :style="{ color: stat.color }">
          <el-icon :size="32"><component :is="stat.icon" /></el-icon>
        </div>
      </el-card>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 对话总量趋势（折线图） -->
      <el-card class="chart-card">
        <template #header>
          <span><strong>对话总量趋势</strong></span>
          <el-select v-model="timeRange" size="small" class="time-select">
            <el-option label="按小时" value="hour" />
            <el-option label="按天" value="day" />
            <el-option label="按月" value="month" />
          </el-select>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="conversationTrendOption" autoresize />
        </div>
      </el-card>

      <!-- 用户满意度分布（饼图） -->
      <el-card class="chart-card">
        <template #header>
          <span><strong>用户满意度分布</strong></span>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="satisfactionOption" autoresize />
        </div>
      </el-card>

      <!-- 独立访客 vs 对话数（柱状图） -->
      <el-card class="chart-card">
        <template #header>
          <span><strong>独立访客(UV) vs 对话数(PV)</strong></span>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="uvVsPvOption" autoresize />
        </div>
      </el-card>

      <!-- 热门意图 Top10（横向柱状图） -->
      <el-card class="chart-card">
        <template #header>
          <span><strong>热门意图 Top10</strong></span>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="topIntentOption" autoresize />
        </div>
      </el-card>

      <!-- 转人工率及原因（堆叠柱状图） -->
      <el-card class="chart-card wide-card">
        <template #header>
          <span><strong>转人工率及转人工原因</strong></span>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="transferRateOption" autoresize />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Document, Folder, DataAnalysis, Message, TrendingUp, Users } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent
])

const timeRange = ref('day')

// 统计数据
const stats = [
  { title: '今日对话量', count: 1234, unit: '次', icon: 'Message', color: '#1890ff' },
  { title: '用户满意度', count: 94.5, unit: '%', icon: 'TrendingUp', color: '#52c41a' },
  { title: '独立访客', count: 856, unit: '人', icon: 'Users', color: '#fa8c16' },
  { title: '转人工率', count: 12.3, unit: '%', icon: 'Document', color: '#f5222d' },
  { title: '公司规章制度', count: 4, unit: '篇', icon: 'Document', color: '#1890ff' },
  { title: '技术文档库', count: 4, unit: '篇', icon: 'Folder', color: '#52c41a' }
]

// Mock数据 - 对话总量趋势
const conversationTrendData = {
  hour: {
    labels: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
    data: [32, 18, 12, 28, 85, 156, 198, 175, 145, 128, 98, 56]
  },
  day: {
    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    data: [892, 956, 1023, 1156, 1234, 654, 523]
  },
  month: {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    data: [28560, 26320, 31250, 29870, 32150, 34680]
  }
}

// Mock数据 - 满意度分布
const satisfactionData = [
  { value: 685, name: '满意', percentage: 68.5 },
  { value: 210, name: '一般', percentage: 21.0 },
  { value: 105, name: '不满意', percentage: 10.5 }
]

// Mock数据 - UV vs PV
const uvPvData = {
  labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  uv: [623, 678, 723, 789, 856, 456, 389],
  pv: [892, 956, 1023, 1156, 1234, 654, 523]
}

// Mock数据 - 热门意图Top10
const topIntentData = [
  { name: '咨询订单', value: 345 },
  { name: '退款流程', value: 289 },
  { name: '产品故障', value: 256 },
  { name: '账户问题', value: 198 },
  { name: '物流查询', value: 178 },
  { name: '发票问题', value: 156 },
  { name: '售后服务', value: 145 },
  { name: '使用帮助', value: 123 },
  { name: '投诉建议', value: 98 },
  { name: '其他', value: 67 }
]

// Mock数据 - 转人工原因
const transferReasonData = {
  labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  aiRefuse: [32, 45, 38, 52, 48, 28, 22],
  userRequest: [28, 32, 45, 38, 56, 35, 28],
  lowConfidence: [18, 22, 15, 28, 22, 15, 12]
}

// 对话总量趋势图表配置
const conversationTrendOption = computed(() => {
  const data = conversationTrendData[timeRange.value as keyof typeof conversationTrendData]
  return {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c} 次'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.labels
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '对话数',
        type: 'line',
        smooth: true,
        data: data.data,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ]
          }
        },
        lineStyle: {
          width: 3,
          color: '#1890ff'
        },
        itemStyle: {
          color: '#1890ff'
        }
      }
    ]
  }
})

// 满意度分布图表配置
const satisfactionOption = {
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c}人 ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      name: '满意度',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}\n{d}%'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 18,
          fontWeight: 'bold'
        }
      },
      data: [
        { value: satisfactionData[0].value, name: '满意', itemStyle: { color: '#52c41a' } },
        { value: satisfactionData[1].value, name: '一般', itemStyle: { color: '#faad14' } },
        { value: satisfactionData[2].value, name: '不满意', itemStyle: { color: '#f5222d' } }
      ]
    }
  ]
}

// UV vs PV 图表配置
const uvVsPvOption = {
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  legend: {
    data: ['独立访客(UV)', '对话数(PV)']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: uvPvData.labels
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '独立访客(UV)',
      type: 'bar',
      data: uvPvData.uv,
      itemStyle: {
        color: '#1890ff',
        borderRadius: [4, 4, 0, 0]
      }
    },
    {
      name: '对话数(PV)',
      type: 'bar',
      data: uvPvData.pv,
      itemStyle: {
        color: '#52c41a',
        borderRadius: [4, 4, 0, 0]
      }
    }
  ]
}

// 热门意图 Top10 图表配置
const topIntentOption = {
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '10%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'value'
  },
  yAxis: {
    type: 'category',
    data: topIntentData.map(item => item.name).reverse()
  },
  series: [
    {
      type: 'bar',
      data: topIntentData.map(item => item.value).reverse(),
      itemStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 1,
          y2: 0,
          colorStops: [
            { offset: 0, color: '#1890ff' },
            { offset: 1, color: '#69c0ff' }
          ]
        },
        borderRadius: [0, 4, 4, 0]
      }
    }
  ]
}

// 转人工率及原因图表配置
const transferRateOption = {
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  legend: {
    data: ['AI拒答', '用户主动要求', '低置信度']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: transferReasonData.labels
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: 'AI拒答',
      type: 'bar',
      stack: 'total',
      data: transferReasonData.aiRefuse,
      itemStyle: { color: '#f5222d' }
    },
    {
      name: '用户主动要求',
      type: 'bar',
      stack: 'total',
      data: transferReasonData.userRequest,
      itemStyle: { color: '#faad14' }
    },
    {
      name: '低置信度',
      type: 'bar',
      stack: 'total',
      data: transferReasonData.lowConfidence,
      itemStyle: { color: '#722ed1' }
    }
  ]
}
</script>

<style scoped lang="scss">
.dashboard-home {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 20px;
    margin-bottom: 24px;
  }
  
  .stat-card {
    position: relative;
    overflow: hidden;
    transition: transform 0.2s;
    
    &:hover {
      transform: translateY(-4px);
    }
    
    .stat-content {
      .stat-title {
        font-size: 14px;
        color: #666;
        margin-bottom: 8px;
      }
      .stat-count {
        font-size: 28px;
        font-weight: bold;
        color: #333;
      }
      .stat-unit {
        font-size: 14px;
        color: #999;
        margin-left: 4px;
      }
    }
    
    .stat-icon {
      position: absolute;
      right: 20px;
      bottom: 20px;
      opacity: 0.6;
    }
  }

  .charts-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }

  .chart-card {
    .time-select {
      margin-left: auto;
    }
  }

  .wide-card {
    grid-column: span 2;
  }

  .chart-container {
    height: 300px;
  }

  .chart {
    width: 100%;
    height: 100%;
  }
}
</style>