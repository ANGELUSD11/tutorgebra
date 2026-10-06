export default {
    template: `
    <div class="relative" @click.stop="toggleOpen">
        <!-- Select Trigger -->
        <div class="w-full p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 focus-within:ring-2 focus-within:ring-indigo-500 transition-all cursor-pointer flex justify-between items-center shadow-sm hover:border-indigo-400 dark:hover:border-indigo-500">
            <span class="truncate block pr-2 text-sm">{{ selectedLabel }}</span>
            <i class="fa-solid fa-chevron-down text-gray-400 dark:text-gray-400 transition-transform duration-300 text-xs" :class="{ 'rotate-180': isOpen }"></i>
        </div>

        <!-- Dropdown Menu -->
        <transition 
            enter-active-class="transition ease-out duration-200" 
            enter-from-class="opacity-0 translate-y-1 scale-95" 
            enter-to-class="opacity-100 translate-y-0 scale-100" 
            leave-active-class="transition ease-in duration-150" 
            leave-from-class="opacity-100 translate-y-0 scale-100" 
            leave-to-class="opacity-0 translate-y-1 scale-95"
        >
            <div v-if="isOpen" class="absolute z-[100] w-full mt-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl overflow-hidden max-h-60 overflow-y-auto custom-scrollbar">
                <template v-for="(item, idx) in options" :key="idx">
                    
                    <!-- If it's an option group -->
                    <div v-if="item.options">
                        <div class="px-3 py-1.5 text-xs font-bold text-indigo-800 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/20 uppercase tracking-wider sticky top-0 backdrop-blur-sm z-10 border-y border-indigo-100 dark:border-indigo-800/50 first:border-t-0">
                            {{ item.label }}
                        </div>
                        <div 
                            v-for="(subItem, subIdx) in item.options" 
                            :key="subIdx"
                            @click.stop="selectItem(subItem.value)"
                            class="px-4 py-2.5 text-sm cursor-pointer transition-colors duration-150 hover:bg-indigo-50 dark:hover:bg-indigo-900/40 flex items-center justify-between"
                            :class="{ 'bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-medium': modelValue === subItem.value, 'text-gray-700 dark:text-gray-200': modelValue !== subItem.value }"
                        >
                            <span class="truncate pr-2">{{ subItem.label }}</span>
                            <i v-if="modelValue === subItem.value" class="fa-solid fa-check text-indigo-600 dark:text-indigo-400 text-xs"></i>
                        </div>
                    </div>
                    
                    <!-- If it's a flat option -->
                    <div 
                        v-else
                        @click.stop="selectItem(item.value)"
                        class="px-4 py-2.5 text-sm cursor-pointer transition-colors duration-150 hover:bg-indigo-50 dark:hover:bg-indigo-900/40 flex items-center justify-between"
                        :class="{ 'bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-medium': modelValue === item.value, 'text-gray-700 dark:text-gray-200': modelValue !== item.value }"
                    >
                        <span class="truncate pr-2">{{ item.label }}</span>
                        <i v-if="modelValue === item.value" class="fa-solid fa-check text-indigo-600 dark:text-indigo-400 text-xs"></i>
                    </div>

                </template>
            </div>
        </transition>
    </div>
    `,
    props: {
        modelValue: {
            required: true
        },
        options: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            isOpen: false
        }
    },
    computed: {
        selectedLabel() {
            // Find the selected label
            for (const item of this.options) {
                if (item.options) {
                    for (const subItem of item.options) {
                        if (subItem.value === this.modelValue) {
                            return subItem.label;
                        }
                    }
                } else {
                    if (item.value === this.modelValue) {
                        return item.label;
                    }
                }
            }
            return 'Select...';
        }
    },
    methods: {
        toggleOpen() {
            this.isOpen = !this.isOpen;
        },
        selectItem(val) {
            this.$emit('update:modelValue', val);
            this.isOpen = false;
        },
        closeDropdown(e) {
            if (!this.$el.contains(e.target)) {
                this.isOpen = false;
            }
        }
    },
    mounted() {
        document.addEventListener('click', this.closeDropdown);
    },
    beforeUnmount() {
        document.removeEventListener('click', this.closeDropdown);
    }
}
