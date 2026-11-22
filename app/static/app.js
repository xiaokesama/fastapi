const API = "/api/v1";
const TOKEN_KEY = "studytrack_token";

const state = {
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  courses: [],
  tasks: [],
  allTasks: [],
  logs: [],
  stats: null,
  courseStats: [],
  taskTotal: 0,
  filters: { course_id: "", status: "" },
};

const els = {};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  cacheElements();
  bindEvents();
  setDefaultDates();

  if (!state.token) {
    showAuth();
    return;
  }

  try {
    await loadApp();
    showApp();
  } catch (error) {
    clearSession();
    showAuth();
    setAuthMessage(error.message || "登录状态已失效");
  }
}

function cacheElements() {
  const ids = [
    "auth-view", "app-view", "login-tab", "register-tab", "login-form", "register-form",
    "auth-message", "user-greeting", "logout-button", "refresh-button", "stat-today",
    "stat-week", "stat-streak", "stat-tasks", "toggle-course-form", "course-form",
    "course-list", "course-empty", "task-form", "task-course", "task-count", "filter-course",
    "filter-status", "task-list", "task-empty", "log-form", "log-course", "log-task",
    "chart", "course-stats", "course-stats-empty", "log-list", "log-empty", "toast",
  ];
  ids.forEach((id) => {
    els[id] = document.getElementById(id);
  });
}

function bindEvents() {
  els["login-tab"].addEventListener("click", () => switchAuthTab("login"));
  els["register-tab"].addEventListener("click", () => switchAuthTab("register"));
  els["login-form"].addEventListener("submit", handleLogin);
  els["register-form"].addEventListener("submit", handleRegister);
  els["logout-button"].addEventListener("click", logout);
  els["refresh-button"].addEventListener("click", () => refreshApp(true));
  els["toggle-course-form"].addEventListener("click", () => {
    els["course-form"].hidden = !els["course-form"].hidden;
  });
  els["course-form"].addEventListener("submit", handleCreateCourse);
  els["task-form"].addEventListener("submit", handleCreateTask);
  els["log-form"].addEventListener("submit", handleCreateLog);
  els["filter-course"].addEventListener("change", () => {
    state.filters.course_id = els["filter-course"].value;
    refreshTasks().catch(showError);
  });
  els["filter-status"].addEventListener("change", () => {
    state.filters.status = els["filter-status"].value;
    refreshTasks().catch(showError);
  });
  els["log-course"].addEventListener("change", renderLogTaskOptions);
  els["course-list"].addEventListener("click", handleCourseAction);
  els["task-list"].addEventListener("click", handleTaskAction);
  els["task-list"].addEventListener("change", handleTaskAction);
  els["log-list"].addEventListener("click", handleLogAction);
}

function setDefaultDates() {
  const today = todayString();
  document.querySelector('#log-form input[name="studied_on"]').value = today;
  document.querySelector('#task-form input[name="due_date"]').min = today;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) {
    headers.set("Authorization", `Bearer ${state.token}`);
  }
  if (options.body && !(options.body instanceof URLSearchParams) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (response.status === 401 && state.token) {
    clearSession();
    showAuth();
    throw new Error("登录状态已过期，请重新登录");
  }

  let payload = null;
  if (response.status !== 204) {
    payload = await response.json().catch(() => null);
  }

  if (!response.ok) {
    const detail = payload?.detail;
    if (Array.isArray(detail)) {
      throw new Error(detail.map((item) => item.msg).join("；"));
    }
    throw new Error(detail || `请求失败（${response.status}）`);
  }
  return payload;
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const data = new FormData(form);
  setAuthMessage("");
  setBusy(button, true, "登录中…");
  try {
    await loginWithCredentials(data.get("username").trim(), data.get("password"));
    await loadApp();
    showApp();
  } catch (error) {
    setAuthMessage(error.message);
  } finally {
    setBusy(button, false);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const data = new FormData(form);
  setAuthMessage("");
  setBusy(button, true, "创建中…");
  try {
    await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        username: data.get("username").trim(),
        email: data.get("email").trim(),
        password: data.get("password"),
      }),
    });
    await loginWithCredentials(data.get("username").trim(), data.get("password"));
    await loadApp();
    showApp();
  } catch (error) {
    setAuthMessage(error.message);
  } finally {
    setBusy(button, false);
  }
}

async function loginWithCredentials(username, password) {
  const response = await api("/auth/login", {
    method: "POST",
    body: new URLSearchParams({ username, password }),
  });
  state.token = response.access_token;
  localStorage.setItem(TOKEN_KEY, state.token);
}

