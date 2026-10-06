// Global application state
let appState = {
    metrics: null,
    alerts: [],
    products: [],
    aiRecommendations: "",
    chatHistory: [],
    currentChart: null,
    chartType: 'revenue' // 'revenue' or 'inventory'
};

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const uploadSection = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const dashboardSection = document.getElementById('dashboardSection');
const resetBtn = document.getElementById('resetBtn');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
    checkExistingState();
});

// Check if server already has analysis cached
async function checkExistingState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        if (data.loaded) {
            populateDashboard(data);
        }
    } catch (error) {
        console.error("Error checking state:", error);
    }
}

// Drag and Drop listeners
function setupDragAndDrop() {
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            handleFileUpload(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length) {
            handleFileUpload(fileInput.files[0]);
        }
    });
}

// Upload file to Backend Flask API
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    // Show Loading
    uploadSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            populateDashboard(data);
        } else {
            alert(data.error || "Failed to process the spreadsheet.");
            // Reset to upload screen
            loadingSection.classList.add('hidden');
            uploadSection.classList.remove('hidden');
        }
    } catch (error) {
        console.error("Upload error:", error);
        alert("An error occurred during file upload. Check backend console logs.");
        loadingSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
    }
}

// Populate UI components with data
function populateDashboard(data) {
    appState.metrics = data.metrics;
    appState.alerts = data.alerts;
    appState.products = data.products;
    appState.aiRecommendations = data.ai_recommendations;

    // Transition sections
    loadingSection.classList.add('hidden');
    uploadSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    resetBtn.classList.remove('hidden');

    // Fill KPI cards
    document.getElementById('kpiRevenue').textContent = formatCurrency(data.metrics.total_revenue);
    document.getElementById('kpiProfit').textContent = formatCurrency(data.metrics.total_profit);
    
    // Average margin percent
    document.getElementById('kpiMargin').textContent = `${data.metrics.avg_profit_margin.toFixed(1)}% Avg Margin`;
    document.getElementById('kpiProducts').textContent = data.metrics.total_products;
    
    // Health Info
    const healthVal = document.getElementById('kpiHealth');
    healthVal.textContent = data.metrics.health_summary;
    healthVal.className = 'kpi-value'; // reset
    if (data.metrics.health_summary === "Healthy") {
        healthVal.style.color = '#34d399'; // green
    } else if (data.metrics.health_summary === "Moderate Risk") {
        healthVal.style.color = '#fbbf24'; // amber
    } else {
        healthVal.style.color = '#f87171'; // red
    }
    document.getElementById('kpiHealthScore').textContent = `Score: ${data.metrics.health_score.toFixed(1)}/100`;

    // Fill recommendations
    document.getElementById('aiRecommendationsContent').innerHTML = parseMarkdown(data.ai_recommendations);

    // Render alerts
    renderAlertsList(data.alerts);

    // Populate database table
    populateProductsTable(data.products);

    // Draw charts
    drawCharts();
}

// Render inventory alerts list
function renderAlertsList(alerts) {
    const listContainer = document.getElementById('alertsList');
    listContainer.innerHTML = '';
    
    // Update badge count
    const badge = document.getElementById('alertsCountBadge');
    badge.textContent = alerts.length;

    if (alerts.length === 0) {
        listContainer.innerHTML = `
            <div class="message system" style="text-align: center; width: 100%; padding: 20px;">
                <p>No critical inventory alerts! Your stock is well-balanced.</p>
            </div>
        `;
        return;
    }

    alerts.forEach(alert => {
        const item = document.createElement('div');
        item.className = `alert-item alert-item-${alert.severity}`;
        
        item.innerHTML = `
            <div class="alert-msg-box">
                <span class="alert-badge badge-${alert.severity}">${alert.type}</span>
                <div class="alert-product">${alert.product}</div>
                <div class="alert-desc">${alert.message}</div>
            </div>
        `;
        listContainer.appendChild(item);
    });
}

