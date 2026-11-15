"use strict";

const STORAGE_KEY = "local-service-ai-conversations";
const ICONS = {
  sparkles: '<path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z"/><path d="m19 14 1.1 2.9L23 18l-2.9 1.1L19 22l-1.1-2.9L15 18l2.9-1.1L19 14Z"/>',
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  message: '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z"/>',
  trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v5"/><path d="M14 11v5"/>',
  chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  chevronRight: '<path d="m9 18 6-6-6-6"/>',
  x: '<path d="m18 6-12 12"/><path d="m6 6 12 12"/>',
  settings: '<path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a8 8 0 0 1-1.7 1l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.8-1l-1.6.7-1.4-2.4L7.3 15a8 8 0 0 1 0-2l-1.4-1.1 1.4-2.4 1.7.7a8 8 0 0 1 1.7-1l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.8 1l1.6-.7 1.4 2.4-1.4 1.1a8 8 0 0 1-.1 2Z"/>',
  bot: '<rect x="4" y="7" width="16" height="13" rx="3"/><path d="M12 3v4"/><path d="M8 12h.01"/><path d="M16 12h.01"/><path d="M9 16h6"/>',
  mapPin: '<path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
  refresh: '<path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M5.6 9a7 7 0 0 1 11.6-2L20 12"/><path d="M18.4 15a7 7 0 0 1-11.6 2L4 12"/>',
  menu: '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
  more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  droplets: '<path d="M12 22a7 7 0 0 0 7-7c0-4-7-13-7-13S5 11 5 15a7 7 0 0 0 7 7Z"/><path d="M8 15a4 4 0 0 0 4 4"/>',
  zap: '<path d="m13 2-3 8h7l-6 12 1-9H5l8-11Z"/>',
  wind: '<path d="M3 8h12a3 3 0 1 0-3-3"/><path d="M2 12h17a3 3 0 1 1-3 3"/><path d="M4 16h6a3 3 0 1 1-3 3"/>',
  arrowRight: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  shield: '<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/>',
  alert: '<path d="m10.3 3.9-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  star: '<path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  checkCircle: '<circle cx="12" cy="12" r="10"/><path d="m8 12 2.5 2.5L16 9"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  rotate: '<path d="M3 12a9 9 0 1 0 2.6-6.4L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>',
  paperclip: '<path d="m21.4 11.1-8.5 8.5a6 6 0 0 1-8.5-8.5l8.5-8.5a4 4 0 0 1 5.7 5.7l-8.5 8.5a2 2 0 0 1-2.8-2.8l8.5-8.5"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2"/><path d="M12 19v3"/><path d="M8 22h8"/>',
  send: '<path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/>',
  user: '<path d="M20 21a8 8 0 0 0-16 0"/><circle cx="12" cy="8" r="5"/>',
  circleDollar: '<circle cx="12" cy="12" r="10"/><path d="M16 8h-5a2 2 0 1 0 0 4h2a2 2 0 1 1 0 4H8"/><path d="M12 6v12"/>'
};

