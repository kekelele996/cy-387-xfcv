<template>
  <el-table :data="tickets" row-key="id" border stripe v-loading="loading" empty-text="暂无工单">
    <el-table-column type="expand">
      <template #default="{ row }">
        <div class="timeline-wrap">
          <h4>处理记录</h4>
          <TicketTimeline :events="row.events" />
        </div>
      </template>
    </el-table-column>

    <el-table-column label="工单号" prop="id" width="90" />
    <el-table-column label="故障类型" width="150">
      <template #default="{ row }">
        <el-tag :type="faultTagType(row.faultType)" effect="dark">{{ row.faultType }}</el-tag>
        <el-text size="small" type="info" class="limit-text">
          限 {{ formatLimitMinutes(row.responseLimitMinutes) }}
        </el-text>
      </template>
    </el-table-column>
    <el-table-column label="故障描述" prop="description" min-width="180" show-overflow-tooltip />
    <el-table-column label="提交时间" width="170">
      <template #default="{ row }">{{ row.createdAt }}</template>
    </el-table-column>
    <el-table-column label="响应截止" width="170">
      <template #default="{ row }">{{ row.deadline }}</template>
    </el-table-column>
    <el-table-column label="响应计时" width="160">
      <template #default="{ row }">
        <div v-if="timer(row).text !== '—'" :class="['timer', { overdue: timer(row).overdue }]">
          <span class="timer-label">{{ timer(row).label }}</span>
          <span class="timer-value">{{ timer(row).text }}</span>
        </div>
        <el-text v-else type="info">—</el-text>
      </template>
    </el-table-column>
    <el-table-column label="状态" width="110">
      <template #default="{ row }">
        <el-tag :type="statusTagType(row)">{{ row.status }}</el-tag>
        <el-tag v-if="row.escalated" type="danger" size="small" effect="plain" class="esc-tag">已升级</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="处理人" width="110">
      <template #default="{ row }">
        {{ row.assigneeName ?? '—' }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="240" fixed="right">
      <template #default="{ row }">
        <el-button
          v-if="row.status === '待响应'"
          type="primary" size="small"
          :disabled="!currentStaffId"
          @click="emit('accept', row)"
        >
          接单
        </el-button>
        <el-button
          v-if="row.status === '处理中' && row.assigneeId === currentStaffId"
          type="success" size="small"
          @click="emit('complete', row)"
        >
          完成
        </el-button>
        <el-button
          v-if="row.status === '待响应' && timer(row).overdue && !row.escalated"
          type="warning" size="small"
          :loading="!!row._busy"
          @click="emit('escalate', row)"
        >
          超时升级
        </el-button>
        <el-text v-if="row.status === '待响应' && row.escalated" type="danger" size="small">
          已转派，不可再升级
        </el-text>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import { getTimerInfo, formatLimitMinutes } from '../../utils/repairTime';
import TicketTimeline from './TicketTimeline.vue';
import type { RepairTicket } from '../../types/domain';

const props = defineProps<{
  tickets: (RepairTicket & { _busy?: boolean })[];
  now: number;
  currentStaffId: number | null;
  loading: boolean;
}>();

const emit = defineEmits<{
  accept: [ticket: RepairTicket];
  complete: [ticket: RepairTicket];
  escalate: [ticket: RepairTicket];
}>();

function timer(row: RepairTicket) {
  return getTimerInfo(row.deadline, row.status, props.now);
}

function faultTagType(faultType: string): 'danger' | 'warning' | 'info' {
  return faultType === '水电' || faultType === '门锁' ? 'danger' : 'warning';
}

function statusTagType(row: RepairTicket): 'warning' | 'primary' | 'success' | 'danger' {
  if (row.status === '已完成') return 'success';
  if (row.status === '处理中') return 'primary';
  return row.isOverdue ? 'danger' : 'warning';
}
</script>

<style scoped>
.timeline-wrap {
  padding: 8px 24px;
}
.limit-text {
  display: block;
  margin-top: 2px;
}
.timer {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}
.timer.overdue .timer-label,
.timer.overdue .timer-value {
  color: var(--el-color-danger);
}
.timer-value {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}
.esc-tag {
  margin-left: 4px;
}
</style>
