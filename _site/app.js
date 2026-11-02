"use strict";

const $ = (selector) => document.querySelector(selector);
const spaces = {
  growth: { key: "videos", title: "w的提升空间", eyebrow: "01 / PERSONAL GROWTH", description: "把努力的过程，留在时光里。每一个片段，都是向前的一步。", emptyTitle: "第一个成长片段，等你放进来。", emptyDescription: "故事慢慢写，成长慢慢来。", icon: "▷" },
  fitness: { key: "photos", title: "w的健身空间", eyebrow: "02 / FITNESS & WELLNESS", description: "每一次流汗，都有自己的光。记录身体的变化，也记录坚持的自己。", emptyTitle: "下一次闪闪发光的自己，记录在这里。", emptyDescription: "下一份运动记忆，值得期待。", icon: "✳" },
};
let library = { videos: [], photos: [] };
let currentSpace = "home";
let visibleItems = [];
const mediaViewer = new MediaViewer($("#viewer-dialog"));

function make(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function loadLibrary() {
  for (const category of ["videos", "photos"]) {
    const filenames = window.LIFE_MEDIA?.[category] || [];
    library[category] = filenames.map((filename) => {
      const name = filename.split("/").pop();
      const stem = name.replace(/\.[^.]+$/, "");
      const match = stem.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
      let date = null;
      let title = stem;
      if (match) {
        const [year, month, day] = match.slice(1).map(Number);
        const parsed = new Date(Date.UTC(year, month - 1, day));
        if (parsed.getUTCFullYear() === year && parsed.getUTCMonth() === month - 1 && parsed.getUTCDate() === day) {
          date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          title = `${year}年${month}月${day}日`;
        }
      }
      return { name, title, date, type: category === "videos" ? "video" : "image", src: `media/${category}/${filename.split("/").map(encodeURIComponent).join("/")}` };
    });
  }
  document.querySelectorAll("[data-count]").forEach((element) => { element.textContent = library[element.dataset.count].length; });
}

function sortedItems(items) {
  return [...items].sort((a, b) => {
    if (!a.date && b.date) return 1;
    if (a.date && !b.date) return -1;
    const order = (a.date || "").localeCompare(b.date || "");
    return (($("#sort-order").value === "oldest") ? order : -order) || a.name.localeCompare(b.name, "zh-CN");
  });
}

function renderCollection() {
  const space = spaces[currentSpace];
  if (!space) return;
  const isVideo = space.key === "videos";
  visibleItems = isVideo ? sortedItems(library[space.key]) : library[space.key];
  $("#sort-label").hidden = !isVideo;
  $("#sort-order").hidden = !isVideo;
  $("#collection-total").textContent = `共 ${visibleItems.length} ${isVideo ? "个成长片段" : "张运动记忆"}`;
  const grid = $("#media-grid");
  grid.className = isVideo ? "video-grid" : "photo-grid";
  grid.replaceChildren();
  $("#empty-state").hidden = visibleItems.length > 0;
  grid.hidden = visibleItems.length === 0;
  $("#empty-title").textContent = space.emptyTitle;
  $("#empty-description").textContent = space.emptyDescription;
  $("#empty-icon").textContent = space.icon;
  visibleItems.forEach((item, index) => {
    if (isVideo) {
      const card = make("article", "video-card");
      const preview = make("button", "video-preview");
      preview.type = "button";
      preview.setAttribute("aria-label", `播放 ${item.name}`);
      const video = make("video");
      video.src = item.src;
      video.preload = "metadata";
      video.muted = true;
      video.playsInline = true;
      video.setAttribute("aria-hidden", "true");
      preview.append(video, make("span", "video-play", "▷"));
      preview.addEventListener("click", () => mediaViewer.open(visibleItems, index));
      const meta = make("div", "video-meta");
      meta.append(make("h2", "", item.title));
      card.append(preview, meta);
      grid.append(card);
    } else {
      const card = make("button", "photo-card");
      card.type = "button";
      card.setAttribute("aria-label", `查看第 ${index + 1} 张图片`);
      const image = make("img");
      image.src = item.src;
      image.alt = `第 ${index + 1} 张图片`;
      image.loading = "lazy";
      image.addEventListener("error", () => {
        image.remove();
        card.append(make("div", "media-load-error", "图片暂时无法显示，点击查看"));
      }, { once: true });
      card.append(image);
      card.addEventListener("click", () => mediaViewer.open(visibleItems, index));
      grid.append(card);
    }
  });
}

function navigate() {
  const route = location.hash.slice(1);
  const nextSpace = route === "spaces" || spaces[route] ? route : "home";
  const changed = currentSpace !== nextSpace;
  if (changed) mediaViewer.close();
  currentSpace = nextSpace;
  const collection = spaces[currentSpace];
  $("#home-view").hidden = currentSpace !== "home";
  $("#spaces-view").hidden = currentSpace !== "spaces";
  $("#space-view").hidden = !collection;
  document.querySelectorAll("[data-nav]").forEach((element) => {
    const active = element.dataset.nav === (collection ? "spaces" : currentSpace);
    element.classList.toggle("active", active);
    if (active) element.setAttribute("aria-current", "page");
    else element.removeAttribute("aria-current");
  });
  document.title = collection ? `${collection.title} · W 的生活空间` : currentSpace === "spaces" ? "我的空间 · W 的生活空间" : "W 的生活空间 · 认真生活，慢慢记录";
  if (collection) {
    const space = collection;
    $("#space-title").textContent = space.title;
    $("#space-eyebrow").textContent = space.eyebrow;
    $("#space-description").textContent = space.description;
    $("#space-symbol").textContent = space.icon;
    if (changed) $("#sort-order").value = "newest";
    renderCollection();
  }
  if (changed) {
    window.scrollTo({ top: 0, behavior: "instant" });
    $("#main").focus({ preventScroll: true });
  }
}

$("#sort-order").addEventListener("change", renderCollection);
$("#refresh-library").addEventListener("click", () => location.reload());
window.addEventListener("hashchange", navigate);
$("#current-year").textContent = new Date().getFullYear();
loadLibrary();
navigate();
