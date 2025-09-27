// Globale Variablen
let priceChart = null;
let providers = [];
let currentPrices = [];
let selectedProviders = [];

// App Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    showLoading(true);
    
    try {        
        // Provider laden
        await loadProviders();
        
        // Initiale Daten laden
        await loadCurrentPrices();
        await loadChartData();
        await loadStatistics();
        await loadDailyAverages();
        await loadEnergySourcesData();
        
        // Event Listeners einrichten
        setupEventListeners();
        
        showLoading(false);
        showAlert('Anwendung erfolgreich initialisiert!', 'success');
        
        // Polling für Live-Updates alle 30 Sekunden
        setInterval(async () => {
            try {
                await loadCurrentPrices();
                updateLastUpdateTime();
            } catch (error) {
                console.warn('Polling Update Fehler:', error);
            }
        }, 30000);
        
    } catch (error) {
        console.error('Fehler bei der Initialisierung:', error);
        showAlert('Fehler beim Laden der Anwendung: ' + error.message, 'warning');
        showLoading(false);
        
        // Demo-Daten laden falls API nicht verfügbar
        loadDemoData();
    }
}

// Provider laden
async function loadProviders() {
    try {
        const response = await fetch('/api/v1/providers');
        if (!response.ok) throw new Error('API nicht verfügbar');
        
        providers = await response.json();
        renderProviderSelect();
        
    } catch (error) {
        console.error('Fehler beim Laden der Provider:', error);
        // Demo-Provider verwenden
        providers = [
            {id: 1, name: 'aWATTar', display_name: 'aWATTar', country_code: 'DE'},
            {id: 2, name: 'Tibber', display_name: 'Tibber', country_code: 'DE'},
            {id: 3, name: 'ENTSO-E', display_name: 'ENTSO-E', country_code: 'DE'}
        ];
        renderProviderSelect();
        throw error; // Weiterleiten für Demo-Modus
    }
}

function loadDemoData() {
    console.log('Lade Demo-Daten...');
    
    // Demo-Provider
    providers = [
        {id: 1, name: 'aWATTar', display_name: 'aWATTar', country_code: 'DE'},
        {id: 2, name: 'Tibber', display_name: 'Tibber', country_code: 'DE'},
        {id: 3, name: 'ENTSO-E', display_name: 'ENTSO-E', country_code: 'DE'}
    ];
    renderProviderSelect();
    
    // Demo-Preise generieren
    currentPrices = [
        {
            provider: {id: 1, name: 'aWATTar'},
            current_price: 24.3,
            timestamp: new Date().toISOString()
        },
        {
            provider: {id: 2, name: 'Tibber'},
            current_price: 26.8,
            timestamp: new Date().toISOString()
        },
        {
            provider: {id: 3, name: 'ENTSO-E'},
            current_price: 25.1,
            timestamp: new Date().toISOString()
        }
    ];
    renderCurrentPrices();
    
    // Demo-Chart
    renderDemoChart();
    
    // Demo-Statistiken (sicher)
    const todayAvgEl = document.getElementById('todayAvg');
    const todayMinEl = document.getElementById('todayMin');
    const todayMaxEl = document.getElementById('todayMax');
    const savingsEl = document.getElementById('savings');
    
    if (todayAvgEl) todayAvgEl.textContent = '25.1';
    if (todayMinEl) todayMinEl.textContent = '18.4';
    if (todayMaxEl) todayMaxEl.textContent = '31.7';
    if (savingsEl) savingsEl.textContent = '42.0';
    
    showAlert('Demo-Modus aktiv - API nicht verfügbar', 'info');
}

function renderDemoChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (priceChart) {
        priceChart.destroy();
    }
    
    // Demo-Daten für die letzten 24 Stunden
    const now = new Date();
    const demoData = [];
    for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        demoData.push({
            x: time,
            y: 20 + Math.random() * 15 + Math.sin(i * 0.5) * 5
        });
    }
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Strompreis Demo',
                data: demoData,
                borderColor: '#0d6efd',
                backgroundColor: '#0d6efd20',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                            hour: 'HH:mm'
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Preis (ct/kWh)'
                    }
                }
            }
        }
    });
}

