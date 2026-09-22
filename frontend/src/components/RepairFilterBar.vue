<template>
  <div class="filter-bar">
    <el-radio-group :model-value="modelValue" @update:model-value="onTabChange">
      <el-radio-button value="all">全部工单</el-radio-button>
      <el-radio-button value="pending">待响应</el-radio-button>
      <el-radio-button value="overdue">已超时</el-radio-button>
      <el-radio-button value="processing">处理中</el-radio-button>
      <el-radio-button value="completed">已完成</el-radio-button>
    </el-radio-group>
    <div class="spacer" />
    <el-select v-model="faultType" placeholder="全部故障类型" clearable style="width: 160px" @change="emitFilter">
      <el-option v-for="type in REPAIR_TYPE_OPTIONS" :key="type" :label="type" :value="type" />
    </el-select>
    <el-button :loading="loading" @click="emitFilter">刷新</el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { REPAIR_TYPE_OPTIONS } from '../types/domain';

const props = defineProps<{ modelValue: string; loading?: boolean }>();
const emit = defineEmits<{
  'update:modelValue': [value: string];
  filter: [payload: { tab: string; faultType: string }];
}>();

const faultType = ref('');

function onTabChange(value: string) {
  emit('update:modelValue', value);
  emit('filter', { tab: value, faultType: faultType.value });
}

function emitFilter() {
  emit('filter', { tab: props.modelValue, faultType: faultType.value });
}
</script>

<style scoped>
.filter-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.spacer { flex: 1; }
</style>
