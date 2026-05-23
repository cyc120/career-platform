<template>
  <div class="personal-center">
    <aside class="sidebar">
      <div class="avatar-placeholder">
        <el-avatar :size="80" :src="avatarUrl" />
      </div>
     <el-menu :default-active="activeTab" class="menu" @select="handleMenuSelect">
      <el-menu-item index="info">
        <el-icon><User /></el-icon>
        <span>个人信息</span>
      </el-menu-item>
      <el-menu-item index="match">
        <el-icon><Connection /></el-icon>
        <span>人岗匹配</span>
      </el-menu-item>
      <el-tooltip
        :disabled="hasMatchData"
        content="请先完成人岗匹配后再使用"
        placement="right"
      >
        <el-menu-item index="growth" :disabled="!hasMatchData" :class="{ 'is-disabled-custom': !hasMatchData }">
          <el-icon><TrendCharts /></el-icon>
          <span>成长追踪中心</span>
        </el-menu-item>
      </el-tooltip>
      <el-menu-item index="report-export">
        <el-icon><DocumentCopy /></el-icon>
        <span>报告优化与导出</span>
      </el-menu-item>
      <el-menu-item index="favorite" class="menu-item-bottom">
      <el-icon><Star /></el-icon>
      <span>目标岗位</span>
    </el-menu-item>
    </el-menu>
    </aside>

    <main class="main-content">
      <div class="content-wrapper">
        
        <template v-if="activeTab === 'info'">
          <div v-if="!isInfoFilled" class="ai-chat-layout">
            <div class="chat-dashboard-upper">
              <section class="chat-section">
                <div class="chat-header">
                  <div class="header-left">
                    <div class="status-indicator">
                      <span class="pulse-dot"></span>
                    </div>
                    <div class="header-text">
                      <h3 class="chat-title">职能助手</h3>
                    </div>
                  </div>
                    <div class="header-right">
                      <el-tooltip effect="dark" content="清空对话，重新填写信息" placement="top">
                        <el-button size="small" class="reset-btn" @click="handleReset">
                          重新填写
                        </el-button>
                      </el-tooltip>
                    </div>
                </div>

                <div ref="messageListRef" class="message-list">
                  <div v-for="(msg, idx) in chatMessages" :key="msg.id" :class="['message-item', msg.role]">
                    <div class="message-avatar">
                      <div v-if="msg.role === 'assistant'" :class="['ai-icon', { spinning: isStreaming && idx === chatMessages.length - 1 }]">
                        <el-icon><MagicStick /></el-icon>
                      </div>
                      <el-avatar v-else :size="36" src="https://ui-avatars.com/api/?name=User&background=667eea&color=fff" />
                    </div>

                    <div class="message-content-wrapper">
                      <div class="message-bubble">
                        {{ msg.content }}
                      </div>
                      <span class="message-time">刚刚</span>
                    </div>
                  </div>
                </div>

                <div class="chat-input-area">
                  <div class="input-container">
                    <el-input
                      v-model="inputValue"
                      type="textarea"
                      :rows="2"
                      placeholder="在此粘贴简历内容..."
                      resize="none"
                      @keydown.enter.prevent="handleSend"
                    />
                    <div class="input-footer">
                      <el-upload
                        action="#"
                        :auto-upload="false"
                        :show-file-list="false"
                        :on-change="handleFileChange"
                        :disabled="fileParsing"
                        accept=".pdf,.doc,.docx,.txt"
                      >
                        <el-button link icon="Upload" :disabled="fileParsing">
                          {{ fileParsing ? '解析中...' : (attachedFile ? '更换附件' : '上传附件') }}
                        </el-button>
                      </el-upload>

                      <div v-if="attachedFile" class="file-tag">
                        <el-tag :type="fileParsing ? 'warning' : 'success'" closable size="small" :disable-transitions="false" @close="removeFile">
                          <span v-if="fileParsing" class="parsing-indicator"></span>
                          {{ fileParsing ? `正在解析 ${attachedFile.name}...` : attachedFile.name }}
                        </el-tag>
                      </div>

                      <el-button
                        type="primary"
                        circle
                        icon="Promotion"
                        @click="handleSend"
                        :disabled="fileParsing || loading"
                        class="send-btn"
                      />
                    </div>
                  </div>
                </div>
              </section>

              <section class="dashboard-preview-section">
                <div class="artifact-card">
                  <div class="artifact-header">
                    <h4>实时画像预览</h4>
                    <div class="completion-status">
                      <span class="percentage">
                        {{ completionLabel }}
                      </span>
                      <span class="label">维度完善度 ({{ analyzedCount }}/7)</span>
                    </div>
                  </div>
                  
                  <div class="scroll-container">
                    <div class="preview-radar-placeholder">
                      <RadarChart :data="currentRadarData" />
                    </div>

                    <div v-if="analyzedCount > 0" class="dimension-grid">
                      <div
                        v-for="(val, key) in dimensionDetails"
                        :key="key"
                        :class="['dimension-card', val.type]"
                      >
                        <div class="dim-header">
                          <span class="dim-name">{{ key }}</span>
                          <span :class="['dim-status', val.type]">
                            {{ val.type === 'success' ? '✓' : '○' }} {{ val.status }}
                          </span>
                        </div>
                        <p class="dim-desc">{{ val.desc }}</p>
                      </div>
                    </div>

                    <p v-else class="empty-preview-tip">
                      请在左侧对话中完善个人信息，AI 将实时生成能力画像
                    </p>
                  </div>
                </div>
              </section>
            </div>

            <div class="bottom-action-bar">
              <el-button 
                type="primary" 
                class="analyze-btn" 
                size="large"
                @click="saveAndContinue"
                :loading="loading"
              >
                <el-icon class="el-icon--left"><MagicStick /></el-icon>
                保存并开始 AI 深度分析
              </el-button>
            </div>
          </div>
          <div v-else class="dashboard-result-view">
             <PersonalInfo :user-info="userInfo" @re-edit="isInfoFilled = false" />
          </div>
        </template>

        <div v-else-if="activeTab === 'match'" class="sub-page">
          <JobMatch />
        </div>
        <div v-else-if="activeTab === 'growth' && hasMatchData" class="sub-page">
          <GrowthTracker :key="selectedJob?.job_title || 'default'" />
        </div>
        <div v-else-if="activeTab === 'growth' && !hasMatchData" class="sub-page">
          <div class="empty-state">
            <el-empty description="请先完成人岗匹配后再使用成长追踪中心" />
          </div>
        </div>
        <div v-else-if="activeTab === 'report-export'" class="sub-page">
          <PolishAndExport />
        </div>
        <div v-else-if="activeTab === 'favorite'" class="sub-page">
          <FavoriteJobs />
        </div>
        
      </div>
    </main>
  </div>