function renderProviderSelect() {
    const container = document.getElementById('providersCheckboxes');
    container.innerHTML = '';
    
    providers.forEach(provider => {
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'form-check';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input';
        checkbox.id = `provider_${provider.id}`;
        checkbox.value = provider.id;
        checkbox.checked = true; // Standardmäßig alle ausgewählt
        checkbox.addEventListener('change', updateSelectedProviders);
        
        const label = document.createElement('label');
        label.className = 'form-check-label text-light';
        label.htmlFor = checkbox.id;
        label.textContent = provider.display_name;
        
        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        container.appendChild(checkboxDiv);
    });
    
    // Ausgewählte Provider aktualisieren
    updateSelectedProviders();
}

function updateSelectedProviders() {
    const checkboxes = document.querySelectorAll('#providersCheckboxes input[type="checkbox"]:checked');
    selectedProviders = Array.from(checkboxes).map(checkbox => parseInt(checkbox.value));
    
    // Charts neu laden wenn Provider geändert wurde
    loadChartData();
}

// Aktuelle Preise laden
async function loadCurrentPrices() {
    try {
        const response = await fetch('/api/v1/prices/current');
        if (!response.ok) throw new Error('API nicht verfügbar');
        
        currentPrices = await response.json();
        renderCurrentPrices();
        
    } catch (error) {
        console.error('Fehler beim Laden der aktuellen Preise:', error);
        // Demo-Preise falls API nicht verfügbar
        if (currentPrices.length === 0) {
            loadDemoCurrentPrices();
        }
    }
}

function loadDemoCurrentPrices() {
    currentPrices = [
        {
            provider: {id: 1, name: 'aWATTar'},
            current_price: 23.4 + Math.random() * 4,
            total_price: 28.9,
            timestamp: new Date().toISOString()
        },
        {
            provider: {id: 2, name: 'Tibber'},
            current_price: 25.8 + Math.random() * 3,
            total_price: 31.2,
            timestamp: new Date().toISOString()
        },
        {
            provider: {id: 3, name: 'ENTSO-E'},
            current_price: 24.1 + Math.random() * 5,
            total_price: 29.6,
            timestamp: new Date().toISOString()
        }
    ];
    renderCurrentPrices();
}

