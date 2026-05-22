<template>
  <div ref="chartRef" class="radar-chart-root"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [0, 0, 0, 0, 0, 0, 0] }
})

const chartRef = ref(null)
let myChart = null
let observer = null

const handleResize = () => myChart?.resize()

function doInit() {
  if (myChart || !chartRef.value) return true
  const el = chartRef.value
  if (el.offsetWidth === 0 || el.offsetHeight === 0) return false

  myChart = echarts.init(el)
  myChart.setOption({
    radar: {
      radius: '55%',
      center: ['50%', '55%'],
      indicator: [
        { name: '专业技能', max: 100 },
        { name: '创新能力', max: 100 },
        { name: '学习能力', max: 100 },
        { name: '实习能力', max: 100 },
        { name: '抗压能力', max: 100 },
        { name: '沟通能力', max: 100 },
        { name: '证书', max: 100 },
      ],
      shape: 'circle',
      splitNumber: 4,
      axisName: { color: '#64748b', fontSize: 11, padding: [2, 10] },
      splitLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } },
      splitArea: { show: false }
    },
    series: [{
      type: 'radar',
      data: [{
        value: props.data,
        name: '能力画像',
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { color: 'rgba(102, 126, 234, 0.4)', offset: 0 },
            { color: 'rgba(118, 75, 162, 0.6)', offset: 1 }
          ])
        },
        lineStyle: { color: '#4f46e5', width: 2 },
        itemStyle: { color: '#4f46e5', borderWidth: 0 },
        symbol: 'none'
      }],
      animationDuration: 1200
    }]
  })
  return true
}

watch(() => props.data, (newData) => {
  if (myChart) {
    myChart.setOption({ series: [{ data: [{ value: newData }] }] })
  }
}, { deep: true })

onMounted(async () => {
  await nextTick()
  requestAnimationFrame(() => {
    if (doInit()) return

    observer = new ResizeObserver(() => {
      if (doInit()) {
        observer?.disconnect()
        observer = null
      }
    })
    observer.observe(chartRef.value)
  })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  observer?.disconnect()
  observer = null
  myChart?.dispose()
  myChart = null
})
</script>

<style scoped>
.radar-chart-root {
  width: 100%;
  height: 100%;
}
</style>
