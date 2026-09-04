<script setup>
</script>

<template>
  <div id="app">
    <nav class="app-nav">
      <router-link to="/kanban" class="nav-link">看板</router-link>
    </nav>
    <router-view />
  </div>
</template>

<style scoped>
.app-nav {
  background: #1a1a2e;
  padding: 12px 24px;
  display: flex;
  gap: 16px;
}

.nav-link {
  color: #e0e0e0;
  text-decoration: none;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
}
</style>
