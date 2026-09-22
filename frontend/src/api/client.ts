import type {
  CreateRepairPayload,
  RepairStaff,
  RepairTicket,
  TicketStatusFilter,
} from '../types/domain';

const API_BASE = '/api';

async function parseJsonOrThrow(response: Response, fallback: string): Promise<never> {
  let message = fallback;
  try {
    const body = await response.json();
    if (body && typeof body.error !== 'undefined') {
      message = typeof body.error === 'string' ? body.error : fallback;
    }
  } catch {
    // 非 JSON 错误体，使用兜底文案
  }
  throw new Error(message);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    await parseJsonOrThrow(response, '请求失败，请稍后重试');
  }
  return response.json() as Promise<T>;
}

export function getProperties() {
  return request<import('../types/domain').PropertyItem[]>('/properties/');
}

export function getRepairTickets(status: TicketStatusFilter = 'all'): Promise<RepairTicket[]> {
  return request<RepairTicket[]>(`/repair/tickets/?status=${encodeURIComponent(status)}`);
}

export function createRepair(payload: CreateRepairPayload): Promise<RepairTicket> {
  let body: BodyInit;
  let headers: Record<string, string> = {};
  if (payload.photo) {
    const form = new FormData();
    form.append('faultType', payload.faultType);
    form.append('description', payload.description);
    if (payload.submitterName) form.append('submitterName', payload.submitterName);
    form.append('photo', payload.photo);
    body = form;
  } else {
    headers = { 'Content-Type': 'application/json' };
    body = JSON.stringify(payload);
  }
  return request<RepairTicket>('/repair/tickets/', { method: 'POST', headers, body });
}

export function acceptRepair(ticketId: number, staffId: number): Promise<RepairTicket> {
  return request<RepairTicket>(`/repair/tickets/${ticketId}/accept/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ staffId }),
  });
}

export function completeRepair(ticketId: number, staffId: number): Promise<RepairTicket> {
  return request<RepairTicket>(`/repair/tickets/${ticketId}/complete/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ staffId }),
  });
}

export function escalateRepair(ticketId: number): Promise<RepairTicket> {
  return request<RepairTicket>(`/repair/tickets/${ticketId}/escalate/`, { method: 'POST' });
}

export function escalateOverdueRepairs(): Promise<{ escalatedCount: number; tickets: RepairTicket[] }> {
  return request('/repair/tickets/escalate-overdue/', { method: 'POST' });
}

export function getRepairStaff(): Promise<RepairStaff[]> {
  return request<RepairStaff[]>('/repair/staff/');
}

export function getServerTime(): Promise<{ now: string }> {
  return request<{ now: string }>('/repair/time/');
}
