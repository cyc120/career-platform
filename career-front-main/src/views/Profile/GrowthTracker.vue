<template>
  <div class="growth-tracking-center fade-in">
    <div class="agent-command-bar glass-card">
      <div class="agent-info">
        <div class="agent-avatar">
          <el-icon class="pulse-icon"><MagicStick /></el-icon>
        </div>
        <div class="agent-message">
          <span class="agent-name">Career Pilot (AI)</span>
          <p class="message-text">{{ aiAnalysis }}</p>
        </div>
      </div>
      <div class="quick-stats" v-if="growthRate !== '--' || consecutiveDays > 0">
        <div class="stat-item">
          <span class="label">成长速度</span>
          <span class="value">{{ growthRate }}</span>
        </div>
        <el-divider direction="vertical" />
        <div class="stat-item">
          <span class="label">打卡周期</span>
          <span class="value">{{ consecutiveDays }}天</span>
        </div>
      </div>
    </div>

    <el-row :gutter="20" class="main-tracking-row equal-height">
      <el-col :span="15">
        <el-card class="glass-card chart-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><TrendCharts /></el-icon> 能力进阶模型</span>
              <el-tag size="small" effect="plain">实时对比</el-tag>
            </div>
          </template>
          <div class="chart-wrapper">
            <div ref="radarChartRef" class="radar-chart"></div>
            <div class="chart-legend">
              <span class="legend-item current">当前水平</span>
              <span class="legend-item target">目标要求</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card class="glass-card path-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Compass /></el-icon> 职业路径步骤</span>
            </div>
          </template>
          <div class="path-steps" v-loading="pathSteps.length === 0">
            <el-empty v-if="pathSteps.length === 0" description="加载职业路径中..." :image-size="60" />
            <el-steps v-else direction="vertical" :active="currentPhaseIndex" finish-status="success">
              <el-step v-for="(step, idx) in pathSteps" :key="idx"
                :title="step.phase_name || step.title"
                :description="step.goals ? step.goals.slice(0, 2).join('；') : step.description || ''" />
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

  <div class="todo-vertical-list">
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
            <el-tag v-if="todo.isAI" size="small" type="warning" effect="plain" class="ai-tag">AI 建议</el-tag>
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

    <div 
  class="floating-agent-wrapper" 
  :class="{ 'is-active': isCoachingOpen, 'is-dragging': isDragging }"
  :style="{ left: position.x + 'px', top: position.y + 'px' }"
  ref="floatBallRef"
