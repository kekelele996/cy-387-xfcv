import { computed, onUnmounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  acceptRepair,
  completeRepair,
  escalateOverdueRepairs,
  escalateRepair,
  getRepairStaff,
  getRepairTickets,
  getServerTime,
} from '../api/client';
import type { RepairStaff, RepairTicket, TicketStatusFilter } from '../types/domain';

/** 报修工作台数据与动作：所有状态变更后都重新从服务端拉取，保证刷新后一致。 */
export function useRepairWorkbench() {
  const tickets = ref<(RepairTicket & { _busy?: boolean })[]>([]);
  const staffList = ref<RepairStaff[]>([]);
  const currentStaffId = ref<number | null>(null);
  const filter = ref<TicketStatusFilter>('all');
  const loading = ref(false);
  const now = ref(Date.now());
  const busyId = ref<number | null>(null);
  // 服务端时间与本地时间的偏差（毫秒），倒计时以此校正，避免客户端时钟不准
  const serverClockOffset = ref(0);

  let tickTimer: ReturnType<typeof setInterval> | null = null;
  let refreshTimer: ReturnType<typeof setInterval> | null = null;

  const pendingCount = computed(() => tickets.value.filter((t) => t.status === '待响应' && !t.isOverdue).length);
  const overdueCount = computed(() => tickets.value.filter((t) => t.status === '待响应' && t.isOverdue).length);

  async function loadTickets() {
    loading.value = true;
    try {
      // 筛选直接走服务端，待响应/已超时的判定以后端数据库时间为准
      tickets.value = await getRepairTickets(filter.value);
    } catch (error) {
      ElMessage.error((error as Error).message || '工单加载失败');
    } finally {
      loading.value = false;
    }
  }

  async function loadStaff() {
    staffList.value = await getRepairStaff();
    if (staffList.value.length > 0 && currentStaffId.value === null) {
      currentStaffId.value = staffList.value[0].id;
    }
  }

  async function runAction(ticketId: number, action: () => Promise<RepairTicket>, successText: string) {
    busyId.value = ticketId;
    try {
      await action();
      ElMessage.success(successText);
      await loadTickets();
    } catch (error) {
      ElMessage.error((error as Error).message || '操作失败');
      throw error;
    } finally {
      busyId.value = null;
    }
  }

  const accept = (ticket: RepairTicket) =>
    runAction(
      ticket.id,
      () => acceptRepair(ticket.id, currentStaffId.value as number),
      `工单 ${ticket.id} 接单成功`,
    );

  const complete = (ticket: RepairTicket) =>
    runAction(
      ticket.id,
      () => completeRepair(ticket.id, currentStaffId.value as number),
      `工单 ${ticket.id} 已完成`,
    );

  const escalate = async (ticket: RepairTicket) => {
    try {
      await runAction(ticket.id, () => escalateRepair(ticket.id), `工单 ${ticket.id} 已升级转派`);
    } catch {
      // 重复升级（如并发触发）会被后端拒绝，重新拉取以呈现最新状态
      await loadTickets();
    }
  };

  async function escalateAllOverdue() {
    try {
      const result = await escalateOverdueRepairs();
      ElMessage.success(`扫描完成，本次升级 ${result.escalatedCount} 个超时工单`);
      await loadTickets();
    } catch (error) {
      ElMessage.error((error as Error).message || '批量升级失败');
    }
  }

  async function syncServerTime() {
    const before = Date.now();
    const { now: serverNow } = await getServerTime();
    const after = Date.now();
    // 以请求往返中点估算网络延迟，得到服务端时钟相对本地时钟的偏差
    const networkDelay = (after - before) / 2;
    serverClockOffset.value = new Date(serverNow).getTime() - before - networkDelay;
  }

  function startTimers() {
    tickTimer = setInterval(() => {
      now.value = Date.now() + serverClockOffset.value;
    }, 1000);
    refreshTimer = setInterval(loadTickets, 10000);
  }

  function stopTimers() {
    if (tickTimer) clearInterval(tickTimer);
    if (refreshTimer) clearInterval(refreshTimer);
  }

  onUnmounted(stopTimers);

  return {
    tickets,
    staffList,
    currentStaffId,
    filter,
    loading,
    now,
    busyId,
    pendingCount,
    overdueCount,
    loadTickets,
    loadStaff,
    syncServerTime,
    accept,
    complete,
    escalate,
    escalateAllOverdue,
    startTimers,
    stopTimers,
  };
}
