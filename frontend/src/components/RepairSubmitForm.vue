<template>
  <el-card shadow="never" class="submit-card">
    <template #header><strong>提交报修工单</strong></template>
    <el-form label-position="top" :model="form">
      <div class="form-row">
        <el-form-item label="故障类型" required>
          <el-select v-model="form.faultType" class="full">
            <el-option v-for="type in REPAIR_TYPE_OPTIONS" :key="type" :label="`${type}（${REPAIR_SLA_LABEL[type]}）`" :value="type" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.residentName" placeholder="住户姓名（选填）" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.residentPhone" placeholder="联系电话（选填）" />
        </el-form-item>
      </div>
      <el-form-item label="故障描述" required>
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请描述故障情况" />
      </el-form-item>
      <el-form-item label="现场照片">
        <el-upload :auto-upload="false" :show-file-list="true" :limit="1" accept="image/*" :on-change="onPhotoChange" :on-remove="onPhotoRemove">
          <el-button>选择照片</el-button>
        </el-upload>
      </el-form-item>
      <div class="actions">
        <el-tag type="warning" effect="plain">{{ REPAIR_SLA_LABEL[form.faultType] }}</el-tag>
        <el-button type="success" :loading="submitting" @click="submit">提交工单</el-button>
      </div>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import type { UploadFile } from 'element-plus';
import { createRepair } from '../api/client';
import { REPAIR_SLA_LABEL, REPAIR_TYPE_OPTIONS } from '../types/domain';

const emit = defineEmits<{ submitted: [] }>();

const form = reactive({
  faultType: '水电',
  description: '',
  residentName: '',
  residentPhone: '',
});
const photo = ref<File | null>(null);
const submitting = ref(false);

function onPhotoChange(file: UploadFile) {
  photo.value = (file.raw as File) ?? null;
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
    const ticket = await createRepair({ ...form, photo: photo.value ?? undefined });
    ElMessage.success(`工单 ${ticket.id} 已提交，请等待物业响应`);
    form.description = '';
    photo.value = null;
    emit('submitted');
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.submit-card { margin-bottom: 16px; }
.form-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0 16px; }
.full { width: 100%; }
.actions { display: flex; justify-content: space-between; align-items: center; }
</style>
