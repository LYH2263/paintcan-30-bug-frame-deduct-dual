<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const open = ref({})
onMounted(async () => { items.value = (await getJSON('/api/history')).items })
const toggle = id => { open.value[id] = !open.value[id] }
</script>
<template><div class="page"><h1>估算记录</h1>
<p class="note">打开记录带回的是<b>钉选当时</b>的各洞扣除、净面积与升数；事后再改某洞留边，旧记录不会跟着变。</p>
<table>
  <tr><th>#</th><th>时间</th><th>房间</th><th>扣除合计 (m²)</th><th>净面积 (m²)</th><th>升数 (L)</th><th></th></tr>
  <tr v-for="h in items" :key="h.id">
    <td>#{{ h.id }}</td>
    <td>{{ h.created_at }}</td>
    <td>#{{ h.room_id }}</td>
    <td>{{ h.result?.openings_m2 ?? '—' }}</td>
    <td><b>{{ h.result?.net_m2 ?? '—' }}</b></td>
    <td>{{ h.result?.liters ?? '—' }}</td>
    <td><button v-if="h.result?.openings?.length" @click="toggle(h.id)">{{ open[h.id] ? '收起' : '各洞' }}</button></td>
  </tr>
</table>
<template v-for="h in items" :key="'d'+h.id">
  <div v-if="open[h.id] && h.result?.openings?.length" class="detail">
    <p class="dhead">记录 #{{ h.id }} 钉选时各洞（留边已固化）</p>
    <table>
      <tr><th>洞口</th><th>洞口宽×高</th><th>留边</th><th>内口宽×高</th><th>扣除 (m²)</th></tr>
      <tr v-for="o in h.result.openings" :key="o.id ?? o.kind">
        <td>{{ o.kind }}</td>
        <td>{{ o.w }}×{{ o.h }}</td>
        <td>{{ o.margin }}</td>
        <td>{{ o.inner_w }}×{{ o.inner_h }}</td>
        <td>{{ o.deduct_m2 }}</td>
      </tr>
    </table>
  </div>
</template>
</div></template>
<style scoped>
.note { color:#446; font-size:.9rem; }
.detail { margin:.25rem 0 .75rem 1rem; padding:.5rem; border:1px dashed #aacce0; }
.dhead { margin:.25rem 0; font-weight:700; }
</style>