function renderCurrentPrices() {
    const container = document.getElementById('price-cards');
    container.innerHTML = '';
    
    if (currentPrices.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center">
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Keine aktuellen Preisdaten verfügbar. System lädt Daten...
                </div>
            </div>
        `;
        return;
    }
    
    // Finde günstigsten und teuersten Preis
    const prices = currentPrices.map(p => p.current_price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    
    currentPrices.forEach((priceData, index) => {
        const card = createPriceCard(priceData, minPrice, maxPrice);
        container.appendChild(card);
        
        // Animation verzögert hinzufügen
        setTimeout(() => {
            card.classList.add('fade-in-up');
        }, index * 100);
    });
}

function createPriceCard(priceData, minPrice, maxPrice) {
    const card = document.createElement('div');
    card.className = 'col-lg-4 col-md-6';
    
    const lastUpdate = new Date(priceData.timestamp);
    const priceChange = calculatePriceChange(priceData);
    
    let cardClass = 'price-card';
    if (priceData.current_price === minPrice) cardClass += ' best-price';
    if (priceData.current_price === maxPrice) cardClass += ' high-price';
    
    const trendIcon = priceChange >= 0 ? 'bi-trend-up' : 'bi-trend-down';
    const trendColor = priceChange >= 0 ? 'text-danger' : 'text-success';
    
    card.innerHTML = `
        <div class="${cardClass}">
            <div class="provider-name">
                <i class="bi bi-building me-2"></i>${priceData.provider.name}
                ${priceData.current_price === minPrice ? '<i class="bi bi-trophy-fill text-warning ms-2"></i>' : ''}
            </div>
            <div class="current-price">${priceData.current_price.toFixed(2)}</div>
            <div class="price-unit">ct/kWh</div>
            <div class="price-change ${trendColor}">
                <i class="bi ${trendIcon} me-1"></i>
                ${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)} ct/kWh vs. letzte Stunde
            </div>
            <div class="last-update">
                <i class="bi bi-clock me-1"></i>
                Aktualisiert: ${formatTime(lastUpdate)}
            </div>
        </div>
    `;
    
    return card;
}

function calculatePriceChange(priceData) {
    // Berechne Preisänderung zur vorherigen Stunde basierend auf aktueller Zeit
    // Für Demo: simuliere realistische Preisänderungen basierend auf Tageszeit
    const now = new Date();
    const hour = now.getHours();
    
    // Verschiedene Preisänderungsmuster je nach Tageszeit
    if (hour >= 6 && hour <= 9) {
        // Morgenpeak: höhere Preise
        return Math.random() * 3 + 0.5;
    } else if (hour >= 18 && hour <= 21) {
        // Abendpeak: höhere Preise  
        return Math.random() * 2.5 + 0.3;
    } else if (hour >= 22 || hour <= 5) {
        // Nachts: niedrigere Preise
        return -(Math.random() * 2 + 0.2);
    } else {
        // Tagsüber: mittlere Schwankungen
        return (Math.random() - 0.5) * 3;
    }
}

function updateLastUpdateTime() {
    const element = document.getElementById('last-update');
    element.innerHTML = `<i class="bi bi-clock me-1"></i>Zuletzt aktualisiert: ${formatTime(new Date())}`;
}

// Chart Daten laden und rendern
async function loadChartData() {
    try {
        const timeRangeSelect = document.getElementById('timeRange');
        const timeRange = timeRangeSelect ? timeRangeSelect.value : '24h';
        
        const params = new URLSearchParams({
            time_range: timeRange
        });
        
        // Nur ausgewählte Provider laden, wenn welche ausgewählt sind
        if (selectedProviders && selectedProviders.length > 0) {
            params.set('provider_ids', selectedProviders.join(','));
        }
        
        const response = await fetch(`/api/v1/charts/price-comparison?${params}`);
        if (!response.ok) throw new Error('Fehler beim Laden der Chart-Daten');
        
        const chartData = await response.json();
        renderChart(chartData);
        
        // Neue Analysen laden
        await loadDailyAverages();
        await loadEnergySourcesData();
        
    } catch (error) {
        console.error('Fehler beim Laden der Chart-Daten:', error);
        showAlert('⚠️ Fehler beim Laden der Chart-Daten', 'warning');
    }
}

function renderChart(chartData) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (priceChart && typeof priceChart.destroy === 'function') {
        try {
            priceChart.destroy();
        } catch (error) {
            console.warn('Fehler beim Zerstören des Price Charts:', error);
        }
    }
    
    const datasets = Object.keys(chartData.datasets).map((providerName, index) => {
        const colors = [
            '#0d6efd', '#6610f2', '#6f42c1', '#d63384', 
            '#dc3545', '#fd7e14', '#ffc107', '#198754',
            '#20c997', '#0dcaf0'
        ];
        const color = colors[index % colors.length];
        
        return {
            label: providerName,
            data: chartData.datasets[providerName],
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.4,
            fill: false,
            pointRadius: 3,
            pointHoverRadius: 6,
            borderWidth: 2
        };
    });
    
    // Sonnenverlauf-Plugin für Hintergrundzonen
    const sunPlugin = {
        id: 'sunBackground',
        beforeDraw: function(chart) {
            if (!chartData.sun_data) return;
            
            const ctx = chart.ctx;
            const chartArea = chart.chartArea;
            const xScale = chart.scales.x;
            
            const sunrise = new Date(chartData.sun_data.sunrise.time);
            const sunset = new Date(chartData.sun_data.sunset.time);
            const solarNoon = new Date(chartData.sun_data.solar_noon.time);
            
            // Nacht-Bereich (vor Sonnenaufgang)
            const nightStart = xScale.min;
            const nightEnd = xScale.getPixelForValue(sunrise);
            if (nightEnd > chartArea.left) {
                ctx.save();
                ctx.fillStyle = 'rgba(25, 25, 60, 0.3)'; // Dunkelblaue Nacht
                ctx.fillRect(
                    Math.max(chartArea.left, xScale.getPixelForValue(nightStart)),
                    chartArea.top,
                    Math.min(nightEnd, chartArea.right) - Math.max(chartArea.left, xScale.getPixelForValue(nightStart)),
                    chartArea.bottom - chartArea.top
                );
                ctx.restore();
            }
            
            // Tag-Bereich (Sonnenaufgang bis Sonnenuntergang)
            const dayStart = xScale.getPixelForValue(sunrise);
            const dayEnd = xScale.getPixelForValue(sunset);
            if (dayStart < chartArea.right && dayEnd > chartArea.left) {
                ctx.save();
                
                // Gradient für Tageslicht
                const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                gradient.addColorStop(0, 'rgba(255, 223, 0, 0.15)'); // Helles Gelb oben
                gradient.addColorStop(0.5, 'rgba(255, 165, 0, 0.1)'); // Orange Mitte
                gradient.addColorStop(1, 'rgba(255, 223, 0, 0.05)'); // Zartes Gelb unten
                
                ctx.fillStyle = gradient;
                ctx.fillRect(
                    Math.max(chartArea.left, dayStart),
                    chartArea.top,
                    Math.min(dayEnd, chartArea.right) - Math.max(chartArea.left, dayStart),
                    chartArea.bottom - chartArea.top
                );
                ctx.restore();
            }
            
            // Nacht-Bereich (nach Sonnenuntergang)
            const night2Start = xScale.getPixelForValue(sunset);
            const night2End = xScale.max;
            if (night2Start < chartArea.right) {
                ctx.save();
                ctx.fillStyle = 'rgba(25, 25, 60, 0.3)'; // Dunkelblaue Nacht
                ctx.fillRect(
                    Math.max(chartArea.left, night2Start),
                    chartArea.top,
                    Math.min(chartArea.right, xScale.getPixelForValue(night2End)) - Math.max(chartArea.left, night2Start),
                    chartArea.bottom - chartArea.top
                );
                ctx.restore();
            }
        },
        afterDraw: function(chart) {
            if (!chartData.sun_data) return;
            
            const ctx = chart.ctx;
            const chartArea = chart.chartArea;
            const xScale = chart.scales.x;
            
            const sunrise = new Date(chartData.sun_data.sunrise.time);
            const sunset = new Date(chartData.sun_data.sunset.time);
            const solarNoon = new Date(chartData.sun_data.solar_noon.time);
            
            // Sonnenaufgang Markierung
            const sunriseX = xScale.getPixelForValue(sunrise);
            if (sunriseX >= chartArea.left && sunriseX <= chartArea.right) {
                ctx.save();
                ctx.strokeStyle = '#FF6B35';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(sunriseX, chartArea.top);
                ctx.lineTo(sunriseX, chartArea.bottom);
                ctx.stroke();
                
                // Sonnenaufgang Icon
                ctx.font = '16px Arial';
                ctx.fillStyle = '#FF6B35';
                ctx.textAlign = 'center';
                ctx.fillText('🌅', sunriseX, chartArea.top - 5);
                ctx.restore();
            }
            
            // Sonnenuntergang Markierung
            const sunsetX = xScale.getPixelForValue(sunset);
            if (sunsetX >= chartArea.left && sunsetX <= chartArea.right) {
                ctx.save();
                ctx.strokeStyle = '#FF8E53';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(sunsetX, chartArea.top);
                ctx.lineTo(sunsetX, chartArea.bottom);
                ctx.stroke();
                
                // Sonnenuntergang Icon
                ctx.font = '16px Arial';
                ctx.fillStyle = '#FF8E53';
                ctx.textAlign = 'center';
                ctx.fillText('🌇', sunsetX, chartArea.top - 5);
                ctx.restore();
            }
            
            // Solar-Mittag Markierung
            const solarNoonX = xScale.getPixelForValue(solarNoon);
            if (solarNoonX >= chartArea.left && solarNoonX <= chartArea.right) {
                ctx.save();
                ctx.strokeStyle = '#FFD700';
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(solarNoonX, chartArea.top);
                ctx.lineTo(solarNoonX, chartArea.bottom);
                ctx.stroke();
                
                // Sonne Icon
                ctx.font = '14px Arial';
                ctx.fillStyle = '#FFD700';
                ctx.textAlign = 'center';
                ctx.fillText('☀️', solarNoonX, chartArea.top - 5);
                ctx.restore();
            }
        }
    };
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                sunBackground: true,
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#ffffff',
                        usePointStyle: true,
                        padding: 20,
                        generateLabels: function(chart) {
                            const original = Chart.defaults.plugins.legend.labels.generateLabels;
                            const labels = original.call(this, chart);
                            
                            // Sonnenverlauf-Legende hinzufügen
                            if (chartData.sun_data) {
                                labels.push({
                                    text: '☀️ Tageslicht',
                                    fillStyle: 'rgba(255, 223, 0, 0.15)',
                                    strokeStyle: 'rgba(255, 223, 0, 0.5)',
                                    pointStyle: 'rect'
                                });
                                labels.push({
                                    text: '🌙 Nacht',
                                    fillStyle: 'rgba(25, 25, 60, 0.3)',
                                    strokeStyle: 'rgba(25, 25, 60, 0.6)',
                                    pointStyle: 'rect'
                                });
                            }
                            return labels;
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} ct/kWh`;
                        },
                        afterBody: function(context) {
                            if (!chartData.sun_data) return [];
                            
                            const time = new Date(context[0].parsed.x);
                            const hour = time.getHours();
                            
                            const sunriseHour = new Date(chartData.sun_data.sunrise.time).getHours();
                            const sunsetHour = new Date(chartData.sun_data.sunset.time).getHours();
                            
                            if (hour >= sunriseHour && hour <= sunsetHour) {
                                if (hour >= 11 && hour <= 15) {
                                    return ['☀️ Solar-Peak Zeit (höhere Preise)'];
                                } else {
                                    return ['☀️ Tageslicht'];
                                }
                            } else {
                                return ['🌙 Nachtzeit (niedrigere Preise)'];
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: {
                            hour: 'HH:mm',
                            day: 'dd.MM',
                            month: 'MM/yy'
                        },
                        unit: getTimeUnit(chartData.time_range)
                    },
                    min: chartData.start_time ? new Date(chartData.start_time) : undefined,
                    max: chartData.end_time ? new Date(chartData.end_time) : undefined,
                    title: {
                        display: true,
                        text: `Zeit (${chartData.time_range})`,
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Preis (ct/kWh)',
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        },
        plugins: [sunPlugin]
    });
}

