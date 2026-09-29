const { createApp, ref } = Vue;

createApp({
    setup() {
        const apiKey = ref('');
        const showApiKeyModal = ref(false);
        const prompt = ref('');
        const ttsVoice = ref('auto');
        const loading = ref(false);
        const error = ref('');
        const steps = ref([]);
        const sessionId = ref(null);
        
        const appletLoaded = ref(false);
        const isPlaying = ref(false);
        const isFullscreen = ref(false);
        const currentStep = ref(0);
        let currentAudio = null;
        let ggbAppletInstance = null;
        let resizeObserver = null;

        // Cleanup on tab close
        window.addEventListener('beforeunload', () => {
            if (sessionId.value) {
                navigator.sendBeacon(`/api/cleanup/${sessionId.value}`);
            }
        });

        // Dark Mode Logic
        const isDark = ref(localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches));

        if (isDark.value) {
            document.documentElement.classList.add('dark');
        }

        const toggleDarkMode = () => {
            isDark.value = !isDark.value;
            if (isDark.value) {
                document.documentElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            }
        };

        const toggleFullscreen = () => {
            isFullscreen.value = !isFullscreen.value;
        };

        const initGeoGebra = () => {
            if (appletLoaded.value) return;
            const container = document.getElementById('ggb-container');
            const params = {
                "appName": "classic",
                "width": container.clientWidth,
                "height": container.clientHeight || 700,
                "showToolBar": true,
                "showAlgebraInput": true,
                "showMenuBar": false,
                "language": "en", // GeoGebra API language
                "appletOnLoad": (api) => {
                    ggbAppletInstance = api;
                    appletLoaded.value = true;
                    
                    resizeObserver = new ResizeObserver(entries => {
                        for (let entry of entries) {
                            if (ggbAppletInstance) {
                                ggbAppletInstance.setSize(entry.contentRect.width, entry.contentRect.height);
                            }
                        }
                    });
                    resizeObserver.observe(container);
                }
            };
            const applet = new GGBApplet(params, true);
            applet.inject('ggb-element');
        };

        const startTutor = async () => {
            // Clean up previous session if it exists
            if (sessionId.value) {
                navigator.sendBeacon(`/api/cleanup/${sessionId.value}`);
            }
            
            loading.value = true;
            error.value = '';
            steps.value = [];
            sessionId.value = null;
            pauseLesson();
            currentStep.value = 0;
            
            if (ggbAppletInstance) {
                ggbAppletInstance.reset();
            } else {
                initGeoGebra();
            }
            
            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: prompt.value,
                        api_key: apiKey.value,
                        voice: ttsVoice.value
                    })
                });
                
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Server error');
                
                steps.value = data.steps;
                sessionId.value = data.session_id;
                // Check if GeoGebra finished loading
                const checkAndPlay = setInterval(() => {
                    if (appletLoaded.value) {
                        clearInterval(checkAndPlay);
                        togglePlay();
                    }
                }, 500);
            } catch (e) {
                error.value = e.message;
            } finally {
                loading.value = false;
            }
        };

        const currentTypedText = ref(null);
        
        const typeCommand = (command, callback) => {
            currentTypedText.value = '';
            let i = 0;
            const typeChar = () => {
                if (!isPlaying.value) {
                    currentTypedText.value = null;
                    return;
                }
                if (i < command.length) {
                    currentTypedText.value += command.charAt(i);
                    i++;
                    setTimeout(typeChar, Math.random() * 40 + 30); // Human-like variable delay
                } else {
                    setTimeout(() => {
                        currentTypedText.value = null;
                        if (isPlaying.value) callback();
                    }, 500); // Dramatic pause before evaluating
                }
            };
            typeChar();
        };

        const playCurrentStep = () => {
            if (currentStep.value >= steps.value.length) {
                isPlaying.value = false;
                return;
            }
            
            const step = steps.value[currentStep.value];
            
            // Simular escritura primero
            typeCommand(step.command, () => {
                if (!isPlaying.value) return;
                
                // Al terminar de escribir, inyectarlo en GeoGebra
                if (ggbAppletInstance) {
                    ggbAppletInstance.evalCommand(step.command);
                }
                
                // Reproducir el audio inmediatamente después de inyectar el gráfico
                if (step.audio_url) {
                    currentAudio = new Audio(step.audio_url);
                    currentAudio.onended = () => {
                        if (isPlaying.value) {
                            currentStep.value++;
                            setTimeout(playCurrentStep, 600); // pause between steps
                        }
                    };
                    currentAudio.play().catch(e => {
                        console.error("Audio blocked by browser, advancing automatically", e);
                        setTimeout(() => {
                            if (isPlaying.value) {
                                currentStep.value++;
                                playCurrentStep();
                            }
                        }, 2000);
                    });
                } else {
                    setTimeout(() => {
                        if (isPlaying.value) {
                            currentStep.value++;
                            playCurrentStep();
                        }
                    }, 1500);
                }
            });
        };

        const togglePlay = () => {
            if (currentStep.value >= steps.value.length) {
                currentStep.value = 0;
                if (ggbAppletInstance) ggbAppletInstance.reset();
            }
            
            isPlaying.value = !isPlaying.value;
            if (isPlaying.value) {
                playCurrentStep();
            } else {
                pauseLesson();
            }
        };
        
        const pauseLesson = () => {
            isPlaying.value = false;
            if (currentAudio) {
                currentAudio.pause();
            }
        };

        const resetLesson = () => {
            pauseLesson();
            currentStep.value = 0;
            if (ggbAppletInstance) ggbAppletInstance.reset();
        };

        const nextStep = () => {
            pauseLesson();
            if (currentStep.value < steps.value.length) {
                const step = steps.value[currentStep.value];
                if (ggbAppletInstance) ggbAppletInstance.evalCommand(step.command);
                currentStep.value++;
            }
        };

        return { 
            isDark, toggleDarkMode, showApiKeyModal, apiKey, prompt, ttsVoice, 
            loading, error, steps, startTutor,
            appletLoaded, isPlaying, currentStep, togglePlay, resetLesson, nextStep,
            isFullscreen, toggleFullscreen, currentTypedText
        };
    }
}).mount('#app');
