// WaveRiderSDR - Main Application JavaScript

// Band Plan Data - Frequency allocations for different bands
const bandPlans = {
    hf: {
        name: 'HF (High Frequency)',
        range: '3-30 MHz',
        minFreq: 3,
        maxFreq: 30,
        uses: 'Shortwave Radio, Amateur Radio, International Broadcasting',
        allocations: [
            { start: 3, end: 4, name: '80m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 4, end: 5, name: 'Fixed/Mobile', color: '#4ECDC4', service: 'Fixed and Mobile Services' },
            { start: 5, end: 7, name: 'Shortwave Broadcasting', color: '#95E1D3', service: 'Broadcasting' },
            { start: 7, end: 7.3, name: '40m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 7.3, end: 10, name: 'Fixed/Broadcasting', color: '#4ECDC4', service: 'Fixed and Broadcasting' },
            { start: 10, end: 14, name: 'Broadcasting', color: '#95E1D3', service: 'Shortwave Broadcasting' },
            { start: 14, end: 14.35, name: '20m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 14.35, end: 18, name: 'Fixed/Mobile', color: '#4ECDC4', service: 'Fixed and Mobile Services' },
            { start: 18, end: 21, name: 'Broadcasting', color: '#95E1D3', service: 'Broadcasting' },
            { start: 21, end: 21.45, name: '15m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 21.45, end: 28, name: 'Fixed/Mobile', color: '#4ECDC4', service: 'Fixed and Mobile Services' },
            { start: 28, end: 29.7, name: '10m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 29.7, end: 30, name: 'Fixed/Mobile', color: '#4ECDC4', service: 'Fixed and Mobile Services' }
        ]
    },
    vhf: {
        name: 'VHF (Very High Frequency)',
        range: '30-300 MHz',
        minFreq: 30,
        maxFreq: 300,
        uses: 'FM Radio, TV Broadcasting, Amateur Radio, Aviation',
        allocations: [
            { start: 30, end: 50, name: 'Public Safety/Government', color: '#FFD93D', service: 'Government and Public Safety' },
            { start: 50, end: 54, name: '6m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 54, end: 88, name: 'TV Channels 2-6', color: '#6BCF7F', service: 'Television Broadcasting' },
            { start: 88, end: 108, name: 'FM Radio', color: '#95E1D3', service: 'FM Broadcasting' },
            { start: 108, end: 137, name: 'Aviation Navigation', color: '#A8DADC', service: 'Aeronautical Navigation' },
            { start: 137, end: 144, name: 'Government/Space', color: '#FFD93D', service: 'Government and Space Operations' },
            { start: 144, end: 148, name: '2m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 148, end: 174, name: 'Government/Mobile', color: '#4ECDC4', service: 'Government and Mobile' },
            { start: 174, end: 216, name: 'TV Channels 7-13', color: '#6BCF7F', service: 'Television Broadcasting' },
            { start: 216, end: 220, name: 'Maritime Mobile', color: '#A8DADC', service: 'Maritime Mobile' },
            { start: 220, end: 225, name: '1.25m Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 225, end: 300, name: 'Military/Government', color: '#FFD93D', service: 'Military and Government' }
        ]
    },
    uhf: {
        name: 'UHF (Ultra High Frequency)',
        range: '300-3000 MHz',
        minFreq: 300,
        maxFreq: 3000,
        uses: 'TV Broadcasting, Mobile Phones, GPS, WiFi, Bluetooth',
        allocations: [
            { start: 300, end: 420, name: 'Military/Government', color: '#FFD93D', service: 'Military and Government' },
            { start: 420, end: 450, name: '70cm Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 450, end: 470, name: 'Land Mobile', color: '#4ECDC4', service: 'Land Mobile Radio' },
            { start: 470, end: 608, name: 'TV Channels 14-36', color: '#6BCF7F', service: 'Television Broadcasting' },
            { start: 608, end: 698, name: 'TV Channels 37-51', color: '#6BCF7F', service: 'Television Broadcasting (cleared)' },
            { start: 698, end: 806, name: 'Mobile Broadband (700 MHz)', color: '#F38BA8', service: 'Mobile Broadband' },
            { start: 806, end: 824, name: 'Public Safety', color: '#FFD93D', service: 'Public Safety' },
            { start: 824, end: 896, name: 'Cellular (800 MHz)', color: '#F38BA8', service: 'Cellular Networks' },
            { start: 896, end: 960, name: 'Cellular/Public Safety', color: '#F38BA8', service: 'Cellular and Public Safety' },
            { start: 960, end: 1215, name: 'Aviation Navigation', color: '#A8DADC', service: 'Aeronautical Navigation' },
            { start: 1215, end: 1300, name: 'GPS/GNSS', color: '#9D84B7', service: 'GPS and Navigation' },
            { start: 1300, end: 1350, name: '23cm Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 1350, end: 1710, name: 'Military/Fixed', color: '#FFD93D', service: 'Military and Fixed' },
            { start: 1710, end: 2200, name: 'Mobile Broadband (AWS/PCS)', color: '#F38BA8', service: 'Mobile Broadband' },
            { start: 2200, end: 2300, name: 'Space Operations', color: '#9D84B7', service: 'Space Operations' },
            { start: 2300, end: 2450, name: 'Amateur/Mobile', color: '#FF6B6B', service: 'Amateur and Mobile' },
            { start: 2450, end: 2500, name: 'WiFi/ISM (2.4 GHz)', color: '#95E1D3', service: 'WiFi and ISM' },
            { start: 2500, end: 2690, name: 'Mobile Broadband (2.5 GHz)', color: '#F38BA8', service: 'Mobile Broadband' },
            { start: 2690, end: 3000, name: 'Satellite/Fixed', color: '#A8DADC', service: 'Satellite and Fixed' }
        ]
    },
    shf: {
        name: 'SHF (Super High Frequency)',
        range: '3-30 GHz',
        minFreq: 3000,
        maxFreq: 30000,
        uses: 'Satellite Communications, Radar, 5G, WiFi 6',
        allocations: [
            { start: 3000, end: 3700, name: 'Satellite/Fixed', color: '#A8DADC', service: 'Satellite and Fixed' },
            { start: 3700, end: 4200, name: '5G C-Band', color: '#F38BA8', service: '5G Mobile' },
            { start: 4200, end: 5000, name: 'Satellite/Fixed', color: '#A8DADC', service: 'Satellite Communications' },
            { start: 5000, end: 5925, name: 'Aviation/Maritime', color: '#4ECDC4', service: 'Aviation and Maritime' },
            { start: 5925, end: 7125, name: 'WiFi 6 (5-6 GHz)', color: '#95E1D3', service: 'WiFi 6/6E' },
            { start: 7125, end: 10000, name: 'Satellite/Fixed', color: '#A8DADC', service: 'Satellite and Fixed' },
            { start: 10000, end: 10700, name: '3cm Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 10700, end: 12750, name: 'Satellite (Ku-band)', color: '#9D84B7', service: 'Satellite Communications' },
            { start: 12750, end: 14500, name: 'Fixed/Mobile', color: '#4ECDC4', service: 'Fixed and Mobile' },
            { start: 14500, end: 18000, name: 'Satellite (Ku-band)', color: '#9D84B7', service: 'Satellite Communications' },
            { start: 18000, end: 24000, name: 'Fixed/Mobile', color: '#4ECDC4', service: 'Fixed and Mobile' },
            { start: 24000, end: 24250, name: '1.2cm Amateur Band', color: '#FF6B6B', service: 'Amateur Radio' },
            { start: 24250, end: 27500, name: 'Satellite (Ka-band)', color: '#9D84B7', service: 'Satellite Communications' },
            { start: 27500, end: 30000, name: '5G mmWave', color: '#F38BA8', service: '5G Millimeter Wave' }
        ]
    }
};

// Application State
let currentBand = 'vhf';
let currentFrequency = 144.000;
let zoomLevel = 1.0;
let panOffset = 0;

// DOM Elements
const bandSelect = document.getElementById('band-select');
const freqInput = document.getElementById('freq-input');
const canvas = document.getElementById('band-plan-canvas');
const ctx = canvas.getContext('2d');
const allocationContent = document.getElementById('allocation-content');
const infoBand = document.getElementById('info-band');
const infoRange = document.getElementById('info-range');
const infoUses = document.getElementById('info-uses');

// Initialize the application
function init() {
    // Set up event listeners
    bandSelect.addEventListener('change', handleBandChange);
    freqInput.addEventListener('input', handleFrequencyInput);
    
    document.querySelectorAll('.tune-btn').forEach(btn => {
        btn.addEventListener('click', handleTuneButton);
    });
    
    document.getElementById('zoom-in').addEventListener('click', () => {
        zoomLevel = Math.min(zoomLevel * 1.5, 10);
        drawBandPlan();
    });
    
    document.getElementById('zoom-out').addEventListener('click', () => {
        zoomLevel = Math.max(zoomLevel / 1.5, 0.5);
        drawBandPlan();
    });
    
    document.getElementById('reset-view').addEventListener('click', () => {
        zoomLevel = 1.0;
        panOffset = 0;
        drawBandPlan();
    });
    
    canvas.addEventListener('mousemove', handleCanvasMouseMove);
    canvas.addEventListener('click', handleCanvasClick);
    
    // Initialize display
    updateBandInfo();
    updateFrequencyDisplay();
    drawBandPlan();
}

// Handle band selection change
function handleBandChange() {
    currentBand = bandSelect.value;
    const plan = bandPlans[currentBand];
    
    // Set frequency to middle of band
    currentFrequency = (plan.minFreq + plan.maxFreq) / 2;
    
    updateBandInfo();
    updateFrequencyDisplay();
    drawBandPlan();
}

// Handle frequency input
function handleFrequencyInput() {
    const value = parseFloat(freqInput.value);
    if (!isNaN(value) && value > 0) {
        currentFrequency = value;
        drawBandPlan();
    }
}

// Handle tuning buttons
function handleTuneButton(e) {
    const step = parseFloat(e.target.dataset.step);
    currentFrequency += step;
    
    // Ensure frequency stays positive
    if (currentFrequency < 0.001) {
        currentFrequency = 0.001;
    }
    
    updateFrequencyDisplay();
    drawBandPlan();
}

// Update band information display
function updateBandInfo() {
    const plan = bandPlans[currentBand];
    infoBand.textContent = plan.name;
    infoRange.textContent = plan.range;
    infoUses.textContent = plan.uses;
}

// Update frequency display
function updateFrequencyDisplay() {
    freqInput.value = currentFrequency.toFixed(3);
}

// Draw the band plan visualization
function drawBandPlan() {
    const plan = bandPlans[currentBand];
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw background
    ctx.fillStyle = '#f9f9f9';
    ctx.fillRect(0, 0, width, height);
    
    // Calculate visible frequency range based on zoom
    const totalRange = plan.maxFreq - plan.minFreq;
    const visibleRange = totalRange / zoomLevel;
    const centerFreq = currentFrequency;
    let startFreq = centerFreq - visibleRange / 2 + panOffset;
    let endFreq = centerFreq + visibleRange / 2 + panOffset;
    
    // Clamp to band limits
    if (startFreq < plan.minFreq) {
        startFreq = plan.minFreq;
        endFreq = startFreq + visibleRange;
    }
    if (endFreq > plan.maxFreq) {
        endFreq = plan.maxFreq;
        startFreq = endFreq - visibleRange;
    }
    
    // Drawing parameters
    const margin = 40;
    const chartHeight = height - 150;
    const chartTop = 80;
    
    // Helper function to convert frequency to x position
    function freqToX(freq) {
        return margin + ((freq - startFreq) / (endFreq - startFreq)) * (width - 2 * margin);
    }
    
    // Draw title
    ctx.font = 'bold 24px Arial';
    ctx.fillStyle = '#1e3c72';
    ctx.textAlign = 'center';
    ctx.fillText(`${plan.name} Band Plan`, width / 2, 40);
    
    // Draw allocations
    plan.allocations.forEach(allocation => {
        // Check if allocation is in visible range
        if (allocation.end < startFreq || allocation.start > endFreq) return;
        
        const x1 = freqToX(Math.max(allocation.start, startFreq));
        const x2 = freqToX(Math.min(allocation.end, endFreq));
        const blockWidth = x2 - x1;
        
        if (blockWidth < 1) return; // Skip if too small
        
        // Draw allocation block
        ctx.fillStyle = allocation.color;
        ctx.fillRect(x1, chartTop, blockWidth, chartHeight);
        
        // Draw border
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.strokeRect(x1, chartTop, blockWidth, chartHeight);
        
        // Draw text if block is wide enough
        if (blockWidth > 60) {
            ctx.save();
            ctx.translate(x1 + blockWidth / 2, chartTop + chartHeight / 2);
            ctx.rotate(-Math.PI / 2);
            ctx.font = 'bold 12px Arial';
            ctx.fillStyle = '#000';
            ctx.textAlign = 'center';
            ctx.fillText(allocation.name, 0, 0);
            ctx.restore();
        }
    });
    
    // Draw frequency scale
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(margin, chartTop + chartHeight);
    ctx.lineTo(width - margin, chartTop + chartHeight);
    ctx.stroke();
    
    // Draw frequency markers
    const numMarkers = 10;
    const freqStep = (endFreq - startFreq) / numMarkers;
    
    ctx.font = '12px Arial';
    ctx.fillStyle = '#333';
    ctx.textAlign = 'center';
    
    for (let i = 0; i <= numMarkers; i++) {
        const freq = startFreq + i * freqStep;
        const x = freqToX(freq);
        
        // Draw tick
        ctx.beginPath();
        ctx.moveTo(x, chartTop + chartHeight);
        ctx.lineTo(x, chartTop + chartHeight + 10);
        ctx.stroke();
        
        // Draw frequency label
        let label;
        if (freq >= 1000) {
            label = (freq / 1000).toFixed(1) + ' GHz';
        } else {
            label = freq.toFixed(1) + ' MHz';
        }
        ctx.fillText(label, x, chartTop + chartHeight + 25);
    }
    
    // Draw current frequency marker
    if (currentFrequency >= startFreq && currentFrequency <= endFreq) {
        const x = freqToX(currentFrequency);
        
        // Draw vertical line
        ctx.strokeStyle = '#ff0000';
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(x, chartTop);
        ctx.lineTo(x, chartTop + chartHeight);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Draw frequency indicator
        ctx.fillStyle = '#ff0000';
        ctx.fillRect(x - 5, chartTop - 10, 10, 10);
        
        ctx.font = 'bold 14px Arial';
        ctx.fillStyle = '#ff0000';
        ctx.textAlign = 'center';
        let currentLabel;
        if (currentFrequency >= 1000) {
            currentLabel = (currentFrequency / 1000).toFixed(3) + ' GHz';
        } else {
            currentLabel = currentFrequency.toFixed(3) + ' MHz';
        }
        ctx.fillText(currentLabel, x, chartTop - 15);
    }
    
    // Draw legend
    drawLegend();
}

// Draw legend for allocation types
function drawLegend() {
    const legendItems = [
        { color: '#FF6B6B', label: 'Amateur Radio' },
        { color: '#95E1D3', label: 'Broadcasting' },
        { color: '#4ECDC4', label: 'Mobile/Fixed' },
        { color: '#6BCF7F', label: 'Television' },
        { color: '#F38BA8', label: 'Mobile Broadband' },
        { color: '#9D84B7', label: 'Satellite/Space' },
        { color: '#FFD93D', label: 'Government/Military' },
        { color: '#A8DADC', label: 'Aviation/Maritime' }
    ];
    
    const legendX = 40;
    const legendY = canvas.height - 60;
    const itemWidth = 140;
    const itemsPerRow = Math.floor((canvas.width - 80) / itemWidth);
    
    ctx.font = '11px Arial';
    ctx.textAlign = 'left';
    
    legendItems.forEach((item, index) => {
        const row = Math.floor(index / itemsPerRow);
        const col = index % itemsPerRow;
        const x = legendX + col * itemWidth;
        const y = legendY + row * 20;
        
        // Draw color box
        ctx.fillStyle = item.color;
        ctx.fillRect(x, y - 8, 15, 12);
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y - 8, 15, 12);
        
        // Draw label
        ctx.fillStyle = '#333';
        ctx.fillText(item.label, x + 20, y);
    });
}

// Handle mouse move over canvas
function handleCanvasMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Scale for canvas resolution
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const canvasX = x * scaleX;
    const canvasY = y * scaleY;
    
    const allocation = getAllocationAtPoint(canvasX, canvasY);
    
    if (allocation) {
        canvas.style.cursor = 'pointer';
    } else {
        canvas.style.cursor = 'crosshair';
    }
}

// Handle canvas click
function handleCanvasClick(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Scale for canvas resolution
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const canvasX = x * scaleX;
    const canvasY = y * scaleY;
    
    const allocation = getAllocationAtPoint(canvasX, canvasY);
    
    if (allocation) {
        displayAllocationDetails(allocation);
    }
}

// Get allocation at a specific point
function getAllocationAtPoint(x, y) {
    const plan = bandPlans[currentBand];
    const width = canvas.width;
    const margin = 40;
    const chartHeight = canvas.height - 150;
    const chartTop = 80;
    
    // Check if y is in chart area
    if (y < chartTop || y > chartTop + chartHeight) return null;
    
    // Calculate frequency range
    const totalRange = plan.maxFreq - plan.minFreq;
    const visibleRange = totalRange / zoomLevel;
    const centerFreq = currentFrequency;
    let startFreq = centerFreq - visibleRange / 2 + panOffset;
    let endFreq = centerFreq + visibleRange / 2 + panOffset;
    
    if (startFreq < plan.minFreq) {
        startFreq = plan.minFreq;
        endFreq = startFreq + visibleRange;
    }
    if (endFreq > plan.maxFreq) {
        endFreq = plan.maxFreq;
        startFreq = endFreq - visibleRange;
    }
    
    // Calculate frequency at x position
    const freq = startFreq + ((x - margin) / (width - 2 * margin)) * (endFreq - startFreq);
    
    // Find allocation containing this frequency
    for (const allocation of plan.allocations) {
        if (freq >= allocation.start && freq <= allocation.end) {
            return allocation;
        }
    }
    
    return null;
}

// Display allocation details
function displayAllocationDetails(allocation) {
    let freqRange;
    if (allocation.start >= 1000 || allocation.end >= 1000) {
        freqRange = `${(allocation.start / 1000).toFixed(1)} - ${(allocation.end / 1000).toFixed(1)} GHz`;
    } else {
        freqRange = `${allocation.start.toFixed(1)} - ${allocation.end.toFixed(1)} MHz`;
    }
    
    const bandwidth = allocation.end - allocation.start;
    let bwString;
    if (bandwidth >= 1000) {
        bwString = `${(bandwidth / 1000).toFixed(2)} GHz`;
    } else {
        bwString = `${bandwidth.toFixed(2)} MHz`;
    }
    
    allocationContent.innerHTML = `
        <p><strong>Name:</strong> ${allocation.name}</p>
        <p><strong>Service:</strong> ${allocation.service}</p>
        <p><strong>Frequency Range:</strong> ${freqRange}</p>
        <p><strong>Bandwidth:</strong> ${bwString}</p>
    `;
}

// Initialize the application when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