async function loadApp() {
  const [user, stats, courseData, taskData, allTaskData, logData, courseStats] = await Promise.all([
    api("/auth/me"),
    api("/stats/overview?days=14"),
    api("/courses"),
    api(`/tasks?${taskQueryParams().toString()}`),
    api("/tasks?page_size=100"),
    api("/study-logs?page_size=8"),
    api("/stats/courses"),
  ]);

  state.user = user;
  state.stats = stats;
  state.courses = courseData.items;
  state.tasks = taskData.items;
  state.taskTotal = taskData.total;
  state.allTasks = allTaskData.items;
  state.logs = logData.items;
  state.courseStats = courseStats;
  renderAll();
}

async function refreshApp(showFeedback = false) {
  const button = els["refresh-button"];
  setBusy(button, true, "刷新中…");
  try {
    await loadApp();
    if (showFeedback) showToast("数据已刷新");
  } catch (error) {
    showError(error);
  } finally {
    setBusy(button, false);
  }
}

function taskQueryParams() {
  const params = new URLSearchParams({ page_size: "100" });
  if (state.filters.course_id) params.set("course_id", state.filters.course_id);
  if (state.filters.status) params.set("status", state.filters.status);
  return params;
}

async function refreshTasks() {
  const data = await api(`/tasks?${taskQueryParams().toString()}`);
  state.tasks = data.items;
  state.taskTotal = data.total;
  renderTasks();
  renderStats();
}

async function handleCreateCourse(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const data = new FormData(form);
  setBusy(button, true, "创建中…");
  try {
    await api("/courses", {
      method: "POST",
      body: JSON.stringify({
        name: data.get("name").trim(),
        description: data.get("description").trim() || null,
        color: data.get("color"),
      }),
    });
    form.reset();
    form.hidden = true;
    await refreshApp();
    showToast("学习项目已创建");
  } catch (error) {
    showError(error);
  } finally {
    setBusy(button, false);
  }
}

async function handleCreateTask(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const data = new FormData(form);
  setBusy(button, true, "添加中…");
  try {
    const payload = {
      course_id: Number(data.get("course_id")),
      title: data.get("title").trim(),
      priority: data.get("priority"),
    };
    if (data.get("due_date")) payload.due_date = data.get("due_date");
    await api("/tasks", { method: "POST", body: JSON.stringify(payload) });
    form.querySelector('input[name="title"]').value = "";
    form.querySelector('input[name="due_date"]').value = "";
    await refreshApp();
    showToast("任务已添加");
  } catch (error) {
    showError(error);
  } finally {
    setBusy(button, false);
  }
}

async function handleCreateLog(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const data = new FormData(form);
  setBusy(button, true, "打卡中…");
  try {
    await api("/study-logs", {
      method: "POST",
      body: JSON.stringify({
        course_id: Number(data.get("course_id")),
        task_id: data.get("task_id") ? Number(data.get("task_id")) : null,
        minutes: Number(data.get("minutes")),
        studied_on: data.get("studied_on"),
        note: data.get("note").trim() || null,
      }),
    });
    form.querySelector('textarea[name="note"]').value = "";
    await refreshApp();
    showToast("打卡成功，今天也辛苦了");
  } catch (error) {
    showError(error);
  } finally {
    setBusy(button, false);
  }
}

async function handleCourseAction(event) {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const courseId = Number(button.dataset.courseId);
  if (button.dataset.action === "archive") {
    try {
      await api(`/courses/${courseId}`, {
        method: "PATCH",
        body: JSON.stringify({ is_archived: true }),
      });
      await refreshApp();
      showToast("项目已归档");
    } catch (error) {
      showError(error);
    }
  }
  if (button.dataset.action === "delete-course") {
    if (!window.confirm("删除项目会同时删除其中的任务和学习记录，确定继续吗？")) return;
    try {
      await api(`/courses/${courseId}`, { method: "DELETE" });
      await refreshApp();
      showToast("项目已删除");
    } catch (error) {
      showError(error);
    }
  }
}

async function handleTaskAction(event) {
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const taskId = Number(target.dataset.taskId);

  if (target.dataset.action === "toggle-task") {
    try {
      await api(`/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: target.checked ? "done" : "todo" }),
      });
      await refreshApp();
    } catch (error) {
      showError(error);
    }
  }

  if (target.dataset.action === "task-status" && event.type === "change") {
    try {
      await api(`/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: target.value }),
      });
      await refreshApp();
    } catch (error) {
      showError(error);
    }
  }

  if (target.dataset.action === "delete-task") {
    if (!window.confirm("确定删除这个任务吗？")) return;
    try {
      await api(`/tasks/${taskId}`, { method: "DELETE" });
      await refreshApp();
      showToast("任务已删除");
    } catch (error) {
      showError(error);
    }
  }
}

