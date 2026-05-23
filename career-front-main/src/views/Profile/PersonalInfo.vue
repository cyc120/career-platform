<template>
  <div class="personal-info-report">
    <transition name="loading-fade">
      <div v-if="reportStatus !== 'ready'" class="custom-loading-overlay">
        <InteractiveLoading
          title="AI 深度诊断中"
          description="正在融合画像数据与诊断模型，生成个性化分析报告"
          statusText="Career Pilot 诊断引擎运行中"
          :steps="loadingSteps"
          :currentStep="currentLoadingStep"
          :progress="loadingProgress"
          :showProgress="true"
          :orbLabels="['技能', '创新', '学习', '实习', '抗压', '沟通', '证书']"
        />
      </div>
    </transition>

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
          <div v-if="!loading && wordCloudData.length >= 3" ref="wordCloudRef" class="chart-container"></div>
          <div v-else-if="!loading" class="cloud-empty">
            <span class="cloud-empty-icon">💡</span>
            <span>技能有待提升哦</span>
          </div>
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
import InteractiveLoading from '@/components/InteractiveLoading.vue'

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

// InteractiveLoading 动画状态
const loadingSteps = ['加载画像数据', '计算能力模型', '生成词云分析', 'AI 深度诊断']
const currentLoadingStep = ref(0)
const loadingProgress = ref(0)
let loadingTimer = null
let progressTimer = null

const startLoadingAnimation = () => {
  currentLoadingStep.value = 0
  loadingProgress.value = 0
  const stepTexts = ['正在加载画像数据...', '正在计算能力模型...', '正在生成词云分析...', '正在调用 AI 诊断...']
  loadingTimer = setInterval(() => {
    if (currentLoadingStep.value < loadingSteps.length - 1) {
      currentLoadingStep.value++
    }
  }, 1200)
  progressTimer = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.random() * 12
    }
  }, 400)
}

const stopLoadingAnimation = () => {
  loadingProgress.value = 100
  currentLoadingStep.value = loadingSteps.length
  clearInterval(loadingTimer)
  clearInterval(progressTimer)
  setTimeout(() => {
    reportStatus.value = 'ready'
  }, 300)
}

// 综合评定等级
const scoreLevel = computed(() => {
  const s = competitivenessScore.value
  if (s >= 80) return '优秀'
  if (s >= 68) return '良好'
  if (s >= 55) return '中等'
  if (s >= 42) return '不错'
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

  // 词云数据 — 只提取具体的技能/特长/成果关键词，不显示维度套话
  const GENERIC_WORDS = new Set([
    '创新能力', '学习能力', '专业技能', '实习能力', '抗压能力', '沟通能力', '证书',
    '暂无信息', '暂无相关信息', '根据关联维度推断', '未提及',
    '能力', '基础', '一定', '较好', '较强', '丰富',
    '已分析', '待补充', '有', '的', '和', '等', '较', '有基础',
    '方面', '方面表现', '掌握', '熟悉', '了解', '使用', '进行',
    '技术栈', '创新力', '学习力', '实战力', '抗压力', '沟通力', '资质',
    '突出', '扎实', '优秀', '良好', '一般', '项目经验', '实习经验',
  ])
  const cloudItems = []
  const seen = new Set()
  DIM_NAMES.forEach((dim, i) => {
    const d = details?.[dim]
    const score = d?.score || radar?.[i] || 0
    if (!d || d.status !== '已分析' || score === 0) return
    const desc = d.desc || ''
    if (desc && !GENERIC_WORDS.has(desc)) {
      const keywords = desc.split(/[,，、\s;；。、]+/).filter(k => {
        const clean = k.replace(/[。.（）()：:]/g, '').trim()
        return clean.length >= 2 && clean.length <= 10
          && !GENERIC_WORDS.has(clean) && !seen.has(clean)
      })
      keywords.forEach(k => {
        const clean = k.replace(/[。.（）()：:]/g, '').trim()
        if (clean && !seen.has(clean)) {
          seen.add(clean)
          cloudItems.push({ name: clean, value: score })
        }
      })
    }
  })
  // 按分数排序，取前8个最突出的
  cloudItems.sort((a, b) => b.value - a.value)
  wordCloudData.value = cloudItems.slice(0, 8)

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
    const allScores = DIM_NAMES.map(d => details?.[d]?.score || 0).filter(s => s > 0)
    const avg = allScores.length ? Math.round(allScores.reduce((a, b) => a + b, 0) / allScores.length) : 0
    let report = ''
    if (analyzed.length) {
      report += `整体竞争力${avg >= 65 ? '较强' : avg >= 50 ? '中等' : '有待提升'}，已分析${analyzed.length}个维度。`
      if (strong.length) {
        const strongDescs = strong.map(d => {
          const desc = details[d]?.desc || ''
          return desc && desc !== '暂无相关信息' && desc !== '根据关联维度推断' ? `${d}（${desc}）` : d
        })
        report += `优势集中在${strongDescs.join('、')}。`
      }
      if (weak.length) report += `${weak.join('、')}方面仍有提升空间。`
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
  startLoadingAnimation()

  await buildFromProfileData()
  await nextTick()
  setTimeout(() => {
    initRadarChart()
    initCompletenessChart()
    initWordCloud()
  }, 150)

  stopLoadingAnimation()
})

// 🌟 4. 这里的销毁和注销很重要
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarInstance?.dispose()
  wordCloudInstance?.dispose()
  completenessInstance?.dispose()
  clearInterval(loadingTimer)
  clearInterval(progressTimer)
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
.custom-loading-overlay {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(246, 248, 255, 0.85);
  backdrop-filter: blur(12px);
  border-radius: 20px;
}

.loading-fade-enter-active,
.loading-fade-leave-active { transition: opacity 0.5s ease; }
.loading-fade-enter-from,
.loading-fade-leave-to { opacity: 0; }

.personal-info-report {
  display: flex; flex-direction: column; gap: 20px; padding: 10px;
  position: relative;
}

.glass-card {
  background: rgba(255, 255, 255, 0.4) !important;
  backdrop-filter: blur(20px) saturate(1.1);
  -webkit-backdrop-filter: blur(20px) saturate(1.1);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.45) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  height: 100%;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.07);
  }

  :deep(.el-card__header) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.3) !important;
    background: rgba(255, 255, 255, 0.2);
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
      overflow: hidden;
    }

    .cloud-empty {
      width: 100%;
      height: 240px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: #94a3b8;
      font-size: 14px;
      .cloud-empty-icon { font-size: 28px; }
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