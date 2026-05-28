<template>
  <div class="personal-info-report">
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

    <template v-else>
      <section class="diagnosis-hero">
        <div class="hero-copy">
          <div class="eyebrow">
            <el-icon><MagicStick /></el-icon>
            AI 深度诊断报告
          </div>
          <h2>{{ userInfo.name || '我的职业画像' }}</h2>
          <div class="profile-line">
            <span><el-icon><School /></el-icon>{{ userInfo.school || '学校待补充' }}</span>
            <span><el-icon><Message /></el-icon>{{ userInfo.email || '邮箱待补充' }}</span>
          </div>
          <div class="hero-actions">
            <el-button class="soft-btn" :icon="Refresh" :loading="loading" @click="refreshDiagnosis">
              重新诊断
            </el-button>
            <el-button class="re-edit-btn" @click="$emit('re-edit')">编辑经历</el-button>
          </div>
        </div>

        <div class="score-orbit" :style="{ '--score-percent': `${competitivenessScore}%` }">
          <div class="score-ring">
            <span class="score-number">{{ competitivenessScore }}</span>
            <span class="score-label">综合评定</span>
          </div>
          <el-tag size="small" class="score-tag" v-if="competitivenessScore > 0">{{ scoreLevel }}</el-tag>
        </div>

        <div class="hero-metrics">
          <div class="metric-item">
            <span class="metric-label">画像完整度</span>
            <strong>{{ displayPercentage }}%</strong>
          </div>
          <div class="metric-item">
            <span class="metric-label">优势维度</span>
            <strong>{{ strongestDimension.name }}</strong>
          </div>
          <div class="metric-item">
            <span class="metric-label">优先提升</span>
            <strong>{{ weakestDimension.name }}</strong>
          </div>
        </div>
      </section>

      <section class="diagnosis-grid">
        <div class="glass-panel dimension-panel">
          <div class="section-heading">
            <span><el-icon><DataAnalysis /></el-icon>能力维度扫描</span>
            <em>{{ analyzedCount }}/7 已分析</em>
          </div>
          <div class="dimension-list">
            <button
              v-for="(dim, idx) in dimensionCards"
              :key="dim.name"
              :class="['dimension-chip', { active: selectedDimensionIndex === idx }]"
              @click="selectDimension(idx)"
            >
              <span class="chip-top">
                <span>{{ dim.name }}</span>
                <strong>{{ dim.score }}</strong>
              </span>
              <span class="chip-bar"><i :style="{ width: `${dim.score}%` }"></i></span>
              <small>{{ dim.status }}</small>
            </button>
          </div>
        </div>

        <div class="glass-panel focus-panel">
          <div class="section-heading">
            <span><el-icon><Aim /></el-icon>{{ selectedDimension.name }}</span>
            <em :class="selectedDimension.levelClass">{{ selectedDimension.level }}</em>
          </div>
          <div class="focus-score">
            <strong>{{ selectedDimension.score }}</strong>
            <span>分</span>
          </div>
          <p>{{ selectedDimension.desc }}</p>
          <div class="focus-tags">
            <span v-for="tag in selectedDimension.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
      </section>

      <section class="chart-gallery">
        <div class="glass-panel chart-card">
          <div class="section-heading"><span>学习技能完整度</span></div>
          <div v-show="!loading" ref="completenessRef" class="chart-container"></div>
        </div>

        <div class="glass-panel chart-card featured-chart">
          <div class="section-heading"><span>核心竞争力模型</span></div>
          <div v-show="!loading" ref="radarRef" class="chart-container"></div>
        </div>

        <div class="glass-panel chart-card">
          <div class="section-heading"><span>技能关键词</span></div>
          <div v-if="!loading && wordCloudData.length >= 3" ref="wordCloudRef" class="chart-container"></div>
          <div v-else-if="!loading" class="cloud-empty">
            <span class="cloud-empty-icon">+</span>
            <span>继续补充经历后生成</span>
          </div>
        </div>
      </section>

      <section class="glass-panel ai-report-card">
        <div class="section-heading">
          <span><el-icon><MagicStick /></el-icon>诊断结论</span>
        </div>
        <div v-if="analysisReport" class="report-content-grid">
          <p v-for="(paragraph, idx) in reportParagraphs" :key="idx">{{ paragraph }}</p>
        </div>
        <el-skeleton v-else :rows="4" animated />
      </section>
    </template>
  </div>
</template>

<script>
// 模块级缓存 — SPA 内组件销毁重建时保留，页面刷新时重置
let _cachedHash = ''
let _cachedResults = null
</script>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { School, Message, MagicStick, Refresh, DataAnalysis, Aim } from '@element-plus/icons-vue'
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
  reportStatus.value = 'ready'
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
const selectedDimensionIndex = ref(0)

