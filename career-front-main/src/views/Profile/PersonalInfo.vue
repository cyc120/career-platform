<template>
  <div class="personal-info-report">
    <el-row :gutter="20" class="row-first">
      <el-col :span="16">
        <el-card class="glass-card header-card">
          <div class="user-profile">
            <el-avatar :size="70" :src="avatarUrl" class="user-avatar" />
            <div class="user-text">
              <div class="name-row">
                <h2>{{ userInfo.name || '--' }}</h2>
                <el-tag size="small" class="status-tag">分析已就绪</el-tag>
              </div>
              <p class="sub-info">
                <el-icon><School /></el-icon> {{ userInfo.school || '--' }}
                <el-divider direction="vertical" />
                <el-icon><Message /></el-icon> {{ userInfo.email || '--' }}
              </p>
            </div>
            <el-button class="re-edit-btn" @click="$emit('re-edit')">重新编辑经历</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="glass-card score-card">
          <div class="score-container">
            <span class="label">综合评分</span>
            <div class="big-score">{{ competitivenessScore }}</div>
            <el-tag size="small" class="score-tag" v-if="competitivenessScore > 0">综合竞争力评估</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="row-second">
      <el-col :span="8">
        <el-card class="glass-card detail-card">
          <template #header><div class="card-header">学习技能完整度</div></template>
          <div class="progress-box">
            <el-progress 
              type="circle" 
              :percentage="displayPercentage" 
              :width="140"
              :stroke-width="12"
              color="#70a1ff" 
            />
            <p class="chart-tip" v-if="displayPercentage > 0">简历信息覆盖率 {{ displayPercentage }}%</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="glass-card detail-card">
          <template #header><div class="card-header">核心竞争力模型</div></template>
          <div v-show="!loading" ref="radarRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="glass-card detail-card">
          <template #header><div class="card-header">技能词云</div></template>
          <div v-show="!loading" ref="wordCloudRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="row-third">
      <el-col :span="24">
        <el-card class="glass-card ai-report-card">
          <template #header>
            <div class="card-header">
              <el-icon><MagicStick /></el-icon> AI 深度诊断报告
            </div>
          </template>
<div class="report-content-grid">
  <div class="report-item" v-if="analysisReport">
    <h4>AI 深度诊断报告</h4>
    <p>{{ analysisReport }}</p>
  </div>
  <div class="report-item" v-else>
    <h4>AI 深度诊断报告</h4>
    <el-skeleton :rows="3" animated />
  </div>
</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, defineProps, defineEmits, nextTick } from 'vue'
import { School, Message, MagicStick } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { currentRadarData, dimensionDetailsRaw } from './profileState.js'
import { careerPlanApi } from '@/api/careerPlan'

const props = defineProps(['userInfo'])
const emit = defineEmits(['re-edit'])

const loading = ref(true)
const radarRef = ref(null)
const wordCloudRef = ref(null)
const competitivenessScore = ref(0)
const aiSuggestions = ref('')

let radarInstance = null
let wordCloudInstance = null

const avatarUrl = 'https://ui-avatars.com/api/?name=User&background=ebf5ff&color=70a1ff'

const DIM_NAMES = ['专业技能', '创新能力', '学习能力', '实习能力', '抗压能力', '沟通能力', '证书']
const analysisReport = ref('')
const skillRadarData = ref([0, 0, 0, 0, 0, 0, 0])
const wordCloudData = ref([])
const displayPercentage = ref(0)

