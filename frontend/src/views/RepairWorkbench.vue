<template>
  <main class="page workbench">
    <section class="toolbar">
      <div>
        <h1>物业报修工作台</h1>
        <p>分级响应：水电、门锁 30 分钟；管道、家电、其他 4 小时。超时未接单可升级一次。</p>
      </div>
      <el-switch v-model="autoRefresh" active-text="自动刷新（20s）" inline-prompt />
    </section>

    <RepairSubmitForm @submitted="reload" />

    <RepairFilterBar v-model="tab" :loading="loading" @filter="onFilter" />

    <el-alert
      v-if="overdueCount > 0 && tab !== 'overdue'"
      :title="`当前有 ${overdueCount} 张工单已超时未接单，请尽快处理或升级`"
      type="error"
      show-icon
      :closable="false"
      class="overdue-alert"
    />

    <div v-loading="loading">
      <RepairTicketCard
        v-for="ticket in tickets"
        :key="ticket.id"
        :ticket="ticket"
        :staff="staff"
        :now="now"
        @accept="onAccept"
        @escalate="onEscalate"
        @complete="onComplete"
      />
      <el-empty v-if="!loading && tickets.length === 0" description="暂无符合条件的工单" />
    </div>
  </main>
</template>

<script setup lang="ts">
defineOptions({ name: 'RepairWorkbench' });

import { onBeforeUnmount, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import RepairFilterBar from '../components/RepairFilterBar.vue';
import RepairSubmitForm from '../components/RepairSubmitForm.vue';
import RepairTicketCard from '../components/RepairTicketCard.vue';
import {
  acceptRepair,
  completeRepair,
  escalateRepair,
  getRepairStaff,
  getRepairs,
} from '../api/client';
import type { RepairStaff, RepairTicket } from '../types/domain';

const tab = ref('all');
const faultType = ref('');
const tickets = ref<RepairTicket[]>([]);
const staff = ref<RepairStaff[]>([]);
const loading = ref(false);
const now = ref(Date.now());
const autoRefresh = ref(true);
const overdueCount = ref(0);

let clockTimer: number | undefined;
let refreshTimer: number | undefined;

function buildParams() {
  const params: { status?: string; overdue?: boolean; faultType?: string } = {};
  if (tab.value === 'pending') params.status = '待响应';
  else if (tab.value === 'processing') params.status = '处理中';
  else if (tab.value === 'completed') params.status = '已完成';
  else if (tab.value === 'overdue') params.overdue = true;
  if (faultType.value) params.faultType = faultType.value;
  return params;
}

async function reload() {
  loading.value = true;
  try {
    const [ticketList, staffList, overdueList] = await Promise.all([
      getRepairs(buildParams()),
      getRepairStaff(),
      tab.value === 'overdue' ? Promise.resolve([]) : getRepairs({ overdue: true }),
    ]);
    tickets.value = ticketList;
    staff.value = staffList;
    overdueCount.value = tab.value === 'overdue' ? ticketList.length : overdueList.length;
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}

function onFilter(payload: { tab: string; faultType: string }) {
  tab.value = payload.tab;
  faultType.value = payload.faultType;
  reload();
}

async function onAccept(id: number, staffId: number) {
  try {
    await acceptRepair(id, staffId);
    ElMessage.success(`工单 ${id} 已接单`);
    await reload();
  } catch (error) {
    ElMessage.error((error as Error).message);
    await reload();
  }
}

async function onEscalate(id: number) {
  try {
    await ElMessageBox.confirm(
      '超时工单只能升级一次，将转派给当前未完成工单最少的物业人员，确认升级？',
      '超时升级',
      { type: 'warning', confirmButtonText: '确认升级', cancelButtonText: '取消' },
    );
  } catch {
    return;
  }
  try {
    const ticket = await escalateRepair(id);
    ElMessage.success(`工单 ${id} 已升级转派给 ${ticket.assigneeName}`);
    await reload();
  } catch (error) {
    ElMessage.error((error as Error).message);
    await reload();
  }
}

async function onComplete(id: number) {
  try {
    await completeRepair(id);
    ElMessage.success(`工单 ${id} 已完成`);
    await reload();
  } catch (error) {
    ElMessage.error((error as Error).message);
    await reload();
  }
}

onMounted(() => {
  reload();
  clockTimer = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
  refreshTimer = window.setInterval(() => {
    if (autoRefresh.value) reload();
  }, 20000);
});

onBeforeUnmount(() => {
  window.clearInterval(clockTimer);
  window.clearInterval(refreshTimer);
});
</script>

<style scoped>
.overdue-alert { margin-bottom: 14px; }
</style>