</template>

<script>
// 模块级状态 — SPA 内组件销毁重建时保留
const _moduleState = {
  chatMessages: [],
  chatGreeted: false,
  currentStepIndex: 0,
  userInfo: { name: '', email: '', rawResumeText: '', school: '' },
}
</script>

<script setup>
import { ref, nextTick, computed, onMounted, onUnmounted, provide } from 'vue'
import { Upload, Connection, User, TrendCharts, DocumentCopy, Star, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { learningPlanApi } from '@/api/learningPlan'
import * as mammoth from 'mammoth'

// 导入你的子组件
import PersonalInfo from './PersonalInfo.vue'
import GrowthTracker from './GrowthTracker.vue'
import PolishAndExport from './PolishAndExport.vue'
import FavoriteJobs from './FavoriteJobs.vue'
import JobMatch from './JobMatch.vue'
import RadarChart from '../../components/RadarChart.vue'
import { currentRadarData, dimensionDetailsRaw, dimensionDetails } from './profileState.js'
const attachedFile = ref(null) // 存储文件对象
const fileExtractedText = ref('') // 从文件中提取的文本
const fileParsing = ref(false) // 文件解析中

// 🌟 从文件中提取文本内容
const extractFileText = async (file) => {
  const ext = file.name.split('.').pop().toLowerCase()

  if (ext === 'txt') {
    return await file.text()
  }

  if (ext === 'docx') {
    const buffer = await file.arrayBuffer()
    const result = await mammoth.extractRawText({ arrayBuffer: buffer })
    return result.value
  }

  // PDF / doc 等格式：转 base64 发给后端解析
  if (ext === 'pdf' || ext === 'doc') {
    const base64 = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const dataUrl = reader.result
        resolve(dataUrl.split(',')[1])
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    })

    const token = localStorage.getItem('access_token')
    const resp = await fetch('http://localhost:8000/api/v1/learning-plan/parse-file', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ filename: file.name, base64 }),
    })

    if (!resp.ok) throw new Error('文件解析服务异常')
    const data = await resp.json()
    if (!data.success) throw new Error(data.error || '解析失败')
    return data.text
  }

  throw new Error(`不支持的文件格式: .${ext}`)
}