const icon = (name, size = 16, extraClass = "") =>
  `<svg class="${extraClass}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
})[char]);

const isRecord = (value) => typeof value === "object" && value !== null && !Array.isArray(value);
const pick = (obj, ...keys) => {
  for (const key of keys) if (obj?.[key] !== undefined && obj[key] !== null) return obj[key];
};
const text = (obj, ...keys) => {
  const value = pick(obj, ...keys);
  return typeof value === "string" || typeof value === "number" ? String(value) : "";
};
const record = (obj, ...keys) => {
  const value = pick(obj, ...keys);
  return isRecord(value) ? value : undefined;
};
const list = (obj, ...keys) => {
  const value = pick(obj, ...keys);
  return Array.isArray(value) ? value : [];
};
const uid = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
const timestamp = () => new Date().toISOString();
const displayTime = (date) => {
  const value = new Date(date);
  return Number.isNaN(value.getTime()) ? "" : new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(value);
};

const suggestions = [
  { icon: "droplets", title: "Plumbing", text: "Find a plumber for water leakage.", color: "aqua" },
  { icon: "zap", title: "Electrical", text: "Get help with electrical problems.", color: "yellow" },
  { icon: "wind", title: "AC Repair", text: "Find technicians for AC servicing.", color: "blue" },
  { icon: "sparkles", title: "Home Cleaning", text: "Book professional home cleaning.", color: "violet" }
];

function createConversation() {
  const now = timestamp();
  return { id: uid(), title: "New conversation", createdAt: now, updatedAt: now, messages: [] };
}

function readConversations() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    if (Array.isArray(saved)) {
      const valid = saved.filter((item) => isRecord(item) && typeof item.id === "string" && Array.isArray(item.messages));
      if (valid.length) return valid;
    }
  } catch (error) {
    console.error("Could not restore saved conversations.", error);
  }
  return [createConversation()];
}

const state = {
  conversations: readConversations(),
  activeId: "",
  collapsed: false,
  mobileOpen: false,
  loading: false,
  listening: false,
  input: "",
  image: "",
  location: { label: "Set location", loading: false },
  search: "",
  booking: null
};
state.activeId = state.conversations[0].id;

const elements = {
  sidebar: document.getElementById("sidebar"),
  conversationList: document.getElementById("conversationList"),
  conversationSearch: document.getElementById("conversationSearch"),
  chatContent: document.getElementById("chatContent"),
  chatScroll: document.getElementById("chatScroll"),
  locationButton: document.getElementById("locationButton"),
  locationText: document.getElementById("locationText"),
  composer: document.getElementById("composer"),
  chatForm: document.getElementById("chatForm"),
  messageInput: document.getElementById("messageInput"),
  sendButton: document.getElementById("sendButton"),
  imageInput: document.getElementById("imageInput"),
  imagePreview: document.getElementById("imagePreview"),
  imagePreviewImage: document.getElementById("imagePreviewImage"),
  voiceButton: document.getElementById("voiceButton"),
  drawerScrim: document.querySelector(".drawer-scrim"),
  modalRoot: document.getElementById("modalRoot")
};

function activeConversation() {
  return state.conversations.find((conversation) => conversation.id === state.activeId) || state.conversations[0];
}

function saveConversations() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.conversations));
  } catch (error) {
    console.error("Could not save conversations in this browser.", error);
  }
}

function renderSidebar() {
  elements.sidebar.classList.toggle("is-collapsed", state.collapsed);
  elements.sidebar.classList.toggle("is-open", state.mobileOpen);
  elements.drawerScrim.hidden = !state.mobileOpen;
  elements.conversationSearch.value = state.search;
  const conversations = state.conversations.filter((item) =>
    item.title.toLowerCase().includes(state.search.toLowerCase())
  );
  elements.conversationList.innerHTML = conversations.map((item) => `
    <div class="conversation-item ${item.id === state.activeId ? "is-active" : ""}" role="button" tabindex="0" data-action="select-conversation" data-id="${escapeHtml(item.id)}" title="${escapeHtml(item.title)}">
      ${icon("message", 16)}
      <span class="conversation-title">${escapeHtml(item.title)}</span>
      <span class="delete-conversation" role="button" tabindex="0" data-action="delete-conversation" data-id="${escapeHtml(item.id)}" aria-label="Delete ${escapeHtml(item.title)}">${icon("trash", 14)}</span>
    </div>
  `).join("");
}

function renderHeader() {
  elements.locationText.textContent = state.location.label;
  elements.locationButton.disabled = state.location.loading;
  const firstIcon = elements.locationButton.querySelector("[data-icon]");
  firstIcon.innerHTML = icon(state.location.loading ? "refresh" : "mapPin", 15, state.location.loading ? "spin" : "");
  elements.locationButton.title = state.location.error || "Refresh current location";
}

function renderWelcome() {
  return `
    <section class="welcome">
      <div class="welcome-orb">${icon("sparkles", 30)}</div>
      <p class="eyebrow">Your home, thoughtfully handled</p>
      <h1>What can we take<br><em>care of today?</em></h1>
      <p class="welcome-copy">Tell us what’s happening. We’ll understand the issue and show matching providers from the local directory.</p>
      <div class="suggestion-grid">
        ${suggestions.map((item) => `
          <button class="suggestion-card" type="button" data-action="suggest" data-prompt="${escapeHtml(item.text)}">
            <span class="suggestion-icon ${item.color}">${icon(item.icon, 19)}</span>
            <span class="suggestion-content"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.text)}</span></span>
            ${icon("arrowRight", 17, "suggestion-arrow")}
          </button>
        `).join("")}
      </div>
      <p class="welcome-note">${icon("shield", 14)} Safety-aware guidance from the service directory</p>
    </section>
  `;
}

function markdown(value) {
  return String(value || "").split("\n").map((line) => {
    const safe = escapeHtml(line).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    return /^[-•]\s/.test(line)
      ? `<div class="bullet-line"><i></i>${safe.slice(2)}</div>`
      : line ? `<p>${safe}</p>` : "<br>";
  }).join("");
}

function renderSafetyWarning(message) {
  return message ? `
    <div class="safety-warning">
      <span>${icon("alert", 18)}</span>
      <div><strong>Safety notice</strong><p>${escapeHtml(message)}</p></div>
    </div>
  ` : "";
}

function renderAnalysis(data) {
  const analysis = record(data, "analysis", "serviceAnalysis", "service_analysis") || data;
  const category = text(analysis, "category", "serviceCategory", "service_category");
  const issue = text(analysis, "issue", "issue_type", "identifiedIssue", "identified_issue");
  const summary = text(analysis, "summary", "problemSummary", "problem_summary");
  const rawConfidence = pick(analysis, "confidence", "confidencePercentage", "confidence_percentage");
  const numericConfidence = typeof rawConfidence === "number"
    ? (rawConfidence <= 1 ? rawConfidence * 100 : rawConfidence)
    : Number.parseFloat(String(rawConfidence ?? ""));
  const confidence = Number.isFinite(numericConfidence) ? Math.min(100, Math.round(numericConfidence)) : null;
  const missing = list(analysis, "missingInformation", "missing_information", "missingFields").map(String);
  if (!category && !issue && !summary && confidence === null && !missing.length) return "";
  return `
    <div class="analysis-card">
      <div class="card-title"><span>${icon("sparkles", 16)}</span><div><strong>Service analysis</strong><small>AI assessment</small></div></div>
      <div class="analysis-grid">
        ${category ? `<div><small>Service category</small><strong>${escapeHtml(category)}</strong></div>` : ""}
        ${issue ? `<div><small>Identified issue</small><strong>${escapeHtml(issue)}</strong></div>` : ""}
      </div>
      ${summary ? `<div class="summary-box"><small>Problem summary</small><p>${escapeHtml(summary)}</p></div>` : ""}
      ${confidence !== null ? `<div class="confidence"><div><span>AI confidence</span><strong>${confidence}%</strong></div><div class="progress"><i style="width:${confidence}%"></i></div></div>` : ""}
      ${missing.length ? `<div class="missing-info"><small>More information may help</small><div>${missing.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div></div>` : ""}
    </div>
  `;
}

function renderFollowUp(data, disabled) {
  const follow = record(data, "followUp", "follow_up", "followUpQuestion");
  const question = text(follow, "question", "message") || text(data, "followUpQuestion", "follow_up_question");
  if (!question) return "";
  const options = (follow
    ? list(follow, "options", "suggestions", "suggestedAnswers")
    : list(data, "suggestedAnswers", "suggestions")).map(String);
  return `
    <div class="follow-up-card">
      <div class="follow-up-title"><span>${icon("message", 17)}</span><div><small>A quick question</small><strong>${escapeHtml(question)}</strong></div></div>
      ${options.length ? `<div class="answer-chips">${options.map((option) => `<button type="button" data-action="answer-chip" data-answer="${escapeHtml(option)}">${escapeHtml(option)}</button>`).join("")}</div>` : ""}
      <form class="inline-answer" data-followup-form>
        <input name="answer" placeholder="Type your answer..." aria-label="Follow-up answer" autocomplete="off">
        <button type="submit" aria-label="Submit answer" ${disabled ? "disabled" : ""}>${icon("arrowRight", 17)}</button>
      </form>
    </div>
  `;
}

function renderProviders(data) {
  const providers = list(data, "providers", "recommended_providers", "recommendations", "serviceProviders", "service_providers")
    .filter(isRecord);
  if (!providers.length) return "";
  return `
    <div class="provider-wrap">
      <div class="component-heading"><div><strong>Matching providers</strong><span>${providers.length} listed providers</span></div></div>
      <div class="provider-grid">
        ${providers.map((provider, index) => {
          const name = text(provider, "name", "shop_name", "providerName", "business_name") || "Service provider";
          const rating = text(provider, "rating");
          const reviews = text(provider, "reviewCount", "reviews", "review_count");
          const distance = text(provider, "distance_km", "distance");
          const area = text(provider, "area", "address");
          const verified = text(provider, "verification_status").toLowerCase() === "verified";
          const slots = list(provider, "slots", "availableSlots", "available_time_slots").map(String);
          const initials = name.split(/\s+/).slice(0, 2).map((part) => part[0] || "").join("").toUpperCase();
          return `
            <article class="provider-card" data-provider="${index}">
              ${provider.recommended || provider.isRecommended || provider.bestMatch ? `<span class="recommended-badge">${icon("sparkles", 11)}Top match</span>` : ""}
              <div class="provider-top">
                <div class="provider-avatar">${escapeHtml(initials)}</div>
                <div class="provider-name">
                  <strong title="${escapeHtml(name)}">${escapeHtml(name)}</strong>
                  <span>${rating ? `${icon("star", 13)}${escapeHtml(rating)}` : ""}${reviews ? ` (${escapeHtml(reviews)} reviews)` : ""}</span>
                </div>
                ${verified ? `<span class="verified">${icon("checkCircle", 18)}</span>` : ""}
              </div>
              <div class="provider-facts">
                ${area ? `<span>${icon("mapPin", 14)}${escapeHtml(area)}</span>` : ""}
                ${distance ? `<span>${icon("mapPin", 14)}${Number.isFinite(Number(distance)) ? `${Number(distance).toFixed(1)} km away` : escapeHtml(distance)}</span>` : ""}
              </div>
              ${slots.length ? `<div class="slots">${slots.slice(0, 3).map((slot) => `<span>${escapeHtml(slot)}</span>`).join("")}</div>` : ""}
            </article>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function renderTimeline(data) {
  const steps = list(data, "agentSteps", "agent_steps", "executionTimeline", "timeline");
  if (!steps.length) return "";
  return `
    <div class="timeline-card">
      <div class="card-title"><span>${icon("bot", 16)}</span><div><strong>Agent workflow</strong><small>MCP execution timeline</small></div></div>
      <div class="timeline">${steps.map((raw, index) => {
        const step = isRecord(raw) ? raw : null;
        const label = step ? text(step, "label", "title", "name", "step") : String(raw);
        const status = step ? text(step, "status", "state").toLowerCase() : "complete";
        const active = ["running", "active", "in_progress", "processing"].includes(status);
        const pending = ["pending", "queued", "waiting"].includes(status);
        return `<div class="timeline-step ${active ? "active" : ""} ${pending ? "pending" : ""}"><span>${active ? icon("refresh", 13, "spin") : pending ? index + 1 : icon("check", 13)}</span><div><strong>${escapeHtml(label)}</strong>${step && text(step, "detail", "description") ? `<small>${escapeHtml(text(step, "detail", "description"))}</small>` : ""}</div></div>`;
      }).join("")}</div>
    </div>
  `;
}

function renderBooking(data) {
  const booking = record(data, "booking", "bookingResult", "booking_result", "confirmation");
  if (!booking) return "";
  const provider = record(booking, "provider");
  const providerName = text(booking, "providerName", "provider_name") || text(provider, "name");
  const reference = text(booking, "reference", "bookingReference", "booking_id", "id");
  const total = text(booking, "total", "totalAmount", "estimatedTotal", "total_estimated_amount");
  const details = [
    ["Professional", providerName],
    ["Service", text(booking, "service", "serviceName", "service_name")],
    ["Appointment", text(booking, "slot", "appointmentSlot", "appointment_slot")],
    ["Arrival", text(booking, "arrivalTime", "eta", "estimated_arrival")]
  ].filter((item) => item[1]);
  return `
    <div class="booking-card">
      <div class="booking-success"><span>${icon("check", 20)}</span><div><strong>Booking prepared</strong><small>${reference ? `Reference ${escapeHtml(reference)}` : "Service request ready"}</small></div></div>
      <div class="demo-note">${icon("shield", 14)}Demo booking — no external provider has been contacted.</div>
      <div class="booking-details">${details.map(([label, value]) => `<div><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong></div>`).join("")}</div>
      <div class="booking-total"><span>${icon("circleDollar", 16)}Estimated total</span><strong>${escapeHtml(total || "Not provided")}</strong></div>
      <button class="view-confirmation" data-action="view-booking">${escapeHtml("View full confirmation")} ${icon("arrowRight", 15)}</button>
    </div>
  `;
}

function renderUserMessage(message) {
  return `
    <div class="message-row user-row">
      <div class="user-message">
        ${message.image ? `<img src="${escapeHtml(message.image)}" alt="User attachment">` : ""}
        ${message.text ? `<p>${escapeHtml(message.text)}</p>` : ""}
        <time>${escapeHtml(displayTime(message.createdAt))}</time>
      </div>
      <div class="user-avatar">${icon("user", 15)}</div>
    </div>
  `;
}

function renderAssistantMessage(message) {
  const data = isRecord(message.data) ? message.data : null;
  const warning = data ? text(data, "safetyWarning", "safety_warning", "emergencyWarning", "warning") : "";
  return `
    <div class="message-row assistant-row" data-message-id="${escapeHtml(message.id)}">
      <div class="ai-avatar">${icon("sparkles", 15)}</div>
      <div class="assistant-content">
        <div class="message-author"><strong>Local Service AI</strong><span>${escapeHtml(displayTime(message.createdAt))}</span></div>
        ${message.text && !message.error ? `<div class="message-text">${markdown(message.text)}</div>` : ""}
        ${message.error ? `<div class="error-label">${icon("alert", 15)}${escapeHtml(message.text)}</div>` : ""}
        ${renderSafetyWarning(warning)}
        ${data ? renderAnalysis(data) : ""}
        ${data ? renderFollowUp(data, state.loading) : ""}
        ${data ? renderProviders(data) : ""}
        ${data ? renderTimeline(data) : ""}
        ${data ? renderBooking(data) : ""}
        <div class="message-tools">
          <button type="button" data-action="copy-message" data-id="${escapeHtml(message.id)}">${icon("copy", 14)}Copy</button>
          <button type="button" data-action="regenerate">${icon("rotate", 14)}Regenerate</button>
        </div>
      </div>
    </div>
  `;
}

function renderTyping() {
  return `
    <div class="message-row assistant-row typing-row">
      <div class="ai-avatar">${icon("sparkles", 15)}</div>
      <div><div class="message-author"><strong>Local Service AI</strong><span>Analyzing your request</span></div><div class="typing-bubble"><i></i><i></i><i></i></div></div>
    </div>
  `;
}

function renderChat() {
  const conversation = activeConversation();
  if (!conversation.messages.length) {
    elements.chatContent.classList.add("is-empty");
    elements.chatContent.innerHTML = renderWelcome();
  } else {
    elements.chatContent.classList.remove("is-empty");
    elements.chatContent.innerHTML = `<div class="messages">${conversation.messages.map((message) =>
      message.role === "user" ? renderUserMessage(message) : renderAssistantMessage(message)
    ).join("")}${state.loading ? renderTyping() : ""}<div id="chatEnd"></div></div>`;
    elements.chatScroll.scrollTop = elements.chatScroll.scrollHeight;
  }
}

function renderComposer() {
  elements.composer.classList.toggle("is-disabled", state.loading);
  elements.messageInput.disabled = state.loading;
  elements.sendButton.disabled = state.loading || (!state.input.trim() && !state.image);
  elements.voiceButton.classList.toggle("is-listening", state.listening);
  elements.imagePreview.hidden = !state.image;
  if (state.image) elements.imagePreviewImage.src = state.image;
  elements.messageInput.value = state.input;
  elements.messageInput.style.height = "0px";
  elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 140)}px`;
}

function renderModal() {
  if (!state.booking) {
    elements.modalRoot.innerHTML = "";
    return;
  }
  const booking = state.booking;
  const provider = record(booking, "provider");
  const details = [
    ["Booking reference", text(booking, "reference", "bookingReference", "booking_id", "id")],
    ["Provider", text(booking, "providerName", "provider_name") || text(provider, "name")],
    ["Service", text(booking, "service", "serviceName", "service_name")],
    ["Appointment", text(booking, "slot", "appointmentSlot", "appointment_slot")],
    ["Estimated arrival", text(booking, "arrivalTime", "eta", "estimated_arrival")],
    ["Visit charge", text(booking, "visitCharge", "visit_charge")],
    ["Service estimate", text(booking, "servicePrice", "estimatedPrice", "estimated_price")]
  ].filter((item) => item[1]);
  elements.modalRoot.innerHTML = `
    <div class="modal-layer" role="dialog" aria-modal="true" aria-label="Booking confirmation">
      <button class="modal-scrim" data-action="close-modal" aria-label="Close"></button>
      <div class="booking-modal">
        <button class="modal-close icon-button" data-action="close-modal" aria-label="Close">${icon("x", 18)}</button>
        <div class="modal-success">${icon("check", 25)}</div>
        <p class="eyebrow">Confirmation summary</p>
        <h2>Your service request is prepared</h2>
        <p class="modal-copy">Review the details below. This is a demo/prepared booking unless your connected provider confirms otherwise.</p>
        <div class="modal-rows">${details.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}</div>
        <div class="modal-total"><span>Total estimated amount</span><strong>${escapeHtml(text(booking, "total", "totalAmount", "estimatedTotal") || "Not provided")}</strong></div>
        <button class="modal-done" data-action="close-modal">Done</button>
      </div>
    </div>
  `;
}

function renderAll() {
  renderSidebar();
  renderHeader();
  renderChat();
  renderComposer();
  renderModal();
}

function updateActive(updater) {
  state.conversations = state.conversations.map((conversation) =>
    conversation.id === state.activeId ? updater(conversation) : conversation
  );
  saveConversations();
}

function normalizeResponse(data) {
  const wrapped = record(data, "data", "result");
  const source = wrapped ? { ...data, ...wrapped } : data;
  const recommendations = record(source, "recommendations");
  const analysis = record(source, "analysis") || record(recommendations, "analysis");
  const followUpQuestion = text(analysis, "follow_up_question");
  return {
    ...source,
    ...(analysis ? { analysis } : {}),
    ...(recommendations ? {
      providers: list(recommendations, "recommended_providers", "providers"),
      safety_warning: text(analysis, "safety_warning") || text(recommendations, "safety_advisory"),
      ...(text(recommendations, "notice") ? { service_notice: text(recommendations, "notice") } : {})
    } : {}),
    ...(followUpQuestion ? {
      followUp: {
        question: followUpQuestion,
        options: list(analysis, "suggested_replies")
      }
    } : {})
  };
}

function responseText(data) {
  const recommendations = record(data, "recommendations");
  const analysis = record(data, "analysis");
  return text(data, "message", "response", "answer", "content", "text")
    || text(record(data, "result"), "message", "response", "answer", "content")
    || text(recommendations, "notice", "service_notice")
    || text(data, "service_notice")
    || text(analysis, "problem_summary")
    || (record(data, "followUp", "follow_up")
      ? "I need a little more information to help you accurately."
      : "Here are the local service options I found.");
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : { message: await response.text() };
  if (!response.ok) {
    const detail = payload.detail ?? payload.error ?? payload.message;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || `Request failed (${response.status})`));
  }
  return payload;
}

