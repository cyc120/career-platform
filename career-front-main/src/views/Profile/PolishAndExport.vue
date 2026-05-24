<template>
  <div class="report-export-page fade-in">
    <div class="main-layout glass-card">

      <div class="report-display-container" v-loading="pageLoading">
        <div class="paper-header">
          <div class="title-text">职业分析报告</div>
          <div class="paper-meta">最后更新：{{ lastUpdateTime }} | 导师：AI Career Pilot</div>
        </div>

        <div class="paper-body">
          <div v-if="generating" class="generating-animation">
            <div class="gen-spinner">
              <div class="spinner-ring"></div>
              <div class="spinner-ring delay-1"></div>
              <div class="spinner-ring delay-2"></div>
            </div>
            <p class="gen-text">AI 正在分析你的个人数据并生成报告...</p>
            <p class="gen-sub">聚合画像、匹配、学习计划、职业规划等模块数据</p>
          </div>
          <div v-else-if="reportContent" class="report-text">{{ reportContent }}</div>
          <div v-else class="empty-hint">
            <el-icon><Document /></el-icon>
            <p>点击"生成报告"按钮，AI 将聚合你的所有数据生成完整职业分析报告</p>
          </div>
        </div>
      </div>

      <div class="control-panel">
        <div class="ai-assistant-box shadow-sm">
          <div class="panel-label">
            <el-icon><MagicStick /></el-icon> 智能润色指令
          </div>

          <div class="instruction-input-wrapper">
            <el-input
              v-model="polishNote"
              type="textarea"
              :rows="3"
              placeholder="输入修改要求，例如：'突出我的架构设计能力'..."
              resize="none"
            />
            <div class="input-footer">
              <el-button
                type="primary"
                @click="handleAIPolish"
                :loading="polishing"
                round
                size="small"
                class="execute-btn"
              >
                <el-icon><Promotion /></el-icon> 执行润色
              </el-button>
            </div>
          </div>

          <div class="quick-tags">
            <el-tag v-for="tag in ['更专业', '更精简', '突出技术', '增加细节', '调整语气']"
                    :key="tag" @click="polishNote = tag" class="tag-item">
              {{ tag }}
            </el-tag>
          </div>
        </div>

        <div class="history-module">
          <div class="panel-label">
            <div class="label-left">
              <el-icon><Clock /></el-icon> 润色历史记录
            </div>
            <el-tooltip content="还原前会自动备份当前版本">
              <el-icon class="info-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>

          <div class="history-list-container">
            <div v-if="polishHistory.length === 0" class="empty-history">
              <el-icon><InfoFilled /></el-icon> 暂无润色记录
            </div>

            <div
              v-for="(item, index) in polishHistory"
              :key="index"
              class="history-card"
              @click="restoreVersion(item)"
            >
              <div class="card-top">
                <span class="version-tag" :class="item.type === 'user' ? 'type-user' : 'type-ai'">
                  {{ item.type === 'user' ? '手动快照' : 'AI 润色' }}
                </span>
                <span class="time">{{ item.time }}</span>
              </div>
              <p class="history-note">"{{ item.note }}"</p>
              <div class="hover-mask">
                <el-icon><RefreshLeft /></el-icon> 切换到此版本
              </div>
            </div>
          </div>
        </div>

        <div class="action-group">
          <el-button type="primary" class="wide-btn generate-btn" @click="handleGenerate" :loading="generating">
            <el-icon><Document /></el-icon> 生成报告
          </el-button>

          <div class="export-row">
            <el-button class="export-btn" @click="handleExport('txt')" :loading="exportingTxt">
              <el-icon><Document /></el-icon> TXT
            </el-button>
            <el-button class="export-btn" @click="handleExport('docx')" :loading="exportingDocx">
              <el-icon><Notebook /></el-icon> Word
            </el-button>
            <el-button class="export-btn" @click="handleExport('pdf')" :loading="exportingPdf">
              <el-icon><Printer /></el-icon> PDF
            </el-button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import {
  MagicStick, Promotion, Clock, InfoFilled, RefreshLeft,
  QuestionFilled, Document, Notebook, Printer
} from '@element-plus/icons-vue'
import { reportApi } from '@/api/report'

const pageLoading = ref(false)
const generating = ref(false)
const polishing = ref(false)
const reportContent = ref('')
const polishNote = ref('')
const lastUpdateTime = ref('--')
const polishHistory = ref([])

const exportingTxt = ref(false)
const exportingDocx = ref(false)
const exportingPdf = ref(false)

onMounted(() => {
  pageLoading.value = false
})