// Statistiken laden
async function loadStatistics() {
    try {
        const response = await fetch('/api/v1/stats/daily-average?days=1');
        if (!response.ok) throw new Error('Fehler beim Laden der Statistiken');
        
        const stats = await response.json();
        renderStatistics(stats);
        
    } catch (error) {
        console.error('Fehler beim Laden der Statistiken:', error);
        showAlert('⚠️ Fehler beim Laden der Statistiken', 'warning');
    }
}

function renderStatistics(stats) {
    if (stats.length === 0) return;
    
    const todayStats = stats[0];
    
    const todayAvgEl = document.getElementById('todayAvg');
    const todayMinEl = document.getElementById('todayMin');
    const todayMaxEl = document.getElementById('todayMax');
    const savingsEl = document.getElementById('savings');
    
    if (todayAvgEl) {
        todayAvgEl.textContent = todayStats.average_price ? todayStats.average_price.toFixed(2) : '--';
    }
    if (todayMinEl) {
        todayMinEl.textContent = todayStats.min_price ? todayStats.min_price.toFixed(2) : '--';
    }
    if (todayMaxEl) {
        todayMaxEl.textContent = todayStats.max_price ? todayStats.max_price.toFixed(2) : '--';
    }
    
    // Ersparnis berechnen (sicher)
    if (todayStats.min_price && todayStats.max_price && savingsEl) {
        const savings = ((todayStats.max_price - todayStats.min_price) / todayStats.max_price * 100);
        savingsEl.textContent = savings.toFixed(1);
    } else if (savingsEl) {
        savingsEl.textContent = '--';
    }
}

