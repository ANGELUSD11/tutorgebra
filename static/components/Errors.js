export default {
    props: {
        message: { type: String, required: true },
        variant: { type: String, default: 'error' }, // 'error' | 'warning'
        compact: { type: Boolean, default: false }
    },
    template: `
    <div role="alert" :class="['rounded-lg border flex items-start gap-2 transition-colors', sizeClasses, variantClasses]">
        <i :class="['mt-0.5', iconClass]"></i>
        <span class="leading-tight">{{ message }}</span>
    </div>
    `,
    computed: {
        variantClasses() {
            return this.variant === 'warning'
                ? 'bg-amber-50 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800'
                : 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800';
        },
        sizeClasses() {
            return this.compact ? 'mt-2 p-2 text-xs' : 'mt-4 p-3 text-sm';
        },
        iconClass() {
            return this.variant === 'warning' ? 'fa-solid fa-volume-xmark' : 'fa-solid fa-triangle-exclamation';
        }
    }
}