// Populate product database table rows
function populateProductsTable(products) {
    const tbody = document.getElementById('productTableBody');
    tbody.innerHTML = '';

    products.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${p.Product_Name}</strong></td>
            <td>${p.Category}</td>
            <td>${p.Current_Stock}</td>
            <td>${p.Monthly_Sales}</td>
            <td>${formatCurrency(p.Selling_Price)}</td>
            <td>${formatCurrency(p.Cost_Price)}</td>
            <td><span style="color: ${p.Profit_Margin_Pct >= 20 ? '#34d399' : '#f87171'}">${p.Profit_Margin_Pct.toFixed(1)}%</span></td>
            <td>${p.Supplier_Delay_Days} days</td>
        `;
        tbody.appendChild(tr);
    });
}

// Trigger browser print operations report
function triggerReportPrint() {
    if (!appState.metrics) return;

    // Fill print data fields
    document.getElementById('printDate').textContent = `Report generated on: ${new Date().toLocaleDateString()}`;
    document.getElementById('printTotalProducts').textContent = appState.metrics.total_products;
    document.getElementById('printTotalRevenue').textContent = formatCurrency(appState.metrics.total_revenue);
    document.getElementById('printTotalProfit').textContent = formatCurrency(appState.metrics.total_profit);
    document.getElementById('printHealthSummary').textContent = `${appState.metrics.health_summary} (${appState.metrics.health_score.toFixed(1)}/100)`;
    
    // Add recommendations markdown parsed to HTML
    document.getElementById('printRecommendationsBody').innerHTML = parseMarkdown(appState.aiRecommendations);

    // Call browser print
    window.print();
}

// Reset application state to upload screen
async function resetApp() {
    if (!confirm("Are you sure you want to upload a new file? Current session metrics will be cleared.")) {
        return;
    }
    
    try {
        await fetch('/api/reset', { method: 'POST' });
        appState.metrics = null;
        appState.alerts = [];
        appState.products = [];
        appState.aiRecommendations = "";
        appState.chatHistory = [];
        if (appState.currentChart) {
            appState.currentChart.destroy();
            appState.currentChart = null;
        }

        // Reset UI Elements
        document.getElementById('chatMessages').innerHTML = `
            <div class="message system">
                <div class="message-text">
                    Hello! I am your operations advisor. I've finished analyzing your spreadsheet. Ask me anything, or choose a common question below:
                </div>
            </div>
        `;
        
        dashboardSection.classList.add('hidden');
        resetBtn.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        fileInput.value = '';
    } catch (error) {
        console.error("Reset error:", error);
    }
}

// Chart.js Switch logic
function switchChart(type) {
    if (appState.chartType === type) return;
    appState.chartType = type;
    
    document.getElementById('toggleRevProf').classList.toggle('active', type === 'revenue');
    document.getElementById('toggleInventory').classList.toggle('active', type === 'inventory');
    
    drawCharts();
}

function drawCharts() {
    const ctx = document.getElementById('analyticsChart').getContext('2d');
    
    // Destroy existing chart to prevent canvas glitching
    if (appState.currentChart) {
        appState.currentChart.destroy();
    }

    const labels = appState.products.map(p => p.Product_Name);
    
    if (appState.chartType === 'revenue') {
        const revenues = appState.products.map(p => p.Selling_Price * p.Monthly_Sales);
        const profits = appState.products.map(p => (p.Selling_Price - p.Cost_Price) * p.Monthly_Sales);

        appState.currentChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Monthly Revenue (₹)',
                        data: revenues,
                        backgroundColor: 'rgba(59, 130, 246, 0.65)',
                        borderColor: '#3b82f6',
                        borderWidth: 1.5,
                        borderRadius: 4
                    },
                    {
                        label: 'Monthly Profit (₹)',
                        data: profits,
                        backgroundColor: 'rgba(16, 185, 129, 0.65)',
                        borderColor: '#10b981',
                        borderWidth: 1.5,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        ticks: { color: '#94a3b8', font: { family: 'Inter' } },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y: {
                        ticks: { color: '#94a3b8', font: { family: 'Inter' } },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#f8fafc', font: { family: 'Inter', weight: '500' } }
                    }
                }
            }
        });
    } else {
        // Stock vs Demand (Monthly Sales)
        const stocks = appState.products.map(p => p.Current_Stock);
        const sales = appState.products.map(p => p.Monthly_Sales);

        appState.currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Current Stock (Units)',
                        data: stocks,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: 'Monthly Sales Volume (Units)',
                        data: sales,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        ticks: { color: '#94a3b8', font: { family: 'Inter' } },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y: {
                        ticks: { color: '#94a3b8', font: { family: 'Inter' } },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#f8fafc', font: { family: 'Inter', weight: '500' } }
                    }
                }
            }
        });
    }
}

// Details table/alerts toggle tabs
function switchDetailTab(tabName) {
    const tabAlerts = document.getElementById('tabAlerts');
    const tabDatabase = document.getElementById('tabDatabase');
    const contentAlerts = document.getElementById('tabContentAlerts');
    const contentDatabase = document.getElementById('tabContentDatabase');

    if (tabName === 'alerts') {
        tabAlerts.classList.add('active');
        tabDatabase.classList.remove('active');
        contentAlerts.classList.remove('hidden');
        contentDatabase.classList.add('hidden');
    } else {
        tabAlerts.classList.remove('active');
        tabDatabase.classList.add('active');
        contentAlerts.classList.add('hidden');
        contentDatabase.classList.remove('hidden');
    }
}

// ==========================================================================
// COPILOT CHATBOT SYSTEM
// ==========================================================================
function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function sendChatChip(text) {
    document.getElementById('chatInput').value = text;
    sendChatMessage();
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const messageText = input.value.trim();
    if (!messageText) return;

    // Clear input
    input.value = '';

    // Append user message
    appendMessage(messageText, 'user');

    // Show typing spinner in chat
    const typingBubble = showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: messageText,
                history: appState.chatHistory
            })
        });
        
        const data = await response.json();
        
        // Remove typing bubble
        typingBubble.remove();

        if (response.ok && data.reply) {
            appendMessage(data.reply, 'system');
            // Update history with both the user query and the system response
            appState.chatHistory.push({ sender: 'user', text: messageText });
            appState.chatHistory.push({ sender: 'system', text: data.reply });
        } else {
            appendMessage(data.error || "Sorry, I had trouble answering that. Please try again.", 'system');
        }
    } catch (error) {
        console.error("Chat error:", error);
        typingBubble.remove();
        appendMessage("Network error. Make sure Python server is running.", 'system');
    }
}

function appendMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    
    // Parse response markdown if system
    const formattedText = sender === 'system' ? parseMarkdown(text) : escapeHtml(text);
    
    msgDiv.innerHTML = `<div class="message-text">${formattedText}</div>`;
    chatMessages.appendChild(msgDiv);
    
    // Scroll chat to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message system';
    msgDiv.innerHTML = `
        <div class="message-text">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
}