const analyzedCount = computed(() => {
  const details = dimensionDetailsRaw.value || {}
  return DIM_NAMES.filter((dim, idx) => {
    const score = details?.[dim]?.score || skillRadarData.value[idx] || 0
    return score > 0 && details?.[dim]?.status === '已分析'
  }).length
})

const getDimensionLevel = (score) => {
  if (score >= 85) return { text: '突出优势', className: 'excellent' }
  if (score >= 70) return { text: '稳定优势', className: 'good' }
  if (score >= 50) return { text: '可塑空间', className: 'normal' }
  if (score > 0) return { text: '优先补强', className: 'weak' }
  return { text: '待补充', className: 'pending' }
}

const extractTags = (text = '') => {
  const words = text.split(/[,，、\s;；。]+/)
    .map(item => item.replace(/[。.（）()：:]/g, '').trim())
    .filter(item => item.length >= 2 && item.length <= 8)
  return [...new Set(words)].slice(0, 4)
}

const dimensionCards = computed(() => {
  const details = dimensionDetailsRaw.value || {}
  return DIM_NAMES.map((name, idx) => {
    const detail = details?.[name] || {}
    const score = detail.score || skillRadarData.value[idx] || 0
    const level = getDimensionLevel(score)
    const desc = detail.desc && detail.desc !== '暂无相关信息'
      ? detail.desc
      : score > 0 ? '该维度已有基础，可结合项目经历继续沉淀可展示成果。' : '当前信息不足，建议补充相关经历、成果或证明材料。'
    return {
      name,
      score,
      status: detail.status || (score > 0 ? '已分析' : '待补充'),
      desc,
      level: level.text,
      levelClass: level.className,
      tags: extractTags(desc).length ? extractTags(desc) : [level.text],
    }
  })
})

const selectedDimension = computed(() => dimensionCards.value[selectedDimensionIndex.value] || dimensionCards.value[0] || {
  name: '能力维度',
  score: 0,
  desc: '暂无画像数据',
  level: '待补充',
  levelClass: 'pending',
  tags: ['待补充'],
})

const scoredDimensions = computed(() => dimensionCards.value.filter(item => item.score > 0))
const strongestDimension = computed(() => scoredDimensions.value.slice().sort((a, b) => b.score - a.score)[0] || { name: '--', score: 0 })
const weakestDimension = computed(() => scoredDimensions.value.slice().sort((a, b) => a.score - b.score)[0] || { name: '--', score: 0 })
const reportParagraphs = computed(() => {
  if (!analysisReport.value) return []
  return analysisReport.value
    .split(/(?<=[。！？!?])\s*/)
    .map(item => item.trim())
    .filter(Boolean)
})

const selectDimension = (idx) => {
  selectedDimensionIndex.value = idx
}

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

const refreshDiagnosis = async () => {
  loading.value = true
  reportStatus.value = 'updating'
  startLoadingAnimation()
  await buildFromProfileData(true)
  stopLoadingAnimation()
  await nextTick()
  initRadarChart()
  initCompletenessChart()
  initWordCloud()
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
    reportStatus.value = 'ready'
    await nextTick()
    initRadarChart()
    initCompletenessChart()
    initWordCloud()
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
  stopLoadingAnimation()
  await nextTick()
  initRadarChart()
  initCompletenessChart()
  initWordCloud()
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
      radius: '56%',
      axisName: { color: '#475569', fontWeight: 'bold', fontSize: 12 },
      axisLine: { lineStyle: { color: 'rgba(80, 152, 249, 0.42)' } },
      splitLine: { lineStyle: { color: 'rgba(80, 152, 249, 0.28)' } },
      splitArea: { areaStyle: { color: ['rgba(255, 255, 255, 0.06)', 'rgba(80, 152, 249, 0.08)'] } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: skillRadarData.value,
        areaStyle: { color: 'rgba(80, 152, 249, 0.22)' },
        lineStyle: { color: '#5098f9', width: 2.5 },
        itemStyle: { color: '#5098f9' }
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
    grid: { left: 72, right: 34, top: 8, bottom: 8, containLabel: false },
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
            { offset: 0, color: '#a1c4fd' },
            { offset: 1, color: '#5098f9' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
      })),
      barWidth: 16,
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
    'rgba(80, 152, 249, 0.82)', 'rgba(161, 196, 253, 0.84)',
    'rgba(107, 208, 137, 0.78)', 'rgba(232, 158, 90, 0.72)',
    'rgba(194, 233, 251, 0.82)', 'rgba(252, 211, 126, 0.72)',
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
        symbolSize: Math.min(Math.max(item.name.length * 12 + 18, 30), 86),
        itemStyle: {
          color: colorPalette[index % colorPalette.length],
          shadowBlur: 15,
          shadowColor: 'rgba(80, 152, 249, 0.26)',
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
  flex: 1;
  min-height: 400px;
  border-radius: 20px;
  overflow: hidden;
}

