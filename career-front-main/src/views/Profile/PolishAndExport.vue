<template>
  <div class="report-export-page fade-in">
    <div class="main-layout glass-card">
      
      <div class="report-display-container" v-loading="pageLoading">
        <div class="paper-header">
          <input v-model="reportData.reportTitle" class="title-input" :readonly="!isEditing" />
          <div class="paper-meta">最后更新：{{ lastUpdateTime }} | 导师：AI Career Pilot</div>
        </div>
        
        <div class="paper-body">
          <el-input
            v-model="reportContent"
            type="textarea"
            :autosize="{ minRows: 22 }"
            :readonly="!isEditing"
            class="article-editor"
            placeholder="正在生成报告内容..."
          />
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
            <el-tag v-for="tag in ['更专业', '更精简', '突出技术', '润色摘要']" 
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
          <el-button :type="isEditing ? 'warning' : 'default'" class="wide-btn" @click="toggleEdit">
            <el-icon><EditPen v-if="!isEditing" /><Checked v-else /></el-icon>
            {{ isEditing ? '保存修改' : '进入手动编辑' }}
          </el-button>

          <el-button type="success" class="wide-btn download-btn" @click="handleDownload" :loading="downloadLoading">
            <el-icon><Download /></el-icon> 导出 PDF 最终版
          </el-button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import {
  MagicStick, EditPen, Download, Promotion,
  Checked, Clock, InfoFilled, RefreshLeft, QuestionFilled
} from '@element-plus/icons-vue'
import html2pdf from 'html2pdf.js'
import { learningPlanApi } from '@/api/learningPlan'

const props = defineProps({
  reportData: {
    type: Object,
    default: () => ({
      reportTitle: ''
    })
  }
})

const pageLoading = ref(true)
const reportContent = ref('')

// 从 learning_plan agent 获取报告
const fetchReport = async () => {
  try {
    const { data } = await learningPlanApi.generate({ plan_type: '长期' })
    if (data.learning_plan?.plan_text) {
      reportContent.value = data.learning_plan.plan_text
    } else if (data.learning_plan?.content) {
      reportContent.value = data.learning_plan.content
    } else if (data.export_text) {
      reportContent.value = data.export_text
    } else {
      reportContent.value = ''
    }
    ElMessage({ message: '职业规划报告已生成', type: 'success', plain: true })
  } catch {
    reportContent.value = ''
    ElMessage.warning('获取报告失败，请检查后端服务是否运行')
  } finally {
    pageLoading.value = false
  }
}

onMounted(() => {
  fetchReport()
})

// 状态管理
const polishNote = ref('')
const isEditing = ref(false)
const polishing = ref(false)
const downloadLoading = ref(false)
const lastUpdateTime = ref(new Date().toLocaleTimeString())




// 历史记录数据
const polishHistory = ref([])

// 逻辑：执行润色并存入历史
const handleAIPolish = async () => {
  if (!polishNote.value) return ElMessage.warning('请输入润色要求')
  polishing.value = true

  try {
    // 存档当前内容
    polishHistory.value.unshift({
      note: polishNote.value,
      content: reportContent.value,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      type: 'ai'
    })

    // 调用 learning_plan agent 润色
    const { data } = await learningPlanApi.polish({ user_feedback: polishNote.value })
    if (data.learning_plan?.plan_text) {
      reportContent.value = data.learning_plan.plan_text
    } else if (data.export_text) {
      reportContent.value = data.export_text
    } else if (data.result) {
      reportContent.value = data.result
    }

    polishing.value = false
    polishNote.value = ''
    lastUpdateTime.value = new Date().toLocaleTimeString()

    ElNotification({
      title: '润色完成',
      message: '旧版本已存入历史，可随时切换回滚',
      type: 'success',
      position: 'bottom-right'
    })
  } catch {
    ElMessage.error('润色失败，请重试')
    polishing.value = false
  }
}

// 逻辑：还原版本（含双向备份）
const restoreVersion = (item) => {
  // 1. 获取当前屏幕上的"即将被覆盖"的内容作为快照
  const currentSnapshot = {
    note: "还原前的当前版本",
    content: reportContent.value,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    type: 'user' // 绿色标签标记
  };

  // 2. 从历史列表中移除要还原的那一项
  const index = polishHistory.value.indexOf(item);
  if (index > -1) {
    polishHistory.value.splice(index, 1);
  }

  // 3. 将当前快照压入历史顶部
  polishHistory.value.unshift(currentSnapshot);

  // 4. 更新正文
  reportContent.value = item.content;
  lastUpdateTime.value = new Date().toLocaleTimeString();
  
  ElMessage.info('已切换版本，原内容已自动备份');
}