// Utility formatting functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 2
    }).format(value);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Simple regex-based Markdown Parser
function parseMarkdown(text) {
    if (!text) return "";
    
    let html = text.trim();
    
    // 1. Double line break to paragraphs, single line break to <br>
    // We should preserve headers and lists, so let's parse block components line by line.
    const lines = html.split('\n');
    let inList = false;
    let listType = null; // 'ul' or 'ol'
    let output = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Skip completely empty lines
        if (line === '') {
            if (inList) {
                output.push(`</${listType}>`);
                inList = false;
                listType = null;
            }
            continue;
        }

        // Check if Alert Box block
        if (line.startsWith('>')) {
            if (inList) {
                output.push(`</${listType}>`);
                inList = false;
                listType = null;
            }
            let alertContent = line.replace(/^>\s*/, '');
            // Handle alert types: [!NOTE], [!WARNING], etc.
            const alertMatch = alertContent.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/);
            if (alertMatch) {
                const alertType = alertMatch[1].toLowerCase();
                let alertBody = alertContent.replace(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/, '');
                // Peek next lines to grab multi-line blockquotes
                while(i + 1 < lines.length && lines[i+1].trim().startsWith('>')) {
                    i++;
                    alertBody += ' ' + lines[i].trim().replace(/^>\s*/, '');
                }
                output.push(`<blockquote class="alert-box alert-${alertType}"><strong>${alertMatch[1]}:</strong> ${inlineMarkdown(alertBody)}</blockquote>`);
            } else {
                output.push(`<blockquote>${inlineMarkdown(alertContent)}</blockquote>`);
            }
            continue;
        }

        // Headings
        if (line.startsWith('### ')) {
            if (inList) { output.push(`</${listType}>`); inList = false; listType = null; }
            output.push(`<h3>${inlineMarkdown(line.slice(4))}</h3>`);
            continue;
        }
        if (line.startsWith('## ')) {
            if (inList) { output.push(`</${listType}>`); inList = false; listType = null; }
            output.push(`<h2>${inlineMarkdown(line.slice(3))}</h2>`);
            continue;
        }
        if (line.startsWith('# ')) {
            if (inList) { output.push(`</${listType}>`); inList = false; listType = null; }
            output.push(`<h1>${inlineMarkdown(line.slice(2))}</h1>`);
            continue;
        }

        // Bullet lists
        const isBullet = line.startsWith('- ') || line.startsWith('* ');
        const isChecklist = line.startsWith('- [ ] ') || line.startsWith('- [x] ') || line.startsWith('* [ ] ') || line.startsWith('* [x] ');
        
        if (isChecklist) {
            if (!inList || listType !== 'ul') {
                if (inList) output.push(`</${listType}>`);
                output.push('<ul style="list-style-type: none; padding-left: 5px;">');
                inList = true;
                listType = 'ul';
            }
            const checked = line.includes('[x]');
            const itemText = line.replace(/^[\-\*]\s*\[[ x]\]\s*/, '');
            output.push(`<li><input type="checkbox" ${checked ? 'checked' : ''} disabled style="margin-right: 8px;"> ${inlineMarkdown(itemText)}</li>`);
            continue;
        }

        if (isBullet) {
            if (!inList || listType !== 'ul') {
                if (inList) output.push(`</${listType}>`);
                output.push('<ul>');
                inList = true;
                listType = 'ul';
            }
            output.push(`<li>${inlineMarkdown(line.slice(2))}</li>`);
            continue;
        }

        // Standard Paragraphs (default)
        if (inList) {
            output.push(`</${listType}>`);
            inList = false;
            listType = null;
        }
        output.push(`<p>${inlineMarkdown(line)}</p>`);
    }

    if (inList) {
        output.push(`</${listType}>`);
    }

    return output.join('\n');
}