const buildFromProfileData = async () => {
  const radar = currentRadarData.value
  const details = dimensionDetailsRaw.value

  // 雷达图数据直接来自画像分析
  if (radar && radar.some(v => v > 0)) {
    skillRadarData.value = [...radar]
  }

  // 综合评分 = 7维加权平均
  const weights = [0.20, 0.12, 0.15, 0.18, 0.10, 0.10, 0.15]
  let totalScore = 0, totalWeight = 0
  DIM_NAMES.forEach((dim, i) => {
    const score = details?.[dim]?.score || radar?.[i] || 0
    if (score > 0) { totalScore += score * weights[i]; totalWeight += weights[i] }
  })
  competitivenessScore.value = totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0

  // 完善度
  if (details) {
    const analyzed = Object.values(details).filter(d => d.status === '已分析').length
    displayPercentage.value = Math.round((analyzed / 7) * 100)
  }

  // 词云数据
  wordCloudData.value = DIM_NAMES.map((dim, i) => ({
    name: dim,
    value: details?.[dim]?.score || radar?.[i] || 0,
  })).filter(d => d.value > 0)

  // AI 诊断报告 — 调用 career_planner 智能体，综合画像分析输出
  try {
    const { data: wrapper } = await careerPlanApi.generate()
    const plan = wrapper?.data || wrapper
    const topJob = plan?.top_job || {}
    const trends = plan?.trends || {}
    const careerPath = plan?.career_path || {}

    const strong = DIM_NAMES.filter(d => (details?.[d]?.score || 0) >= 60)
    const weak = DIM_NAMES.filter(d => { const s = details?.[d]?.score || 0; return s > 0 && s < 40 })
    const pending = DIM_NAMES.filter(d => !details?.[d] || details[d].score === 0)

    let report = ''
    // 画像分析摘要
    if (strong.length) report += `优势维度：${strong.join('、')}。`
    if (weak.length) report += `待提升：${weak.join('、')}。`
    if (pending.length) report += `未采集：${pending.join('、')}。`
    // 职业规划信息
    if (topJob.job_name) report += `\n目标岗位：${topJob.job_name}`
    if (topJob.match_score) report += `，匹配度${Math.round(topJob.match_score * 100)}分。`
    if (trends.salary_forecast?.length) {
      const latest = trends.salary_forecast[trends.salary_forecast.length - 1]
      report += `\n薪资预测：${latest.year}年预计月薪${latest.value}k。`
    }
    if (careerPath?.suggestion) report += `\n职业建议：${careerPath.suggestion}`
    if (!report) report = '请在职能助手中提供更多个人信息以生成诊断报告。'
    analysisReport.value = report
  } catch {
    // career_planner 调用失败时，用画像数据生成基础报告
    const strong = DIM_NAMES.filter(d => (details?.[d]?.score || 0) >= 60)
    const weak = DIM_NAMES.filter(d => { const s = details?.[d]?.score || 0; return s > 0 && s < 40 })
    const pending = DIM_NAMES.filter(d => !details?.[d] || details[d].score === 0)
    let report = ''
    if (strong.length) report += `优势维度：${strong.join('、')}。`
    if (weak.length) report += `待提升：${weak.join('、')}。`
    if (pending.length) report += `未采集：${pending.join('、')}。`
    if (!report) report = '请在职能助手中提供更多个人信息以生成诊断报告。'
    analysisReport.value = report
  }

  loading.value = false
}

// 🌟 3. 补全缺失的适配函数
const handleResize = () => {
  radarInstance?.resize()
  wordCloudInstance?.resize()
}

onMounted(async () => {
  await buildFromProfileData()
  await nextTick()
  setTimeout(() => {
    initRadarChart()
    initWordCloud()
    window.addEventListener('resize', handleResize)
  }, 150)
})

// 🌟 4. 这里的销毁和注销很重要
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarInstance?.dispose()
  wordCloudInstance?.dispose()
})

const initRadarChart = () => {
  if (!radarRef.value) return
  if (radarInstance) radarInstance.dispose()
  
  // 修正：只初始化一次并赋值给变量
  radarInstance = echarts.init(radarRef.value)
  radarInstance.setOption({
    radar: {
      indicator: [
        { name: '专业技能', max: 100 },
        { name: '创新能力', max: 100 },
        { name: '学习能力', max: 100 },
        { name: '实习能力', max: 100 },
        { name: '抗压能力', max: 100 },
        { name: '沟通能力', max: 100 },
        { name: '证书', max: 100 },
      ],
      radius: '60%',
      axisName: { color: '#475569', fontWeight: 'bold', fontSize: 12 },
      axisLine: { lineStyle: { color: 'rgba(112, 161, 255, 0.5)' } },
      splitLine: { lineStyle: { color: 'rgba(112, 161, 255, 0.4)' } },
      splitArea: { areaStyle: { color: ['rgba(255, 255, 255, 0.05)', 'rgba(112, 161, 255, 0.1)'] } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: skillRadarData.value,
        areaStyle: { color: 'rgba(112, 161, 255, 0.25)' },
        lineStyle: { color: '#70a1ff', width: 2.5 },
        itemStyle: { color: '#70a1ff' }
      }]
    }]
  })
}