async function handleLogAction(event) {
  const button = event.target.closest('[data-action="delete-log"]');
  if (!button) return;
  if (!window.confirm("确定删除这条学习记录吗？")) return;
  try {
    await api(`/study-logs/${button.dataset.logId}`, { method: "DELETE" });
    await refreshApp();
    showToast("学习记录已删除");
  } catch (error) {
    showError(error);
  }
}

function renderAll() {
  els["user-greeting"].textContent = `你好，${state.user.username}`;
  syncCourseSelects();
  renderStats();
  renderCourses();
  renderTasks();
  renderChart();
  renderCourseStats();
  renderLogs();
}

function renderStats() {
  const stats = state.stats;
  if (!stats) return;
  els["stat-today"].textContent = stats.today_minutes;
  els["stat-week"].textContent = stats.week_minutes;
  els["stat-streak"].textContent = stats.current_streak;
  els["stat-tasks"].textContent = `${stats.completed_tasks} / ${stats.total_tasks}`;
}

function renderCourses() {
  const courses = state.courses;
  els["course-empty"].hidden = courses.length > 0;
  els["course-list"].innerHTML = courses.map((course) => `
    <article class="course-item">
      <span class="course-dot" style="background:${safeColor(course.color)}"></span>
      <div class="course-copy">
        <strong title="${escapeHtml(course.name)}">${escapeHtml(course.name)}</strong>
        <small>${escapeHtml(course.description || "还没有项目说明")}</small>
      </div>
      <div class="course-actions">
        <button class="icon-button" type="button" title="归档" data-action="archive" data-course-id="${course.id}">⌑</button>
        <button class="icon-button" type="button" title="删除" data-action="delete-course" data-course-id="${course.id}">×</button>
      </div>
    </article>
  `).join("");
}

function renderTasks() {
  const courseMap = new Map(state.courses.map((course) => [course.id, course]));
  els["task-count"].textContent = `${state.taskTotal} 项`;
  els["task-empty"].hidden = state.tasks.length > 0;
  els["task-list"].innerHTML = state.tasks.map((task) => {
    const course = courseMap.get(task.course_id);
    const done = task.status === "done";
    const overdue = task.due_date && !done && task.due_date < todayString();
    const meta = [
      `<span class="badge course">${escapeHtml(course?.name || "未知项目")}</span>`,
      `<span class="badge ${task.priority}">${priorityLabel(task.priority)}</span>`,
    ];
    if (task.due_date) {
      meta.push(`<span class="badge ${overdue ? "overdue" : ""}">${overdue ? "已逾期 " : ""}${formatDate(task.due_date)}</span>`);
    }
    if (task.estimated_minutes) {
      meta.push(`<span class="badge">预计 ${task.estimated_minutes} 分钟</span>`);
    }

    return `
      <article class="task-item ${done ? "done" : ""}">
        <input class="task-check" type="checkbox" ${done ? "checked" : ""}
          data-action="toggle-task" data-task-id="${task.id}" aria-label="标记完成">
        <div class="task-main">
          <div class="task-title">${escapeHtml(task.title)}</div>
          <div class="task-meta">${meta.join("")}</div>
        </div>
        <div class="task-actions">
          <select class="status-select" data-action="task-status" data-task-id="${task.id}" aria-label="任务状态">
            ${statusOption("todo", "待开始", task.status)}
            ${statusOption("in_progress", "进行中", task.status)}
            ${statusOption("done", "已完成", task.status)}
          </select>
          <button class="icon-button" type="button" title="删除" data-action="delete-task" data-task-id="${task.id}">×</button>
        </div>
      </article>
    `;
  }).join("");
}

function renderChart() {
  const days = state.stats?.daily_minutes || [];
  const max = Math.max(...days.map((item) => item.minutes), 1);
  const today = todayString();
  els["chart"].innerHTML = days.map((item) => {
    const height = item.minutes > 0 ? Math.max(7, Math.round((item.minutes / max) * 100)) : 3;
    const label = item.date === today ? "今天" : item.date.slice(5).replace("-", "/");
    return `
      <div class="chart-bar-wrap" title="${item.date}：${item.minutes} 分钟">
        <div class="chart-bar ${item.date === today ? "today" : ""}" style="height:${height}%"></div>
        <span class="chart-day">${label}</span>
      </div>
    `;
  }).join("");
}

