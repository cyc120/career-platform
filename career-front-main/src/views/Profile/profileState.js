import { ref, computed } from 'vue'

const DIMENSIONS = ['专业技能', '创新能力', '学习能力', '实习能力', '抗压能力', '沟通能力', '证书']

// 模块级变量 — SPA 内组件销毁重建时保留，页面刷新时重置
export const currentRadarData = ref([0, 0, 0, 0, 0, 0, 0])
export const dimensionDetailsRaw = ref(null)

export const dimensionDetails = computed(() => {
  if (dimensionDetailsRaw.value) return dimensionDetailsRaw.value
  return Object.fromEntries(DIMENSIONS.map(d => [d, { status: '待采集', desc: '请通过对话提供信息', type: 'info' }]))
})
