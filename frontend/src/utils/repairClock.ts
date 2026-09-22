/** 工单计时工具：以响应截止时间为基准，输出剩余或超时时间。 */

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

/** 输出 HH:MM:SS 或 X天 HH:MM:SS 形式的持续时间。 */
export function formatDuration(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(Math.abs(ms) / 1000));
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const clock = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  return days > 0 ? `${days}天 ${clock}` : clock;
}

export interface TicketClock {
  overdue: boolean;
  /** 距响应截止的毫秒数；超时后为负数。 */
  diffMs: number;
  /** 剩余时间或已超时时长（正数）。 */
  durationMs: number;
  text: string;
}

export function getTicketClock(deadline: string, now: number = Date.now()): TicketClock {
  const diffMs = new Date(deadline).getTime() - now;
  return {
    overdue: diffMs < 0,
    diffMs,
    durationMs: Math.abs(diffMs),
    text: formatDuration(diffMs),
  };
}

export function formatDateTime(value: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
