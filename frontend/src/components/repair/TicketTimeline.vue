<template>
  <el-timeline>
    <el-timeline-item
      v-for="event in events"
      :key="event.id"
      :type="timelineType(event.type)"
      :timestamp="event.time"
      placement="top"
    >
      <div class="event-line">
        <el-tag size="small" :type="timelineType(event.type)" effect="plain">{{ event.type }}</el-tag>
        <span class="event-remark">{{ event.remark }}</span>
      </div>
      <div v-if="event.type === '升级'" class="event-detail">
        <el-text type="info" size="small">
          {{ event.fromAssigneeName ? `${event.fromAssigneeName} → ` : '' }}{{ event.toAssigneeName ?? '' }}
        </el-text>
      </div>
    </el-timeline-item>
  </el-timeline>
</template>

<script setup lang="ts">
import type { RepairEvent } from '../../types/domain';

defineProps<{ events: RepairEvent[] }>();

function timelineType(type: RepairEvent['type']): 'primary' | 'success' | 'warning' | 'info' {
  switch (type) {
    case '提交':
      return 'primary';
    case '接单':
      return 'success';
    case '升级':
      return 'warning';
    case '完成':
      return 'info';
  }
}
</script>

<style scoped>
.event-line {
  display: flex;
  align-items: center;
  gap: 8px;
}
.event-remark {
  font-size: 13px;
}
.event-detail {
  margin-top: 2px;
}
</style>
