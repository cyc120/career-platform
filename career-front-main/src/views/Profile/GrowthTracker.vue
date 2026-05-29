<template>
  <div class="growth-tracking-center fade-in">
    <!-- 顶部标题卡片 -->
    <div class="action-bar">
      <div class="action-left">
        <h2 class="page-title">
          <el-icon><TrendCharts /></el-icon>
          成长追踪中心
        </h2>
        <p class="page-desc">AI 驱动的个性化学习计划，助你稳步成长</p>
      </div>
    </div>

    <!-- 加载状态 - 与人岗匹配一致 -->
    <div v-if="pageLoading" class="loading-section">
      <InteractiveLoading
        title="分析中"
        description="正在融合多维数据，为你生成个性化学习计划"
        statusText="职能助手引擎运行中"
        :steps="loadingSteps"
        :currentStep="currentLoadingStep"
        :progress="loadingProgress"
        :showProgress="true"
        :orbLabels="['技能', '创新', '学习', '实习', '抗压', '沟通', '证书', '岗位']"
      />
    </div>

    <template v-else>
    <div class="agent-command-bar glass-card">
      <div class="agent-info">
        <div class="agent-avatar">
          <el-icon class="pulse-icon"><MagicStick /></el-icon>
        </div>
        <div class="agent-message">
          <div class="agent-header-row">
            <span class="agent-name">职能助手</span>
            <el-tag v-if="targetPosition" size="small" effect="plain" type="primary">{{ targetPosition }}</el-tag>
          </div>
          <p class="message-text">{{ aiAnalysis }}</p>
        </div>
      </div>
      <div class="quick-stats" v-if="growthRate !== '--' || pathSteps.length > 0">
        <div class="stat-item">
          <span class="label">成长速度</span>
          <span class="value">{{ growthRate }}</span>
        </div>
        <el-divider direction="vertical" />
        <div class="stat-item">
          <span class="label">学习阶段</span>
          <span class="value">{{ pathSteps.length }}阶段</span>
        </div>
      </div>
    </div>

    <el-row :gutter="20" class="main-tracking-row equal-height">
      <el-col :xs="24" :md="14" :lg="15">
        <el-card class="glass-card chart-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><TrendCharts /></el-icon> 能力进阶模型</span>
              <el-tag size="small" effect="plain">实时对比</el-tag>
            </div>
          </template>
          <div class="chart-wrapper" v-if="hasCapabilityData">
            <div ref="radarChartRef" class="radar-chart"></div>
            <div class="chart-legend">
              <span class="legend-item current">当前水平</span>
              <span class="legend-item target">目标要求</span>
            </div>
          </div>
          <el-empty v-else description="请先完成人岗匹配后查看能力模型" :image-size="80" />
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10" :lg="9">
        <el-card class="glass-card path-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Compass /></el-icon> 职业路径步骤</span>
            </div>
          </template>
          <div class="path-steps" v-loading="pageLoading && pathSteps.length === 0">
            <el-empty v-if="!hasLearningPlan && pathSteps.length === 0" description="请先完成人岗匹配后生成职业路径" :image-size="60" />
            <el-steps v-else-if="pathSteps.length > 0" direction="vertical" :active="currentPhaseIndex" finish-status="success">
              <el-step v-for="(step, idx) in pathSteps" :key="idx">
                <template #title>
                  <div class="step-title-row">
                    <span>{{ step.phase_name || step.title }}</span>
                    <el-tag v-if="step.duration" size="small" effect="plain" type="info">{{ step.duration }}</el-tag>
                  </div>
                </template>
                <template #description>
                  <div class="step-desc">{{ step.goals ? step.goals.slice(0, 2).join('；') : step.description || '' }}</div>
                </template>
              </el-step>
            </el-steps>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="glass-card todo-section">
  <template #header>
    <div class="card-header">
      <span><el-icon><Checked /></el-icon> 代理人分配任务</span>
      <span class="todo-subtitle" v-if="targetPosition">完成任务可提升 {{ targetPosition }} 匹配度</span>
    </div>
  </template>

  <el-empty v-if="todoList.length === 0 && !pageLoading" description="请先完成人岗匹配后生成学习任务" :image-size="60" />
  <div v-else class="todo-vertical-list">
    <div 
      v-for="todo in todoList" 
      :key="todo.id" 
      class="todo-item-refined" 
      :class="{ 'is-completed': todo.completed }"
    >
      <div class="todo-main-row">
        <el-checkbox v-model="todo.completed" size="large" />
        <div class="todo-content">
          <div class="todo-title-row">
            <span class="todo-text">{{ todo.text }}</span>
            <el-tag v-if="todo.isAI" size="small" type="warning" effect="plain" class="ai-tag">助手建议</el-tag>
          </div>
          
          <div class="todo-details">
            <p class="todo-desc">
              {{ todo.desc || '点击查看该任务的详细执行建议与学习资源...' }}
            </p>
            <div class="todo-meta">
              <span class="meta-tag"><el-icon><Timer /></el-icon> 预计 {{ todo.time || '30' }}min</span>
              <span class="meta-tag"><el-icon><StarFilled /></el-icon> 难度：{{ todo.difficulty || '中等' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</el-card>
    </template>

    <div
  class="floating-agent-wrapper" 
  :class="{ 'is-active': isCoachingOpen, 'is-dragging': isDragging }"
  :style="{ left: position.x + 'px', top: position.y + 'px' }"
  ref="floatBallRef"
>
      <div class="floating-avatar-btn" @mousedown="handleMouseDown">
        <el-icon class="pulse-icon"><MagicStick /></el-icon>
        <span class="avatar-label">职能助手</span>
      </div>

      <el-card class="coaching-dialog glass-card">
        <template #header>
          <div class="dialog-header">
            <h4>职能助手</h4>
            <el-button type="info" link icon="Close" @click="isCoachingOpen = false" />
          </div>
        </template>
        
<div class="dialog-body-content">
  <div class="chat-messages" ref="chatMessagesRef">
    <!-- 对话历史（含 AI 初始问候） -->
    <div v-for="(msg, idx) in chatHistory" :key="idx" :class="msg.role === 'user' ? 'user-msg-wrapper' : 'bot-msg-wrapper'">
      <div v-if="msg.role === 'assistant'" class="bot-avatar-mini"><el-icon><MagicStick /></el-icon></div>
      <div :class="msg.role === 'user' ? 'user-content' : 'bot-content'">
        <span class="bot-info" v-if="msg.role === 'assistant'">职能助手</span>
        <span class="bot-info" v-else>我</span>
        <div :class="msg.role === 'user' ? 'user-prompt' : 'bot-prompt'">{{ msg.content }}</div>
      </div>
    </div>
    <!-- 加载指示器 -->
    <div v-if="isCoachingLoading" class="bot-msg-wrapper">
      <div class="bot-avatar-mini"><el-icon><MagicStick /></el-icon></div>
      <div class="bot-content">
        <span class="bot-info">职能助手</span>
        <div class="bot-prompt typing-indicator">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    </div>
  </div>

  <div class="input-area">
    <div class="input-container">
      <el-input
        v-model="coachInputValue"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="输入你的职业困惑，或粘贴简历内容..."
        resize="none"
        @keydown.enter.exact.prevent="sendCoachMessage"
      />
      <div class="input-footer">
        <el-button
          type="primary"
          class="send-icon-btn"
          @click="sendCoachMessage"
          :loading="isCoachingLoading"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, reactive, watch, inject } from 'vue'
import { MagicStick, TrendCharts, Compass, Checked, Promotion, Close, Timer, StarFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { learningPlanApi } from '@/api/learningPlan'
import { matchingApi } from '@/api/matching'
import { currentRadarData, matchVersion } from './profileState.js'
import InteractiveLoading from '@/components/InteractiveLoading.vue'

// --- 缓存机制 ---
const CACHE_KEY = 'growth_tracker_cache'

const generateCacheKey = (profileData, jobTitle) => {
  const profileHash = JSON.stringify(profileData || [])
  return `${profileHash}_${jobTitle || 'none'}`
}

const loadFromCache = () => {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const saveToCache = (cacheKey, data) => {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ cacheKey, ...data, matchVersion: matchVersion.value, timestamp: Date.now() }))
  } catch { /* quota exceeded, ignore */ }
}

