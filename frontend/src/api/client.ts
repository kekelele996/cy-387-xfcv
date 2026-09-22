import type {
  PropertyItem,
  RepairCreatePayload,
  RepairStaff,
  RepairTicket,
} from '../types/domain';

const API_BASE = '/api';

async function parseError(response: Response, fallback: string): Promise<Error> {
  try {
    const body = await response.json();
    if (body && typeof body.error === 'string') return new Error(body.error);
  } catch {
    /* 忽略非标准响应体 */
  }
  return new Error(fallback);
}

export async function getProperties(): Promise<PropertyItem[]> {
  const response = await fetch(`${API_BASE}/properties/`);
  if (!response.ok) throw new Error('房源加载失败');
  return response.json();
}

export async function getRepairs(params: {
  status?: string;
  overdue?: boolean;
  faultType?: string;
} = {}): Promise<RepairTicket[]> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (typeof params.overdue === 'boolean') query.set('overdue', String(params.overdue));
  if (params.faultType) query.set('faultType', params.faultType);
  const suffix = query.toString() ? `?${query.toString()}` : '';
  const response = await fetch(`${API_BASE}/repairs/${suffix}`);
  if (!response.ok) throw await parseError(response, '工单加载失败');
  return response.json();
}

export async function createRepair(payload: RepairCreatePayload): Promise<RepairTicket> {
  const form = new FormData();
  form.append('faultType', payload.faultType);
  form.append('description', payload.description);
  if (payload.residentName) form.append('residentName', payload.residentName);
  if (payload.residentPhone) form.append('residentPhone', payload.residentPhone);
  if (payload.photo) form.append('photo', payload.photo);

  const response = await fetch(`${API_BASE}/repairs/`, { method: 'POST', body: form });
  if (!response.ok) throw await parseError(response, '报修提交失败');
  return response.json();
}

export async function acceptRepair(ticketId: number, staffId: number): Promise<RepairTicket> {
  const response = await fetch(`${API_BASE}/repairs/${ticketId}/accept/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ staffId }),
  });
  if (!response.ok) throw await parseError(response, '接单失败');
  return response.json();
}

export async function escalateRepair(ticketId: number): Promise<RepairTicket> {
  const response = await fetch(`${API_BASE}/repairs/${ticketId}/escalate/`, { method: 'POST' });
  if (!response.ok) throw await parseError(response, '升级失败');
  return response.json();
}

export async function completeRepair(ticketId: number): Promise<RepairTicket> {
  const response = await fetch(`${API_BASE}/repairs/${ticketId}/complete/`, { method: 'POST' });
  if (!response.ok) throw await parseError(response, '完成操作失败');
  return response.json();
}

export async function getRepairStaff(): Promise<RepairStaff[]> {
  const response = await fetch(`${API_BASE}/repair-staff/`);
  if (!response.ok) throw await parseError(response, '物业人员加载失败');
  return response.json();
}