.personal-info-report {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 10px;
  position: relative;
  color: #172033;
  overflow-x: hidden;

  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }
}

.glass-panel,
.diagnosis-hero {
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.62), rgba(245, 252, 255, 0.24) 42%, rgba(236, 248, 255, 0.42)),
    radial-gradient(circle at 18% 8%, rgba(255, 255, 255, 0.86), transparent 30%),
    radial-gradient(circle at 86% 18%, rgba(80, 152, 249, 0.18), transparent 32%),
    radial-gradient(circle at 70% 92%, rgba(107, 208, 137, 0.12), transparent 28%);
  border: 1px solid rgba(255, 255, 255, 0.58);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.82),
    inset 0 -18px 36px rgba(255, 255, 255, 0.18),
    0 18px 46px rgba(80, 152, 249, 0.08),
    0 2px 10px rgba(15, 23, 42, 0.04);
  backdrop-filter: blur(24px) saturate(1.35);
  -webkit-backdrop-filter: blur(24px) saturate(1.35);
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    inset: 1px;
    border-radius: inherit;
    pointer-events: none;
    background:
      linear-gradient(135deg, rgba(255,255,255,0.68), transparent 38%),
      linear-gradient(315deg, rgba(255,255,255,0.32), transparent 34%);
    opacity: 0.82;
  }

  &::after {
    content: "";
    position: absolute;
    width: 180px;
    height: 180px;
    right: -72px;
    top: -86px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.34);
    filter: blur(2px);
    pointer-events: none;
  }

  > * {
    position: relative;
    z-index: 1;
  }
}

.diagnosis-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(150px, 190px) minmax(210px, 0.8fr);
  gap: 18px;
  align-items: center;
  border-radius: 28px;
  padding: 24px;

  .hero-copy {
    min-width: 0;
  }

  .eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 11px;
    border-radius: 999px;
    color: #5098f9;
    background: rgba(80, 152, 249, 0.1);
    font-size: 12px;
    font-weight: 700;
  }

  h2 {
    margin: 16px 0 10px;
    font-size: 28px;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: 0;
    color: #0f172a;
    word-break: break-word;
  }

  .profile-line {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    color: #64748b;
    font-size: 13px;

    span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }
  }

  .hero-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 22px;
  }

  .soft-btn,
  .re-edit-btn {
    border-radius: 12px;
    font-weight: 700;
    min-width: 96px;
  }

  .soft-btn {
    border: 0;
    color: #fff;
    background: linear-gradient(135deg, #a1c4fd 0%, #5098f9 100%);
    box-shadow: 0 10px 24px rgba(80, 152, 249, 0.22);
  }

  .re-edit-btn {
    border-color: rgba(80, 152, 249, 0.22);
    color: #5098f9;
    background: rgba(255, 255, 255, 0.65);
  }
}

.score-orbit {
  justify-self: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;

  .score-ring {
    width: clamp(132px, 13vw, 158px);
    aspect-ratio: 1;
    border-radius: 50%;
    display: grid;
    place-items: center;
    align-content: center;
    background:
      radial-gradient(circle at 36% 26%, rgba(255,255,255,0.95) 0 11%, transparent 12%),
      radial-gradient(circle at center, rgba(255,255,255,0.9) 0 57%, transparent 58%),
      conic-gradient(#5098f9 0 var(--score-percent), rgba(107, 208, 137, 0.42) var(--score-percent) 100%);
    box-shadow:
      inset 0 10px 22px rgba(255,255,255,0.72),
      inset 0 -12px 28px rgba(80, 152, 249, 0.08),
      0 14px 35px rgba(80, 152, 249, 0.14);
  }

  .score-number {
    font-size: clamp(34px, 3.6vw, 42px);
    font-weight: 900;
    line-height: 1;
    color: #0f172a;
  }

  .score-label {
    margin-top: 6px;
    font-size: 12px;
    font-weight: 700;
    color: #64748b;
  }

  .score-tag {
    border: 0;
    color: #52b970;
    background: rgba(107, 208, 137, 0.14);
  }
}

.hero-metrics {
  display: grid;
  gap: 10px;

  .metric-item {
    min-height: 58px;
    padding: 11px 13px;
    border-radius: 18px 14px 18px 14px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0.22));
    border: 1px solid rgba(255, 255, 255, 0.52);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.76);
    transition: transform 0.2s ease, border-color 0.2s ease;

    &:hover {
      transform: translateX(2px);
      border-color: rgba(80, 152, 249, 0.24);
    }
  }

  .metric-label {
    display: block;
    margin-bottom: 6px;
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
  }

  strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #0f172a;
    font-size: 17px;
    font-weight: 800;
  }
}

