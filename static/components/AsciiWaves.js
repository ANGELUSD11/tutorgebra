// Animated ASCII wave background.
// Color comes from Tailwind classes: purple in light mode, white in dark mode.
const RAMP = '   ..··::•';
const FONT_SIZE = 14;
const FRAME_MS = 1000 / 30;

export default {
    template: `
    <pre ref="canvas" aria-hidden="true"
         class="fixed inset-0 -z-10 m-0 overflow-hidden pointer-events-none select-none font-mono text-primary-600/30 dark:text-white/20 transition-colors duration-200"
         :style="{ fontSize: fontSize + 'px', lineHeight: fontSize + 'px' }"></pre>
    `,
    data() {
        return { fontSize: FONT_SIZE };
    },
    mounted() {
        this.cols = 0;
        this.rows = 0;
        this.lastFrame = 0;
        this.rafId = null;

        this.measure();
        // Watch the element itself: on mobile the layout viewport can be wider than window.innerWidth.
        this.resizeObserver = new ResizeObserver(() => {
            clearTimeout(this.resizeTimer);
            this.resizeTimer = setTimeout(() => {
                this.measure();
                if (this.reducedMotion) this.draw(0);
            }, 150);
        });
        this.resizeObserver.observe(this.$refs.canvas);

        this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (this.reducedMotion) {
            this.draw(0);
        } else {
            this.rafId = requestAnimationFrame(this.tick);
        }
    },
    unmounted() {
        cancelAnimationFrame(this.rafId);
        clearTimeout(this.resizeTimer);
        this.resizeObserver.disconnect();
    },
    methods: {
        measure() {
            const el = this.$refs.canvas;
            const probe = document.createElement('span');
            probe.textContent = 'M'.repeat(20);
            el.textContent = '';
            el.appendChild(probe);
            const charWidth = probe.getBoundingClientRect().width / 20 || FONT_SIZE * 0.6;
            el.removeChild(probe);
            const width = el.clientWidth || window.innerWidth;
            const height = el.clientHeight || window.innerHeight;
            this.cols = Math.ceil(width / charWidth) + 2;
            this.rows = Math.ceil(height / this.fontSize) + 2;
        },
        tick(now) {
            this.rafId = requestAnimationFrame(this.tick);
            if (now - this.lastFrame < FRAME_MS) return;
            this.lastFrame = now;
            this.draw(now / 1000);
        },
        draw(t) {
            const { cols, rows } = this;
            const last = RAMP.length - 1;
            const lines = new Array(rows);
            for (let y = 0; y < rows; y++) {
                let line = '';
                for (let x = 0; x < cols; x++) {
                    // Three overlapping waves; the middle one bends with x so the crests roll.
                    const v =
                        Math.sin(x * 0.09 + t * 0.9) +
                        Math.sin(y * 0.22 - t * 0.7 + Math.sin(x * 0.04 + t * 0.3) * 2) +
                        Math.sin((x + y) * 0.05 - t * 0.5);
                    const n = (v + 3) / 6; // 0..1
                    line += RAMP[Math.min(last, Math.max(0, Math.floor(n * RAMP.length)))];
                }
                lines[y] = line;
            }
            this.$refs.canvas.textContent = lines.join('\n');
        }
    }
};