// 🌟 处理文件选择逻辑
const handleFileChange = async (file) => {
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('上传附件大小不能超过 5MB!')
    return
  }

  attachedFile.value = file.raw
  fileExtractedText.value = ''
  fileParsing.value = true

  try {
    const text = await extractFileText(file.raw)
    fileExtractedText.value = text
    ElMessage.success(`已解析附件: ${file.name}，${text.length}字`)
  } catch (err) {
    console.error('[Upload] File extraction failed:', err)
    ElMessage.error(err.message || '文件解析失败')
    attachedFile.value = null
    fileExtractedText.value = ''
  } finally {
    fileParsing.value = false
  }
}

// 🌟 移除附件逻辑
const removeFile = () => {
  attachedFile.value = null
  fileExtractedText.value = ''
  fileParsing.value = false
}

const activeTab = ref('info')
const loading = ref(false)
const isStreaming = ref(false)
const inputValue = ref('')
const messageListRef = ref(null)
const avatarUrl = ref('https://ui-avatars.com/api/?name=User&size=120&background=409EFF&color=fff')

const userInfo = ref(_moduleState.userInfo)

// isInfoFilled 不持久化，切回来时显示聊天界面
const isInfoFilled = ref(false)

// 匹配数据状态 — 控制成长追踪中心是否可用
const hasMatchData = ref(false)
provide('hasMatchData', hasMatchData)

// 当前锁定的岗位 — 成长追踪中心根据此岗位刷新数据
const selectedJob = ref(null)
provide('selectedJob', selectedJob)

// --- 聊天状态（使用模块级数据，SPA 内切换保留） ---
const currentStepIndex = ref(_moduleState.currentStepIndex)
const chatMessages = ref(_moduleState.chatMessages)
const chatGreeted = ref(_moduleState.chatGreeted)

// AI 初始问候 — 固定开场白
const GREETING_TEXT = `你好！我是你的职能助手 👋

我可以帮你分析职业画像、评估岗位匹配度。请告诉我：

1. 你的学校和专业是什么？
2. 你目前大几 / 研几？
3. 你的目标方向是什么？（如前端、后端、算法、AI、产品等）

直接回复即可，我会根据你的信息生成专属画像分析。`

const initChatGreeting = () => {
  if (chatGreeted.value) return
  chatGreeted.value = true
  chatMessages.value.push({ id: Date.now(), role: 'assistant', content: GREETING_TEXT })
}

onMounted(() => {
  // 已有聊天记录则跳过问候
  if (chatMessages.value.length === 0) {
    initChatGreeting()
  }
  // 检查是否有实际的匹配缓存数据，且用户已填写个人信息（雷达数据不全为0）
  try {
    const raw = sessionStorage.getItem('job_match_cache')
    const hasRadarData = currentRadarData.value && currentRadarData.value.some(v => v > 0)
    if (raw && hasRadarData) {
      const cached = JSON.parse(raw)
      hasMatchData.value = cached.results && cached.results.length > 0
    } else {
      hasMatchData.value = false
    }
  } catch {
    hasMatchData.value = false
  }
})

// 组件销毁前同步状态到模块级变量
onUnmounted(() => {
  _moduleState.chatMessages = chatMessages.value
  _moduleState.chatGreeted = chatGreeted.value
  _moduleState.currentStepIndex = currentStepIndex.value
  Object.assign(_moduleState.userInfo, userInfo.value)
})