.diagnosis-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(260px, 0.75fr);
  gap: 16px;
}

.glass-panel {
  border-radius: 24px;
  padding: 18px;
  min-width: 0;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  color: #0f172a;
  font-size: 15px;
  font-weight: 800;

  span {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  em {
    flex-shrink: 0;
    font-style: normal;
    color: #64748b;
    font-size: 12px;
    font-weight: 700;

    &.excellent { color: #6bd089; }
    &.good { color: #5098f9; }
    &.normal { color: #e89e5a; }
    &.weak { color: #dc2626; }
    &.pending { color: #64748b; }
  }
}

.dimension-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(122px, 1fr));
  gap: 9px;
}

.dimension-chip {
  min-width: 0;
  min-height: 88px;
  padding: 11px;
  border: 1px solid rgba(255, 255, 255, 0.52);
  border-radius: 19px 15px 19px 15px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.56), rgba(255, 255, 255, 0.2)),
    radial-gradient(circle at 22% 0%, rgba(255,255,255,0.62), transparent 34%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
  cursor: pointer;
  text-align: left;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    border-color: rgba(80, 152, 249, 0.26);
    box-shadow: 0 10px 22px rgba(30, 41, 59, 0.07);
  }

  &.active {
    background:
      linear-gradient(145deg, rgba(232, 245, 255, 0.72), rgba(236, 253, 245, 0.44)),
      radial-gradient(circle at 18% 8%, rgba(255,255,255,0.74), transparent 34%);
    border-color: rgba(80, 152, 249, 0.32);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.8), 0 12px 26px rgba(80, 152, 249, 0.1);
  }

  .chip-top {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    color: #1e293b;
    font-size: 13px;
    font-weight: 800;

    span {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  strong {
    color: #5098f9;
  }

  .chip-bar {
    display: block;
    height: 6px;
    margin: 13px 0 9px;
    border-radius: 999px;
    background: rgba(226, 232, 240, 0.9);
    overflow: hidden;

    i {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #a1c4fd, #5098f9);
    }
  }

  small {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
  }
}

.focus-panel {
  min-height: 0;

  .focus-score {
    display: flex;
    align-items: baseline;
    gap: 5px;
    margin-bottom: 8px;

    strong {
      font-size: 42px;
      line-height: 1;
      color: #0f172a;
    }

    span {
      color: #64748b;
      font-weight: 700;
    }
  }

  p {
    max-height: 92px;
    margin: 0 0 14px;
    color: #475569;
    font-size: 13px;
    line-height: 1.7;
    overflow: auto;
  }

  .focus-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    span {
      padding: 6px 9px;
      border-radius: 999px;
      color: #5098f9;
      background: rgba(80, 152, 249, 0.1);
      font-size: 12px;
      font-weight: 700;
    }
  }
}

.chart-gallery {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.chart-card {
  height: 306px;
  min-width: 0;
  overflow: hidden;

  &.featured-chart {
    background:
      linear-gradient(135deg, rgba(255,255,255,0.84), rgba(235, 245, 255, 0.55));
  }

  .chart-container {
    width: 100%;
    height: 236px;
    max-width: 100%;
    overflow: hidden;
  }

  .cloud-empty {
    height: 240px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: #64748b;
    font-size: 13px;
    font-weight: 700;
  }

  .cloud-empty-icon {
    width: 38px;
    height: 38px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    color: #5098f9;
    background: rgba(80, 152, 249, 0.1);
    font-size: 24px;
  }
}

.ai-report-card {
  .report-content-grid {
    display: grid;
    gap: 12px;
  }

  p {
    margin: 0;
    padding: 14px 15px;
    border-radius: 18px 14px 18px 14px;
    color: #334155;
    background: linear-gradient(135deg, rgba(255,255,255,0.54), rgba(255,255,255,0.24));
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-left: 4px solid rgba(80, 152, 249, 0.42);
    font-size: 14px;
    line-height: 1.85;
    text-align: justify;
  }
}

@media (max-width: 1180px) {
  .diagnosis-hero {
    grid-template-columns: minmax(0, 1fr) 170px;
  }

  .hero-metrics {
    grid-column: 1 / -1;
    grid-template-columns: repeat(3, 1fr);
  }

  .dimension-list {
    grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  }

  .chart-gallery {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 820px) {
  .diagnosis-hero,
  .diagnosis-grid {
    grid-template-columns: 1fr;
  }

  .score-orbit {
    justify-self: start;
  }

  .hero-metrics,
  .dimension-list {
    grid-template-columns: 1fr;
  }

  .dimension-chip {
    min-height: 82px;
  }

  .chart-gallery {
    grid-template-columns: 1fr;
  }

  .chart-card {
    height: 292px;
  }
}
</style>
