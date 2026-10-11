/**
 * PatientCare Healthcare Platform
 * Multilingual AI Patient Support & Intelligent Navigation Assistant (ai-chat.js)
 * Supports English, Hindi, and Marathi.
 */

(function () {
    let currentLanguage = 'en';

    const UI_TRANSLATIONS = {
        en: {
            title: 'PatientCare AI Assistant',
            subtitle: 'Multilingual Clinical & Scheme Guidance',
            placeholder: 'Ask about symptoms, schemes, 90% reserve, appointments...',
            send: 'Send',
            disclaimer: 'AI guidance is informational only. Not a medical diagnosis or prescription.',
            quickPills: [
                'How does 90% Reserve work?',
                'Maharashtra MJPJAY coverage',
                'Book Doctor Appointment',
                'Explain my prescription'
            ]
        },
        hi: {
            title: 'पेशेंटकेयर एआई सहायक',
            subtitle: 'बहुभाषी स्वास्थ्य एवं सरकारी योजना मार्गदर्शन',
            placeholder: 'लक्षण, सरकारी योजनाएं, 90% रिज़र्व के बारे में पूछें...',
            send: 'भेजें',
            disclaimer: 'एआई सलाह केवल सामान्य जानकारी है। यह चिकित्सकीय नुस्खा या निदान नहीं है।',
            quickPills: [
                '90% रिज़र्व खाता कैसे काम करता है?',
                'महाराष्ट्र MJPJAY योजना के नियम',
                'डॉक्टर अपॉइंटमेंट कैसे लें?',
                'दवाइयों का सरल विवरण'
            ]
        },
        mr: {
            title: 'पेशंटकेअर एआय सहाय्यक',
            subtitle: 'बहुभाषिक आरोग्य आणि शासकीय योजना सहाय्य',
            placeholder: 'लक्षणे, योजना, ९०% रिझर्व्हबद्दल विचारा...',
            send: 'पाठवा',
            disclaimer: 'एआय सल्ला केवळ माहितीसाठी आहे. हे अंतिम निदान किंवा औषधोपचार नाही.',
            quickPills: [
                '९०% रिझर्व्ह खाते कसे कार्य करते?',
                'महाराष्ट्र MJPJAY मोफत उपचार योजना',
                'डॉक्टर भेट कशी निश्चित करावी?',
                'औषधांचा सोपा अर्थ सांगा'
            ]
        }
    };

    function initAIChatWidget() {
        if (document.getElementById('aiChatWidgetRoot')) return;

        const root = document.createElement('div');
        root.id = 'aiChatWidgetRoot';
        root.innerHTML = `
            <style>
                #aiChatToggleBtn {
                    position: fixed;
                    bottom: 24px;
                    right: 24px;
                    z-index: 9990;
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    box-shadow: 0 4px 16px rgba(13, 110, 253, 0.4);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 26px;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                #aiChatToggleBtn:hover {
                    transform: scale(1.08);
                    box-shadow: 0 6px 20px rgba(13, 110, 253, 0.5);
                }
                #aiChatWindow {
                    position: fixed;
                    bottom: 96px;
                    right: 24px;
                    z-index: 9991;
                    width: 380px;
                    max-width: calc(100vw - 32px);
                    height: 520px;
                    max-height: calc(100vh - 120px);
                    background: #ffffff;
                    border-radius: 16px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                    border: 1px solid #dee2e6;
                }
                .ai-msg {
                    padding: 10px 14px;
                    border-radius: 14px;
                    margin-bottom: 8px;
                    font-size: 0.88rem;
                    line-height: 1.4;
                    max-width: 85%;
                }
                .ai-msg-assistant {
                    background: #f0f4f9;
                    color: #1e293b;
                    align-self: flex-start;
                    border-bottom-left-radius: 4px;
                }
                .ai-msg-user {
                    background: #0d6efd;
                    color: #ffffff;
                    align-self: flex-end;
                    border-bottom-right-radius: 4px;
                }
                .ai-pill-btn {
                    font-size: 0.75rem;
                    padding: 4px 10px;
                    border-radius: 20px;
                    border: 1px solid #cbd5e1;
                    background: #ffffff;
                    color: #475569;
                    cursor: pointer;
                    white-space: nowrap;
                    transition: all 0.15s;
                }
                .ai-pill-btn:hover {
                    background: #e2e8f0;
                    color: #0f172a;
                }
            </style>

            <!-- Floating Toggle Button -->
            <button id="aiChatToggleBtn" class="btn btn-primary" title="AI Healthcare Assistant">
                🤖
            </button>

            <!-- Chat Window -->
            <div id="aiChatWindow">
                <!-- Header -->
                <div class="bg-primary text-white p-3 d-flex justify-content-between align-items-center">
                    <div>
                        <div class="fw-bold d-flex align-items-center gap-1" id="aiHeaderTitle">
                            <span>🤖</span> PatientCare AI
                        </div>
                        <small class="text-white-50" id="aiHeaderSub" style="font-size: 0.75rem;">Multilingual Healthcare Assistant</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <!-- Language Selector -->
                        <select id="aiLangSelect" class="form-select form-select-sm bg-light text-dark border-0 py-0" style="width: 80px; font-size: 0.75rem;">
                            <option value="en">EN</option>
                            <option value="hi">हिन्दी</option>
                            <option value="mr">मराठी</option>
                        </select>
                        <button type="button" class="btn-close btn-close-white" id="aiChatCloseBtn"></button>
                    </div>
                </div>

                <!-- Messages Stream -->
                <div id="aiMessagesStream" class="flex-grow-1 p-3 d-flex flex-column" style="overflow-y: auto;">
                    <div class="ai-msg ai-msg-assistant">
                        <strong class="d-block text-primary small mb-1">PatientCare Assistant</strong>
                        Hello! How can I assist you today? I can help with doctor appointments, symptoms, government schemes (MJPJAY, PM-JAY), or your 90% Healthcare Reserve.
                    </div>
                </div>

                <!-- Quick Query Pills -->
                <div id="aiQuickPillsContainer" class="p-2 border-top bg-light d-flex gap-1 overflow-x-auto"></div>

                <!-- Input Footer -->
                <div class="p-2 border-top bg-white">
                    <form id="aiChatForm" class="d-flex gap-2">
                        <input type="text" id="aiChatInput" class="form-control form-control-sm" placeholder="Ask a question..." required>
                        <button type="submit" class="btn btn-primary btn-sm px-3" id="aiSendBtn">
                            <i class="bi bi-send-fill"></i>
                        </button>
                    </form>
                    <div class="text-center mt-1" style="font-size: 0.68rem; color: #64748b;" id="aiDisclaimerText">
                        AI guidance is informational only. Not a medical diagnosis.
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(root);

        const toggleBtn = document.getElementById('aiChatToggleBtn');
        const chatWin = document.getElementById('aiChatWindow');
        const closeBtn = document.getElementById('aiChatCloseBtn');
        const form = document.getElementById('aiChatForm');
        const langSelect = document.getElementById('aiLangSelect');

        toggleBtn.addEventListener('click', () => {
            const isVisible = chatWin.style.display === 'flex';
            chatWin.style.display = isVisible ? 'none' : 'flex';
            if (!isVisible) document.getElementById('aiChatInput').focus();
        });

        closeBtn.addEventListener('click', () => {
            chatWin.style.display = 'none';
        });

        langSelect.addEventListener('change', (e) => {
            currentLanguage = e.target.value;
            applyLanguage();
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('aiChatInput');
            const msg = input.value.trim();
            if (!msg) return;

            appendMessage(msg, 'user');
            input.value = '';

            const user = API.Storage.getUser();
            const patientId = user?.profile?.patient_id || '';

            const sendBtn = document.getElementById('aiSendBtn');
            sendBtn.disabled = true;

            try {
                const res = await API.reportAPI.aiChat(msg, currentLanguage, patientId);
                appendMessage(res.reply, 'assistant', res.is_emergency);
            } catch (err) {
                appendMessage('Sorry, I encountered an issue connecting to the healthcare knowledge base. Please try again.', 'assistant');
            } finally {
                sendBtn.disabled = false;
            }
        });

        applyLanguage();
    }

    function applyLanguage() {
        const t = UI_TRANSLATIONS[currentLanguage] || UI_TRANSLATIONS.en;
        const titleEl = document.getElementById('aiHeaderTitle');
        const subEl = document.getElementById('aiHeaderSub');
        const inputEl = document.getElementById('aiChatInput');
        const discEl = document.getElementById('aiDisclaimerText');
        const pillsContainer = document.getElementById('aiQuickPillsContainer');

        if (titleEl) titleEl.innerHTML = `<span>🤖</span> ${t.title}`;
        if (subEl) subEl.innerText = t.subtitle;
        if (inputEl) inputEl.placeholder = t.placeholder;
        if (discEl) discEl.innerText = t.disclaimer;

        if (pillsContainer) {
            pillsContainer.innerHTML = t.quickPills.map(p => `
                <button type="button" class="ai-pill-btn" onclick="window.sendAIPillQuery('${p.replace(/'/g, "\\'")}')">${p}</button>
            `).join('');
        }
    }

    function appendMessage(text, sender, isEmergency = false) {
        const stream = document.getElementById('aiMessagesStream');
        if (!stream) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-msg ai-msg-${sender} ${isEmergency ? 'border border-danger bg-danger-subtle text-danger-emphasis' : ''}`;
        msgDiv.innerHTML = text.replace(/\n/g, '<br>');

        stream.appendChild(msgDiv);
        stream.scrollTop = stream.scrollHeight;
    }

    window.sendAIPillQuery = function (query) {
        const input = document.getElementById('aiChatInput');
        const form = document.getElementById('aiChatForm');
        if (input && form) {
            input.value = query;
            form.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAIChatWidget);
    } else {
        initAIChatWidget();
    }
})();