// 🌟 修复核心：确保菜单选择逻辑能干净地切换 activeTab
const handleMenuSelect = (index) => {
  // 人岗匹配未完成时，禁止切换到成长追踪中心
  if (index === 'growth' && !hasMatchData.value) {
    ElMessage.warning('请先完成人岗匹配后再使用成长追踪中心')
    return
  }
  activeTab.value = index
}

// 重新填写：清空对话，重置画像
const handleReset = () => {
  // 清空聊天记录
  chatMessages.value = []
  chatGreeted.value = false
  currentStepIndex.value = 0
  inputValue.value = ''
  attachedFile.value = null
  fileExtractedText.value = ''

  // 重置画像数据
  currentRadarData.value = [0, 0, 0, 0, 0, 0, 0]
  dimensionDetailsRaw.value = null

  // 清空模块级状态
  _moduleState.chatMessages = []
  _moduleState.chatGreeted = false
  _moduleState.currentStepIndex = 0

  // 重新发起问候
  initChatGreeting()
  ElMessage.success('已重置，请重新填写信息')
}

// 🌟 发送消息：真实 AI 驱动
const handleSend = async () => {
  if (fileParsing.value) {
    ElMessage.warning('附件正在解析中，请稍后')
    return
  }
  if (!inputValue.value.trim() && !attachedFile.value) {
    ElMessage.warning('请输入内容或上传简历附件')
    return
  }

  let displayContent = inputValue.value
  const extractedText = fileExtractedText.value
  if (attachedFile.value) {
    displayContent += displayContent ? `\n[附件: ${attachedFile.value.name}]` : `[附件: ${attachedFile.value.name}]`
  }

  chatMessages.value.push({
    id: Date.now(),
    role: 'user',
    content: displayContent,
    time: new Date().toLocaleTimeString()
  })

  if (inputValue.value) {
    userInfo.value.rawResumeText += inputValue.value
  }

  inputValue.value = ''
  attachedFile.value = null
  fileExtractedText.value = ''

  // 推送空的 AI 消息占位，后续逐字填充
  const aiMsg = { id: Date.now() + 1, role: 'assistant', content: '' }
  chatMessages.value.push(aiMsg)

  loading.value = true
  isStreaming.value = true
  await scrollToBottom()

  try {
    const history = chatMessages.value
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(0, -2) // exclude current user msg and empty assistant msg
      .map(m => ({ role: m.role, content: m.content }))

    const userTyped = displayContent.replace(/\[附件:.*?\]/g, '').trim()
    let userText = userTyped
    if (extractedText) {
      userText = userTyped
        ? `${userTyped}\n\n以下是我的简历内容：\n${extractedText}`
        : `以下是我的简历内容：\n${extractedText}`
    }

    await learningPlanApi.coachStream(
      userText || '请分析我的简历',
      history,
      { previous_radar_data: currentRadarData.value, previous_details: dimensionDetailsRaw.value },
      // onToken: 逐字追加
      (token) => {
        aiMsg.content += token
        scrollToBottom()
      },
      // onRadar: 更新画像
      (radar) => {
        console.log('[Coach] Radar event received:', radar)
        if (radar.radar_data) currentRadarData.value = radar.radar_data
        if (radar.dimension_details && Object.keys(radar.dimension_details).length > 0) {
          dimensionDetailsRaw.value = radar.dimension_details
          currentStepIndex.value = 2
        }
        console.log('[Coach] Radar updated, currentRadarData:', currentRadarData.value)
      },
      // onDone
      null
    )

    if (!aiMsg.content) {
      aiMsg.content = '抱歉，暂时无法回复。'
    }
  } catch (err) {
    console.error('[Coach] Send failed:', err)
    aiMsg.content = aiMsg.content || '抱歉，AI 服务暂时不可用，请稍后再试。'
  } finally {
    loading.value = false
    isStreaming.value = false
    await scrollToBottom()
  }
}

const saveAndContinue = () => {
  // 检查已分析维度数量，少于4个不允许深度分析
  const details = dimensionDetails.value
  const analyzedCount = Object.values(details).filter(d => d.status === '已分析').length
  if (analyzedCount < 4) {
    ElMessage.warning(`当前仅有 ${analyzedCount} 个维度已分析，请至少补充到 4 个维度后再进行深度分析`)
    return
  }
  isInfoFilled.value = true
  ElMessage.success('简历保存成功！')
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) messageListRef.value.scrollTop = messageListRef.value.scrollHeight
}