async function requestAnalysis(prompt, attachment, conversation) {
  const history = conversation.messages
    .filter((message) => message.text && message.text.trim())
    .map((message) => ({ role: message.role, content: message.text }));
  return parseResponse(await fetch("/api/service-ai/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      problem_description: prompt,
      session_id: conversation.id,
      image_base64: attachment || undefined,
      conversation_history: history,
      latitude: state.location.latitude,
      longitude: state.location.longitude,
      city: state.location.label
    })
  }));
}

async function requestFollowUp(prompt, conversation) {
  return parseResponse(await fetch("/api/service-ai/follow-up", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: conversation.id, clarification: prompt })
  }));
}

async function appendAndRequest(prompt, attachment = "", followUp = false, regenerate = false) {
  if (state.loading || (!prompt.trim() && !attachment)) return;
  const conversation = activeConversation();
  const userMessage = {
    id: uid(),
    role: "user",
    text: prompt.trim(),
    image: attachment || undefined,
    createdAt: timestamp()
  };
  updateActive((current) => {
    const messages = regenerate
      ? current.messages.slice(0, -1)
      : [...current.messages, userMessage];
    return {
      ...current,
      title: current.messages.length === 0
        ? (prompt.trim() || "Image request").slice(0, 42)
        : current.title,
      updatedAt: timestamp(),
      messages
    };
  });
  state.input = "";
  state.image = "";
  state.loading = true;
  renderAll();

  try {
    const response = followUp
      ? await requestFollowUp(prompt, conversation)
      : await requestAnalysis(prompt, attachment, conversation);
    const data = normalizeResponse(response);
    const assistant = {
      id: uid(),
      role: "assistant",
      text: responseText(data),
      data,
      createdAt: timestamp()
    };
    updateActive((current) => ({
      ...current,
      updatedAt: assistant.createdAt,
      messages: [...current.messages, assistant]
    }));
  } catch (error) {
    const assistant = {
      id: uid(),
      role: "assistant",
      error: true,
      text: error instanceof Error ? error.message : "The request could not be completed.",
      createdAt: timestamp()
    };
    updateActive((current) => ({
      ...current,
      updatedAt: assistant.createdAt,
      messages: [...current.messages, assistant]
    }));
  } finally {
    state.loading = false;
    renderAll();
  }
}

