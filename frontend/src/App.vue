<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="brand">RentFind 租房与物业报修平台</div>
      <el-menu :default-active="active" mode="horizontal" :ellipsis="false" @select="active = $event">
        <el-menu-item index="home">房源列表</el-menu-item>
        <el-menu-item index="repair">物业报修</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <HomeView v-if="active === 'home'" @open-repair="active = 'repair'" />
      <RepairWorkbenchView v-else />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import HomeView from './views/HomeView.vue';
import RepairWorkbenchView from './views/RepairWorkbenchView.vue';

const active = ref<'home' | 'repair'>('repair');
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}
.app-header {
  display: flex;
  align-items: center;
  gap: 32px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: #fff;
}
.brand {
  font-weight: 700;
  font-size: 16px;
  white-space: nowrap;
}
.app-header .el-menu {
  border-bottom: none;
  flex: 1;
}
</style>