// dimensionDetails 已从 profileState.js 导入

const analyzedCount = computed(() => {
  const details = dimensionDetails.value
  if (!details) return 0
  return Object.values(details).filter(d => d.status === '已分析').length
})

const completionLabel = computed(() => {
  const n = analyzedCount.value
  if (n === 0) return '--'
  if (n <= 3) return '建议继续补充'
  if (n <= 5) return '完善度较高'
  return '已完善可分析'
})
</script>

<style scoped lang="scss">
.personal-center {
  display: flex;
  min-height: 100vh;
  background: #f0f2f8;
  background-image:
    radial-gradient(at 20% 20%, rgba(102, 126, 234, 0.08) 0px, transparent 50%),
    radial-gradient(at 80% 80%, rgba(118, 75, 162, 0.06) 0px, transparent 50%),
    radial-gradient(at 50% 50%, rgba(64, 158, 255, 0.04) 0px, transparent 60%);
}

/* 侧边栏整体重构 */
.sidebar {
  width: 240px;
  height: 100vh;
  background: linear-gradient(180deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.06) 50%, rgba(255, 255, 255, 0.3) 100%);
  backdrop-filter: blur(24px) saturate(1.2);
  -webkit-backdrop-filter: blur(24px) saturate(1.2);
  border-right: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  z-index: 100;
  box-shadow: 4px 0 20px rgba(102, 126, 234, 0.06);

  .avatar-placeholder {
    padding: 40px 0 28px;
    text-align: center;

    .el-avatar {
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.25);
      border: 3px solid rgba(255, 255, 255, 0.9);
      transition: all 0.3s ease;
      &:hover {
        transform: scale(1.08);
        box-shadow: 0 12px 32px rgba(102, 126, 234, 0.35);
      }
    }
  }

  /* 菜单样式定制 */
  .el-menu {
    border: none;
    background: transparent;
    padding: 0 12px 20px;
    display: flex;
    flex-direction: column;
    height: calc(100% - 140px);

    .el-menu-item {
      height: 48px;
      line-height: 48px;
      margin-bottom: 6px;
      border-radius: 14px;
      color: #475569;
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;

      &::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 3px;
        height: 100%;
        background: linear-gradient(180deg, #667eea, #764ba2);
        border-radius: 0 4px 4px 0;
        opacity: 0;
        transition: opacity 0.25s ease;
      }

      :deep(.el-icon) {
        font-size: 18px;
        transition: all 0.25s ease;
      }

      span {
        font-weight: 500;
        margin-left: 8px;
        font-size: 14px;
      }

      /* 鼠标悬停 */
      &:hover {
        background: rgba(102, 126, 234, 0.1) !important;
        color: #4f46e5;

        :deep(.el-icon) {
          color: #667eea;
        }
      }

      /* 激活状态 */
      &.is-active {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%) !important;
        color: #4f46e5 !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);

        &::before {
          opacity: 1;
        }

        :deep(.el-icon) {
          color: #667eea;
        }
      }

&.menu-item-bottom {
  margin-top: auto !important;
  margin-bottom: 16px;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;

  span {
    font-size: 14px;
    color: #475569;
    transition: all 0.25s ease;
  }

  :deep(.el-icon) {
    font-size: 18px;
    color: #64748b;
    transition: all 0.25s ease;
  }

  &:hover {
    background: transparent !important;
    transform: none !important;

    span {
      color: #667eea !important;
      font-weight: 600 !important;
    }

    :deep(.el-icon) {
      color: #667eea !important;
    }
  }

  &.is-active {
    background: transparent !important;
    box-shadow: none !important;

    span {
      color: #4f46e5 !important;
      font-weight: 700 !important;
    }

    :deep(.el-icon) {
      color: #4f46e5 !important;
      font-size: 20px !important;
    }
  }
}
    }
  }
}

