<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON } from '../api'
import OpeningEditor from '../components/OpeningEditor.vue'
const route = useRoute()
const room = ref(null)
const openings = ref([])
const detail = ref(null)
const load = async () => {
  detail.value = await getJSON(`/api/rooms/${route.params.id}`)
  room.value = detail.value.room
  openings.value = detail.value.openings || []
}
onMounted(load); watch(() => route.params.id, load)
</script>
<template><div class="page" v-if="room">
  <h1>{{ room.name }}</h1>
  <p>墙面 {{ room.length }}×{{ room.width }}×{{ room.height }} m</p>
  <p v-if="openings.length" class="muted">
    洞口内口扣除合计
    {{ (detail.openings_m2 ?? openings.reduce((s, o) => s + (o.deduct_m2 ?? 0), 0)).toFixed(2) }} m²
  </p>
  <OpeningEditor :room-id="route.params.id" />
</div></template>