const toggleEdit = () => {
  isEditing.value = !isEditing.value
  if (!isEditing.value) ElMessage.success('手动修改已保存')
}

const handleDownload = async () => {
  downloadLoading.value = true

  // 首先调用 export API 获取最新内容
  try {
    const { data } = await learningPlanApi.export({})
    if (data.export_text) {
      reportContent.value = data.export_text
    }
  } catch {
    // 继续使用当前内容
  }

  const element = document.querySelector('.report-display-container')
  if (!element) {
    ElMessage.error('未找到报告内容')
    downloadLoading.value = false
    return
  }

  const opt = {
    margin: [10, 10],
    filename: `${props.reportData.reportTitle || '职业规划报告'}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, letterRendering: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }

  html2pdf()
    .set(opt)
    .from(element)
    .save()
    .then(() => {
      downloadLoading.value = false
      ElMessage.success('PDF 导出成功')
    })
    .catch((err) => {
      console.error('导出失败:', err)
      downloadLoading.value = false
      ElMessage.error('导出失败，请重试')
    })
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
    .title-input {
      border: none; outline: none; font-size: 26px; font-weight: bold; width: 100%; color: #1e293b;
      background: transparent;
    }
    .paper-meta { font-size: 12px; color: #94a3b8; margin-top: 5px; }
  }

  .article-editor {
    :deep(.el-textarea__inner) {
      border: none !important; box-shadow: none !important;
      padding: 0; font-size: 16px; line-height: 1.8; color: #334155;
      background: transparent;
    }
  }
}

.control-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow: hidden;

  /* 🌟 修正：统一 ai-assistant-box 样式，确保毛玻璃生效 */
  .ai-assistant-box {
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.2) !important; // 极高的透明度
    backdrop-filter: blur(12px) saturate(180%) !important;
    padding: 20px !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important; // 强调白色边缘
    box-shadow: none !important; // 去掉沉重的阴影
    margin-bottom: 0; // 移除多余间距

    /* 🌟 核心修改：输入框包装器模拟图一的纯白悬浮感 */
    .instruction-input-wrapper {
      background: #ffffff !important; // 改为纯白
      border-radius: 12px;
      padding: 12px;
      border: none !important; // 移除图二看到的灰色边框
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04) !important; // 极淡阴影增加层级
      
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
    background: rgba(255, 255, 255, 0.2) !important; // 极高的透明度
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
      transition: all 0.2s !important;
      &:nth-child(1) { background: rgba(165, 220, 252, 0.185) !important; color: #262626 !important; }
      &:nth-child(2) { background: rgba(253, 181, 230, 0.1) !important; color: #262626 !important; }
      &:nth-child(3) { background: rgba(198, 238, 198, 0.161) !important; color: #262626 !important; }
      &:nth-child(4) { background: rgba(253, 186, 116, 0.1) !important; color: #262626 !important; }
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

.wide-btn {
  background: linear-gradient(135deg, #f2fbfd 0%, #e6f7fc5d 100%) !important;
  border: 1.5px dashed #e2e8f0 !important;
  color: rgb(74, 72, 72) !important;
  width: 100% !important;
  max-width: 320px;
  height: 48px !important;
  margin: 0 !important;
  border-radius: 12px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-sizing: border-box !important;
  font-weight: bold;
  font-size: 14px;
  box-sizing: border-box;
  padding: 0 20px !important;
  .el-icon { margin-right: 8px; font-size: 16px; }
  &:hover {
    border-style: solid !important;
    border-color: #113354 !important;
    color: #0e2857 !important;
    background: white !important;
  }
}

.download-btn {
  margin: 0 !important;
  background: linear-gradient(135deg, #f2fbfd 0%, #e6f7fc5d 100%) !important;
  color: rgb(74, 72, 72) !important;
  font-weight: bold;
  box-shadow: 0 6px 18px rgba(45, 212, 191, 0.15) !important;
  &:hover { box-shadow: 0 8px 25px rgba(45, 212, 191, 0.25) !important; filter: saturate(1.1); }
}

.fade-in { animation: fadeIn 0.6s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>