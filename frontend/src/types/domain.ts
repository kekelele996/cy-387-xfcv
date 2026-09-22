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

export type RepairStatus = '待响应' | '处理中' | '已完成';

export interface RepairEvent {
  id: number;
  type: '提交' | '接单' | '升级' | '完成';
  time: string;
  operatorName: string | null;
  fromAssigneeName: string | null;
  toAssigneeName: string | null;
  remark: string;
}

export interface RepairTicket {
  id: number;
  faultType: string;
  description: string;
  photoUrl: string | null;
  submitterName: string;
  status: RepairStatus;
  assigneeId: number | null;
  assigneeName: string | null;
  responseLimitMinutes: number;
  deadline: string;
  createdAt: string;
  acceptedAt: string | null;
  completedAt: string | null;
  escalated: boolean;
  isOverdue: boolean;
  events: RepairEvent[];
}

export interface RepairStaff {
  id: number;
  name: string;
  phone: string;
  is_active: boolean;
  openCount: number | null;
}

export type TicketStatusFilter = 'all' | 'pending' | 'overdue' | 'processing' | 'completed';

export interface CreateRepairPayload {
  faultType: string;
  description: string;
  submitterName?: string;
  photo?: File | null;
}