async function refreshLocation() {
  if (!navigator.geolocation) {
    state.location = { label: "Location unavailable", loading: false, error: "Geolocation is not supported." };
    renderHeader();
    return;
  }
  state.location = { ...state.location, loading: true, error: "" };
  renderHeader();
  navigator.geolocation.getCurrentPosition(async ({ coords }) => {
    try {
      const params = new URLSearchParams({
        latitude: String(coords.latitude),
        longitude: String(coords.longitude)
      });
      const place = await parseResponse(await fetch(`/api/location/resolve?${params}`));
      state.location = {
        label: text(place, "label", "location", "displayName", "display_name", "place_name", "city") || "Current location",
        latitude: coords.latitude,
        longitude: coords.longitude,
        loading: false
      };
    } catch (error) {
      console.error("Could not resolve the current location.", error);
      state.location = {
        label: "Current location",
        latitude: coords.latitude,
        longitude: coords.longitude,
        loading: false,
        error: error instanceof Error ? error.message : "Could not resolve location."
      };
    }
    renderHeader();
  }, () => {
    state.location = {
      label: "Location blocked",
      loading: false,
      error: "Allow location access to find nearby providers."
    };
    renderHeader();
  }, { enableHighAccuracy: false, timeout: 10000 });
}

function startVoiceInput() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    window.alert("Voice input is not supported by this browser.");
    return;
  }
  const recognition = new Recognition();
  recognition.lang = navigator.language;
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onresult = (event) => {
    const spoken = event.results?.[0]?.[0]?.transcript || "";
    state.input = `${state.input}${state.input ? " " : ""}${spoken}`;
    renderComposer();
    elements.messageInput.focus();
  };
  recognition.onerror = (event) => {
    state.listening = false;
    renderComposer();
    if (event.error !== "no-speech" && event.error !== "aborted") {
      window.alert(`Voice input failed: ${event.error}`);
    }
  };
  recognition.onend = () => {
    state.listening = false;
    renderComposer();
  };
  state.listening = true;
  renderComposer();
  recognition.start();
}

