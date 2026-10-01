const { createApp, ref, watch } = Vue;

createApp({
    setup() {
        const apiKey = ref('');
        const showApiKeyModal = ref(false);
        const prompt = ref('');
        const ttsVoice = ref('auto');
        const edgeVoice = ref('es-MX-JorgeNeural');
        const useEdgeTts = ref(false);
        const toggleEdgeTts = () => { useEdgeTts.value = !useEdgeTts.value; };
        const loading = ref(false);
        const loadingMessage = ref('Iniciando...');
        const loadingPercent = ref(0);
        const error = ref('');
        const steps = ref([]);
        const sessionId = ref(null);
        
        const appletLoaded = ref(false);
        const isPlaying = ref(false);
        const isFullscreen = ref(false);
        const currentStep = ref(0);
        const volume = ref(1.0);
        let currentAudio = null;

        watch(volume, (newVol) => {
            if (currentAudio) {
                currentAudio.volume = newVol;
            }
        });
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
                    
                    let resizeTimeout;
                    resizeObserver = new ResizeObserver(entries => {
                        clearTimeout(resizeTimeout);
                        resizeTimeout = setTimeout(() => {
                            if (ggbAppletInstance) {
                                const rect = entries[0].contentRect;
                                if (rect.width > 0 && rect.height > 0) {
                                    ggbAppletInstance.setSize(rect.width, rect.height);
                                }
                            }
                        }, 150); // wait for rotation/animations to finish
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
                        voice: useEdgeTts.value ? null : ttsVoice.value,
                        edge_voice: useEdgeTts.value ? edgeVoice.value : null
                    })
                });
                
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || 'Server error');
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = "";
                let completedSuccessfully = false;
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // keep incomplete chunk
                    
                    for (let line of lines) {
                        line = line.trim();
                        if (!line) continue;
                        
                        if (line.startsWith('data:')) {
                            // Extract JSON string and safely parse
                            const jsonStr = line.substring(5).trim();
                            if (!jsonStr) continue;
                            
                            let data;
                            try {
                                data = JSON.parse(jsonStr);
                            } catch (err) {
                                console.error("Error parsing SSE JSON:", jsonStr, err);
                                continue;
                            }
                            
                            if (data.status === 'progress') {
                                loadingMessage.value = data.message;
                                loadingPercent.value = data.percent;
                            } else if (data.status === 'done') {
                                completedSuccessfully = true;
                                steps.value = data.steps;
                                sessionId.value = data.session_id;
                                // Check if GeoGebra finished loading
                                const checkAndPlay = setInterval(() => {
                                    if (appletLoaded.value) {
                                        clearInterval(checkAndPlay);
                                        togglePlay();
                                    }
                                }, 500);
                            } else if (data.status === 'error') {
                                throw new Error(data.detail || 'Error during generation');
                            }
                        }
                    }
                }
                
                if (!completedSuccessfully) {
                    throw new Error("La conexión se interrumpió inesperadamente. Intenta nuevamente.");
                }
            } catch (e) {
                error.value = e.message;
            } finally {
                loading.value = false;
            }
        };

        const currentTypedText = ref(null);
        
        let audioCtx = null;
        const playTypingSound = () => {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            
            const osc = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            
            // Tono corto y seco
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(300 + Math.random() * 100, audioCtx.currentTime);
            
            // Envolvente de volumen atado a volume.value
            const maxVol = 0.1 * volume.value;
            gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
            gainNode.gain.linearRampToValueAtTime(maxVol, audioCtx.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
            
            osc.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            
            osc.start(audioCtx.currentTime);
            osc.stop(audioCtx.currentTime + 0.05);
        };

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
                    playTypingSound();
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
                if (ggbAppletInstance && step.command && step.command.trim() !== '') {
                    ggbAppletInstance.evalCommand(step.command);
                }
                
                // Reproducir el audio inmediatamente después de inyectar el gráfico
                if (step.audio_url) {
                    currentAudio = new Audio(step.audio_url);
                    currentAudio.volume = volume.value;
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
            useEdgeTts, edgeVoice, toggleEdgeTts,
            loading, loadingMessage, loadingPercent, error, steps, startTutor,
            appletLoaded, isPlaying, currentStep, togglePlay, resetLesson, nextStep,
            isFullscreen, toggleFullscreen, currentTypedText, volume
        };
    }
}).mount('#app');
