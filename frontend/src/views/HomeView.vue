<template>
  <main class="page">
    <section class="toolbar">
      <div>
        <h1>RentFind 租房平台</h1>
        <p>房源搜索、预约看房、合同管理和物业报修集中处理。</p>
      </div>
      <el-segmented v-model="mode" :options="['列表视图', '地图视图']" />
    </section>

    <section class="filters">
      <el-input v-model="region" placeholder="区域" />
      <el-input-number v-model="maxRent" :min="1000" :step="500" />
      <el-select v-model="layout" placeholder="户型">
        <el-option label="全部" value="全部" />
        <el-option label="一室一厅" value="一室一厅" />
        <el-option label="两室一厅" value="两室一厅" />
        <el-option label="三室两厅" value="三室两厅" />
      </el-select>
    </section>

    <section v-if="mode === '地图视图'" class="map-panel">高德地图区域：按经纬度展示房源点位，当前示例加载 {{ filtered.length }} 套房源。</section>
    <section class="grid">
      <PropertyCard v-for="item in filtered" :key="item.id" :item="item" />
    </section>

    <section class="repair-entry">
      <h2>物业报修</h2>
      <p>水电、门锁 30 分钟内响应；管道、家电、其他 4 小时内响应，超时未接单自动升级。</p>
      <el-button type="success" @click="$emit('openRepair')">进入物业报修工作台</el-button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import PropertyCard from '../components/PropertyCard.vue';
import { getProperties } from '../api/client';
import type { PropertyItem } from '../types/domain';

defineEmits<{ openRepair: [] }>();

const properties = ref<PropertyItem[]>([]);
const mode = ref('列表视图');
const region = ref('');
const maxRent = ref(7000);
const layout = ref('全部');

onMounted(async () => {
  properties.value = await getProperties();
});

const filtered = computed(() => properties.value.filter((item) => {
  const hitRegion = !region.value || item.region.includes(region.value);
  const hitRent = item.rent <= maxRent.value;
  const hitLayout = layout.value === '全部' || item.layout === layout.value;
  return hitRegion && hitRent && hitLayout;
}));
</script>

<style scoped>
.repair-entry {
  margin-top: 24px;
  padding: 20px;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
}
.repair-entry p {
  color: var(--el-text-color-secondary);
  margin: 8px 0 16px;
}
</style>
