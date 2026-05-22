<template>
  <div class="personal-info-report">
    <Transition name="status-fade">
      <div v-if="reportStatus !== 'ready'" class="report-status-overlay">
        <div class="status-card">
          <div class="status-spinner"></div>
          <p class="status-text">{{ reportStatus === 'loading' ? '你的报告正在生成，请稍等' : '你的报告正在优化，请稍后' }}</p>
        </div>
      </div>
    </Transition>

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
            <span class="label">综合评定</span>
            <div class="big-score">{{ competitivenessScore }}</div>
            <el-tag size="small" class="score-tag" v-if="competitivenessScore > 0">{{ scoreLevel }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="row-second">
      <el-col :span="8">
        <el-card class="glass-card detail-card">
          <template #header><div class="card-header">学习技能完整度</div></template>
          <div v-show="!loading" ref="completenessRef" class="chart-container"></div>
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

<script>
// 模块级缓存 — SPA 内组件销毁重建时保留，页面刷新时重置
let _cachedHash = ''
let _cachedResults = null
</script>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { School, Message, MagicStick } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { currentRadarData, dimensionDetailsRaw } from './profileState.js'
import { diagnosisApi } from '@/api/diagnosis'

const props = defineProps(['userInfo'])
const emit = defineEmits(['re-edit'])

// 组件创建时检查缓存
const _hashNow = JSON.stringify(currentRadarData.value || []) + JSON.stringify(dimensionDetailsRaw.value || {})
const _cacheHit = !!(_cachedResults && _cachedHash === _hashNow)

const reportStatus = ref(_cacheHit ? 'ready' : 'loading')
const loading = ref(!_cacheHit)
const radarRef = ref(null)
const wordCloudRef = ref(null)
const completenessRef = ref(null)
const competitivenessScore = ref(0)
const aiSuggestions = ref('')

// 综合评定等级
const scoreLevel = computed(() => {
  const s = competitivenessScore.value
  if (s >= 75) return '优秀'
  if (s >= 65) return '良好'
  if (s >= 55) return '中等'
  if (s >= 45) return '不错'
  if (s > 0) return '需要进步'
  return ''
})

let radarInstance = null
let wordCloudInstance = null
let completenessInstance = null

const avatarUrl = 'https://ui-avatars.com/api/?name=User&background=ebf5ff&color=70a1ff'

const DIM_NAMES = ['专业技能', '创新能力', '学习能力', '实习能力', '抗压能力', '沟通能力', '证书']
const analysisReport = ref('')
const skillRadarData = ref([0, 0, 0, 0, 0, 0, 0])
const wordCloudData = ref([])
const displayPercentage = ref(0)

const computeHash = () => {
  const r = currentRadarData.value || []
  const d = dimensionDetailsRaw.value || {}
  return JSON.stringify(r) + JSON.stringify(d)
}

const applyCached = (cache) => {
  analysisReport.value = cache.analysisReport
  skillRadarData.value = [...cache.skillRadarData]
  competitivenessScore.value = cache.competitivenessScore
  wordCloudData.value = [...cache.wordCloudData]
  displayPercentage.value = cache.displayPercentage
}

const buildFromProfileData = async (forceApi = false) => {
  const radar = currentRadarData.value
  const details = dimensionDetailsRaw.value
  const hash = computeHash()

  // 缓存命中且非强制刷新 → 直接复用
  if (!forceApi && _cachedResults && _cachedHash === hash) {
    applyCached(_cachedResults)
    loading.value = false
    reportStatus.value = 'ready'
    return
  }

  // 雷达图数据直接来自画像分析
  if (radar && radar.some(v => v > 0)) {
    skillRadarData.value = [...radar]
  }

  // 综合评分 = 7维加权平均
  const weights = [0.18, 0.15, 0.18, 0.16, 0.10, 0.10, 0.13]
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

  // 词云数据 — 从已分析维度中提取核心技能描述
  const GENERIC_WORDS = new Set([
    '创新能力', '学习能力', '专业技能', '实习能力', '抗压能力', '沟通能力', '证书',
    '暂无信息', '暂无相关信息', '根据关联维度推断', '未提及',
    '能力', '经验', '经历', '基础', '一定', '较好', '较强', '丰富',
    '已分析', '待补充', '有', '的', '和', '等', '较', '有基础',
  ])
  const cloudItems = []
  DIM_NAMES.forEach((dim, i) => {
    const d = details?.[dim]
    const score = d?.score || radar?.[i] || 0
    if (!d || d.status !== '已分析' || score === 0) return
    const desc = d.desc || ''
    // 从描述中提取关键词，过滤套话
    if (desc && !GENERIC_WORDS.has(desc)) {
      const keywords = desc.split(/[,，、\s]+/).filter(k =>
        k.length >= 2 && k.length <= 10 && !GENERIC_WORDS.has(k)
      )
      keywords.forEach(k => cloudItems.push({ name: k, value: score }))
    }
  })
  wordCloudData.value = cloudItems

  // AI 诊断报告 — 调用 diagnosis 智能体，生成300-400字深度分析
  try {
    const { data: res } = await diagnosisApi.generate({
      radar_data: skillRadarData.value,
      dimension_details: details || {},
    })
    analysisReport.value = res?.report || res?.data?.report || ''
    if (!analysisReport.value) throw new Error('Empty report')
  } catch (e) {
    console.warn('[Diagnosis] API failed, using fallback:', e?.message)
    const analyzed = DIM_NAMES.filter(d => details?.[d]?.status === '已分析')
    const strong = DIM_NAMES.filter(d => (details?.[d]?.score || 0) >= 60)
    const weak = DIM_NAMES.filter(d => { const s = details?.[d]?.score || 0; return s > 0 && s < 40 })
    const pending = DIM_NAMES.filter(d => !details?.[d] || details[d].score === 0)
    let report = ''
    if (analyzed.length) {
      report += '根据画像分析，'
      if (strong.length) report += `你在${strong.join('、')}方面表现突出。`
      if (weak.length) report += `${weak.join('、')}方面仍有提升空间。`
      analyzed.forEach(d => {
        const desc = details[d].desc
        if (desc && desc !== '暂无信息' && desc !== '暂无相关信息' && desc !== '根据关联维度推断') {
          report += `${d}方面${desc}。`
        }
      })
    }
    if (pending.length) report += `尚未采集${pending.join('、')}相关信息。`
    if (!report) report = '请在职能助手中提供更多个人信息以生成诊断报告。'
    analysisReport.value = report
  }

  // 写入模块级缓存
  _cachedHash = hash
  _cachedResults = {
    analysisReport: analysisReport.value,
    skillRadarData: [...skillRadarData.value],
    competitivenessScore: competitivenessScore.value,
    wordCloudData: [...wordCloudData.value],
    displayPercentage: displayPercentage.value,
  }
  loading.value = false
}

// 🌟 3. 补全缺失的适配函数
const handleResize = () => {
  radarInstance?.resize()
  wordCloudInstance?.resize()
  completenessInstance?.resize()
}

// 监听画像数据变化 — 仅当数据真正改变时才重新分析
watch([currentRadarData, dimensionDetailsRaw], async () => {
  const hash = computeHash()
  if (hash === _cachedHash) return // 数据未变，跳过
  if (reportStatus.value === 'ready') {
    reportStatus.value = 'updating'
    await buildFromProfileData(true)
    await nextTick()
    initRadarChart()
    initCompletenessChart()
    initWordCloud()
    setTimeout(() => { reportStatus.value = 'ready' }, 1500)
  }
}, { deep: true })

onMounted(async () => {
  window.addEventListener('resize', handleResize)

  // 检查模块级缓存
  if (_cachedResults && _cachedHash === computeHash()) {
    applyCached(_cachedResults)
    loading.value = false
    reportStatus.value = 'ready'
    await nextTick()
    initRadarChart()
    initCompletenessChart()
    initWordCloud()
    return
  }

  // 首次加载 → 展示加载动画
  const startTime = Date.now()
  const MIN_DISPLAY = 2000

  await buildFromProfileData()
  await nextTick()
  setTimeout(() => {
    initRadarChart()
    initCompletenessChart()
    initWordCloud()
  }, 150)

  const elapsed = Date.now() - startTime
  if (elapsed < MIN_DISPLAY) {
    await new Promise(r => setTimeout(r, MIN_DISPLAY - elapsed))
  }
  reportStatus.value = 'ready'
})

// 🌟 4. 这里的销毁和注销很重要
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarInstance?.dispose()
  wordCloudInstance?.dispose()
  completenessInstance?.dispose()
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

const initCompletenessChart = () => {
  if (!completenessRef.value) return
  if (completenessInstance) completenessInstance.dispose()

  completenessInstance = echarts.init(completenessRef.value)
  const scores = skillRadarData.value

  completenessInstance.setOption({
    grid: { left: 80, right: 30, top: 10, bottom: 10 },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { show: false },
      axisLine: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'category',
      data: DIM_NAMES,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#475569', fontSize: 12, fontWeight: 'bold' },
    },
    series: [{
      type: 'bar',
      data: scores.map((v) => ({
        value: v,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#70a1ff' },
            { offset: 1, color: '#a5b4fc' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
      })),
      barWidth: 18,
      label: {
        show: true,
        position: 'right',
        formatter: '{c}分',
        color: '#475569',
        fontSize: 12,
      },
    }],
  })
}

const initWordCloud = () => {
  if (!wordCloudRef.value) return
  if (wordCloudInstance) wordCloudInstance.dispose()

  wordCloudInstance = echarts.init(wordCloudRef.value)
  const data = wordCloudData.value
  if (!data.length) return

  const colorPalette = [
    'rgba(112, 161, 255, 0.85)', 'rgba(165, 180, 252, 0.85)',
    'rgba(153, 246, 228, 0.85)', 'rgba(254, 240, 138, 0.85)',
    'rgba(125, 211, 252, 0.85)', 'rgba(196, 181, 253, 0.85)',
  ]

  wordCloudInstance.setOption({
    series: [{
      type: 'graph',
      layout: 'force',
      roam: false,
      draggable: true,
      force: { repulsion: 120, edgeLength: 30, gravity: 0.1 },
      data: data.map((item, index) => ({
        name: item.name,
        symbolSize: Math.max(item.name.length * 14 + 20, 30),
        itemStyle: {
          color: colorPalette[index % colorPalette.length],
          shadowBlur: 15,
          shadowColor: 'rgba(112, 161, 255, 0.3)',
          borderColor: 'rgba(255,255,255,0.6)',
          borderWidth: 2,
        },
      })),
      label: {
        show: true,
        fontSize: 11,
        color: '#1e293b',
        fontWeight: 'bold',
        formatter: '{b}',
      },
    }],
  })
}
</script>

<style scoped lang="scss">
.report-status-overlay {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(246, 248, 255, 0.85);
  backdrop-filter: blur(12px);

  .status-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    padding: 48px 64px;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 24px;
    border: 1px solid rgba(112, 161, 255, 0.15);
    box-shadow: 0 16px 48px rgba(112, 161, 255, 0.08);
  }

  .status-spinner {
    width: 40px; height: 40px;
    border: 3px solid rgba(112, 161, 255, 0.15);
    border-top-color: #70a1ff;
    border-radius: 50%;
    animation: statusSpin 0.8s linear infinite;
  }

  .status-text {
    font-size: 16px;
    font-weight: 600;
    color: #3c4e68;
    letter-spacing: 0.5px;
    margin: 0;
  }
}

@keyframes statusSpin { to { transform: rotate(360deg); } }

.status-fade-enter-active,
.status-fade-leave-active { transition: opacity 0.4s ease; }
.status-fade-enter-from,
.status-fade-leave-to { opacity: 0; }

.personal-info-report {
  display: flex; flex-direction: column; gap: 20px; padding: 10px;
  position: relative;
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