/* 找到 .chat-section 下的 .chat-header 样式进行替换 */
.chat-header {
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    /* 🌟 AI 状态指示器样式 */
    .status-indicator {
      width: 14px;
      height: 14px;
      display: flex;
      align-items: center;
      justify-content: center;

      .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #67c23a; /* ElementPlus 成功绿色 */
        border-radius: 50%;
        position: relative;
        box-shadow: 0 0 6px #67c23a;

        /* 呼吸灯动画效果 */
        &::after {
          content: "";
          width: 100%;
          height: 100%;
          background-color: #67c23a;
          border-radius: 50%;
          position: absolute;
          left: 0;
          top: 0;
          animation: pulse 2s infinite ease-in-out;
          opacity: 0.8;
        }
      }
    }

    .header-text {
      display: flex;
      flex-direction: column;

      .chat-title {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #1e293b; /* 更高级的灰黑色 */
        line-height: 1.2;
      }

      .ai-status-desc {
        font-size: 11px;
        color: #94a3b8; /* 较浅的灰色 */
        margin-top: 2px;
      }
    }
  }

  .header-right {
    .reset-btn {
      padding: 0 12px;
      height: 28px;
      line-height: 26px;
      border-radius: 14px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: rgba(28, 61, 111, 0.08) !important;
      color: #161e5d !important;
      border: 1px solid rgba(118, 75, 162, 0.2) !important;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        background: rgba(28, 61, 111, 0.15) !important;
        transform: scale(1.05);
      }
    }
  }
}

/* 呼吸灯动画 */
@keyframes pulse {
  0% { transform: scale(1); opacity: 0.8; }
  70% { transform: scale(2.5); opacity: 0; }
  100% { transform: scale(1); opacity: 0; }
}

/* 增强主内容区的呼吸感 */
.main-content {
  flex: 1;
  padding: 24px;
  background: transparent;
  overflow-y: auto;
  position: relative;

  &::before {
    content: "";
    position: fixed;
    top: 0;
    left: 260px;
    right: 0;
    bottom: 0;
    background:
      radial-gradient(circle at 20% 30%, rgba(102, 126, 234, 0.06) 0%, transparent 40%),
      radial-gradient(circle at 80% 70%, rgba(118, 75, 162, 0.05) 0%, transparent 40%),
      radial-gradient(circle at 50% 50%, rgba(64, 158, 255, 0.03) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }
}


/* 1. 整体布局容器 */
/* 1. 调整外层，确保它占据整个屏幕高度，并去掉可能存在的干扰 */
.ai-chat-layout {
  display: flex;
  flex-direction: column;
  /* 调小画布并居中 */
  width: 95%; 
  margin: 0 auto;
  /* 锁定高度，确保不超出屏幕产生滚动 */
  height: 90vh; 
  gap: 20px;
  overflow: hidden;
}

/* 2. 第一行：强制子元素高度同步 */
.chat-dashboard-upper {
  display: flex;
  gap: 24px;
  flex: 1;             /* 占据除按钮外的剩余高度 */
  min-height: 0;       /* 必须设置，否则 flex 内部滚动失效 */
  align-items: stretch; /* 强制左右两个 section 高度拉伸至一致 */
}

/* 3. 左侧对话框：内部结构调整 */
.chat-section {
  flex: 1.2;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(20px) saturate(1.1);
  -webkit-backdrop-filter: blur(20px) saturate(1.1);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.6);


  .message-list {
    flex: 1;           /* 核心：占据中间所有剩余空间 */
    overflow-y: auto;   /* 只有这里产生滚动 */
    padding: 20px;
  }
}

/* 4. 右侧看板：这是你之前失败的关键点 */
.dashboard-preview-section {
  flex: 0.8;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border-radius: 24px;

  .artifact-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(20px) saturate(1.1);
    -webkit-backdrop-filter: blur(20px) saturate(1.1);
    border-radius: 24px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);

    /* 让内部的雷达图占位符也撑开 */
    .preview-radar-placeholder {
      flex: 1;         /* 让虚线框区域自动垂直拉伸 */
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 20px;
      border: 2px dashed rgba(0, 0, 0, 0.05);
      margin: 20px 0;
    }
  }
}

/* 5. 底部按钮区域 */
.bottom-action-bar {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  padding: 10px 0;

.analyze-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: #fff !important;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  border-radius: 14px;
  padding: 12px 32px !important;
  font-weight: 600;
  letter-spacing: 0.5px;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(102, 126, 234, 0.45);
  }

  &:active {
    transform: translateY(0);
  }
}
}

