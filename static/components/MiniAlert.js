export default {
    template: `
    <div class="mt-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-3 border border-yellow-200 dark:border-yellow-800/50 transition-colors relative overflow-hidden" @mouseenter="pause" @mouseleave="resume">
        <h3 class="text-[10px] font-bold text-yellow-800 dark:text-yellow-300 mb-1 uppercase tracking-wider flex items-center gap-1">
            <i class="fa-solid fa-circle-info"></i> Did you know?
        </h3>
        
        <div class="h-10 relative flex items-center">
            <transition name="slide-fade" mode="out-in">
                <p :key="currentIndex" class="text-xs text-gray-700 dark:text-gray-300 absolute w-full inset-y-0 flex items-center leading-tight">
                    {{ tips[currentIndex] }}
                </p>
            </transition>
        </div>
        
        <div class="flex justify-center gap-1 mt-1">
            <div v-for="(tip, idx) in tips" :key="idx" @click="setIndex(idx)"
                 :class="['h-1 cursor-pointer rounded-full transition-all duration-300', idx === currentIndex ? 'bg-yellow-500 w-4' : 'bg-yellow-200 dark:bg-yellow-800 w-2 hover:bg-yellow-300 dark:hover:bg-yellow-700']">
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            currentIndex: 0,
            tips: [
                "The gpt-4o-mini model can hallucinate with complex problems. We recommend using gpt-4o.",
                "Star this repository on GitHub! ⭐",
                "See an issue / hallucination? Open an issue, we'll look into it!",
                "Have an OpenRouter API key? You can use it!",
                "Open a discussion on GitHub to suggest changes or new features!",
                "We are looking for expert help to improve the application! Contributions are welcome."
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
                this.currentIndex = (this.currentIndex + 1) % this.tips.length;
            }, 5000);
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
        }
    }
}

