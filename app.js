// ==========================================================================
// iPhone Comparison Dashboard Engine - Vanilla JS Application
// ==========================================================================

let allProducts = [];
let filteredProducts = [];
let selectedCompareIds = new Set();
let priceByYearChart = null;
let storeStockChart = null;

// Store Image Fallback map
const STORE_LOGOS = {
    'Celltronics': 'https://celltronics.lk/wp-content/uploads/2021/04/Celltronics-Logo.png',
    'Greenware': 'https://www.greenware.lk/wp-content/uploads/2021/03/greenware-logo.png',
    'LuxuryX': 'https://luxuryx.lk/wp-content/uploads/2021/08/luxuryx_logo.png',
    'ONEi': 'https://onei.lk/cdn/shop/files/onei_logo.png',
    'Rooter': 'https://rooter.lk/cdn/shop/files/rooter_logo.png'
};

const DEFAULT_IPHONE_IMG = 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-1inch-naturaltitanium?wid=512&hei=512&fmt=p-jpeg';

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await loadData();
}

async function loadData() {
    try {
        try {
            const response = await fetch('data/iphones.json');
            if (response.ok) {
                allProducts = await response.json();
            } else if (window.IPHONE_DATA) {
                allProducts = window.IPHONE_DATA;
            } else {
                throw new Error('Failed to load JSON data');
            }
        } catch (fetchErr) {
            if (window.IPHONE_DATA) {
                console.log('Loaded dataset via window.IPHONE_DATA fallback (file:// protocol mode)');
                allProducts = window.IPHONE_DATA;
            } else {
                throw fetchErr;
            }
        }

        // Calculate best deals
        computeBestDeals();

        filteredProducts = [...allProducts];

        updateStatsBanner();
        renderGridView();
        renderMatrixView();
        renderAnalyticsCharts();
    } catch (err) {
        console.error('Error loading data:', err);
        document.getElementById('productGridContainer').innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: #f43f5e;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <h3>Unable to load dataset</h3>
                <p>${err.message}</p>
            </div>
        `;
    }
}

// Compute lowest price per model to tag "BEST DEAL"
function computeBestDeals() {
    const minPrices = {};

    allProducts.forEach(p => {
        // Normalize model key (e.g. "iphone 16 pro max 256gb")
        const normKey = p.title.toLowerCase()
            .replace(/apple\s*/g, '')
            .replace(/\(.*?\)/g, '')
            .replace(/\s+/g, ' ')
            .strip ? p.title.toLowerCase().strip() : p.title.toLowerCase().trim();

        if (p.price > 0) {
            if (!minPrices[normKey] || p.price < minPrices[normKey]) {
                minPrices[normKey] = p.price;
            }
        }
    });

    allProducts.forEach(p => {
        const normKey = p.title.toLowerCase()
            .replace(/apple\s*/g, '')
            .replace(/\(.*?\)/g, '')
            .replace(/\s+/g, ' ')
            .trim();

        p.isBestDeal = p.price > 0 && minPrices[normKey] && p.price <= minPrices[normKey];
    });
}

function updateStatsBanner() {
    const totalCount = allProducts.length;
    const lowest = Math.min(...allProducts.filter(p => p.price > 0).map(p => p.price));
    const inStockCount = allProducts.filter(p => p.in_stock).length;

    document.getElementById('statTotalProducts').textContent = totalCount;
    document.getElementById('statLowestPrice').textContent = `LKR ${lowest.toLocaleString()}`;
    document.getElementById('statInStockCount').textContent = `${inStockCount} Models`;
}

function extractStorage(title) {
    const match = title.match(/\b(64GB|128GB|256GB|512GB|1TB)\b/i);
    return match ? match[1].toUpperCase() : null;
}

function matchesColor(title, targetColor) {
    if (targetColor === 'all') return true;
    const t = title.toLowerCase();
    if (targetColor === 'Black') return t.includes('black') || t.includes('space gray') || t.includes('midnight');
    if (targetColor === 'White') return t.includes('white') || t.includes('silver') || t.includes('starlight');
    if (targetColor === 'Titanium') return t.includes('titanium') || t.includes('desert') || t.includes('natural');
    if (targetColor === 'Blue') return t.includes('blue') || t.includes('ultramarine') || t.includes('pacific');
    if (targetColor === 'Pink') return t.includes('pink') || t.includes('rose');
    if (targetColor === 'Green') return t.includes('green') || t.includes('teal');
    if (targetColor === 'Yellow') return t.includes('yellow') || t.includes('gold');
    return true;
}

function getCheckedValues(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    const checked = container.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checked).map(cb => cb.value);
}

function uncheckAllInContainer(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
}

function updateSelectAllState(containerId) {
    const selectAllCb = document.querySelector(`.select-all-cb[data-target="${containerId}"]`);
    if (!selectAllCb) return;
    const container = document.getElementById(containerId);
    if (!container) return;
    const cbs = container.querySelectorAll('input[type="checkbox"]');
    const checkedCbs = container.querySelectorAll('input[type="checkbox"]:checked');
    selectAllCb.checked = (cbs.length > 0 && checkedCbs.length === cbs.length);
}

// Setup Event Listeners
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            if (clearBtn) clearBtn.style.display = e.target.value ? 'block' : 'none';
            applyFilters();
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            clearBtn.style.display = 'none';
            applyFilters();
        });
    }

    // Theme Toggle
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            themeBtn.innerHTML = newTheme === 'light' ? '<i class="fa-solid fa-moon"></i> Dark Theme' : '<i class="fa-solid fa-sun"></i> Light Theme';
            renderAnalyticsCharts();
        });
    }

    // Price Range Slider
    const priceSlider = document.getElementById('priceRangeInput');
    const priceDisplay = document.getElementById('priceRangeValue');
    if (priceSlider && priceDisplay) {
        priceSlider.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            priceDisplay.textContent = `LKR ${val.toLocaleString()}`;
            applyFilters();
        });
    }

    // Checklist & Select All listeners
    document.querySelectorAll('.select-all-cb').forEach(selectAllCb => {
        selectAllCb.addEventListener('change', (e) => {
            const targetId = e.target.dataset.target;
            const container = document.getElementById(targetId);
            if (container) {
                container.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.checked = e.target.checked;
                });
                applyFilters();
            }
        });
    });

    ['storeChecklist', 'yearChecklist', 'storageChecklist', 'colorChecklist', 'stockChecklist'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', (e) => {
                updateSelectAllState(id);
                applyFilters();
            });
        }
    });

    document.getElementById('sortSelect').addEventListener('change', applyFilters);
    document.getElementById('bestDealsOnlyCheckbox').addEventListener('change', applyFilters);

    document.getElementById('resetFiltersBtn').addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        if (clearBtn) clearBtn.style.display = 'none';
        ['storeChecklist', 'yearChecklist', 'storageChecklist', 'colorChecklist', 'stockChecklist'].forEach(uncheckAllInContainer);
        document.querySelectorAll('.select-all-cb').forEach(cb => cb.checked = false);
        document.getElementById('sortSelect').value = 'price_asc';
        document.getElementById('bestDealsOnlyCheckbox').checked = false;
        if (priceSlider && priceDisplay) {
            priceSlider.value = 700000;
            priceDisplay.textContent = 'LKR 700,000';
        }
        applyFilters();
    });

    // View Switcher Tabs
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const targetView = tab.dataset.view;
            document.querySelectorAll('.view-content').forEach(v => v.classList.remove('active'));
            document.getElementById(`${targetView}View`).classList.add('active');
        });
    });

    // Compare Tray Click
    document.getElementById('compareTrayTrigger').addEventListener('click', openCompareModal);
    document.getElementById('closeModalBtn').addEventListener('click', closeCompareModal);

    // Refresh Data button
    document.getElementById('rescrapeBtn').addEventListener('click', async () => {
        const btn = document.getElementById('rescrapeBtn');
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Refreshing...`;
        await loadData();
        btn.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Refresh Data`;
    });
}

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
    const selectedStores = getCheckedValues('storeChecklist');
    const selectedYears = getCheckedValues('yearChecklist');
    const selectedStorages = getCheckedValues('storageChecklist');
    const selectedColors = getCheckedValues('colorChecklist');
    const selectedStocks = getCheckedValues('stockChecklist');
    const sortBy = document.getElementById('sortSelect').value;
    const bestDealsOnly = document.getElementById('bestDealsOnlyCheckbox').checked;
    const priceSlider = document.getElementById('priceRangeInput');
    const maxPrice = priceSlider ? parseInt(priceSlider.value) : Infinity;

    filteredProducts = allProducts.filter(p => {
        // Price filter
        if (p.price > 0 && p.price > maxPrice) return false;

        // Search filter
        if (searchTerm && !p.title.toLowerCase().includes(searchTerm)) return false;

        // Store filter (Multi-select)
        if (selectedStores.length > 0 && !selectedStores.includes(p.store)) return false;

        // Year filter (Multi-select)
        if (selectedYears.length > 0 && !selectedYears.includes(p.year.toString())) return false;

        // Storage filter (Multi-select)
        if (selectedStorages.length > 0) {
            const itemStorage = extractStorage(p.title);
            if (!itemStorage || !selectedStorages.includes(itemStorage)) return false;
        }

        // Color filter (Multi-select)
        if (selectedColors.length > 0) {
            const match = selectedColors.some(c => matchesColor(p.title, c));
            if (!match) return false;
        }

        // Stock filter (Multi-select)
        if (selectedStocks.length > 0) {
            const isStockMatch = selectedStocks.some(s => {
                if (s === 'in_stock' && p.in_stock) return true;
                if (s === 'out_stock' && !p.in_stock) return true;
                return false;
            });
            if (!isStockMatch) return false;
        }

        // Best deals filter
        if (bestDealsOnly && !p.isBestDeal) return false;

        return true;
    });

    // Render active filter chips
    renderActiveFilterTags(searchTerm, selectedStores, selectedYears, selectedStorages, selectedColors, selectedStocks, maxPrice, bestDealsOnly);

    // Sort logic
    filteredProducts.sort((a, b) => {
        if (sortBy === 'price_asc') return a.price - b.price;
        if (sortBy === 'price_desc') return b.price - a.price;
        if (sortBy === 'year_desc') return b.year - a.year;
        if (sortBy === 'title_asc') return a.title.localeCompare(b.title);
        return 0;
    });

    renderGridView();
}

function renderActiveFilterTags(searchTerm, stores, years, storages, colors, stocks, maxPrice, bestDeals) {
    const container = document.getElementById('activeFilterTagsContainer');
    const tagsList = document.getElementById('tagsList');
    if (!container || !tagsList) return;

    const tags = [];
    if (searchTerm) tags.push({ label: `"${searchTerm}"`, clear: () => { document.getElementById('searchInput').value = ''; } });
    
    stores.forEach(s => tags.push({ label: `Store: ${s}`, clear: () => uncheckSpecificValue('storeChecklist', s) }));
    years.forEach(y => tags.push({ label: `Year: ${y}`, clear: () => uncheckSpecificValue('yearChecklist', y) }));
    storages.forEach(st => tags.push({ label: `Storage: ${st}`, clear: () => uncheckSpecificValue('storageChecklist', st) }));
    colors.forEach(c => tags.push({ label: `Color: ${c}`, clear: () => uncheckSpecificValue('colorChecklist', c) }));
    stocks.forEach(stk => tags.push({ label: `Status: ${stk === 'in_stock' ? 'In Stock' : 'Out of Stock'}`, clear: () => uncheckSpecificValue('stockChecklist', stk) }));

    if (maxPrice < 700000) tags.push({ label: `Max Price: LKR ${maxPrice.toLocaleString()}`, clear: () => { document.getElementById('priceRangeInput').value = 700000; document.getElementById('priceRangeValue').textContent = 'LKR 700,000'; } });
    if (bestDeals) tags.push({ label: `Best Deals Only`, clear: () => { document.getElementById('bestDealsOnlyCheckbox').checked = false; } });

    if (tags.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';
    tagsList.innerHTML = tags.map((t, idx) => `
        <span class="active-tag-chip">
            ${t.label}
            <i class="fa-solid fa-xmark" onclick="removeFilterTag(${idx})"></i>
        </span>
    `).join('');

    window.activeFilterClears = tags.map(t => t.clear);
}

function uncheckSpecificValue(containerId, val) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const cb = container.querySelector(`input[type="checkbox"][value="${val}"]`);
    if (cb) cb.checked = false;
}

// Render Grid View Cards
function renderGridView() {
    const container = document.getElementById('productGridContainer');
    const resultsCount = document.getElementById('resultsCount');

    resultsCount.textContent = `Showing ${filteredProducts.length} of ${allProducts.length} products`;

    if (filteredProducts.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
                <i class="fa-solid fa-magnifying-glass" style="font-size: 2.5rem; margin-bottom: 1rem;"></i>
                <h3>No matching iPhones found</h3>
                <p>Try resetting filters or searching with a different term.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filteredProducts.map(p => {
        const isSelected = selectedCompareIds.has(p.id);
        const storeClass = p.store.toLowerCase().replace(/[^a-z]/g, '');
        const imageSrc = (p.image && !p.image.includes('lazy.svg')) ? p.image : DEFAULT_IPHONE_IMG;

        return `
            <div class="card-product ${p.isBestDeal ? 'is-best-deal' : ''}">
                ${p.isBestDeal ? '<div class="best-deal-ribbon"><i class="fa-solid fa-bolt"></i> Best Price</div>' : ''}
                
                <div class="card-image-area">
                    <img src="${imageSrc}" alt="${p.title}" onerror="this.onerror=null; this.src='${DEFAULT_IPHONE_IMG}';">
                </div>

                <div class="card-header-meta">
                    <span class="badge-store ${storeClass}">${p.store_badge}</span>
                    <span class="badge-year"><i class="fa-regular fa-calendar-days"></i> ${p.year}</span>
                </div>

                <h3 class="card-title" title="${p.title}">${p.title}</h3>

                <div class="card-stock-row ${p.in_stock ? 'stock-in' : 'stock-out'}">
                    <span class="stock-dot"></span>
                    <span>${p.stock_status}</span>
                </div>

                <div class="card-footer">
                    <div class="price-display">${p.price_formatted}</div>
                    
                    <div class="card-actions-row">
                        <a href="${p.url}" target="_blank" rel="noopener" class="btn btn-buy">
                            Store Link <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        </a>
                        <button class="btn-compare-check ${isSelected ? 'selected' : ''}" 
                                onclick="toggleCompareItem('${p.id}')" 
                                title="${isSelected ? 'Remove from compare' : 'Add to compare'}">
                            <i class="fa-solid ${isSelected ? 'fa-check' : 'fa-plus'}"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Toggle Compare Selection
function toggleCompareItem(id) {
    if (selectedCompareIds.has(id)) {
        selectedCompareIds.delete(id);
    } else {
        if (selectedCompareIds.size >= 4) {
            alert('You can compare up to 4 products at a time.');
            return;
        }
        selectedCompareIds.add(id);
    }

    updateCompareTray();
    renderGridView();
}

function updateCompareTray() {
    const trigger = document.getElementById('compareTrayTrigger');
    const countBadge = document.getElementById('compareCount');

    countBadge.textContent = selectedCompareIds.size;
    trigger.style.display = selectedCompareIds.size > 0 ? 'flex' : 'none';
}

function openCompareModal() {
    const modal = document.getElementById('compareModal');
    const body = document.getElementById('modalCompareBody');

    const selectedItems = allProducts.filter(p => selectedCompareIds.has(p.id));

    if (selectedItems.length === 0) return;

    body.innerHTML = selectedItems.map(p => `
        <div class="card-product">
            <div class="card-header-meta">
                <span class="badge-store ${p.store.toLowerCase()}">${p.store}</span>
                <span class="badge-year">${p.year}</span>
            </div>
            <h3 class="card-title">${p.title}</h3>
            <div class="price-display" style="color: var(--accent-emerald); margin: 1rem 0;">${p.price_formatted}</div>
            <div class="card-stock-row ${p.in_stock ? 'stock-in' : 'stock-out'}">
                <span class="stock-dot"></span> ${p.stock_status}
            </div>
            <a href="${p.url}" target="_blank" class="btn btn-primary" style="margin-top: 1rem; width: 100%; justify-content: center;">
                Go to ${p.store}
            </a>
        </div>
    `).join('');

    modal.classList.add('active');
}

function closeCompareModal() {
    document.getElementById('compareModal').classList.remove('active');
}

// Render Side-by-Side Comparison Matrix Table
function renderMatrixView() {
    const tbody = document.getElementById('matrixTableBody');

    // Group products by canonical model family
    const grouped = {};
    allProducts.forEach(p => {
        let key = p.title
            .replace(/apple\s*/i, '')
            .replace(/\s+/g, ' ')
            .trim();

        if (!grouped[key]) {
            grouped[key] = {
                model: key,
                year: p.year,
                stores: {}
            };
        }
        // Save price under store
        if (!grouped[key].stores[p.store] || p.price < grouped[key].stores[p.store].price) {
            grouped[key].stores[p.store] = p;
        }
    });

    const rows = Object.values(grouped);
    // Sort rows by year desc, then model name
    rows.sort((a, b) => b.year - a.year || a.model.localeCompare(b.model));

    const stores = ['Greenware', 'LuxuryX', 'Rooter', 'ONEi', 'Celltronics'];

    tbody.innerHTML = rows.slice(0, 40).map(r => {
        // Find lowest price among stores present for this model
        let lowestPrice = Infinity;
        stores.forEach(s => {
            if (r.stores[s] && r.stores[s].price > 0 && r.stores[s].price < lowestPrice) {
                lowestPrice = r.stores[s].price;
            }
        });

        const storeCells = stores.map(s => {
            const item = r.stores[s];
            if (!item) return `<td class="cell-na">-</td>`;

            const isLowest = item.price === lowestPrice;
            return `
                <td>
                    <span class="cell-price ${isLowest ? 'lowest' : ''}">
                        ${item.price_formatted}
                    </span>
                </td>
            `;
        }).join('');

        // Determine best price store name
        let bestStore = 'N/A';
        stores.forEach(s => {
            if (r.stores[s] && r.stores[s].price === lowestPrice) {
                bestStore = s;
            }
        });

        return `
            <tr>
                <td class="cell-model-name">${r.model}</td>
                <td><span class="badge-year">${r.year}</span></td>
                ${storeCells}
                <td><strong style="color: var(--accent-emerald);">${bestStore}</strong></td>
            </tr>
        `;
    }).join('');
}

// Render Chart Analytics
function renderAnalyticsCharts() {
    const yearAvg = {};
    const yearCounts = {};

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#f5f5f7' : '#1d1d1f';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';

    allProducts.forEach(p => {
        if (p.price > 0) {
            yearAvg[p.year] = (yearAvg[p.year] || 0) + p.price;
            yearCounts[p.year] = (yearCounts[p.year] || 0) + 1;
        }
    });

    const years = Object.keys(yearAvg).sort((a, b) => a - b);
    const avgPrices = years.map(y => Math.round(yearAvg[y] / yearCounts[y]));

    // Chart 1: Avg Price by Year
    const ctx1 = document.getElementById('priceByYearChart').getContext('2d');
    if (priceByYearChart) priceByYearChart.destroy();
    priceByYearChart = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: years.map(y => `iPhone ${y}`),
            datasets: [{
                label: 'Average Price (LKR)',
                data: avgPrices,
                backgroundColor: 'rgba(0, 113, 227, 0.65)',
                borderColor: '#0071e3',
                borderWidth: 1.5,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                },
                x: {
                    ticks: { color: textColor },
                    grid: { display: false }
                }
            }
        }
    });

    // Chart 2: Store breakdown
    const storeCounts = {};
    allProducts.forEach(p => {
        storeCounts[p.store] = (storeCounts[p.store] || 0) + 1;
    });

    const storeNames = Object.keys(storeCounts);
    const storeData = storeNames.map(s => storeCounts[s]);

    const ctx2 = document.getElementById('storeStockChart').getContext('2d');
    if (storeStockChart) storeStockChart.destroy();
    storeStockChart = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: storeNames,
            datasets: [{
                data: storeData,
                backgroundColor: [
                    '#ec4899', // Celltronics
                    '#10b981', // Greenware
                    '#f59e0b', // LuxuryX
                    '#8b5cf6', // ONEi
                    '#06b6d4'  // Rooter
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: textColor, padding: 15, font: { family: 'Plus Jakarta Sans', weight: '600' } }
                }
            }
        }
    });
}