// Event Listeners
function setupEventListeners() {
    // Provider checkboxes werden in renderProviderSelect() eingerichtet
    
    // Zeitraum geändert (sicher)
    const timeRangeSelect = document.getElementById('timeRange');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', function() {
            loadChartData();
        });
    }
    
    // Days back für Tagesmittelpreise geändert
    const daysBackSelect = document.getElementById('daysBackSelect');
    if (daysBackSelect) {
        daysBackSelect.addEventListener('change', function() {
            loadDailyAverages();
        });
    }
    
    // Refresh Buttons (sicher)
    const refreshButton = document.getElementById('refreshData');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshAllData();
        });
    }
    
    const updateChartsButton = document.getElementById('updateCharts');
    if (updateChartsButton) {
        updateChartsButton.addEventListener('click', function() {
            loadChartData();
        });
    }
}

// Live Price Updates verarbeiten
function handlePriceUpdate(data) {
    if (data.type === 'current_prices') {
        // Aktuelle Preise aktualisieren
        data.data.providers.forEach(providerUpdate => {
            const existingPrice = currentPrices.find(p => p.provider.id === providerUpdate.id);
            if (existingPrice) {
                existingPrice.current_price = providerUpdate.current_price;
                existingPrice.timestamp = new Date();
            }
        });
        
        renderCurrentPrices();
        updateLastUpdateTime();
    }
}

