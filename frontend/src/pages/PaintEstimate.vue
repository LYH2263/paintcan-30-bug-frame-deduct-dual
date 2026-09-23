<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const room_id = ref(1)
const out = ref(null)
const error = ref('')

function errDetail(msg) {
  try { return JSON.parse(msg).detail || msg } catch { return msg }
}

const run = async () => {
  error.value = ''; out.value = null
  try {
    out.value = await postJSON('/api/estimate', { room_id: room_id.value, persist: true })
  } catch (e) {
    // 内口宽/高 <= 0：整单拒绝、不写记录
    error.value = '估算被拒（未写记录）：' + errDetail(e.message)
  }
}
</script>
<template><div class="page"><h1>估漆工作台</h1>
<label>房间ID <input v-model.number="room_id" /></label>
<button @click="run">估算并钉选</button>
<p v-if="error" class="banner">{{ error }}</p>
<div v-if="out">
  <p class="totals">
    墙面 {{ out.gross_m2 }} m² · 扣除合计 <b>{{ out.openings_m2 }} m²</b> ·
    净面积 <b>{{ out.net_m2 }} m²</b> · <span class="hero-num">{{ out.liters }} L</span>（{{ out.coats }} 遍 @ {{ out.coverage }} m²/L）
  </p>
  <table v-if="out.openings && out.openings.length">
    <tr><th>洞口</th><th>留边 (m)</th><th>内口宽×高 (m)</th><th>扣除 (m²)</th></tr>
    <tr v-for="o in out.openings" :key="o.id ?? o.kind">
      <td>{{ o.kind }}</td><td>{{ o.margin }}</td>
      <td>{{ o.inner_w }}×{{ o.inner_h }}</td><td>{{ o.deduct_m2 }}</td>
    </tr>
  </table>
  <p class="pinned">已钉选为记录 #{{ out.run_id }}；各洞扣除、净面积与升数固化，后续改留边不影响本记录。</p>
</div></div></template>
<style scoped>
.totals b { color: var(--line); }
.pinned { color:#446; font-size:.85rem; }
.banner { background:#fde8e8; border:1px solid #d64545; color:#8a1f1f; padding:.5rem; }
</style>