// --- 拖拽核心逻辑 ---
const isDragging = ref(false)
const position = reactive({ 
  x: window.innerWidth - 100, // 初始靠右
  y: window.innerHeight - 150  // 初始靠下
})

let dragOffset = { x: 0, y: 0 }
let startPos = { x: 0, y: 0 }

const handleMouseDown = (e) => {
  isDragging.value = true
  startPos = { x: e.clientX, y: e.clientY }
  dragOffset = { x: e.clientX - position.x, y: e.clientY - position.y }

  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseup', handleMouseUp)
}

const handleMouseMove = (e) => {
  if (!isDragging.value) return
  
  let newX = e.clientX - dragOffset.x
  let newY = e.clientY - dragOffset.y

  // 边界检查：不让球飞出浏览器
  const ballSize = 60
  newX = Math.max(10, Math.min(newX, window.innerWidth - ballSize - 10))
  newY = Math.max(10, Math.min(newY, window.innerHeight - ballSize - 10))

  position.x = newX
  position.y = newY
}

const handleMouseUp = (e) => {
  isDragging.value = false
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)

  // 区分点击与拖拽：位移小于 5px 才视为点击打开对话框
  const moveDist = Math.sqrt(Math.pow(e.clientX - startPos.x, 2) + Math.pow(e.clientY - startPos.y, 2))
  if (moveDist < 5) {
    isCoachingOpen.value = !isCoachingOpen.value
  }
}

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
})