const handleGenerate = async () => {
  generating.value = true
  try {
    const { data } = await reportApi.generate()
    if (data.report_text) {
      reportContent.value = data.report_text
      lastUpdateTime.value = new Date().toLocaleTimeString()
      ElMessage.success('报告生成成功')
    } else {
      ElMessage.warning('报告内容为空')
    }
  } catch {
    ElMessage.error('报告生成失败，请重试')
  } finally {
    generating.value = false
  }
}

const handleAIPolish = async () => {
  if (!polishNote.value) return ElMessage.warning('请输入润色要求')
  polishing.value = true

  try {
    polishHistory.value.unshift({
      note: polishNote.value,
      content: reportContent.value,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      type: 'ai',
    })

    const { data } = await reportApi.polish(polishNote.value)
    if (data.report_text) {
      reportContent.value = data.report_text
      lastUpdateTime.value = new Date().toLocaleTimeString()
    }

    polishNote.value = ''
    ElNotification({
      title: '润色完成',
      message: '旧版本已存入历史，可随时切换回滚',
      type: 'success',
      position: 'bottom-right',
    })
  } catch {
    ElMessage.error('润色失败，请重试')
  } finally {
    polishing.value = false
  }
}

const restoreVersion = (item) => {
  const currentSnapshot = {
    note: '还原前的当前版本',
    content: reportContent.value,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    type: 'user',
  }
  const index = polishHistory.value.indexOf(item)
  if (index > -1) polishHistory.value.splice(index, 1)
  polishHistory.value.unshift(currentSnapshot)
  reportContent.value = item.content
  lastUpdateTime.value = new Date().toLocaleTimeString()
  ElMessage.info('已切换版本，原内容已自动备份')
}

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const handleExport = async (format) => {
  const loadingMap = { txt: exportingTxt, docx: exportingDocx, pdf: exportingPdf }
  loadingMap[format].value = true
  try {
    const resp = await reportApi.exportFile(format)
    const extMap = { txt: 'txt', docx: 'docx', pdf: 'pdf' }
    downloadBlob(resp.data, `职业分析报告.${extMap[format]}`)
    ElMessage.success(`${format.toUpperCase()} 导出成功`)
  } catch {
    ElMessage.error('导出失败，请先生成报告')
  } finally {
    loadingMap[format].value = false
  }
}
</script>

<style scoped lang="scss">
.report-export-page {
  height: 90vh;
  padding: 20px;
  display: flex;
  justify-content: center;
  background: transparent;

  .main-layout {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 20px;
    width: 100%;
    max-width: 1260px;
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(20px) saturate(1.1);
    -webkit-backdrop-filter: blur(20px) saturate(1.1);
    border-radius: 24px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.45);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  }
}

.report-display-container {
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 40px 50px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);

  .paper-header {
    margin-bottom: 25px;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 15px;
    .title-text {
      font-size: 26px;
      font-weight: bold;
      color: #1e293b;
    }
    .paper-meta { font-size: 12px; color: #94a3b8; margin-top: 5px; }
  }

  .paper-body {
    .report-text {
      white-space: pre-wrap;
      word-wrap: break-word;
      font-size: 15px;
      line-height: 1.85;
      color: #334155;
    }
    .empty-hint {
      text-align: center;
      padding: 80px 0;
      color: #94a3b8;
      .el-icon { font-size: 48px; margin-bottom: 16px; }
      p { font-size: 14px; }
    }
    .generating-animation {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 100px 0;
      .gen-spinner {
        position: relative;
        width: 64px;
        height: 64px;
        margin-bottom: 28px;
        .spinner-ring {
          position: absolute;
          inset: 0;
          border: 3px solid transparent;
          border-top-color: #70a1ff;
          border-radius: 50%;
          animation: spin 1.2s linear infinite;
          &.delay-1 {
            inset: 6px;
            border-top-color: #a78bfa;
            animation-delay: 0.15s;
            animation-duration: 1s;
          }
          &.delay-2 {
            inset: 12px;
            border-top-color: #f472b6;
            animation-delay: 0.3s;
            animation-duration: 0.8s;
          }
        }
      }
      .gen-text {
        font-size: 16px;
        font-weight: 600;
        color: #334155;
        margin: 0 0 8px;
      }
      .gen-sub {
        font-size: 13px;
        color: #94a3b8;
        margin: 0;
      }
    }
  }
}

