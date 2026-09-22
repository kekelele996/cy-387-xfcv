<template>
  <el-card shadow="never" class="submit-card">
    <template #header>
      <span>提交报修工单</span>
      <el-text type="info" size="small" class="sla-hint">
        水电、门锁 30 分钟内响应；管道、家电、其他 4 小时内响应
      </el-text>
    </template>
    <el-form label-position="top" :model="form">
      <el-form-item label="住户称呼">
        <el-input v-model="form.submitterName" placeholder="选填，方便物业联系" />
      </el-form-item>
      <el-form-item label="故障类型">
        <el-select v-model="form.faultType">
          <el-option v-for="item in faultTypes" :key="item" :label="item" :value="item" />
        </el-select>
        <el-tag size="small" type="warning" effect="plain" class="limit-tag">
          响应时限：{{ limitText }}
        </el-tag>
      </el-form-item>
      <el-form-item label="故障描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请描述故障情况" />
      </el-form-item>
      <el-form-item label="故障照片">
        <el-upload :auto-upload="false" :show-file-list="true" :limit="1" accept="image/*"
                   :on-change="onPhotoChange" :on-remove="onPhotoRemove">
          <el-button>选择照片</el-button>
        </el-upload>
      </el-form-item>
      <el-form-item>
        <el-button type="success" :loading="submitting" @click="submit">提交工单</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import type { UploadFile } from 'element-plus';
import { REPAIR_FAULT_TYPES } from '../../constants/repair';
import { createRepair } from '../../api/client';
import { formatLimitMinutes } from '../../utils/repairTime';
import type { RepairTicket } from '../../types/domain';

const emit = defineEmits<{ submitted: [ticket: RepairTicket] }>();

const faultTypes = REPAIR_FAULT_TYPES;
const form = reactive({
  submitterName: '',
  faultType: '水电',
  description: '',
});
const photo = ref<File | null>(null);
const submitting = ref(false);

const LIMIT_MINUTES: Record<string, number> = { 水电: 30, 门锁: 30, 管道: 240, 家电: 240, 其他: 240 };
const limitText = computed(() => formatLimitMinutes(LIMIT_MINUTES[form.faultType]));

function onPhotoChange(uploadFile: UploadFile) {
  photo.value = (uploadFile.raw as File) ?? null;
}

function onPhotoRemove() {
  photo.value = null;
}

async function submit() {
  if (!form.description.trim()) {
    ElMessage.warning('请填写故障描述');
    return;
  }
  submitting.value = true;
  try {
    const ticket = await createRepair({
      faultType: form.faultType,
      description: form.description.trim(),
      submitterName: form.submitterName.trim(),
      photo: photo.value,
    });
    ElMessage.success(`工单 ${ticket.id} 已提交，响应截止 ${ticket.deadline}`);
    form.description = '';
    photo.value = null;
    emit('submitted', ticket);
  } catch (error) {
    ElMessage.error((error as Error).message || '报修提交失败');
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.sla-hint {
  margin-left: 12px;
}
.limit-tag {
  margin-left: 12px;
}
</style>