// --- 注入父组件提供的状态 ---
const hasMatchData = inject('hasMatchData', ref(false))
const selectedJob = inject('selectedJob', ref(null))

// --- 响应式数据和逻辑 ---
const aiAnalysis = ref('正在加载学习计划...')
const targetPosition = ref('')
const growthRate = ref('--')
const currentPhaseIndex = ref(0)
const pathSteps = ref([])
const hasLearningPlan = ref(false)
const radarChartRef = ref(null)
let radarInstance = null

const currentLevelData = ref([])
const targetLevelData = ref([])
const radarIndicators = ref([])
const hasCapabilityData = ref(false)

const todoList = ref([])
const pageLoading = ref(true)

// 加载动画状态
const currentLoadingStep = ref(0)
const loadingProgress = ref(0)
const loadingSteps = ['获取岗位信息', '分析能力模型', '生成学习计划', '规划每日任务']
let loadingTimer = null
let progressTimer = null

// 验证缓存是否有效（需同时匹配画像+岗位 和 匹配版本）
const isCacheValid = (cacheKey) => {
  const cached = loadFromCache()
  if (!cached || !cached.cacheKey) return false
  return cached.cacheKey === cacheKey && cached.matchVersion === matchVersion.value
}

// 从缓存恢复数据
const restoreFromCache = () => {
  const cached = loadFromCache()
  if (!cached) return false

  if (cached.targetPosition) targetPosition.value = cached.targetPosition
  if (cached.aiAnalysis) aiAnalysis.value = cached.aiAnalysis
  if (cached.growthRate) growthRate.value = cached.growthRate
  if (cached.pathSteps) {
    pathSteps.value = cached.pathSteps
    hasLearningPlan.value = cached.pathSteps.length > 0
  }
  if (cached.todoList) todoList.value = cached.todoList
  if (cached.currentLevelData) currentLevelData.value = cached.currentLevelData
  if (cached.targetLevelData) targetLevelData.value = cached.targetLevelData
  if (cached.radarIndicators) radarIndicators.value = cached.radarIndicators
  hasCapabilityData.value = cached.hasCapabilityData || false

  return true
}

// 获取所有数据并保存到缓存
const fetchAllDataAndCache = async (cacheKey, forceRefresh = false) => {
  startLoadingAnimation()
  try {
    // 必须先生成学习计划，再获取每日任务（任务依赖计划存在）
    await fetchLearningPlan(forceRefresh)
    await Promise.all([fetchDailyTasks(), fetchCapabilityModel()])

    // 保存到缓存
    saveToCache(cacheKey, {
      targetPosition: targetPosition.value,
      aiAnalysis: aiAnalysis.value,
      growthRate: growthRate.value,
      pathSteps: pathSteps.value,
      todoList: todoList.value,
      currentLevelData: currentLevelData.value,
      targetLevelData: targetLevelData.value,
      radarIndicators: radarIndicators.value,
      hasCapabilityData: hasCapabilityData.value,
    })
  } catch (err) {
    console.error('[GrowthTracker] fetchAllDataAndCache error:', err)
    aiAnalysis.value = '数据加载失败，请返回人岗匹配重新锁定岗位后再试'
  } finally {
    stopLoadingAnimation()
  }
}

// 调用 learning_plan agent
const fetchLearningPlan = async (forceRefresh = false) => {
  try {
    const { data } = await learningPlanApi.generate({ plan_type: '长期', force_refresh: forceRefresh })
    console.log('[GrowthTracker] fetchLearningPlan response:', data.learning_plan?.target_job)
    if (data.learning_plan) {
      const plan = data.learning_plan
      if (plan.target_job) targetPosition.value = plan.target_job

      // 如果有错误信息，显示提示
      if (plan.error) {
        aiAnalysis.value = plan.error
        return
      }

      // 没有阶段数据，说明未匹配岗位
      if (!plan.phases || plan.phases.length === 0) {
        aiAnalysis.value = '请先完成人岗匹配，我将为你生成个性化学习计划'
        return
      }

      // 构建 AI 分析摘要
      const parts = []
      if (plan.total_duration) parts.push(`预计总时长：${plan.total_duration}`)
      if (plan.estimated_difficulty) parts.push(`难度等级：${plan.estimated_difficulty}`)
      const phaseCount = plan.phases.length
      parts.push(`共 ${phaseCount} 个学习阶段`)
      if (plan.total_duration) {
        parts.push('我已为你拆解了职业路径步骤，点击右侧查看详情')
      }
      aiAnalysis.value = parts.join('；') || '学习计划已生成，请查看下方详情'

      // 路径步骤
      if (plan.phases && plan.phases.length > 0) {
        pathSteps.value = plan.phases.map((p) => ({
          phase_name: p.phase_name || p.title || '',
          goals: p.goals || [],
          content: p.content || [],
          duration: p.duration || '',
          description: p.goals ? p.goals.slice(0, 2).join('；') : '',
        }))
        currentPhaseIndex.value = 0
        hasLearningPlan.value = true
      }

      // 成长速度 / 打卡天数（估算值）
      if (phaseCount > 0 && plan.total_duration) {
        growthRate.value = `+${Math.min(phaseCount * 5, 50)}%`
      }

    }
  } catch (err) {
    console.error('[GrowthTracker] fetchLearningPlan error:', err)
    aiAnalysis.value = '请先完成人岗匹配，我将为你生成个性化学习计划'
  }
}

