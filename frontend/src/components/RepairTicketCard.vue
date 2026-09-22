<template>
  <el-card shadow="hover" class="ticket-card" :class="{ overdue: showOverdue }">
    <template #header>
      <div class="card-header">
        <div class="title">
          <strong>#{{ ticket.id }} {{ ticket.faultType }} 报修</strong>
          <el-tag :type="statusTagType" size="small">{{ ticket.status }}</el-tag>
          <el-tag v-if="ticket.escalated" type="danger" size="small" effect="dark">已升级</el-tag>
        </div>
        <div v-if="timer" class="timer" :class="timer.overdue ? 'is-overdue' : 'is-running'">
          <span class="dot" />
          {{ timer.overdue ? '已超时' : '剩余' }} {{ timer.text }}
        </div>
      </div>
    </template>

    <p class="desc">{{ ticket.description }}</p>
    <div class="meta">
      <span>提交时间：{{ formatDateTime(ticket.submittedAt) }}</span>
      <span>响应时限：{{ ticket.deadlineMinutes }} 分钟（截止 {{ formatDateTime(ticket.responseDeadline) }}）</span>
      <span>处理人：{{ ticket.assigneeName || '待派单' }}<template v-if="ticket.previousAssigneeName">（原 {{ ticket.previousAssigneeName }}）</template></span>
      <span v-if="ticket.acceptedAt">接单时间：{{ formatDateTime(ticket.acceptedAt) }}</span>
      <span v-if="ticket.escalatedAt">升级时间：{{ formatDateTime(ticket.escalatedAt) }}</span>
    </div>

    <el-image
      v-if="ticket.photoUrl"
      :src="ticket.photoUrl"
      fit="cover"
      class="photo"
      :preview-src-list="[ticket.photoUrl]"
      preview-teleported
    />

    <el-collapse class="records">
      <el-collapse-item title="流转记录" :name="1">
        <el-timeline>
          <el-timeline-item
            v-for="event in ticket.events"
            :key="event.id"
            :type="eventTagType(event.eventType)"
            :timestamp="formatDateTime(event.createdAt)"
          >
            <strong>{{ event.eventType }}</strong>
            <span v-if="event.operatorName"> · {{ event.operatorName }}</span>
            <div class="event-detail">{{ event.detail }}</div>
          </el-timeline-item>
        </el-timeline>
      </el-collapse-item>
    </el-collapse>

    <div class="actions">
      <template v-if="ticket.status === '待响应'">
        <el-select v-model="selectedStaff" :placeholder="ticket.assigneeName ? `指派给 ${ticket.assigneeName}` : '选择处理物业'" size="small" style="width: 180px">
          <el-option v-for="staff in staff" :key="staff.id" :label="`${staff.name}（在手 ${staff.unfinishedCount}）`" :value="staff.id" />
        </el-select>
        <el-button type="primary" size="small" :disabled="!selectedStaff" @click="onAccept(ticket.id)">接单</el-button>
        <el-button type="danger" size="small" plain :disabled="!ticket.overdue || ticket.escalated" @click="emit('escalate', ticket.id)">
          {{ ticket.escalated ? '已升级' : ticket.overdue ? '超时升级' : '未超时不可升级' }}
        </el-button>
      </template>
      <el-button v-if="ticket.status === '处理中'" type="success" size="small" @click="emit('complete', ticket.id)">完成处理</el-button>
      <span v-if="ticket.status === '已完成'" class="done-text">已完成于 {{ formatDateTime(ticket.completedAt) }}</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
defineOptions({ name: 'RepairTicketCard' });
import { computed, ref } from 'vue';
import type { RepairStaff, RepairTicket } from '../types/domain';
import { formatDateTime, getTicketClock } from '../utils/repairClock';

const props = defineProps<{
  ticket: RepairTicket;
  staff: RepairStaff[];
  now: number;
}>();

const emit = defineEmits<{
  accept: [id: number, staffId: number];
  escalate: [id: number];
  complete: [id: number];
}>();

const selectedStaff = ref<number | null>(props.ticket.assigneeId);

const timer = computed(() => {
  if (props.ticket.acceptedAt) return null;
  return getTicketClock(props.ticket.responseDeadline, props.now);
});

const showOverdue = computed(() => timer.value?.overdue ?? false);

const statusTagType = computed(() => {
  if (props.ticket.status === '待响应') return showOverdue.value ? 'danger' : 'warning';
  if (props.ticket.status === '处理中') return 'primary';
  return 'success';
});

function eventTagType(type: string): 'primary' | 'success' | 'danger' | 'info' {
  if (type === '接单') return 'primary';
  if (type === '升级') return 'danger';
  if (type === '完成') return 'success';
  return 'info';
}

function onAccept(id: number) {
  if (selectedStaff.value) emit('accept', id, selectedStaff.value);
}
</script>

<style scoped>
.ticket-card { margin-bottom: 14px; }
.ticket-card.overdue :deep(.el-card__header) { background: #fff1f0; }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.title { display: flex; align-items: center; gap: 8px; }
.timer { display: flex; align-items: center; gap: 6px; font-variant-numeric: tabular-nums; font-size: 13px; font-weight: 600; }
.timer .dot { width: 8px; height: 8px; border-radius: 50%; }
.timer.is-running { color: #d48806; }
.timer.is-running .dot { background: #faad14; animation: blink 1s infinite; }
.timer.is-overdue { color: #cf1322; }
.timer.is-overdue .dot { background: #cf1322; }
@keyframes blink { 50% { opacity: 0.3; } }
.desc { margin: 0 0 10px; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 4px 16px; color: #5b6472; font-size: 13px; }
.photo { width: 120px; height: 90px; border-radius: 6px; margin-top: 10px; }
.records { margin-top: 10px; }
.event-detail { color: #5b6472; }
.actions { display: flex; align-items: center; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
.done-text { color: #52c41a; font-size: 13px; }
</style>