// Inline formatting (bold, links)
function inlineMarkdown(text) {
    let clean = escapeHtml(text);
    // Replace **bold** with <strong>bold</strong>
    clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Replace *italic* with <em>italic</em>
    clean = clean.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return clean;
}

// Download local sample csv
function downloadSampleCSV(e) {
    // Prevent default route transition, serve local raw content
    e.preventDefault();
    const csvContent = `Product_Name,Category,Current_Stock,Monthly_Sales,Cost_Price,Selling_Price,Supplier_Delay_Days,Customer_Rating
Cooking Oil,Groceries,5,45,8.00,12.00,7,4.5
Basmati Rice,Groceries,50,60,15.00,20.00,3,4.8
Whole Wheat Flour,Groceries,120,20,6.00,9.50,4,4.2
Detergent Powder,Household,2,30,5.50,9.00,10,4.0
Organic Honey,Groceries,15,3,12.00,18.00,5,4.9
Potato Chips,Snacks,80,150,1.00,2.50,2,4.3
Milk Carton,Dairy,8,200,1.20,2.00,1,4.7
Tomato Ketchup,Groceries,25,30,2.50,4.00,4,4.4
Chocolate Bars,Snacks,95,10,1.50,3.00,3,4.6
Olive Oil,Groceries,12,5,20.00,35.00,8,4.8
Liquid Handwash,Household,4,40,2.00,4.50,6,4.1
Greek Yogurt,Dairy,3,60,1.50,3.00,2,4.6
Soap Bars,Household,60,80,0.80,1.80,3,4.3
Green Tea Pack,Beverages,35,12,4.00,7.50,5,4.5
Instant Coffee,Beverages,8,50,5.00,9.00,6,4.7`;

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "MSME_sample_data.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
