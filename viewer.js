/* 图片和视频共用的查看壳层。用法：viewer.open([{type, src, title, name}], index)。 */
(() => {
  "use strict";

  class MediaViewer {
    constructor(dialog) {
      this.dialog = dialog;
      this.content = dialog.querySelector("[data-viewer-content]");
      this.title = dialog.querySelector("[data-viewer-title]");
      this.counter = dialog.querySelector("[data-viewer-counter]");
      this.status = dialog.querySelector("[data-viewer-status]");
      this.previous = dialog.querySelector("[data-viewer-previous]");
      this.next = dialog.querySelector("[data-viewer-next]");
      this.items = [];
      this.index = -1;
      this.media = null;

      this.previous.addEventListener("click", () => this.step(-1));
      this.next.addEventListener("click", () => this.step(1));
      dialog.querySelector("[data-viewer-close]").addEventListener("click", () => this.close());
      dialog.addEventListener("close", () => {
        if (!dialog.open) this.reset();
      });
      dialog.addEventListener("keydown", (event) => {
        // 视频获得焦点时保留播放器原生的快进、后退操作。
        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
            event.target.closest("video, input, textarea, select, [contenteditable]")) return;
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          event.preventDefault();
          this.step(event.key === "ArrowLeft" ? -1 : 1);
        }
      });
      dialog.addEventListener("click", (event) => {
        if (event.target === dialog || event.target === this.content || event.target.classList.contains("viewer-stage")) this.close();
      });

      let touchStart = null;
      this.content.addEventListener("touchstart", (event) => {
        if (event.touches.length !== 1 || event.target.closest("video")) {
          touchStart = null;
          return;
        }
        touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
      }, { passive: true });
      this.content.addEventListener("touchend", (event) => {
        if (!touchStart || !event.changedTouches.length) return;
        const dx = event.changedTouches[0].clientX - touchStart.x;
        const dy = event.changedTouches[0].clientY - touchStart.y;
        touchStart = null;
        if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) this.step(dx < 0 ? 1 : -1);
      }, { passive: true });
      this.content.addEventListener("touchcancel", () => { touchStart = null; });
    }

    open(items, index = 0) {
      if (!items.length || !items[index]) return;
      this.items = [...items];
      this.index = index;
      this.render();
      document.documentElement.classList.add("viewer-open");
      if (!this.dialog.open) this.dialog.showModal();
    }

    step(direction) {
      if (!this.dialog.open || this.items.length < 2) return;
      this.index = (this.index + direction + this.items.length) % this.items.length;
      this.render();
    }

    clearMedia() {
      const previous = this.media;
      this.media = null;
      if (previous?.tagName === "VIDEO") {
        previous.pause();
        previous.removeAttribute("src");
        previous.load();
      }
      this.content.replaceChildren();
    }

    render() {
      this.clearMedia();
      const item = this.items[this.index];
      const isVideo = item.type === "video";
      const media = document.createElement(isVideo ? "video" : "img");
      this.media = media;
      media.className = "viewer-media";
      if (isVideo) {
        media.controls = true;
        media.autoplay = true;
        media.playsInline = true;
        media.preload = "auto";
        media.setAttribute("aria-label", item.title || item.name || "视频");
      } else {
        media.alt = `第 ${this.index + 1} 张图片`;
        media.draggable = false;
      }
      this.title.textContent = isVideo ? item.title || item.name || "视频" : "图片预览";
      this.counter.textContent = `${this.index + 1} / ${this.items.length}`;
      this.previous.disabled = this.items.length < 2;
      this.next.disabled = this.items.length < 2;
      this.status.textContent = "正在加载…";
      this.status.hidden = false;
      this.content.setAttribute("aria-busy", "true");
      media.addEventListener(isVideo ? "loadeddata" : "load", () => {
        if (this.media !== media) return;
        this.status.hidden = true;
        this.content.setAttribute("aria-busy", "false");
      }, { once: true });
      media.addEventListener("error", () => {
        if (this.media !== media) return;
        this.status.textContent = "暂时无法打开这个文件，可以切换查看其他记录。";
        this.status.hidden = false;
        this.content.setAttribute("aria-busy", "false");
      }, { once: true });
      media.src = item.src;
      this.content.append(media);
    }

    reset() {
      this.clearMedia();
      this.items = [];
      this.index = -1;
      this.status.hidden = true;
      this.content.setAttribute("aria-busy", "false");
      document.documentElement.classList.remove("viewer-open");
    }

    close() {
      if (this.dialog.open) this.dialog.close();
      this.reset();
    }
  }

  window.MediaViewer = MediaViewer;
})();
