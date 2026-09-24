<script setup>
import { onMounted, ref, watch } from 'vue'
import { getJSON, postJSON, patchJSON } from '../api'

const props = defineProps({ roomId: { type: [Number, String], required: true } })
const emit = defineEmits(['updated'])

const detail = ref(null)
const est = ref(null)
const drafts = ref({})
const error = ref('')
const savingId = ref(null)

function errDetail(msg) {
  try { return JSON.parse(msg).detail || msg } catch { return msg }
}

const load = async () => {
  error.value = ''
  const id = +props.roomId
  try {
    detail.value = await getJSON(`/api/rooms/${id}`)
    drafts.value = {}
    for (const o of detail.value.openings) drafts.value[o.id] = String(o.margin ?? 0)
    est.value = await postJSON('/api/estimate', { room_id: id, persist: false })
  } catch (e) {
    // 房间当前存在内口 <=0 的洞：预览整单拒绝，仍允许编辑留边改回合法值
    est.value = null
    error.value = '当前存在非法洞口（内口不大于 0），估算已拒绝：' + errDetail(e.message)
  }
}
onMounted(load)
watch(() => props.roomId, load)

function draftOf(o) {
  const m = parseFloat(drafts.value[o.id])
  const margin = Number.isFinite(m) ? m : 0
  const iw = o.w - 2 * margin
  const ih = o.h - 2 * margin
  // 与估漆回包同一套内口口径：本洞扣除 = (w-2m)(h-2m)；内口非法时不显示
  const ok = iw > 0 && ih > 0
  const deduct = ok ? iw * ih : null
  return { margin, iw, ih, ok, deduct }
}

async function save(o) {
  const { margin, iw, ih } = draftOf(o)
  error.value = ''
  if (margin < 0) { error.value = `#${o.id} 留边不可为负`; return }
  if (iw <= 0 || ih <= 0) {
    error.value = `#${o.id} 内口 ${iw.toFixed(2)}×${ih.toFixed(2)} 不大于 0，整单拒绝且不写记录`
    return
  }
  savingId.value = o.id
  try {
    await patchJSON(`/api/openings/${o.id}/margin`, { margin })
    await load()
    emit('updated')
  } catch (e) {
    error.value = `#${o.id} 保存被拒：${errDetail(e.message)}`
    drafts.value[o.id] = String(o.margin ?? 0)
  } finally {
    savingId.value = null
  }
}
</script>

<template>
  <div>
    <p v-if="error" class="banner">{{ error }}</p>
    <table v-if="detail">
      <tr><th>洞口</th><th>洞口宽×高 (m)</th><th>单侧留边 (m)</th><th>内口宽×高 (m)</th><th>本洞扣除 (m²)</th><th></th></tr>
      <tr v-for="o in detail.openings" :key="o.id">
        <td>#{{ o.id }} {{ o.kind }}</td>
        <td>{{ o.w }}×{{ o.h }}</td>
        <td><input v-model="drafts[o.id]" type="number" min="0" step="0.01" style="width:5.5rem" @keyup.enter="save(o)" /></td>
        <td :class="{ bad: !draftOf(o).ok }">
          {{ draftOf(o).iw.toFixed(2) }}×{{ draftOf(o).ih.toFixed(2) }}
        </td>
        <td>{{ draftOf(o).deduct == null ? '—' : draftOf(o).deduct.toFixed(2) }}</td>
        <td><button :disabled="savingId === o.id" @click="save(o)">保存</button></td>
      </tr>
    </table>
    <p v-if="est" class="summary">
      墙面 {{ est.gross_m2 }} m² · 扣除合计 <b>{{ est.openings_m2 }} m²</b> ·
      净面积 <b>{{ est.net_m2 }} m²</b> · 需漆 <span class="hero-num">{{ est.liters }} L</span>（{{ est.coats }} 遍）
    </p>
  </div>
</template>

<style scoped>
.banner { background:#fde8e8; border:1px solid #d64545; color:#8a1f1f; padding:.5rem; }
.bad { color:#d64545; font-weight:700; }
.summary { margin-top:.75rem; }
</style>