.control-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow: hidden;

  .ai-assistant-box {
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(12px) saturate(180%) !important;
    padding: 20px !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    box-shadow: none !important;

    .instruction-input-wrapper {
      background: #ffffff !important;
      border-radius: 12px;
      padding: 12px;
      border: none !important;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04) !important;

      :deep(.el-textarea__inner) {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0;
        font-size: 13px;
        color: #475569;
        &::placeholder { color: #cbd5e1; }
      }

      .input-footer {
        display: flex;
        justify-content: flex-end;
        margin-top: 8px;
      }
    }
  }

  .panel-label {
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
    color: #475569;
    .el-icon { color: #70a1ff; }
    .info-icon { color: #cbd5e1; font-size: 14px; cursor: help; }
  }

  .execute-btn {
    background: linear-gradient(135deg, #fffdea56 0%, #f5f5f8 100%) !important;
    border: none !important;
    color: rgb(12, 25, 66) !important;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(129, 140, 248, 0.15) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(129, 140, 248, 0.3) !important;
      filter: brightness(1.05);
    }
  }

  .history-module {
    flex: 1;
    background: rgba(255, 255, 255, 0.2) !important;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #eef2f6;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .history-list-container {
      flex: 1;
      overflow-y: auto;
      padding-right: 4px;

      .history-card {
        background: #b1bcc11f;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        cursor: pointer;
        position: relative;
        transition: 0.3s;
        border: 1px solid transparent;

        &:hover {
          background: #f0f7ff;
          border-color: #70a1ff;
          .hover-mask { opacity: 1; }
        }

        .card-top {
          display: flex;
          justify-content: space-between;
          margin-bottom: 6px;
          .version-tag {
            font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;
            &.type-ai { background: rgba(112, 161, 255, 0.1); color: #70a1ff; }
            &.type-user { background: rgba(16, 185, 129, 0.1); color: #10b981; }
          }
          .time { font-size: 10px; color: #94a3b8; }
        }

        .history-note { font-size: 12px; color: #080808; margin: 0; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }

        .hover-mask {
          position: absolute; inset: 0; background: rgba(205, 228, 238, 0.61);
          border-radius: 10px; display: flex; align-items: center; justify-content: center;
          color: rgb(18, 51, 111); font-size: 12px; font-weight: bold; gap: 5px; opacity: 0; transition: 0.3s;
          border: 1px solid #2a3242b2;
        }
      }
    }
  }

  .quick-tags {
    margin: 12px 0;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    .tag-item {
      border: 1px solid transparent !important;
      padding: 4px 12px !important;
      font-weight: 500;
      border-radius: 8px !important;
      cursor: pointer;
      transition: all 0.2s !important;
      &:nth-child(1) { background: rgba(165, 220, 252, 0.185) !important; color: #262626 !important; }
      &:nth-child(2) { background: rgba(253, 181, 230, 0.1) !important; color: #262626 !important; }
      &:nth-child(3) { background: rgba(198, 238, 198, 0.161) !important; color: #262626 !important; }
      &:nth-child(4) { background: rgba(253, 186, 116, 0.1) !important; color: #262626 !important; }
      &:nth-child(5) { background: rgba(200, 180, 255, 0.1) !important; color: #262626 !important; }
      &:hover { background: #ffffff !important; border-color: currentColor !important; transform: scale(1.05); }
    }
  }

  .action-group {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 100%;
    align-items: center;
    box-sizing: border-box;
  }
}

.generate-btn {
  background: linear-gradient(135deg, #9acaf679 0%, #f9ceee80 100%) !important;
  border: none !important;
  color: #1c3c74 !important;
  width: 100% !important;
  max-width: 320px;
  height: 48px !important;
  border-radius: 12px !important;
  font-weight: bold;
  font-size: 14px;
  .el-icon { margin-right: 8px; font-size: 16px; }
  &:hover {
    filter: brightness(1.08);
    box-shadow: 0 6px 20px rgba(112, 161, 255, 0.3) !important;
  }
}

.export-row {
  display: flex;
  gap: 8px;
  width: 100%;
  max-width: 320px;
}

.export-btn {
  flex: 1;
  background: linear-gradient(135deg, #f2fbfd 0%, #e6f7fc5d 100%) !important;
  border: 1.5px dashed #e2e8f0 !important;
  color: rgb(74, 72, 72) !important;
  height: 42px !important;
  border-radius: 10px !important;
  font-weight: 600;
  font-size: 12px;
  padding: 0 8px !important;
  .el-icon { margin-right: 4px; font-size: 14px; }
  &:hover {
    border-style: solid !important;
    border-color: #113354 !important;
    color: #0e2857 !important;
    background: white !important;
  }
}

.fade-in { animation: fadeIn 0.6s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
