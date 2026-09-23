<script setup>
import OpeningEditor from '../components/OpeningEditor.vue'
// 洞口示意页默认展示种子房间（卧室，多种洞）；留边可就地编辑
const roomId = 2
</script>
<template><div class="page">
  <h1>洞口示意（种子房间 #{{ roomId }}）</h1>
  <p class="hint">框留边 = 洞口四周各减一条；扣除面积按<b>内口</b>（洞口宽高 − 两侧留边）计算。留边缺省 0。</p>
  <OpeningEditor :room-id="roomId" />
</div></template>
<style scoped>.hint { color:#446; font-size:.9rem; }</style>
