/**
 * Slidemaker — логика интерфейса
 * 
 * Модули:
 * - FileUpload: Работа с загрузкой файлов
 * - FontManager: Управление шрифтами и превью
 * - PreviewManager: Живое превью слайдов
 * - ColorManager: Управление цветами и градиентами
 * - FormHandler: Обработка формы генерации
 */

// ==========================================
// Utility Functions
// ==========================================

/**
 * Настройка зоны drag-and-drop загрузки файлов
 */
function setupUploadZone(zone, input, onFile) {
    ['dragenter', 'dragover'].forEach(e => {
        zone.addEventListener(e, (ev) => {
            ev.preventDefault();
            zone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(e => {
        zone.addEventListener(e, (ev) => {
            ev.preventDefault();
            zone.classList.remove('dragover');
        });
    });

    zone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) {
            input.files = files;
            onFile(files[0]);
        }
    });

    input.addEventListener('change', () => {
        if (input.files.length) {
            onFile(input.files[0]);
        }
    });
}

// ==========================================
// File Upload Module
// ==========================================
const FileUpload = {
    init() {
        this.mdUpload = document.getElementById('mdUpload');
        this.mdFile = document.getElementById('markdownFile');
        this.mdFilename = document.getElementById('mdFilename');
        this.generateBtn = document.getElementById('generateBtn');
        
        if (this.mdUpload && this.mdFile) {
            setupUploadZone(this.mdUpload, this.mdFile, (file) => {
                this.handleMarkdownUpload(file);
            });
        }
    },
    
    handleMarkdownUpload(file) {
        this.mdFilename.textContent = file.name;
        this.mdUpload.classList.add('has-file');
        this.generateBtn.disabled = false;
        
        // Parse markdown for preview
        PreviewManager.parseMarkdown(file);
    }
};

// ==========================================
// Background Manager Module
// ==========================================
const BackgroundManager = {
    currentBgUrl: null,
    
    init() {
        this.uploadZone = document.getElementById('bgUploadZone');
        this.uploadInput = document.getElementById('bgUploadInput');
        this.previewImg = document.getElementById('bgPreviewImg');
        this.deleteBtn = document.getElementById('bgDeleteBtn');
        this.changeHint = document.getElementById('bgChangeHint');
        this.bgValue = document.getElementById('backgroundValue');
        
        if (!this.uploadZone) return;
        
        this.bindEvents();
    },
    
    bindEvents() {
        this.uploadInput.addEventListener('change', () => this.handleUpload());
        this.deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.hideBgPreview();
        });
        this.changeHint.addEventListener('click', (e) => {
            e.stopPropagation();
            this.uploadInput.click();
        });
    },
    
    async handleUpload() {
        if (!this.uploadInput.files.length) return;
        
        const file = this.uploadInput.files[0];
        
        // Show local preview immediately
        const localUrl = URL.createObjectURL(file);
        this.showBgPreview(localUrl);

        // Upload to server
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/upload/background', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                this.bgValue.value = data.filename;
                this.currentBgUrl = '/uploads/backgrounds/' + encodeURIComponent(data.filename);
                this.previewImg.src = this.currentBgUrl;
                PreviewManager.updateBackground(this.currentBgUrl);
            }
        } catch (err) {
            console.error('Upload error:', err);
        }
    },
    
    showBgPreview(url) {
        this.previewImg.src = url;
        this.previewImg.style.display = 'block';
        this.uploadZone.classList.add('has-image');
        PreviewManager.updateBackground(url);
    },
    
    hideBgPreview() {
        this.previewImg.src = '';
        this.previewImg.style.display = 'none';
        this.uploadZone.classList.remove('has-image');
        this.bgValue.value = 'default';
        this.currentBgUrl = null;
        this.uploadInput.value = '';
        PreviewManager.updateBackground(null);
    }
};