const normalizeTasks = (tasks) => {
  return tasks.map((t, i) => ({
    id: t.id || i + 1,
    text: t.content || t.title || t.task || `任务 ${i + 1}`,
    desc: t.description || t.desc || '',
    time: t.estimated_time || t.time || t.duration || '30',
    difficulty: t.difficulty || t.type || '中等',
    completed: false,
    isAI: true,
  }))
}

const fetchDailyTasks = async () => {
  try {
    const { data } = await learningPlanApi.dailyTasks({ phase_index: 0, _t: Date.now() })
    console.log('[GrowthTracker] fetchDailyTasks response:', data)

    const expectedJob = selectedJob.value?.job_title || targetPosition.value || ''
    const returnedJob = data.target_job || ''

    // 岗位不匹配或任务为空 → 强制刷新重试
    const needRetry = (expectedJob && returnedJob && expectedJob !== returnedJob)
      || (!data.daily_tasks || data.daily_tasks.length === 0)

    if (needRetry) {
      console.warn(`[GrowthTracker] daily tasks need retry: mismatch=${expectedJob !== returnedJob}, empty=${!data.daily_tasks?.length}`)
      const { data: retry } = await learningPlanApi.dailyTasks({ phase_index: 0, force_refresh: true, _t: Date.now() })
      if (retry.daily_tasks && retry.daily_tasks.length > 0) {
        todoList.value = normalizeTasks(retry.daily_tasks)
        return
      }
      // 二次重试仍为空，设置提示
      console.warn('[GrowthTracker] daily tasks still empty after retry')
      return
    }

    todoList.value = normalizeTasks(data.daily_tasks)
  } catch (err) {
    console.error('[GrowthTracker] fetchDailyTasks error:', err)
  }
}

const fetchCapabilityModel = async () => {
  try {
    const { data } = await matchingApi.getCapabilityModel()
    console.log('[GrowthTracker] fetchCapabilityModel response:', data.data?.job_title)
    if (data.success && data.data) {
      const model = data.data
      if (model.dimensions && model.dimensions.length > 0) {
        radarIndicators.value = model.dimensions.map((d) => ({ name: d, max: 100 }))
        hasCapabilityData.value = true
      }
      if (model.current_level && model.current_level.length > 0) currentLevelData.value = model.current_level
      if (model.target_level && model.target_level.length > 0) targetLevelData.value = model.target_level
      if (model.job_title) targetPosition.value = model.job_title
    }
  } catch (err) {
    console.error('[GrowthTracker] fetchCapabilityModel error:', err)
  }
}

// 雷达图初始化
const initRadarChart = () => {
  if (!radarChartRef.value || !hasCapabilityData.value) return
  if (radarInstance) radarInstance.dispose()

  radarInstance = echarts.init(radarChartRef.value)
  const option = {
    color: ['#70a1ff', '#e2e8f0'],
    radar: {
      indicator: radarIndicators.value,
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(112, 161, 255, 0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(112, 161, 255, 0.1)' } }
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: currentLevelData.value,
          name: '当前水平',
          areaStyle: { color: 'rgba(112, 161, 255, 0.2)' },
          lineStyle: { color: '#70a1ff', width: 2 }
        },
        {
          value: targetLevelData.value,
          name: '目标要求',
          lineStyle: { type: 'dashed', color: '#94a3b8', width: 1 },
          symbol: 'none'
        }
      ]
    }]
  }
  radarInstance.setOption(option)
}

const handleResize = () => radarInstance?.resize()

