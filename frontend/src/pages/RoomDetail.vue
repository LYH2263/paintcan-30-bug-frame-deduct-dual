<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON } from '../api'
import OpeningEditor from '../components/OpeningEditor.vue'
const route = useRoute()
const room = ref(null)
const openings = ref([])
const openingsM2 = ref(null)
const load = async () => {
  const d = await getJSON(`/api/rooms/${route.params.id}`)
  room.value = d.room
  openings.value = d.openings || []
  // 与估漆回包同一套内口径（后端按精确内口积求和后取整）
  openingsM2.value = d.openings_m2 ?? Number(openings.value.reduce(
    (s, o) => o.invalid ? s : s + (o.w - 2 * (o.margin ?? 0)) * (o.h - 2 * (o.margin ?? 0)), 0).toFixed(2))
}
onMounted(load); watch(() => route.params.id, load)
</script>
<template><div class="page" v-if="room">
  <h1>{{ room.name }}</h1>
  <p>墙面 {{ room.length }}×{{ room.width }}×{{ room.height }} m</p>
  <p v-if="openings.length" class="muted">
    洞口扣除合计（内口径，与估漆一致）
    {{ Number(openingsM2 ?? 0).toFixed(2) }} m²
  </p>
  <OpeningEditor :room-id="route.params.id" />
</div></template>