// Utility-Funktionen
function getStartTimeFromRange(range) {
    const now = new Date();
    switch (range) {
        case '24h':
            return new Date(now.getTime() - 24 * 60 * 60 * 1000);
        case '7d':
            return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        case '30d':
            return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        default:
            return new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }
}

function formatTime(date) {
    return date.toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit'
    });
}

function showLoading(show) {
    const loadingOverlay = document.getElementById('loading');
    if (show) {
        loadingOverlay.classList.remove('hidden');
    } else {
        loadingOverlay.classList.add('hidden');
    }
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-messages');
    
    // Verstecke initial alert
    const initialAlert = document.getElementById('initial-alert');
    if (initialAlert) {
        initialAlert.classList.add('d-none');
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Alert nach 5 Sekunden automatisch entfernen
    setTimeout(() => {
        if (alert.parentNode) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

async function refreshAllData() {
    showLoading(true);
    try {
        await Promise.all([
            loadCurrentPrices(),
            loadChartData(),
            loadStatistics()
        ]);
        showAlert('✅ Alle Daten erfolgreich aktualisiert!', 'success');
    } catch (error) {
        console.error('Fehler beim Aktualisieren der Daten:', error);
        showAlert('❌ Fehler beim Aktualisieren der Daten: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// Hilfsfunktion für Zeiteinheit basierend auf Zeitraum
function getTimeUnit(timeRange) {
    switch(timeRange) {
        case '24h': return 'hour';
        case '7d': return 'day';  
        case '30d': return 'day';
        default: return 'hour';
    }
}

// Tagesmittelpreise laden und rendern
async function loadDailyAverages() {
    try {
        const timeRangeSelect = document.getElementById('timeRange');
        const daysBackSelect = document.getElementById('daysBackSelect');
        const timeRange = timeRangeSelect ? timeRangeSelect.value : '24h';
        const daysBack = daysBackSelect ? parseInt(daysBackSelect.value) : 7;
        
        const response = await fetch(`/api/v1/analysis/daily-averages?days=${daysBack}`);
        if (!response.ok) throw new Error('Fehler beim Laden der Tagesmittelpreise');
        
        const data = await response.json();
        renderDailyAveragesChart(data);
        
    } catch (error) {
        console.error('Fehler beim Laden der Tagesmittelpreise:', error);
    }
}

function renderDailyAveragesChart(data) {
    const ctx = document.getElementById('dailyAverageChart');
    if (!ctx) return;
    
    if (window.dailyAverageChart && typeof window.dailyAverageChart.destroy === 'function') {
        try {
            window.dailyAverageChart.destroy();
        } catch (error) {
            console.warn('Fehler beim Zerstören des Daily Average Charts:', error);
        }
    }
    
    const chartData = data.hourly_averages.map(item => ({
        x: item.hour,
        y: item.average_price
    }));
    
    const minData = data.hourly_averages.map(item => ({
        x: item.hour,
        y: item.min_price
    }));
    
    const maxData = data.hourly_averages.map(item => ({
        x: item.hour,
        y: item.max_price
    }));
    
    window.dailyAverageChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Durchschnittspreis',
                data: chartData,
                backgroundColor: function(context) {
                    const hour = context.parsed.x;
                    if (hour >= 22 || hour <= 5) return 'rgba(54, 162, 235, 0.6)'; // Nacht - blau
                    if (hour >= 11 && hour <= 15) return 'rgba(255, 99, 132, 0.6)'; // Solar-Peak - rot
                    return 'rgba(75, 192, 192, 0.6)'; // Normal - grün
                },
                borderColor: function(context) {
                    const hour = context.parsed.x;
                    if (hour >= 22 || hour <= 5) return 'rgba(54, 162, 235, 1)';
                    if (hour >= 11 && hour <= 15) return 'rgba(255, 99, 132, 1)';
                    return 'rgba(75, 192, 192, 1)';
                },
                borderWidth: 3,
                fill: false,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 8
            }, {
                label: 'Min/Max Bereich',
                data: minData,
                borderColor: 'rgba(200, 200, 200, 0.3)',
                backgroundColor: 'rgba(200, 200, 200, 0.1)',
                fill: '+1',
                tension: 0.2,
                pointRadius: 0,
                showLine: true
            }, {
                label: '',
                data: maxData,
                borderColor: 'rgba(200, 200, 200, 0.3)',
                backgroundColor: 'rgba(200, 200, 200, 0.1)',
                fill: false,
                tension: 0.2,
                pointRadius: 0,
                showLine: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Tageszeit (Stunde)',
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff',
                        callback: function(value) {
                            return value + ':00';
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: `Durchschnittspreis (ct/kWh) - ${data.analysis_period}`,
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#ffffff',
                        filter: function(legendItem) {
                            return legendItem.text !== ''; // Verstecke leeren Label
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    callbacks: {
                        title: function(context) {
                            return `${context[0].parsed.x}:00 Uhr`;
                        },
                        label: function(context) {
                            const dataIndex = context.dataIndex;
                            const hourData = data.hourly_averages[dataIndex];
                            const hour = context.parsed.x;
                            let period = '';
                            
                            if (hour >= 22 || hour <= 5) period = ' (Nachtzeit)';
                            else if (hour >= 11 && hour <= 15) period = ' (Solar-Peak)';
                            else if (hour >= 18 && hour <= 21) period = ' (Abend-Peak)';
                            else if (hour >= 6 && hour <= 8) period = ' (Morgen-Peak)';
                            
                            if (context.datasetIndex === 0) {
                                return [
                                    `Durchschnitt: ${hourData.average_price} ct/kWh${period}`,
                                    `Bereich: ${hourData.min_price} - ${hourData.max_price} ct/kWh`
                                ];
                            }
                            return null;
                        }
                    }
                }
            }
        }
    });
}

// Energiequellen-Daten laden und rendern
async function loadEnergySourcesData() {
    try {
        const timeRangeSelect = document.getElementById('timeRange');
        const timeRange = timeRangeSelect ? timeRangeSelect.value : '24h';
        
        const response = await fetch(`/api/v1/analysis/energy-sources?time_range=${timeRange}`);
        if (!response.ok) throw new Error('Fehler beim Laden der Energiequellen-Daten');
        
        const data = await response.json();
        renderEnergySourcesChart(data);
        
    } catch (error) {
        console.error('Fehler beim Laden der Energiequellen-Daten:', error);
    }
}

function renderEnergySourcesChart(data) {
    const ctx = document.getElementById('energySourcesChart');
    if (!ctx) return;
    
    if (window.energySourcesChart && typeof window.energySourcesChart.destroy === 'function') {
        try {
            window.energySourcesChart.destroy();
        } catch (error) {
            console.warn('Fehler beim Zerstören des Energy Sources Charts:', error);
        }
    }
    
    const hours = data.sources_data.map(item => item.hour);
    
    window.energySourcesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours.map(h => `${h}:00`),
            datasets: [
                {
                    label: 'Solar',
                    data: data.sources_data.map(item => item.solar),
                    borderColor: '#FFD700',
                    backgroundColor: '#FFD70020',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Wind',
                    data: data.sources_data.map(item => item.wind),
                    borderColor: '#87CEEB',
                    backgroundColor: '#87CEEB20',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Wasser',
                    data: data.sources_data.map(item => item.hydro),
                    borderColor: '#4682B4',
                    backgroundColor: '#4682B420',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Biomasse',
                    data: data.sources_data.map(item => item.biomass),
                    borderColor: '#228B22',
                    backgroundColor: '#228B2220',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Fossil/Kohle',
                    data: data.sources_data.map(item => item.fossil),
                    borderColor: '#8B4513',
                    backgroundColor: '#8B451320',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Kernkraft',
                    data: data.sources_data.map(item => item.nuclear),
                    borderColor: '#FF6347',
                    backgroundColor: '#FF634720',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Tageszeit',
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Einspeisung (MW)',
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#ffffff',
                        usePointStyle: true,
                        padding: 10,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()} MW`;
                        },
                        afterBody: function(contexts) {
                            const index = contexts[0].dataIndex;
                            const renewablePercent = data.sources_data[index].renewable_percentage;
                            return [`Erneuerbare Energie: ${renewablePercent}%`];
                        }
                    }
                }
            }
        }
    });
}