/* 消息列表气泡样式优化 */
/* 消息列表基础布局 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 30px; /* 增加内边距更显高级 */
  display: flex;
  flex-direction: column;
  gap: 24px;

  /* 自定义滚动条样式，更细更轻盈 */
  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.05); border-radius: 10px; }

  .message-item {
    display: flex;
    gap: 12px;
    max-width: 85%;
    align-items: flex-start;

    /* AI 助手样式 */
    &.assistant {
      align-self: flex-start;
      .ai-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
      }
      .message-bubble {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        color: #334155;
        border-radius: 16px 16px 16px 4px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.6);
      }
    }

    /* 用户样式 */
    &.user {
      flex-direction: row-reverse;
      align-self: flex-end;
      .message-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 16px 16px 4px 16px;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.25);
      }
      .message-time { text-align: right; }
    }
  }

  .message-content-wrapper {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .message-bubble {
    padding: 12px 18px;
    font-size: 14.5px;
    line-height: 1.6;
    word-break: break-word;
    position: relative;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-1px);
    }
  }

  .message-time {
    font-size: 11px;
    color: #94a3b8;
    padding: 0 4px;
  }
}

/* 消息输入区域轻量化 */
.chat-input-area {
  padding: 24px;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.4);

  .input-container {
    background: rgba(255, 255, 255, 0.7);
    padding: 12px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;

    &:focus-within {
      border-color: #667eea;
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.12);
    }

    :deep(.el-textarea__inner) {
      border: none;
      box-shadow: none;
      font-size: 14px;
      color: #1e293b;
      &::placeholder { color: #cbd5e1; }
    }
  }
}

.input-footer {
  display: flex;
  justify-content: space-between; /* 关键：这会让上传按钮在左，发送按钮在右 */
  align-items: center;
  margin-top: 12px;
  padding: 0 4px;
  gap: 12px; // 按钮和标签之间的间距

  /* 上传按钮样式优化 */
  :deep(.el-button--text) {
    color: #94a3b8;
    &:hover { color: #764ba2; }
  }

  .file-tag {
    flex: 1; // 让文件名占据剩余空间
    display: flex;
    align-items: center;

    :deep(.el-tag) {
      background: rgba(102, 126, 234, 0.1);
      border: 1px solid rgba(102, 126, 234, 0.2);
      color: #4f46e5;
    }
    :deep(.el-tag--warning) {
      background: rgba(230, 162, 60, 0.1);
      border: 1px solid rgba(230, 162, 60, 0.3);
      color: #e6a23c;
    }
  }
  .parsing-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid rgba(230, 162, 60, 0.3);
    border-top-color: #e6a23c;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 4px;
    vertical-align: middle;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  /* 发送按钮美化 */
  .send-btn {
    width: 40px;
    height: 40px;
    border: none;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.35);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      transform: scale(1.1);
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.45);
    }

    &:active {
      transform: scale(0.95);
    }

    :deep(.el-icon) {
      font-size: 18px;
    }
  }
}

/* 顺便优化一下输入框容器，增加整体高级感 */
.input-container {
  background: rgba(255, 255, 255, 0.7);
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;

  &:focus-within {
    border-color: #667eea !important;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.12);
  }
}


/* AI 加载动效 */
.spinning { animation: rotate 2s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.loading-dots span {
  width: 5px; height: 5px; background: #94a3b8; border-radius: 50%; display: inline-block;
  margin: 0 2px; animation: bounce 1.4s infinite ease-in-out;
  &:nth-child(1) { animation-delay: -0.32s; }
  &:nth-child(2) { animation-delay: -0.16s; }
}
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.dashboard-preview-section {
  flex: 0.8;
  .artifact-card {
    height: 100%;
    background: rgba(255,255,255,0.4);
    border-radius: 20px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.8);
  }
  .preview-radar-placeholder {
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed rgba(0,0,0,0.05);
    border-radius: 20px;
    margin-top: 20px;
    color: #94a3b8;
  }
}

