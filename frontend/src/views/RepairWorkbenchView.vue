<template>
  <main class="repair-page">
    <section class="page-head">
      <div>
        <h2>物业报修工作台</h2>
        <p>分级响应 · 接单留痕 · 超时自动升级</p>
      </div>
      <div class="head-actions">
        <el-select v-model="workbench.currentStaffId" placeholder="选择物业人员" style="width: 180px">
          <el-option
            v-for="staff in workbench.staffList"
            :key="staff.id"
            :label="staff.name"
            :value="staff.id"
          />
        </el-select>
        <el-button @click="workbench.loadTickets()">刷新</el-button>
        <el-button type="warning" @click="workbench.escalateAllOverdue()">一键扫描超时升级</el-button>
      </div>
    </section>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat">
            <span class="stat-label">待响应（未超时）</span>
            <span class="stat-num">{{ workbench.pendingCount }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat">
            <span class="stat-label">已超时</span>
            <span class="stat-num danger">{{ workbench.overdueCount }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <div class="sla-rules">
            <el-tag type="danger" effect="dark">水电 / 门锁：30 分钟内响应</el-tag>
            <el-tag type="warning" effect="dark">管道 / 家电 / 其他：4 小时内响应</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="list-header">
          <el-radio-group v-model="workbench.filter" @change="workbench.loadTickets()">
            <el-radio-button v-for="item in filters" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio-button>
          </el-radio-group>
          <el-text type="info" size="small">每 10 秒自动刷新，计时以服务端截止时间为准</el-text>
        </div>
      </template>
      <TicketTable
        :tickets="ticketRows"
        :now="workbench.now"
        :current-staff-id="workbench.currentStaffId"
        :loading="workbench.loading"
        @accept="workbench.accept"
        @complete="workbench.complete"
        @escalate="workbench.escalate"
      />
    </el-card>

    <el-row :gutter="16" class="bottom-row">
      <el-col :span="14">
        <RepairSubmitForm @submitted="onSubmitted" />
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>升级规则说明</template>
          <ul class="rules">
            <li>超过响应时限仍未接单的工单可升级，<b>每个工单只能升级一次</b>。</li>
            <li>升级后转派给<b>未完成工单最少</b>的在岗物业人员。</li>
            <li>重复或并发升级不会重复转派；状态、处理人和升级记录要么一并成功，要么全部不变。</li>
            <li>展开任意工单可查看完整处理记录（提交 / 接单 / 升级 / 完成）。</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import RepairSubmitForm from '../components/repair/RepairSubmitForm.vue';
import TicketTable from '../components/repair/TicketTable.vue';
import { TICKET_STATUS_FILTERS } from '../constants/repair';
import { useRepairWorkbench } from '../composables/useRepairWorkbench';

const filters = TICKET_STATUS_FILTERS;
// reactive 包裹后模板中 ref 自动解包，方法与计算属性可直接使用
const workbench = reactive(useRepairWorkbench());

// 正在执行升级操作的工单行显示 loading
const ticketRows = computed(() =>
  workbench.tickets.map((ticket) => ({ ...ticket, _busy: workbench.busyId === ticket.id })),
);

onMounted(async () => {
  await Promise.all([workbench.loadStaff(), workbench.syncServerTime()]);
  await workbench.loadTickets();
  workbench.startTimers();
});

function onSubmitted() {
  workbench.filter = 'pending';
  workbench.loadTickets();
}
</script>

<style scoped>
.repair-page {
  padding: 20px 24px;
  max-width: 1280px;
  margin: 0 auto;
}
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.head-actions {
  display: flex;
  gap: 8px;
}
.stat-row,
.bottom-row {
  margin-bottom: 16px;
}
.stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
}
.stat-num.danger {
  color: var(--el-color-danger);
}
.sla-rules {
  display: flex;
  gap: 12px;
  align-items: center;
  height: 100%;
}
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rules {
  margin: 0;
  padding-left: 18px;
  line-height: 2;
  color: var(--el-text-color-regular);
}
</style>
