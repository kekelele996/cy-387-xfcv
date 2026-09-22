export interface PropertyItem {
  id: number;
  community: string;
  region: string;
  layout: string;
  area: number;
  rent: number;
  deposit: number;
  payment: string;
  facilities: string[];
  status: string;
  landlordPhone: string;
}

export interface RepairEvent {
  id: number;
  eventType: '提交' | '接单' | '升级' | '完成';
  operatorName: string;
  detail: string;
  createdAt: string;
}

export interface RepairStaff {
  id: number;
  name: string;
  phone: string;
  unfinishedCount: number;
}

export type RepairStatus = '待响应' | '处理中' | '已完成';

export interface RepairTicket {
  id: number;
  faultType: string;
  description: string;
  photoUrl: string;
  residentName: string;
  residentPhone: string;
  status: RepairStatus;
  submittedAt: string;
  responseDeadline: string;
  acceptedAt: string | null;
  escalatedAt: string | null;
  completedAt: string | null;
  deadlineMinutes: number;
  overdue: boolean;
  escalated: boolean;
  assigneeId: number | null;
  assigneeName: string;
  previousAssigneeName: string;
  events: RepairEvent[];
}

export interface RepairCreatePayload {
  faultType: string;
  description: string;
  residentName?: string;
  residentPhone?: string;
  photo?: File;
}

export const REPAIR_TYPE_OPTIONS = ['水电', '门锁', '管道', '家电', '其他'] as const;
export const REPAIR_SLA_LABEL: Record<string, string> = {
  水电: '30 分钟内响应',
  门锁: '30 分钟内响应',
  管道: '4 小时内响应',
  家电: '4 小时内响应',
  其他: '4 小时内响应',
};
