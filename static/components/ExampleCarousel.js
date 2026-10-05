export default {
    template: `
    <div class="mt-6 mb-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-4 border border-indigo-100 dark:border-indigo-800/50 transition-colors relative overflow-hidden" @mouseenter="pause" @mouseleave="resume">
        <h3 class="text-xs font-bold text-indigo-800 dark:text-indigo-300 mb-2 uppercase tracking-wider flex items-center gap-2">
            <i class="fa-solid fa-lightbulb"></i> Ideas / Examples
        </h3>
        
        <div class="h-20 sm:h-16 relative">
            <transition name="slide-fade" mode="out-in">
                <p :key="currentIndex" @click="selectExample(examples[currentIndex].text)" class="text-sm text-gray-700 dark:text-gray-300 italic absolute inset-0 cursor-pointer hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors duration-300" title="Click to use this example">
                    "{{ examples[currentIndex].text }}"
                </p>
            </transition>
        </div>
        
        <div class="flex justify-between items-center mt-2">
            <div class="flex gap-1">
                <div v-for="(ex, idx) in examples" :key="idx" @click="setIndex(idx)"
                     :class="['h-1.5 cursor-pointer rounded-full transition-all duration-300', idx === currentIndex ? 'bg-indigo-500 w-6' : 'bg-indigo-200 dark:bg-indigo-800 w-4 hover:bg-indigo-300 dark:hover:bg-indigo-700']">
                </div>
            </div>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded text-indigo-700 bg-indigo-100 dark:bg-indigo-800/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-700/50 uppercase">
                {{ examples[currentIndex].lang }}
            </span>
        </div>
    </div>
    `,
    data() {
        return {
            currentIndex: 0,
            examples: [
                { text: "Dibuja un triángulo con vértices en A=(-4, -2), B=(2, 5) y C=(6, 0). Encuentra su baricentro y dibuja su circunferencia inscrita para hallar el incentro.", lang: "ES" },
                { text: "Draw a regular pentagon centered at the origin with radius 4. Draw its incircle and calculate its area.", lang: "EN" },
                { text: "Dibuja la parábola f(x) = -x^2 + 4x + 1. Encuentra su vértice. Luego, traza la recta tangente a esta parábola en x = 3.", lang: "ES" },
                { text: "Draw an ellipse with equation x^2/25 + y^2/9 = 1. Plot its foci and vertices.", lang: "EN" },
                { text: "Dibuja una circunferencia con centro en el origen y radio 4. Luego traza la recta y = x - 1 y encuentra sus puntos de intersección.", lang: "ES" }
            ],
            intervalId: null
        }
    },
    mounted() {
        this.resume();
    },
    beforeUnmount() {
        this.pause();
    },
    methods: {
        resume() {
            this.pause();
            this.intervalId = setInterval(() => {
                this.currentIndex = (this.currentIndex + 1) % this.examples.length;
            }, 6000);
        },
        pause() {
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
        },
        setIndex(idx) {
            this.currentIndex = idx;
            this.resume();
        },
        selectExample(text) {
            this.$emit('select', text);
        }
    }
}