function setNewConversation() {
  const conversation = createConversation();
  state.conversations.unshift(conversation);
  state.activeId = conversation.id;
  state.mobileOpen = false;
  state.input = "";
  state.image = "";
  saveConversations();
  renderAll();
}

function deleteConversation(id) {
  state.conversations = state.conversations.filter((conversation) => conversation.id !== id);
  if (!state.conversations.length) state.conversations.push(createConversation());
  if (state.activeId === id) state.activeId = state.conversations[0].id;
  saveConversations();
  renderAll();
}

function handleImage(file) {
  if (!file || !file.type.startsWith("image/")) {
    window.alert("Choose an image file to attach.");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    state.image = String(reader.result || "");
    renderComposer();
  };
  reader.onerror = () => window.alert("The selected image could not be read.");
  reader.readAsDataURL(file);
}

document.querySelectorAll("[data-icon]").forEach((element) => {
  element.innerHTML = icon(element.dataset.icon, 18);
});
renderAll();
refreshLocation();

elements.conversationSearch.addEventListener("input", (event) => {
  state.search = event.target.value;
  renderSidebar();
});

elements.messageInput.addEventListener("input", (event) => {
  state.input = event.target.value;
  renderComposer();
  elements.messageInput.focus();
});

elements.messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.chatForm.requestSubmit();
  }
});