// 加载动画控制
const startLoadingAnimation = () => {
  currentLoadingStep.value = 0
  loadingProgress.value = 0

  loadingTimer = setInterval(() => {
    if (currentLoadingStep.value < loadingSteps.length - 1) {
      currentLoadingStep.value++
    }
  }, 800)

  progressTimer = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.random() * 15
    }
  }, 300)
}

const stopLoadingAnimation = async () => {
  loadingProgress.value = 100
  currentLoadingStep.value = loadingSteps.length
  clearInterval(loadingTimer)
  clearInterval(progressTimer)
  pageLoading.value = false
  await nextTick()
  initRadarChart()
  window.addEventListener('resize', handleResize)
}

// 生命周期
onMounted(async () => {
  // 没有个人信息或没有匹配数据时直接显示空状态，不调用API
  const hasProfile = currentRadarData.value && currentRadarData.value.some(v => v > 0)
  if (!hasProfile || !hasMatchData.value) {
    aiAnalysis.value = '请先完善个人信息并完成人岗匹配，我将为你生成个性化学习计划'
    pageLoading.value = false
    return
  }

  // 生成缓存键：基于个人信息和锁定岗位
  const jobTitle = selectedJob.value?.job_title || ''
  const cacheKey = generateCacheKey(currentRadarData.value, jobTitle)

  // 检查缓存是否有效
  if (isCacheValid(cacheKey)) {
    restoreFromCache()
    pageLoading.value = false
    await nextTick()
    initRadarChart()
    window.addEventListener('resize', handleResize)
    return
  }

  // 缓存无效，重新获取数据
  await fetchAllDataAndCache(cacheKey)
})

// 监听匹配状态变化，匹配完成后加载数据
watch(hasMatchData, async (newVal) => {
  if (!newVal) return

  const jobTitle = selectedJob.value?.job_title || ''
  const cacheKey = generateCacheKey(currentRadarData.value, jobTitle)

  // 检查缓存
  if (isCacheValid(cacheKey)) {
    restoreFromCache()
    pageLoading.value = false
    await nextTick()
    initRadarChart()
    return
  }

  await fetchAllDataAndCache(cacheKey)
})

// 监听重新匹配事件，清除缓存并重新加载
watch(matchVersion, async () => {
  // 清除缓存，确保拿到最新数据
  sessionStorage.removeItem(CACHE_KEY)

  // 重置状态
  hasLearningPlan.value = false
  hasCapabilityData.value = false
  pathSteps.value = []
  todoList.value = []
  targetPosition.value = ''
  aiAnalysis.value = '正在加载学习计划...'
  growthRate.value = '--'
  currentLevelData.value = []
  targetLevelData.value = []
  radarIndicators.value = []

  pageLoading.value = true

  // 没有个人信息或匹配数据时不请求
  const hasProfile = currentRadarData.value && currentRadarData.value.some(v => v > 0)
  if (!hasProfile || !hasMatchData.value) {
    aiAnalysis.value = '请先完善个人信息并完成人岗匹配，我将为你生成个性化学习计划'
    pageLoading.value = false
    return
  }

  // 直接重新获取数据，不依赖 hasMatchData watcher（hasMatchData 可能一直为 true 不触发）
  const jobTitle = selectedJob.value?.job_title || ''
  const cacheKey = generateCacheKey(currentRadarData.value, jobTitle)
  await fetchAllDataAndCache(cacheKey, true)
})

// 监听锁定岗位变化，切换岗位时刷新数据
watch(selectedJob, async (newJob, oldJob) => {
  if (!newJob) return
  // 只有岗位真正改变时才刷新
  if (oldJob && newJob.job_title === oldJob.job_title && newJob.company === oldJob.company) return

  // 清除缓存，强制从后端重新获取
  sessionStorage.removeItem(CACHE_KEY)

  // 重置状态
  hasLearningPlan.value = false
  hasCapabilityData.value = false
  pathSteps.value = []
  todoList.value = []
  targetPosition.value = ''
  aiAnalysis.value = '正在加载学习计划...'
  growthRate.value = '--'
  currentLevelData.value = []
  targetLevelData.value = []
  radarIndicators.value = []
  hasCapabilityData.value = false

  pageLoading.value = true

  const cacheKey = generateCacheKey(currentRadarData.value, newJob.job_title)
  await fetchAllDataAndCache(cacheKey, true)
})

// 能力数据就绪后初始化雷达图
watch(hasCapabilityData, async (ready) => {
  if (ready && !pageLoading.value) {
    await nextTick()
    if (!radarInstance && radarChartRef.value) initRadarChart()
  }
})