// ==========================================
// Font Manager Module
// ==========================================
const FontManager = {
    fontFaces: {},
    
    init() {
        this.dropdown = document.getElementById('fontDropdown');
        this.trigger = document.getElementById('fontDropdownTrigger');
        this.menu = document.getElementById('fontDropdownMenu');
        this.valueDisplay = document.getElementById('fontDropdownValue');
        this.hiddenSelect = document.getElementById('fontSelect');
        this.fontUpload = document.getElementById('fontUpload');
        this.fontFile = document.getElementById('fontFile');
        
        if (!this.dropdown) return;
        
        this.bindEvents();
    },
    
    bindEvents() {
        // Toggle dropdown
        this.trigger.addEventListener('click', () => {
            this.dropdown.classList.toggle('open');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.dropdown.contains(e.target)) {
                this.dropdown.classList.remove('open');
            }
        });

        // Font option selection
        this.menu.addEventListener('click', (e) => {
            const option = e.target.closest('.font-option');
            if (option) {
                const fontName = option.dataset.font;
                this.selectFont(fontName);
                this.dropdown.classList.remove('open');
            }
        });

        // Hover preview on font options
        this.menu.addEventListener('mouseover', async (e) => {
            const option = e.target.closest('.font-option');
            if (option) {
                const fontName = option.dataset.font;
                await this.loadFontForPreview(fontName);
                const preview = option.querySelector('.font-option-preview');
                if (preview && this.fontFaces[fontName]) {
                    preview.style.fontFamily = fontName;
                }
            }
        });
        
        // Font upload
        if (this.fontUpload && this.fontFile) {
            setupUploadZone(this.fontUpload, this.fontFile, (file) => {
                this.handleFontUpload(file);
            });
        }
    },
    
    async loadFontForPreview(fontName) {
        if (this.fontFaces[fontName] !== undefined) return;
        
        try {
            // Используем API endpoint который найдёт правильный файл шрифта
            const fontUrl = `/api/font/${encodeURIComponent(fontName)}`;
            const font = new FontFace(fontName, `url(${fontUrl})`);
            await font.load();
            document.fonts.add(font);
            this.fontFaces[fontName] = true;
        } catch (e) {
            // Пробуем Google Fonts как fallback
            try {
                const googleFontUrl = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(fontName.replace(/ /g, '+'))}:wght@400;700&display=swap`;
                const link = document.createElement('link');
                link.href = googleFontUrl;
                link.rel = 'stylesheet';
                document.head.appendChild(link);
                // Ждём загрузки
                await document.fonts.load(`16px "${fontName}"`);
                this.fontFaces[fontName] = true;
            } catch (e2) {
                this.fontFaces[fontName] = false;
            }
        }
    },
    
    selectFont(fontName) {
        // Update hidden input
        this.hiddenSelect.value = fontName;
        
        // Update trigger text
        this.valueDisplay.textContent = fontName;
        
        // Update selected state
        document.querySelectorAll('.font-option').forEach(opt => {
            opt.classList.toggle('selected', opt.dataset.font === fontName);
        });
        
        // Update live preview
        PreviewManager.updateFont(fontName, this);
    },
    
    async handleFontUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Показываем индикатор загрузки
        this.fontUpload.classList.add('loading');

        try {
            const res = await fetch('/api/upload/font', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                // Сначала загружаем шрифт для preview
                const fontUrl = `/api/font/${encodeURIComponent(data.font_name)}`;
                try {
                    const font = new FontFace(data.font_name, `url(${fontUrl})`);
                    await font.load();
                    document.fonts.add(font);
                    this.fontFaces[data.font_name] = true;
                } catch (fontLoadErr) {
                    console.warn('Font preview load failed:', fontLoadErr);
                    this.fontFaces[data.font_name] = false;
                }

                // Add new option to dropdown
                const newOption = document.createElement('div');
                newOption.className = 'font-option';
                newOption.dataset.font = data.font_name;
                newOption.innerHTML = `
                    <span class="font-option-name">${data.font_name}</span>
                    <span class="font-option-preview" data-preview-font="${data.font_name}" style="font-family: '${data.font_name}', sans-serif">Пример текста Aa</span>
                `;
                this.menu.appendChild(newOption);

                // Also add to text font dropdown if exists
                const textFontMenu = document.getElementById('textFontDropdownMenu');
                if (textFontMenu) {
                    const textOption = document.createElement('div');
                    textOption.className = 'font-option';
                    textOption.dataset.font = data.font_name;
                    textOption.innerHTML = `
                        <span class="font-option-name">${data.font_name}</span>
                        <span class="font-option-preview" data-preview-font="${data.font_name}" style="font-family: '${data.font_name}', sans-serif">Пример текста</span>
                    `;
                    textFontMenu.appendChild(textOption);
                }
                
                // Select the new font
                this.selectFont(data.font_name);
                this.fontUpload.classList.add('has-file');
            } else {
                alert(data.error || 'Ошибка загрузки шрифта');
            }
        } catch (err) {
            console.error('Font upload error:', err);
            alert('Ошибка соединения с сервером');
        } finally {
            this.fontUpload.classList.remove('loading');
        }
    }
};

// ==========================================
// Preview Manager Module
// ==========================================
const PreviewManager = {
    slides: [],
    currentSlide: 0,
    
    init() {
        this.canvas = document.getElementById('previewCanvas');
        this.bg = document.getElementById('previewBg');
        this.overlay = document.getElementById('previewOverlay');
        this.heading = document.getElementById('previewHeading');
        this.text = document.getElementById('previewText');
        this.slideNum = document.getElementById('previewSlideNum');
        this.prevBtn = document.getElementById('prevSlideBtn');
        this.nextBtn = document.getElementById('nextSlideBtn');
        
        if (!this.canvas) return;
        
        this.bindEvents();
    },
    
    bindEvents() {
        this.prevBtn.addEventListener('click', () => {
            if (this.currentSlide > 0) {
                this.currentSlide--;
                this.updateSlideContent();
                this.updateNavigation();
            }
        });

        this.nextBtn.addEventListener('click', () => {
            if (this.currentSlide < this.slides.length - 1) {
                this.currentSlide++;
                this.updateSlideContent();
                this.updateNavigation();
            }
        });
    },
    
    parseMarkdown(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            this.slides = [];
            
            const lines = content.split('\n');
            let currentSlide = null;
            let isFirst = true;
            
            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) continue;
                
                // Проверяем заголовки (# ## ### и т.д.)
                const headerMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
                
                if (headerMatch) {
                    // Сохраняем предыдущий слайд
                    if (currentSlide) {
                        this.slides.push(currentSlide);
                    }
                    
                    const title = headerMatch[2].trim();
                    currentSlide = {
                        heading: title,
                        items: [],  // Только элементы списка
                        text: ''    // Будет сформирован из items
                    };
                    isFirst = false;
                }
                // Элементы списка (- item)
                else if (trimmed.startsWith('- ') && currentSlide) {
                    currentSlide.items.push(trimmed.slice(2).trim());
                }
            }
            
            // Добавляем последний слайд
            if (currentSlide) {
                this.slides.push(currentSlide);
            }
            
            // Формируем текст из элементов списка (как в генераторе)
            for (const slide of this.slides) {
                slide.text = slide.items.length > 0 
                    ? slide.items.join('\n') 
                    : '';
            }
            
            // Если слайдов нет, создаём дефолтный
            if (this.slides.length === 0) {
                this.slides.push({
                    heading: 'Заголовок',
                    text: '',
                    items: []
                });
            }
            
            this.currentSlide = 0;
            this.updateSlideContent();
            this.updateNavigation();
        };
        reader.readAsText(file);
    },

    /**
     * Парсит markdown форматирование и возвращает HTML
     * **bold** -> акцентный цвет
     * *italic* -> убираем звёздочки
     */
    parseInlineMarkdown(text) {
        // Получаем текущий акцентный цвет
        const accentColor = '#' + (document.getElementById('accentColor')?.value || 'ff6b6b');
        
        // Экранируем HTML
        let result = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Обрабатываем **bold** -> акцентный цвет
        result = result.replace(/\*\*(.+?)\*\*/g, `<span class="accent-text" style="color: ${accentColor}">$1</span>`);
        
        // Обрабатываем *italic* -> убираем звёздочки
        result = result.replace(/\*(.+?)\*/g, '$1');
        
        return result;
    },
    
    updateSlideContent() {
        if (this.slides.length > 0) {
            const slide = this.slides[this.currentSlide];
            // Парсим markdown для заголовка и текста
            this.heading.innerHTML = this.parseInlineMarkdown(slide.heading);
            // Для текста заменяем переносы строк на <br>
            const textHtml = slide.text
                .split('\n')
                .map(line => this.parseInlineMarkdown(line))
                .join('<br>');
            this.text.innerHTML = textHtml;
            this.slideNum.textContent = `Слайд ${this.currentSlide + 1} из ${this.slides.length}`;
        }
    },
    
    updateNavigation() {
        this.prevBtn.disabled = this.currentSlide === 0 || this.slides.length === 0;
        this.nextBtn.disabled = this.currentSlide >= this.slides.length - 1 || this.slides.length === 0;
    },
    
    updateBackground(url) {
        if (url) {
            this.bg.style.backgroundImage = `url(${url})`;
        } else {
            this.bg.style.backgroundImage = 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)';
        }
    },
    
    updateOverlay(effect, intensity) {
        const normalizedIntensity = intensity / 10;
        
        if (effect === 'darken') {
            this.overlay.style.background = `rgba(0, 0, 0, ${normalizedIntensity})`;
        } else if (effect === 'lighten') {
            this.overlay.style.background = `rgba(255, 255, 255, ${normalizedIntensity})`;
        } else {
            this.overlay.style.background = 'transparent';
        }
    },
    
    async updateFont(fontName, fontManager) {
        await fontManager.loadFontForPreview(fontName);
        // Применяем шрифт в любом случае - браузер использует fallback если не загружен
        this.heading.style.fontFamily = `"${fontName}", sans-serif`;
        // Текст обновляется отдельно через updateTextFont
    },

    async updateTextFont(fontName) {
        if (fontName) {
            await FontManager.loadFontForPreview(fontName);
            this.text.style.fontFamily = `"${fontName}", sans-serif`;
        }
    },
    
    updateColors(colors) {
        const {
            headingColor,
            textColor,
            headingGradientEnabled,
            textGradientEnabled,
            headingGradientEnd,
            textGradientEnd
        } = colors;

        const accentColor = '#' + (document.getElementById('accentColor')?.value || 'ff6b6b');

        if (headingGradientEnabled) {
            this.heading.style.background = `linear-gradient(90deg, ${headingColor}, ${headingGradientEnd})`;
            this.heading.style.webkitBackgroundClip = 'text';
            this.heading.style.webkitTextFillColor = 'transparent';
            this.heading.style.backgroundClip = 'text';
            // Исправляем акцентные элементы в заголовке - они должны иметь свой цвет
            this.heading.querySelectorAll('.accent-text').forEach(el => {
                el.style.background = 'none';
                el.style.webkitBackgroundClip = 'unset';
                el.style.webkitTextFillColor = accentColor;
                el.style.backgroundClip = 'unset';
            });
        } else {
            this.heading.style.background = 'none';
            this.heading.style.webkitBackgroundClip = 'unset';
            this.heading.style.webkitTextFillColor = 'unset';
            this.heading.style.backgroundClip = 'unset';
            this.heading.style.color = headingColor;
            // Акцентные элементы получают свой цвет
            this.heading.querySelectorAll('.accent-text').forEach(el => {
                el.style.color = accentColor;
                el.style.webkitTextFillColor = 'unset';
            });
        }

        if (textGradientEnabled) {
            this.text.style.background = `linear-gradient(90deg, ${textColor}, ${textGradientEnd})`;
            this.text.style.webkitBackgroundClip = 'text';
            this.text.style.webkitTextFillColor = 'transparent';
            this.text.style.backgroundClip = 'text';
            // Исправляем акцентные элементы в тексте - они должны иметь свой цвет
            this.text.querySelectorAll('.accent-text').forEach(el => {
                el.style.background = 'none';
                el.style.webkitBackgroundClip = 'unset';
                el.style.webkitTextFillColor = accentColor;
                el.style.backgroundClip = 'unset';
            });
        } else {
            this.text.style.background = 'none';
            this.text.style.webkitBackgroundClip = 'unset';
            this.text.style.webkitTextFillColor = 'unset';
            this.text.style.backgroundClip = 'unset';
            this.text.style.color = textColor;
            // Акцентные элементы получают свой цвет
            this.text.querySelectorAll('.accent-text').forEach(el => {
                el.style.color = accentColor;
                el.style.webkitTextFillColor = 'unset';
            });
        }
    }
};

// ==========================================
// Color Manager Module
// ==========================================
const ColorManager = {
    init() {
        this.bgEffect = document.getElementById('bgEffect');
        this.intensityGroup = document.getElementById('intensityGroup');
        this.bgIntensity = document.getElementById('bgIntensity');
        this.intensityValue = document.getElementById('intensityValue');
        
        if (!this.bgEffect) return;
        
        this.bindEvents();
        this.setupColorPickers();
        this.setupGradientToggles();
    },
    
    bindEvents() {
        this.bgEffect.addEventListener('change', () => {
            this.intensityGroup.style.display = this.bgEffect.value !== 'none' ? 'block' : 'none';
            this.updateOverlay();
        });

        this.bgIntensity.addEventListener('input', () => {
            this.intensityValue.textContent = this.bgIntensity.value;
            this.updateOverlay();
        });
    },
    
    updateOverlay() {
        PreviewManager.updateOverlay(this.bgEffect.value, parseInt(this.bgIntensity.value));
    },
    
    setupColorPicker(picker, input, preview, updateCallback) {
        if (!picker || !input) return;
        
        picker.addEventListener('input', () => {
            const hex = picker.value.replace('#', '');
            input.value = hex;
            if (preview) preview.style.background = picker.value;
            if (updateCallback) updateCallback();
        });

        input.addEventListener('input', () => {
            const hex = input.value.replace('#', '');
            if (/^[0-9A-Fa-f]{6}$/.test(hex)) {
                picker.value = '#' + hex;
                if (preview) preview.style.background = '#' + hex;
                if (updateCallback) updateCallback();
            }
        });
    },
    
    setupColorPickers() {
        const updateColors = () => this.updatePreviewColors();
        
        this.setupColorPicker(
            document.getElementById('headingColorPicker'),
            document.getElementById('headingColor'),
            document.getElementById('headingColorPreview'),
            updateColors
        );

        this.setupColorPicker(
            document.getElementById('textColorPicker'),
            document.getElementById('textColor'),
            document.getElementById('textColorPreview'),
            updateColors
        );

        this.setupColorPicker(
            document.getElementById('headingGradientEndPicker'),
            document.getElementById('headingGradientEnd'),
            document.getElementById('headingGradientEndPreview'),
            updateColors
        );

        this.setupColorPicker(
            document.getElementById('textGradientEndPicker'),
            document.getElementById('textGradientEnd'),
            document.getElementById('textGradientEndPreview'),
            updateColors
        );

        // Акцентный цвет - теперь обновляет live preview
        this.setupColorPicker(
            document.getElementById('accentColorPicker'),
            document.getElementById('accentColor'),
            document.getElementById('accentColorPreview'),
            () => this.updateAccentColor()
        );
    },
    
    setupGradientToggle(toggle, hidden, settings) {
        if (!toggle) return;
        
        toggle.addEventListener('change', () => {
            hidden.value = toggle.checked ? 'yes' : 'no';
            settings.classList.toggle('open', toggle.checked);
            this.updatePreviewColors();
        });
    },
    
    setupGradientToggles() {
        this.setupGradientToggle(
            document.getElementById('headingGradientToggle'),
            document.getElementById('headingGradient'),
            document.getElementById('headingGradientSettings')
        );

        this.setupGradientToggle(
            document.getElementById('textGradientToggle'),
            document.getElementById('textGradient'),
            document.getElementById('textGradientSettings')
        );
    },
    
    updatePreviewColors() {
        const headingColorInput = document.getElementById('headingColor');
        const textColorInput = document.getElementById('textColor');
        
        if (!headingColorInput || !textColorInput) return;
        
        PreviewManager.updateColors({
            headingColor: '#' + headingColorInput.value,
            textColor: '#' + textColorInput.value,
            headingGradientEnabled: document.getElementById('headingGradientToggle')?.checked || false,
            textGradientEnabled: document.getElementById('textGradientToggle')?.checked || false,
            headingGradientEnd: '#' + (document.getElementById('headingGradientEnd')?.value || 'ffffff'),
            textGradientEnd: '#' + (document.getElementById('textGradientEnd')?.value || 'ffffff')
        });
    },

    updateAccentColor() {
        const accentColor = '#' + (document.getElementById('accentColor')?.value || 'ff6b6b');
        // Обновляем все акцентные элементы в live preview
        const accentElements = document.querySelectorAll('.accent-text');
        accentElements.forEach(el => {
            el.style.color = accentColor;
        });
        // Перерисовываем слайд если есть контент
        if (PreviewManager.slides.length > 0) {
            PreviewManager.updateSlideContent();
        }
    }
};

// ==========================================
// Form Handler Module
// ==========================================
const FormHandler = {
    init() {
        this.form = document.getElementById('generateForm');
        this.result = document.getElementById('result');
        this.resultText = document.getElementById('resultText');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.generateBtn = document.getElementById('generateBtn');
        this.mdFile = document.getElementById('markdownFile');
        
        if (!this.form) return;
        
        this.bindEvents();
    },
    
    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    },
    
    async handleSubmit(e) {
        e.preventDefault();

        if (!this.mdFile.files.length) {
            alert('Выберите Markdown файл');
            return;
        }

        this.generateBtn.disabled = true;
        this.generateBtn.classList.add('loading');
        this.result.classList.remove('visible', 'success', 'error');

        const formData = new FormData(this.form);

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (data.success) {
                this.result.classList.add('visible', 'success');
                this.resultText.textContent = 'Презентация успешно создана!';

                // Create blob from base64 and download
                const byteCharacters = atob(data.file_base64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: data.mime_type || 'application/pdf' });
                const url = URL.createObjectURL(blob);

                this.downloadBtn.href = url;
                this.downloadBtn.download = data.filename;
                this.downloadBtn.style.display = 'inline-block';
            } else {
                this.result.classList.add('visible', 'error');
                this.resultText.textContent = data.error || 'Произошла ошибка';
                this.downloadBtn.style.display = 'none';
            }
        } catch (err) {
            this.result.classList.add('visible', 'error');
            this.resultText.textContent = 'Ошибка соединения с сервером';
            this.downloadBtn.style.display = 'none';
        } finally {
            this.generateBtn.disabled = false;
            this.generateBtn.classList.remove('loading');
        }
    }
};

// ==========================================
// Format Selector Module
// ==========================================
const FormatSelector = {
    init() {
        this.buttons = document.querySelectorAll('.format-btn');
        this.hiddenInput = document.getElementById('formatValue');
        this.previewCanvas = document.getElementById('previewCanvas');
        this.bgUploadZone = document.getElementById('bgUploadZone');

        if (!this.buttons.length) return;

        this.bindEvents();
    },

    bindEvents() {
        this.buttons.forEach(btn => {
            btn.addEventListener('click', () => this.selectFormat(btn));
        });
    },

    selectFormat(btn) {
        const format = btn.dataset.format;

        // Update active button
        this.buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update hidden input
        if (this.hiddenInput) {
            this.hiddenInput.value = format;
        }

        // Update preview canvas aspect ratio
        if (this.previewCanvas) {
            this.previewCanvas.classList.toggle('vertical', format === 'vertical');
        }

        // Update background upload zone aspect ratio
        if (this.bgUploadZone) {
            this.bgUploadZone.classList.toggle('vertical', format === 'vertical');
        }
    }
};

// ==========================================
// Modal Manager Module
// ==========================================
const ModalManager = {
    init() {
        this.modal = document.getElementById('instructionsModal');
        this.openBtn = document.getElementById('instructionsBtn');
        this.closeBtn = document.getElementById('closeModal');
        this.copyBtn = document.getElementById('copyPromptBtn');
        this.promptText = document.getElementById('promptText');

        if (!this.modal) return;

        this.bindEvents();
    },

    bindEvents() {
        if (this.openBtn) {
            this.openBtn.addEventListener('click', () => this.open());
        }

        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }

        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('open')) {
                this.close();
            }
        });

        // Copy prompt
        if (this.copyBtn && this.promptText) {
            this.copyBtn.addEventListener('click', () => this.copyPrompt());
        }
    },

    open() {
        this.modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    },

    close() {
        this.modal.classList.remove('open');
        document.body.style.overflow = '';
    },

    async copyPrompt() {
        try {
            await navigator.clipboard.writeText(this.promptText.textContent);
            this.copyBtn.textContent = 'Скопировано!';
            this.copyBtn.classList.add('copied');

            setTimeout(() => {
                this.copyBtn.textContent = 'Копировать';
                this.copyBtn.classList.remove('copied');
            }, 2000);
        } catch (err) {
            // Fallback for older browsers
            const range = document.createRange();
            range.selectNode(this.promptText);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            document.execCommand('copy');
            window.getSelection().removeAllRanges();

            this.copyBtn.textContent = 'Скопировано!';
            this.copyBtn.classList.add('copied');

            setTimeout(() => {
                this.copyBtn.textContent = 'Копировать';
                this.copyBtn.classList.remove('copied');
            }, 2000);
        }
    }
};

// ==========================================
// Text Font Manager Module
// ==========================================
const TextFontManager = {
    init() {
        this.dropdown = document.getElementById('textFontDropdown');
        this.trigger = document.getElementById('textFontDropdownTrigger');
        this.menu = document.getElementById('textFontDropdownMenu');
        this.valueDisplay = document.getElementById('textFontDropdownValue');
        this.hiddenSelect = document.getElementById('textFontSelect');

        if (!this.dropdown) return;

        this.bindEvents();
    },

    bindEvents() {
        // Toggle dropdown
        this.trigger.addEventListener('click', () => {
            this.dropdown.classList.toggle('open');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.dropdown.contains(e.target)) {
                this.dropdown.classList.remove('open');
            }
        });

        // Font option selection
        this.menu.addEventListener('click', (e) => {
            const option = e.target.closest('.font-option');
            if (option) {
                const fontName = option.dataset.font;
                this.selectFont(fontName);
                this.dropdown.classList.remove('open');
            }
        });

        // Hover preview on font options
        this.menu.addEventListener('mouseover', async (e) => {
            const option = e.target.closest('.font-option');
            if (option && option.dataset.font) {
                const fontName = option.dataset.font;
                await FontManager.loadFontForPreview(fontName);
                const preview = option.querySelector('.font-option-preview');
                if (preview && FontManager.fontFaces[fontName]) {
                    preview.style.fontFamily = fontName;
                }
            }
        });
    },

    selectFont(fontName) {
        // Update hidden input
        this.hiddenSelect.value = fontName;

        // Update trigger text
        this.valueDisplay.textContent = fontName || 'Как у заголовка';

        // Update selected state
        this.menu.querySelectorAll('.font-option').forEach(opt => {
            opt.classList.toggle('selected', opt.dataset.font === fontName);
        });

        // Update live preview text font
        PreviewManager.updateTextFont(fontName || FontManager.hiddenSelect?.value);
    }
};

// ==========================================
// Export Format Selector Module
// ==========================================
const ExportFormatSelector = {
    init() {
        this.buttons = document.querySelectorAll('.export-format-btn');
        this.hiddenInput = document.getElementById('exportFormat');

        if (!this.buttons.length) return;

        this.bindEvents();
    },

    bindEvents() {
        this.buttons.forEach(btn => {
            btn.addEventListener('click', () => this.selectFormat(btn));
        });
    },

    selectFormat(btn) {
        const format = btn.dataset.format;

        // Update active button
        this.buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update hidden input
        if (this.hiddenInput) {
            this.hiddenInput.value = format;
        }
    }
};

// ==========================================
// AI Agent Module
// ==========================================
const AIAgent = {
    markdown: '',

    init() {
        this.uploadZone = document.getElementById('aiUploadZone');
        this.fileInput = document.getElementById('aiFileInput');
        this.uploadContent = document.getElementById('aiUploadContent');
        this.processing = document.getElementById('aiProcessing');
        this.result = document.getElementById('aiResult');
        this.resultPreview = document.getElementById('aiResultPreview');
        this.downloadBtn = document.getElementById('aiDownloadBtn');
        this.applyBtn = document.getElementById('aiApplyBtn');
        this.clearBtn = document.getElementById('aiClearBtn');

        if (!this.uploadZone) return;

        this.bindEvents();
    },

    bindEvents() {
        // Drag and drop
        ['dragenter', 'dragover'].forEach(e => {
            this.uploadZone.addEventListener(e, (ev) => {
                ev.preventDefault();
                this.uploadZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(e => {
            this.uploadZone.addEventListener(e, (ev) => {
                ev.preventDefault();
                this.uploadZone.classList.remove('dragover');
            });
        });

        this.uploadZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length) {
                this.handleFile(files[0]);
            }
        });

        // File input change
        this.fileInput.addEventListener('change', () => {
            if (this.fileInput.files.length) {
                this.handleFile(this.fileInput.files[0]);
            }
        });

        // Download button
        this.downloadBtn.addEventListener('click', () => this.downloadMarkdown());

        // Apply button
        this.applyBtn.addEventListener('click', () => this.applyToGenerator());

        // Clear button
        this.clearBtn.addEventListener('click', () => this.reset());
    },

    async handleFile(file) {
        // Validate extension
        const ext = file.name.toLowerCase().split('.').pop();
        const allowed = ['txt', 'md', 'markdown', 'docx'];

        if (!allowed.includes(ext)) {
            alert('Неподдерживаемый формат. Разрешены: .txt, .md, .docx');
            return;
        }

        // Show processing state
        this.uploadContent.style.display = 'none';
        this.processing.style.display = 'flex';
        this.result.style.display = 'none';

        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/ai/prepare', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                this.markdown = data.markdown;
                this.showResult();
            } else {
                alert(data.error || 'Ошибка обработки');
                this.reset();
            }
        } catch (err) {
            console.error('AI Agent error:', err);
            alert('Ошибка соединения с сервером');
            this.reset();
        }
    },

    showResult() {
        this.processing.style.display = 'none';
        this.uploadContent.style.display = 'none';
        this.result.style.display = 'block';
        this.resultPreview.textContent = this.markdown;
    },

    reset() {
        this.markdown = '';
        this.processing.style.display = 'none';
        this.result.style.display = 'none';
        this.uploadContent.style.display = 'flex';
        this.fileInput.value = '';
        this.resultPreview.textContent = '';
    },

    downloadMarkdown() {
        if (!this.markdown) return;

        const blob = new Blob([this.markdown], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'presentation.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    applyToGenerator() {
        if (!this.markdown) return;

        // Create a File object from markdown content
        const blob = new Blob([this.markdown], { type: 'text/markdown' });
        const file = new File([blob], 'presentation.md', { type: 'text/markdown' });

        // Create a DataTransfer to set the file input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);

        // Set the file to markdown input
        const mdFile = document.getElementById('markdownFile');
        if (mdFile) {
            mdFile.files = dataTransfer.files;
            
            // Dispatch change event to ensure form detects the file
            mdFile.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Also manually trigger FileUpload handler for preview
            FileUpload.handleMarkdownUpload(file);
        }

        // Scroll to generator section
        const generatorSection = document.querySelector('.upload-sections');
        if (generatorSection) {
            generatorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
};

// ==========================================
// Size Manager Module
// ==========================================
const SizeManager = {
    init() {
        // Heading controls
        this.headingFontSize = document.getElementById('headingFontSize');
        this.headingFontSizeValue = document.getElementById('headingFontSizeValue');
        this.headingWidth = document.getElementById('headingWidth');
        this.headingWidthValue = document.getElementById('headingWidthValue');

        // Text controls
        this.textFontSize = document.getElementById('textFontSize');
        this.textFontSizeValue = document.getElementById('textFontSizeValue');
        this.textWidth = document.getElementById('textWidth');
        this.textWidthValue = document.getElementById('textWidthValue');

        if (!this.headingFontSize) return;

        this.bindEvents();
        this.updatePreview();
    },

    bindEvents() {
        // Heading font size
        this.headingFontSize.addEventListener('input', () => {
            this.headingFontSizeValue.textContent = this.headingFontSize.value;
            this.updatePreview();
        });

        // Heading width
        this.headingWidth.addEventListener('input', () => {
            this.headingWidthValue.textContent = this.headingWidth.value + '%';
            this.updatePreview();
        });

        // Text font size
        this.textFontSize.addEventListener('input', () => {
            this.textFontSizeValue.textContent = this.textFontSize.value;
            this.updatePreview();
        });

        // Text width
        this.textWidth.addEventListener('input', () => {
            this.textWidthValue.textContent = this.textWidth.value + '%';
            this.updatePreview();
        });

        // Reset buttons
        this.bindResetButton('resetHeadingFontSize', this.headingFontSize, this.headingFontSizeValue, false);
        this.bindResetButton('resetHeadingWidth', this.headingWidth, this.headingWidthValue, true);
        this.bindResetButton('resetTextFontSize', this.textFontSize, this.textFontSizeValue, false);
        this.bindResetButton('resetTextWidth', this.textWidth, this.textWidthValue, true);
    },

    bindResetButton(buttonId, slider, valueSpan, isPercent) {
        const btn = document.getElementById(buttonId);
        if (!btn) return;
        
        btn.addEventListener('click', () => {
            const defaultValue = btn.dataset.default;
            slider.value = defaultValue;
            valueSpan.textContent = isPercent ? defaultValue + '%' : defaultValue;
            this.updatePreview();
        });
    },

    updatePreview() {
        const previewHeading = document.getElementById('previewHeading');
        const previewText = document.getElementById('previewText');

        if (previewHeading) {
            // Scale factor: preview is smaller than actual slide
            // Preview width ~280px, slide width 1600px, so scale ~0.175
            const scaleFactor = 0.35;
            
            const headingSize = parseInt(this.headingFontSize.value) * scaleFactor;
            const headingWidth = parseInt(this.headingWidth.value);
            
            previewHeading.style.fontSize = headingSize + 'px';
            previewHeading.style.width = headingWidth + '%';
            previewHeading.style.marginLeft = 'auto';
            previewHeading.style.marginRight = 'auto';
        }

        if (previewText) {
            const scaleFactor = 0.35;
            
            const textSize = parseInt(this.textFontSize.value) * scaleFactor;
            const textWidth = parseInt(this.textWidth.value);
            
            previewText.style.fontSize = textSize + 'px';
            previewText.style.width = textWidth + '%';
            previewText.style.marginLeft = 'auto';
            previewText.style.marginRight = 'auto';
        }
    }
};

// ==========================================
// Application Initialization
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all modules
    FileUpload.init();
    BackgroundManager.init();
    FontManager.init();
    TextFontManager.init();
    PreviewManager.init();
    ColorManager.init();
    SizeManager.init();
    FormHandler.init();
    FormatSelector.init();
    ExportFormatSelector.init();
    ModalManager.init();
    AIAgent.init();

    // Initial preview update
    ColorManager.updatePreviewColors();
    ColorManager.updateOverlay();
    SizeManager.updatePreview();
    PreviewManager.updateBackground(null);

    // Pre-load fonts for dropdown preview when dropdown opens
    const fontDropdown = document.getElementById('fontDropdown');
    if (fontDropdown) {
        let fontsPreloaded = false;
        fontDropdown.addEventListener('click', async () => {
            if (fontsPreloaded) return;
            fontsPreloaded = true;

            // Load all fonts in parallel
            const fontOptions = document.querySelectorAll('.font-option-preview');
            const loadPromises = [];

            fontOptions.forEach(preview => {
                const fontName = preview.dataset.previewFont;
                if (fontName) {
                    loadPromises.push(
                        FontManager.loadFontForPreview(fontName).then(() => {
                            preview.style.fontFamily = `"${fontName}", sans-serif`;
                        })
                    );
                }
            });

            await Promise.all(loadPromises);
        });
    }
});