elements.chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  appendAndRequest(state.input, state.image);
});

elements.imageInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (file) handleImage(file);
  event.target.value = "";
});

document.addEventListener("submit", (event) => {
  const form = event.target.closest("[data-followup-form]");
  if (!form) return;
  event.preventDefault();
  const answer = new FormData(form).get("answer");
  if (typeof answer === "string" && answer.trim()) appendAndRequest(answer.trim(), "", true);
});

document.addEventListener("click", async (event) => {
  const actionElement = event.target.closest("[data-action]");
  if (!actionElement) return;
  const { action, id } = actionElement.dataset;
  if (action === "delete-conversation") {
    event.stopPropagation();
    deleteConversation(id);
  } else if (action === "select-conversation") {
    state.activeId = id;
    state.mobileOpen = false;
    renderAll();
  } else if (action === "new-chat") {
    setNewConversation();
  } else if (action === "toggle-sidebar") {
    state.collapsed = !state.collapsed;
    renderSidebar();
  } else if (action === "open-menu") {
    state.mobileOpen = true;
    renderSidebar();
  } else if (action === "close-menu") {
    state.mobileOpen = false;
    renderSidebar();
  } else if (action === "refresh-location") {
    refreshLocation();
  } else if (action === "suggest") {
    appendAndRequest(actionElement.dataset.prompt || "");
  } else if (action === "answer-chip") {
    const form = actionElement.closest(".follow-up-card")?.querySelector("[name=answer]");
    if (form) {
      form.value = actionElement.dataset.answer || "";
      form.focus();
    }
  } else if (action === "remove-image") {
    state.image = "";
    renderComposer();
  } else if (action === "voice-input") {
    startVoiceInput();
  } else if (action === "copy-message") {
    const message = activeConversation().messages.find((item) => item.id === id);
    if (message) {
      try {
        await navigator.clipboard.writeText(message.text || "");
      } catch (error) {
        console.error("Could not copy the response.", error);
        window.alert("Could not copy the response. Check clipboard permissions.");
      }
    }
  } else if (action === "regenerate") {
    const lastUser = [...activeConversation().messages].reverse().find((message) => message.role === "user");
    if (lastUser) appendAndRequest(lastUser.text, lastUser.image || "", false, true);
  } else if (action === "view-booking") {
    const assistant = [...activeConversation().messages].reverse().find((message) => message.role === "assistant" && record(message.data, "booking", "bookingResult", "booking_result", "confirmation"));
    state.booking = assistant ? record(assistant.data, "booking", "bookingResult", "booking_result", "confirmation") : null;
    renderModal();
  } else if (action === "close-modal") {
    state.booking = null;
    renderModal();
  }
});

document.addEventListener("keydown", (event) => {
  const item = event.target.closest('[data-action="select-conversation"]');
  if (item && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    state.activeId = item.dataset.id;
    state.mobileOpen = false;
    renderAll();
  }
  const remove = event.target.closest('[data-action="delete-conversation"]');
  if (remove && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    event.stopPropagation();
    deleteConversation(remove.dataset.id);
  }
});