// 监听个人信息变化，清除缓存以便下次进入时重新获取
watch(currentRadarData, (newVal, oldVal) => {
  if (!newVal || !oldVal) return
  // 只有数据真正变化时才清除缓存
  if (JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
    sessionStorage.removeItem(CACHE_KEY)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarInstance?.dispose()
})

// --- 智能辅导对话框 ---
const isCoachingOpen = ref(false)
const coachInputValue = ref('')
const isCoachingLoading = ref(false)
const chatHistory = ref([]) // [{role: "user"|"assistant", content: str}]
const chatMessagesRef = ref(null)
const coachGreeted = ref(false)

const scrollChatToBottom = () => {
  nextTick(() => {
    const el = chatMessagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// AI 生成初始问候
const initCoachGreeting = async () => {
  if (coachGreeted.value) return
  coachGreeted.value = true
  isCoachingLoading.value = true
  try {
    console.log('[GrowthCoach] Sending greeting...')
    const resp = await learningPlanApi.coach('你好，请简单介绍一下你自己，并告诉我你能如何帮助我进行职业规划。', [])
    console.log('[GrowthCoach] Response:', resp.status, resp.data)
    const reply = resp.data?.reply
    if (reply) {
      chatHistory.value.push({ role: 'assistant', content: reply })
    } else {
      console.warn('[GrowthCoach] No reply in response:', resp.data)
    }
  } catch (err) {
    console.error('[GrowthCoach] Greeting failed:', err)
  } finally {
    isCoachingLoading.value = false
  }
}

const sendCoachMessage = async () => {
  const text = coachInputValue.value.trim()
  if (!text) return

  chatHistory.value.push({ role: 'user', content: text })
  coachInputValue.value = ''
  isCoachingLoading.value = true
  scrollChatToBottom()

  try {
    console.log('[GrowthCoach] Sending message:', text)
    const resp = await learningPlanApi.coach(
      text,
      chatHistory.value.slice(0, -1)
    )
    console.log('[GrowthCoach] Response:', resp.status, resp.data)
    const reply = resp.data?.reply
    chatHistory.value.push({ role: 'assistant', content: reply || '抱歉，暂时无法回复。' })
  } catch (err) {
    console.error('[GrowthCoach] Send failed:', err)
    chatHistory.value.push({ role: 'assistant', content: '抱歉，职能助手暂时不可用，请稍后再试。' })
  } finally {
    isCoachingLoading.value = false
    scrollChatToBottom()
  }
}

// 打开对话框时自动触发 AI 问候
watch(isCoachingOpen, (open) => {
  if (open) {
    coachInputValue.value = ''
    initCoachGreeting()
  }
})
</script>

<style scoped lang="scss">
.growth-tracking-center {
  padding: 10px;
  background: transparent;
  position: relative;
  min-height: 100%;

  .glass-card {
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(20px) saturate(1.1);
    -webkit-backdrop-filter: blur(20px) saturate(1.1);
    border: 1px solid rgba(255, 255, 255, 0.45);
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
    overflow: hidden !important;

    :deep(.el-card__header) {
      border-bottom: 1px solid rgba(255, 255, 255, 0.3);
      padding: 16px 20px;
      background: rgba(255, 255, 255, 0.2);
      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        color: #1e293b;
        .el-icon { margin-right: 8px; color: #667eea; }
      }
    }

    :deep(.el-card__body) {
      overflow: hidden !important;
    }
  }

  .agent-command-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 25px;
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(20px) saturate(1.1);
    -webkit-backdrop-filter: blur(20px) saturate(1.1);
    border: 1px solid rgba(255, 255, 255, 0.45);
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
    
    .agent-info {
      display: flex;
      align-items: flex-start;
      gap: 15px;
      flex: 1;
      .agent-avatar {
        width: 45px; height: 45px;
        background: #70a1ff;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        flex-shrink: 0;
        .pulse-icon { animation: pulse 2s infinite; }
      }
      .agent-message {
        flex: 1;
        min-width: 0;
        .agent-header-row {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 6px;
        }
        .agent-name { font-size: 14px; color: #1e293b; font-weight: 700; }
        .message-text { margin: 0; font-size: 13px; color: #64748b; line-height: 1.5; }
      }
    }
    
    .quick-stats {
      display: flex;
      align-items: center;
      gap: 24px;
      flex-shrink: 0;
      .stat-item {
        text-align: center;
        .label { font-size: 11px; color: #94a3b8; display: block; margin-bottom: 2px; }
        .value { font-size: 20px; font-weight: 800; color: #70a1ff; }
      }
      .el-divider--vertical { height: 30px; }
    }
  }

  .chart-wrapper {
    flex: 1;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    align-items: center;
    .radar-chart { width: 100%; flex: 1; min-height: 250px; }
    .chart-legend {
      display: flex;
      gap: 20px;
      font-size: 12px;
      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        &::before { content: ''; width: 12px; height: 2px; }
        &.current::before { background: #70a1ff; }
        &.target::before { background: #94a3b8; border-top: 1px dashed #94a3b8; height: 0; }
      }
    }
  }

  .path-steps {
    padding: 10px 8px;
    flex: 1;
    overflow-y: auto;

    .step-title-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
    }

    .step-desc {
      font-size: 12px;
      color: #94a3b8;
      line-height: 1.4;
    }

    :deep(.el-step__title.is-process) { color: #70a1ff; font-weight: 700; }
  }

  /* 原有呼吸和 fadeIn 动画保留 */
  @keyframes pulse { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.1); opacity: 0.8; } 100% { transform: scale(1); opacity: 1; } }
  .fade-in { animation: fadeIn 0.8s ease-out; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

  /* 🌟 新增悬浮辅导员组件样式 */
  .floating-agent-wrapper {
  position: fixed;
  z-index: 2000;
  touch-action: none;

  /* 1. 悬浮球样式 */
  .floating-avatar-btn {
    width: 65px;
    height: 65px;
    background: linear-gradient(135deg, #70a1ff 0%, #4a8cff 100%);
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: white;
    cursor: grab;
    box-shadow: 0 10px 30px rgba(112, 161, 255, 0.4);
    transition: transform 0.2s;
    user-select: none;

    &:active { cursor: grabbing; }
    &:hover { transform: scale(1.05); }

    .el-icon { font-size: 26px; }
    .avatar-label { font-size: 10px; font-weight: bold; margin-top: 2px; }
  }

  /* 2. 大尺寸中心对话框样式 */
  .coaching-dialog {
    position: absolute;
    bottom: 40px;
    right: 65px !important;
    left: auto !important;
    top: auto !important;
    transform: scale(0.8); /* 初始缩放 */
    transform-origin: bottom right;

    /* 模仿图二的大尺寸 */
    width: 35vw;
    max-width: 800px;
    height: 80vh;
    max-height: 600px;
    
    opacity: 0;
    visibility: hidden;
    transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    z-index: 2100;
    display: flex;
    flex-direction: column;
    border-radius: 24px;
    border: 1px solid rgba(112, 161, 255, 0.3);

:deep(.el-card__header) {
  padding: 14px 20px;
  background: rgba(255, 255, 255, 0.8);
  .dialog-header {
    display: flex;
    justify-content: space-between; /* 🌟 关键：将标题推向左，叉叉推向右 */
    align-items: center;
    h4 { 
      margin: 0; 
      font-size: 16px; 
      color: #1e293b; 
      display: flex; 
      align-items: center;
      &::before { /* 模拟图二左侧的绿色在线状态点 */
        content: '';
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
      }
    }
  }
}

   :deep(.el-card__body) {
      flex: 1;
      padding: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      height: 100%;
    }

    .dialog-body-content {
      flex: 1;
      padding: 20px;
      display: flex;
      flex-direction: column;
      background: #fcfcfd; // 浅色背景区分聊天区

      .chat-messages {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 15px;

        .bot-msg-wrapper {
          display: flex;
          gap: 12px;
          align-items: flex-start;
          
          .bot-avatar-mini {
            width: 32px;
            height: 32px;
            background: #70a1ff;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            flex-shrink: 0;
          }

          .bot-content {
            .bot-info { font-size: 12px; color: #94a3b8; margin-bottom: 4px; display: block; }
            .bot-prompt {
              background: white;
              padding: 12px 16px;
              border-radius: 4px 16px 16px 16px;
              color: #334155;
              font-size: 14px;
              line-height: 1.5;
              box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
              border: 1px solid #f1f5f9;
            }
          }
        }

        // 用户消息样式
        .user-msg-wrapper {
          display: flex;
          justify-content: flex-end;
          margin-bottom: 12px;

          .user-content {
            max-width: 85%;
            .bot-info { font-size: 11px; color: #94a3b8; margin-bottom: 4px; display: block; text-align: right; }
            .user-prompt {
              background: linear-gradient(135deg, #70a1ff 0%, #4a8cff 100%);
              color: #ffffff;
              padding: 12px 16px;
              border-radius: 16px 4px 16px 16px;
              font-size: 14px;
              line-height: 1.5;
              box-shadow: 0 2px 12px rgba(112, 161, 255, 0.2);
            }
          }
        }

        // 打字指示器
        .typing-indicator {
          display: flex;
          align-items: center;
          gap: 5px;
          padding: 14px 20px !important;
          .dot {
            width: 7px;
            height: 7px;
            background: #94a3b8;
            border-radius: 50%;
            animation: typingBounce 1.4s ease-in-out infinite;
            &:nth-child(2) { animation-delay: 0.2s; }
            &:nth-child(3) { animation-delay: 0.4s; }
          }
        }

        @keyframes typingBounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-6px); opacity: 1; }
        }
      }

      /* 实现图二样式的输入框区域 */
.input-area {
  padding: 16px 20px;
  background: transparent;

  .input-container {
    background: #ffffff;
    border: 1px solid #eef2f6;
    border-radius: 16px;
    padding: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    transition: all 0.3s ease;

    &:focus-within {
      border-color: #70a1ff;
      box-shadow: 0 4px 20px rgba(112, 161, 255, 0.1);
    }

    :deep(.el-textarea__inner) {
      border: none !important;      /* 彻底移除灰色边框 */
      box-shadow: none !important;  /* 移除聚焦时的蓝色外边框阴影 */
      background: transparent;     /* 确保背景透明 */
      padding: 5px;
      font-size: 14px;
      color: #334155;
      resize: none;
      &::placeholder {
        color: #cbd5e1;
      }
      &:focus {
        box-shadow: none;
      }
    }

    .input-footer {
      display: flex;
      justify-content: flex-end; /* 🌟 确保按钮在右边 */
      margin-top: 8px;

      .send-icon-btn {
        width: 36px;
        height: 36px;
        padding: 0;
        border-radius: 50%; /* 圆形按钮 */
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #70a1ff 0%, #4a8cff 100%);
        border: none;
        transition: transform 0.2s;

        &:hover {
          transform: scale(1.1);
          box-shadow: 0 4px 12px rgba(112, 161, 255, 0.3);
        }

        .el-icon {
          font-size: 18px;
          color: white;
          margin: 0;
        }
      }
    }
  }
}
    }
  }

  /* 3. 激活状态 */
  &.is-active .coaching-dialog {
    opacity: 1;
    visibility: visible;
    transform: scale(1);
  }

}

.equal-height {
  display: flex;
  align-items: stretch;
  margin-bottom: 20px !important;

  :deep(.el-col) {
    display: flex;
    flex-direction: column;
    margin-bottom: 0;
  }

  .glass-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    margin-bottom: 0;
  }

  :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .equal-height {
    flex-direction: column;
    :deep(.el-col) { margin-bottom: 20px; }
  }
  .agent-command-bar {
    flex-direction: column;
    gap: 16px;
  }
}

/* 拖拽过程中禁用动画以防抖动 */
.is-dragging {
  transition: none !important;
}
}

.todo-section {
  /* 保持卡片本身的毛玻璃质感 */
  background: rgba(255, 255, 255, 0.4) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;

  .todo-vertical-list {
    display: flex;
    flex-direction: column;
    gap: 12px; // 任务项之间的垂直间距
  }

  .todo-item-refined {
    background: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(226, 232, 240, 0.6);
    border-radius: 12px;
    padding: 16px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      background: #ffffff;
      transform: translateX(4px); // 轻微右移增加灵动感
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
      border-color: rgba(102, 126, 234, 0.3);
    }

    &.is-completed {
      opacity: 0.7;
      background: rgba(241, 245, 249, 0.5);
      .todo-text { text-decoration: line-through; color: #94a3b8; }
    }

    .todo-main-row {
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }

    .todo-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .todo-title-row {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .todo-text {
        font-weight: 600;
        color: #1e293b;
        font-size: 15px;
      }
    }

    .todo-details {
      .todo-desc {
        font-size: 13px;
        color: #64748b;
        margin: 0 0 8px 0;
        line-height: 1.5;
      }

      .todo-meta {
        display: flex;
        gap: 16px;
        
        .meta-tag {
          font-size: 11px;
          color: #94a3b8;
          display: flex;
          align-items: center;
          gap: 4px;
          
          .el-icon { color: #667eea; }
        }
      }
    }
  }
}

/* AI 标签的素雅处理 */
.ai-tag {
  border-radius: 4px;
  font-weight: 500;
  letter-spacing: 0.5px;
  background: rgba(255, 186, 116, 0.1) !important;
  color: #f59e0b !important;
  border: 1px solid rgba(255, 186, 116, 0.2) !important;
}

/* 加载状态 - 自适应容器大小 */
.loading-section {
  height: 78vh;
  min-height: 580px;
  border-radius: 20px;
  overflow: hidden;
}

/* 顶部操作栏 */
.action-bar {
  padding: 14px 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(240, 248, 255, 0.3));
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  margin-bottom: 20px;

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 8px;
    line-height: 1.4;
    word-break: break-word;
    .el-icon { color: #5098f9; font-size: 22px; flex-shrink: 0; }
  }
  .page-desc {
    margin: 5px 0 0;
    font-size: 13px;
    color: #94a3b8;
    font-weight: 500;
    line-height: 1.5;
    word-break: break-word;
  }
}
</style>