function renderCourseStats() {
  const items = state.courseStats;
  els["course-stats-empty"].hidden = items.length > 0;
  els["course-stats"].innerHTML = items.map((item) => {
    const percent = item.total_tasks ? Math.round((item.completed_tasks / item.total_tasks) * 100) : 0;
    return `
      <div>
        <div class="course-stat-head">
          <strong>${escapeHtml(item.course_name)}</strong>
          <span>${item.minutes} 分钟 · ${percent}%</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:${percent}%"></div></div>
      </div>
    `;
  }).join("");
}

function renderLogs() {
  const courseMap = new Map(state.courses.map((course) => [course.id, course]));
  els["log-empty"].hidden = state.logs.length > 0;
  els["log-list"].innerHTML = state.logs.map((log) => {
    const course = courseMap.get(log.course_id);
    return `
      <article class="log-item">
        <span class="log-minutes">${log.minutes} 分</span>
        <div class="log-copy">
          <strong>${escapeHtml(course?.name || "未知项目")} · ${formatDate(log.studied_on)}</strong>
          <p title="${escapeHtml(log.note || "")}">${escapeHtml(log.note || "完成一次学习打卡")}</p>
        </div>
        <button class="icon-button" type="button" title="删除记录"
          data-action="delete-log" data-log-id="${log.id}">×</button>
      </article>
    `;
  }).join("");
}

function syncCourseSelects() {
  const courses = state.courses;
  const options = courses.map((course) =>
    `<option value="${course.id}">${escapeHtml(course.name)}</option>`
  ).join("");

  setSelectOptions(els["task-course"], options || '<option value="">请先创建项目</option>');
  setSelectOptions(els["log-course"], options || '<option value="">请先创建项目</option>');
  setSelectOptions(els["filter-course"], `<option value="">全部项目</option>${options}`);

  els["task-course"].disabled = courses.length === 0;
  els["log-course"].disabled = courses.length === 0;
  document.querySelector('#task-form button[type="submit"]').disabled = courses.length === 0;
  document.querySelector('#log-form button[type="submit"]').disabled = courses.length === 0;
  renderLogTaskOptions();
}

function setSelectOptions(select, markup) {
  const current = select.value;
  select.innerHTML = markup;
  if ([...select.options].some((option) => option.value === current)) {
    select.value = current;
  }
}

function renderLogTaskOptions() {
  const courseId = Number(els["log-course"].value);
  const tasks = state.allTasks.filter((task) => task.course_id === courseId && task.status !== "done");
  els["log-task"].innerHTML = '<option value="">不关联任务</option>' + tasks.map((task) =>
    `<option value="${task.id}">${escapeHtml(task.title)}</option>`
  ).join("");
}

function switchAuthTab(tab) {
  const login = tab === "login";
  els["login-tab"].classList.toggle("active", login);
  els["register-tab"].classList.toggle("active", !login);
  els["login-form"].hidden = !login;
  els["register-form"].hidden = login;
  setAuthMessage("");
}

function showApp() {
  els["auth-view"].hidden = true;
  els["app-view"].hidden = false;
}

function showAuth() {
  els["app-view"].hidden = true;
  els["auth-view"].hidden = false;
  document.querySelectorAll(".stack-form").forEach((form) => form.reset());
  setDefaultDates();
}

function logout() {
  clearSession();
  showAuth();
  switchAuthTab("login");
}

function clearSession() {
  state.token = null;
  state.user = null;
  localStorage.removeItem(TOKEN_KEY);
}

function setAuthMessage(message) {
  els["auth-message"].textContent = message;
}

function showError(error) {
  console.error(error);
  showToast(error.message || "操作失败", true);
}

let toastTimer;
function showToast(message, isError = false) {
  els["toast"].textContent = message;
  els["toast"].classList.toggle("error", isError);
  els["toast"].classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => els["toast"].classList.remove("show"), 2800);
}

function setBusy(button, busy, busyText = "处理中…") {
  if (busy) {
    button.dataset.originalText = button.textContent;
    button.textContent = busyText;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
  }
}

function statusOption(value, label, selected) {
  return `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`;
}

function priorityLabel(priority) {
  return { low: "低优先级", medium: "中优先级", high: "高优先级" }[priority] || priority;
}

function formatDate(value) {
  return value ? value.replaceAll("-", "/") : "";
}

function todayString() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function safeColor(value) {
  return /^#[0-9a-fA-F]{6}$/.test(value || "") ? value : "#6366f1";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}