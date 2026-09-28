const { createApp, ref } = Vue;

createApp({
    setup() {
        const apiKey = ref('');
        const prompt = ref('');
        const loading = ref(false);
        const error = ref('');
        const success = ref(false);
        const botState = ref('idle');
        const botMessage = ref('');
        let pollInterval = null;
        const steps = ref([]);

        const startTutor = async () => {
            loading.value = true;
            error.value = '';
            success.value = false;
            steps.value = [];
            
            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: prompt.value,
                        api_key: apiKey.value
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Server error');
                }
                
                steps.value = data.steps;
                success.value = true;
                startPolling();
            } catch (e) {
                error.value = e.message;
            } finally {
                loading.value = false;
            }
        };

        const startPolling = () => {
            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(async () => {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();
                    botState.value = data.state;
                    botMessage.value = data.message;
                    if (data.state === 'finished' || data.state === 'error') {
                        clearInterval(pollInterval);
                    }
                } catch (e) {}
            }, 1000);
        };
        
        return { botState, botMessage, apiKey, prompt, loading, error, success, steps, startTutor }
    }
}).mount('#app');