.sub-page {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

.dashboard-result-view {
  animation: slideUp 0.6s ease-out;
  padding: 20px;
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(16px) saturate(1.1);
  -webkit-backdrop-filter: blur(16px) saturate(1.1);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.4);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.artifact-header {
  display: flex;
  justify-content: space-between; /* 🌟 关键：将标题推向左边，数值推向右边 */
  align-items: flex-start;       /* 顶部对齐 */
  margin-bottom: 20px;

  .completion-status {
    text-align: right;           /* 文字向右对齐 */
    
    .percentage {
      display: block;
      font-size: 20px;
      font-weight: 700;
      color: #6366f1;            /* 使用你的主题紫色 */
      line-height: 1;
    }

    .label {
      font-size: 11px;
      color: #94a3b8;            /* 辅助说明文字颜色 */
      margin-top: 4px;
      display: block;
    }
  }
}

/* 看板头部完成度 */
.artifact-card {
  height: 100%; /* 保持容器高度由父级决定，不被内容撑开 */
  display: flex;
  flex-direction: column;
  overflow: hidden; // 确保外层不出现滚动条
}

/* 🌟 核心：滚动区域样式 */
.scroll-container {
  flex: 1; // 自动占满剩余高度
  overflow-y: auto; // 内容超出时显示滚动条
  padding-right: 8px; // 为滚动条留出一点空隙，防止遮挡内容

  /* 美化滚动条 (可选) */
  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    border-radius: 10px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

/* 保持雷达图有固定高度，不会因为滚动而坍塌 */
.preview-radar-placeholder {
  height: 300px;
  min-height: 300px;
  width: 100%;
  min-width: 0;
}

/* 核心亮点标签 */
.highlight-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  
  .glow-tag {
    border-radius: 6px;
    background: rgba(99, 102, 241, 0.05);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #6366f1;
  }
}

/* AI 建议区域 */
.ai-suggestions {
  margin-top: 15px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  border-left: 4px solid #6366f1;

  .suggestion-title {
    font-size: 13px;
    font-weight: 600;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 4px;
  }

  .suggestion-text {
    font-size: 12px;
    color: #64748b;
    line-height: 1.5;
    margin: 0;
  }
}

/* 缩小雷达图容器以适应新内容 */
.preview-radar-placeholder {
  height: 260px !important; /* 稍微减小高度给文字腾空间 */
  margin: 10px 0 !important;
}

.dimension-grid {
  display: grid;
  grid-template-columns: 1fr; // 单列布局，如果想两列可以改用 1fr 1fr
  gap: 10px;
  margin-top: 15px;
}

/* 找到 Index.vue 最后的 <style> 部分，替换原本的 .dimension-card 相关样式 */
.dimension-card {
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
  border: 1px solid transparent;
  transition: all 0.3s ease;

  // 🌟 状态 1：已完善 (绿色)
  &.success {
    background: rgba(16, 185, 129, 0.08); // 浅绿背景
    border-color: rgba(16, 185, 129, 0.2);
    .dim-status { color: #10b981; }
    .dim-desc { color: #065f46; }
  }

  // 🌟 状态 2：不清楚 (橙色)
  &.warning {
    background: rgba(245, 158, 11, 0.08); // 浅橙背景
    border-color: rgba(245, 158, 11, 0.2);
    .dim-status { color: #f59e0b; }
    .dim-desc { color: #92400e; }
  }

  // 🌟 状态 3：未提及 (灰色)
  &.info {
    background: rgba(148, 163, 184, 0.08); // 浅灰背景
    border-color: rgba(148, 163, 184, 0.2);
    .dim-status { color: #64748b; }
    .dim-desc { color: #475569; }
  }

  .dim-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    
    .dim-name {
      font-size: 14px;
      font-weight: 600;
      color: #1e293b;
    }
    
    .dim-status {
      font-size: 12px;
      font-weight: 700;
    }
  }

  .dim-desc {
    font-size: 12px;
    line-height: 1.5;
    margin: 0;
  }
}

// 自定义禁用状态样式
.is-disabled-custom {
  opacity: 0.5;
  cursor: not-allowed !important;

  &:hover {
    background-color: transparent !important;
  }
}

// 空状态样式
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(16px) saturate(1.1);
  -webkit-backdrop-filter: blur(16px) saturate(1.1);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.4);
}

</style>