const initWordCloud = () => {
  if (!wordCloudRef.value) return
  if (wordCloudInstance) wordCloudInstance.dispose()

  wordCloudInstance = echarts.init(wordCloudRef.value)
  const colorPalette = ['#7dd3fc', '#a5b4fc', '#99f6e4', '#fef08a']
  const data = wordCloudData.value

  wordCloudInstance.setOption({
    series: [{
      type: 'graph', 
      layout: 'force',
      roam: true, 
      draggable: true, 
      force: { repulsion: 60, edgeLength: 40 },
      data: data.map((i, index) => ({ 
        name: i.name, 
        symbolSize: i.value, 
        itemStyle: { 
          color: colorPalette[index % colorPalette.length],
          shadowBlur: 10,
          shadowColor: 'rgba(112, 161, 255, 0.2)' 
        } 
      })),
      label: { show: true, fontSize: 12, color: '#475569', fontWeight: 'bold' }
    }]
  })
}
</script>

<style scoped lang="scss">
.personal-info-report {
  display: flex; flex-direction: column; gap: 20px; padding: 10px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.45) !important;
  backdrop-filter: blur(15px);
  border-radius: 20px;
  /* 🌟 边框改为淡蓝色 */
  border: 1px solid rgba(112, 161, 255, 0.15) !important;
  box-shadow: 0 8px 32px rgba(112, 161, 255, 0.05);
  height: 100%;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.55) !important;
    border-color: rgba(112, 161, 255, 0.3) !important;
  }

  :deep(.el-card__header) {
    border-bottom: 1px solid rgba(112, 161, 255, 0.1) !important;
  }
}

.row-first {
  .user-profile {
    display: flex; align-items: center; gap: 24px; height: 100px;
    .user-text { 
      flex: 1; 
      h2 { margin: 0; color: #1e293b; } 
      .sub-info { color: #64748b; font-size: 14px; margin-top: 5px; } 
    }
    
    /* 🌟 Tag 颜色修改 */
    :deep(.status-tag) {
      background: rgba(112, 161, 255, 0.1) !important;
      color: #70a1ff !important;
      border: 1px solid rgba(112, 161, 255, 0.2) !important;
    }

    /* 🌟 按钮颜色修改 */
    .re-edit-btn {
      margin-left: auto; background: transparent; 
      border: 1px solid rgba(112, 161, 255, 0.3); color: #70a1ff;
      &:hover { background: rgba(112, 161, 255, 0.05); }
    }
  }

  .score-card {
    .score-container {
      display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100px;
      .label { font-size: 12px; color: #94a3b8; }
      /* 🌟 分数改用淡蓝渐变 */
      .big-score { 
        font-size: 48px; font-weight: 800; 
        background: linear-gradient(135deg, #0e3378 0%, #bdc3fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1; margin: 5px 0; 
      }
      :deep(.el-tag) { background: rgba(112, 161, 255, 0.05) !important; color: #70a1ff !important; border: none; }
    }
  }
}

/* 找到对应的词云容器样式 */
/* 请找到这部分样式，并加上注释了"🌟"的两行 */
.row-second {
  .detail-card {
    height: 320px;
    /* 1. 确保卡片本身不出现滚动条 */
    overflow: hidden !important; 

    /* 2. 🌟 关键：强制覆盖 Element Plus 卡片内部容器的溢出设置 */
    :deep(.el-card__body) {
      height: 270px; 
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;    
      justify-content: center; 
      padding: 0; 
      overflow: hidden !important; /* 🌟 加上这一行，干掉内层滚动条 */
    }

    .chart-container { 
      width: 100%; 
      height: 240px; 
      flex: 1;
      /* 3. 确保 ECharts 容器也不会因为微小溢出产生滚动 */
      overflow: hidden; 
    }
  }
}

.row-third {
  .ai-report-card {
    .card-header { 
      display: flex; align-items: center; gap: 8px; font-weight: bold; color: #70a1ff; 
    }
    .report-content-grid {
      display: block; padding: 10px 0;
      .report-item {
  margin-bottom: 30px;

  h4 {
    font-size: 17px;
    font-weight: 700;
    color: #1e1b4b;
    margin-bottom: 16px;
    display: flex;
    align-items: center;

    // 增加一个小装饰条
    &::before {
      content: "";
      width: 4px;
      height: 18px;
      background: #6366f1;
      margin-right: 10px;
      border-radius: 2px;
    }
  }

  p {
    font-size: 14px;
    line-height: 1.8;
    color: #475569;
    margin-bottom: 12px; // 段落之间的间距
    text-align: justify; // 保证边缘整齐
    
    // 如果不想要缩进，可以删掉下面这行
    text-indent: 0; 
  }
}
    }
  }
}
</style>