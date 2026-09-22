/** 报修工单的倒计时与文案工具：计时基准来自服务端返回的 deadline。 */

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

export function formatDuration(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
}

export function formatLimitMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes} 分钟`;
  const hours = minutes / 60;
  return Number.isInteger(hours) ? `${hours} 小时` : `${hours} 小时`;
}

export interface TimerInfo {
  overdue: boolean;
  label: string;
  text: string;
}

/** 返回当前计时状态；截止时间完全以服务端 deadline 为准。 */
export function getTimerInfo(deadline: string, status: string, now: number = Date.now()): TimerInfo {
  if (status !== '待响应') {
    return { overdue: false, label: '', text: '—' };
  }
  const diff = new Date(deadline.replace(' ', 'T')).getTime() - now;
  if (diff > 0) {
    return { overdue: false, label: '剩余响应时间', text: formatDuration(diff) };
  }
  return { overdue: true, label: '已超时', text: formatDuration(-diff) };
}
