import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import RepairWorkbench from '../views/RepairWorkbench.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/repair', name: 'repair', component: RepairWorkbench },
  ],
});
