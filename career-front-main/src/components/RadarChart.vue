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
      axisLine: { lineStyle: { color: 'rgba(80, 152, 249, 0.16)' } },
      splitLine: { lineStyle: { color: 'rgba(80, 152, 249, 0.12)' } },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(255,255,255,0.04)', 'rgba(80,152,249,0.05)']
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: props.data,
        name: '能力画像',
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { color: 'rgba(161, 196, 253, 0.35)', offset: 0 },
            { color: 'rgba(80, 152, 249, 0.42)', offset: 1 }
          ])
        },
        lineStyle: { color: '#5098f9', width: 2 },
        itemStyle: { color: '#5098f9', borderColor: '#fff', borderWidth: 1 },
        symbol: 'circle',
        symbolSize: 4
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