>
      <div class="floating-avatar-btn" @mousedown="handleMouseDown">
        <el-icon class="pulse-icon"><MagicStick /></el-icon>
        <span class="avatar-label">智能辅导</span>
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
        <span class="bot-info" v-if="msg.role === 'assistant'">Career Pilot</span>
        <span class="bot-info" v-else>我</span>
        <div :class="msg.role === 'user' ? 'user-prompt' : 'bot-prompt'">{{ msg.content }}</div>
      </div>
    </div>
    <!-- 加载指示器 -->
    <div v-if="isCoachingLoading" class="bot-msg-wrapper">
      <div class="bot-avatar-mini"><el-icon><MagicStick /></el-icon></div>
      <div class="bot-content">
        <span class="bot-info">Career Pilot</span>
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
import { ref, onMounted, onUnmounted, nextTick, reactive, watch } from 'vue'
import { MagicStick, TrendCharts, Compass, Checked, Promotion, Close, Timer, StarFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { learningPlanApi } from '@/api/learningPlan'

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

// --- 响应式数据和逻辑 ---
const aiAnalysis = ref('')
const targetPosition = ref('')
const consecutiveDays = ref(0)
const growthRate = ref('--')
const currentPhaseIndex = ref(0)
const pathSteps = ref([])
const radarChartRef = ref(null)
let radarInstance = null

const currentLevelData = ref([85, 70, 75, 90, 80])
const targetLevelData = ref([95, 90, 85, 95, 90])
const radarIndicators = ref([
  { name: '技术广度', max: 100 }, { name: '业务理解', max: 100 },
  { name: '沟通能力', max: 100 }, { name: '工程化', max: 100 },
  { name: '解决问题', max: 100 }
])

const todoList = ref([])

// 调用 learning_plan agent
const fetchLearningPlan = async () => {
  try {
    const { data } = await learningPlanApi.generate({ plan_type: '长期' })
    if (data.learning_plan) {
      const plan = data.learning_plan
      if (plan.target_job) targetPosition.value = plan.target_job
      // 构建 AI 分析摘要
      const parts = []
      if (plan.total_duration) parts.push(`预计总时长：${plan.total_duration}`)
      if (plan.estimated_difficulty) parts.push(`难度等级：${plan.estimated_difficulty}`)
      const phaseCount = (plan.phases || []).length
      if (phaseCount > 0) {
        parts.push(`共 ${phaseCount} 个学习阶段`)
        if (plan.total_duration) {
          parts.push('我已为你拆解了职业路径步骤，点击右侧查看详情')
        }
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
        currentPhaseIndex.value = 0 // 当前激活第一个阶段
      }

      // 成长速度 / 打卡天数（估算值）
      if (phaseCount > 0 && plan.total_duration) {
        growthRate.value = `+${Math.min(phaseCount * 5, 50)}%`
      }

      // 能力雷达
      if (plan.current_level) {
        const vals = Object.values(plan.current_level)
        if (vals.length > 0) currentLevelData.value = vals
      }
      if (plan.target_level) {
        const vals = Object.values(plan.target_level)
        if (vals.length > 0) targetLevelData.value = vals
      }
      if (plan.dimensions) {
        radarIndicators.value = plan.dimensions.map((d) => ({ name: d, max: 100 }))
      }
    }
  } catch {
    ElMessage.warning('获取学习规划失败')
  }
}

const fetchDailyTasks = async () => {
  try {
    const { data } = await learningPlanApi.dailyTasks({ phase_index: 0 })
    if (data.daily_tasks) {
      todoList.value = data.daily_tasks.map((t, i) => ({
        id: t.id || i + 1,
        text: t.content || t.title || t.task,
        desc: t.description || t.desc || '',
        time: t.estimated_time || t.time || 30,
        difficulty: t.difficulty || '中等',
        completed: false,
        isAI: true,
      }))
    } else if (data.learning_plan?.phases) {
      // 从 learning_plan phases 提取任务
      const tasks = []
      data.learning_plan.phases.forEach((phase, pi) => {
        (phase.tasks || []).forEach((t, ti) => {
          tasks.push({
            id: tasks.length + 1,
            text: t.content || t.title || t.task,
            desc: t.description || t.desc || phase.name || '',
            time: t.estimated_time || 30,
            difficulty: t.difficulty || '中等',
            completed: false,
            isAI: true,
          })
        })
      })
      if (tasks.length > 0) todoList.value = tasks
    }
  } catch {
    // 从 generate 的返回中获取任务
  }
}

// 雷达图初始化
const initRadarChart = () => {
  if (!radarChartRef.value) return
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

// 生命周期
onMounted(async () => {
  await Promise.all([fetchLearningPlan(), fetchDailyTasks()])

  await nextTick()
  setTimeout(() => {
    initRadarChart()
    window.addEventListener('resize', handleResize)
  }, 200)
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

const toggleCoaching = () => {
  isCoachingOpen.value = !isCoachingOpen.value
}

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
    chatHistory.value.push({ role: 'assistant', content: '抱歉，AI 服务暂时不可用，请稍后再试。' })
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
  
  /* 原有所有卡片样式保留 */
  .glass-card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.7);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(112, 161, 255, 0.1);
    margin-bottom: 20px;
    overflow: hidden !important;

    :deep(.el-card__header) {
      border-bottom: 1px solid rgba(112, 161, 255, 0.1);
      padding: 15px 20px;
      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: bold;
        color: #1e293b;
        .el-icon { margin-right: 8px; color: #70a1ff; }
      }
    }
    
    :deep(.el-card__body) {
      overflow: hidden !important; 
    }
  }

  /* 原有其他所有样式保留 */
  .agent-command-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 25px;
    background: linear-gradient(90deg, rgba(112, 161, 255, 0.1) 0%, rgba(255,255,255,0.6) 100%);
    
    .agent-info {
      display: flex;
      align-items: center;
      gap: 15px;
      .agent-avatar {
        width: 45px; height: 45px;
        background: #70a1ff;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        .pulse-icon { animation: pulse 2s infinite; }
      }
      .agent-name { font-size: 12px; color: #70a1ff; font-weight: bold; }
      .message-text { margin: 0; font-size: 14px; color: #475569; }
    }
    
    .quick-stats {
      display: flex;
      align-items: center;
      gap: 20px;
      .stat-item {
        text-align: right;
        .label { font-size: 12px; color: #94a3b8; display: block; }
        .value { font-size: 18px; font-weight: bold; color: #70a1ff; }
      }
    }
  }

  .chart-wrapper {
    height: 380px;
    display: flex;
    flex-direction: column;
    align-items: center;
    .radar-chart { width: 100%; height: 320px; }
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

  .path-steps { padding: 20px 10px; height: 380px; }

  .todo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 15px;
    padding: 10px 0;
    
    .todo-item-card {
      background: rgba(255, 255, 255, 0.4);
      padding: 15px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      transition: all 0.3s;
      border: 1px solid transparent;
      
      &:hover { border-color: #70a1ff; background: white; }
      &.is-completed { opacity: 0.6; .todo-text { text-decoration: line-through; } }
      .todo-info { display: flex; flex-direction: column; gap: 4px; .todo-text { font-size: 14px; color: #334155; } .ai-tag { width: fit-content; border: none; } }
    }
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

    /* 删掉原本的 dialog-footer 样式，因为按钮已移入 input-area */

    .dialog-footer {
      padding: 16px 24px;
      border-top: 1px solid #f1f5f9;
      display: flex;
      justify-content: flex-end;
      .el-button { padding: 12px 24px; border-radius: 12px; }
    }
  }

  /* 3. 激活状态 */
  &.is-active .coaching-dialog {
    opacity: 1;
    visibility: visible;
    transform: scale(1);
  }

  /* 4. 遮罩层 */
  .dialog-overlay {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: rgba(15, 23, 42, 0.3);
    backdrop-filter: blur(4px);
    z-index: 2050;
  }
}

.equal-height {
  display: flex;
  align-items: stretch; /* 确保子项（el-col）高度一致 */
  margin-bottom: 20px !important;

  :deep(.el-col) {
    display: flex;
    flex-direction: column;
  }

  /* 强制卡片撑满 col 高度 */
  .glass-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    margin-bottom: 0; /* 移除间距防止溢出 */
  }

  /* 确保卡片内容区自动填充剩余空间 */
  :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
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
</style>