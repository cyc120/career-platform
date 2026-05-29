<template>
  <div class="job-card">
    <!-- 岗位标题 -->
    <h3 class="job-title">{{ job.jobTitle }}</h3>
    
    <!-- 公司与薪资 -->
    <div class="job-info">
      <span class="company">{{ job.companyName }}</span>
      <span class="divider">|</span>
      <span class="salary">{{ job.salary }}</span>
    </div>

    <!-- 匹配度展示 -->
    <div class="match-section">
      <div class="match-rate" :style="{ color: getMatchColor(job.matchRate) }">
        {{ job.matchRate }}%
      </div>
      <div class="match-label">人岗匹配度</div>
    </div>

    <!-- 操作按钮 -->
    <el-button 
      class="analysis-btn" 
      size="small"
    >
      <el-icon class="btn-icon"><DataLine /></el-icon>
      查看岗位画像
    </el-button>
  </div>
</template>

<script setup>
// 定义组件接收的属性 (Props)
// 父组件必须传入一个 job 对象，包含 jobTitle, companyName, salary, matchRate
const props = defineProps({
  job: {
    type: Object,
    required: true,
    default: () => ({
      jobTitle: '未知岗位',
      companyName: '未知公司',
      salary: '面议',
      matchRate: 0
    })
  }
})

// 辅助函数：根据匹配度返回颜色
const getMatchColor = (rate) => {
  if (rate >= 90) return '#67C23A' // 绿色 - 高匹配
  if (rate >= 75) return '#E6A23C' // 橙色 - 中匹配
  return '#F56C6C' // 红色 - 低匹配
}
</script>

<style scoped>
/* 卡片容器样式 */
.job-card {
  position: relative;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px 18px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: auto;
  min-height: 150px;

 .job-card.is-active {
  background-color: #ecf5ff;
  border-color: #409EFF;
  position: relative; /* 别忘了这个，否则 before 会乱跑 */
}

.analysis-btn {
  width: 100%;
  margin-top: 8px;
  height: 32px;
  border-radius: 16px !important;
  border: 1px solid rgba(64, 158, 255, 0.3) !important;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%) !important;
  color: #409eff !important;
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.5px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;

  .btn-icon {
    font-size: 14px;
    transition: transform 0.3s;
  }

  &:hover {
    /* 悬浮时的状态：背景略微加深，投影增强 */
    background: linear-gradient(135deg, #e1f0ff 0%, #f0f7ff 100%) !important;
    border-color: #409eff !important;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2) !important;
    transform: translateY(-1px);

    .btn-icon {
      transform: scale(1.2) rotate(5deg);
    }
  }

  &:active {
    transform: translateY(1px);
    box-shadow: 0 2px 6px rgba(64, 158, 255, 0.1) !important;
  }
}

.job-card.is-active::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #409EFF;
  border-radius: 4px 0 0 4px;
}
}

/* 鼠标悬停效果 */
.job-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  border-color: #409EFF;
}

/* 标题样式 */
.job-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

/* 信息行样式 */
.job-info {
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.divider {
  margin: 0 8px;
  color: #dcdfe6;
}

/* 匹配度区域样式 */
.match-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.match-rate {
  font-size: 24px;
  font-weight: 800;
  line-height: 1;
}

.match-label {
  font-size: 11px;
  color: #909399;
}
</style>