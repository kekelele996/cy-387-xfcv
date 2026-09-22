/** 报修模块前端常量，与后端 constants/enums.py 保持一致。 */
export const REPAIR_FAULT_TYPES = ['水电', '门锁', '管道', '家电', '其他'] as const;

export const TICKET_STATUS_FILTERS = [
  { label: '全部', value: 'all' },
  { label: '待响应', value: 'pending' },
  { label: '已超时', value: 'overdue' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
] as const;
