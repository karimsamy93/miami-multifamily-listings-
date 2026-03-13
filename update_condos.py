import re

with open("condos.html", "r") as f:
    orig = f.read()

# Replace fonts
orig = orig.replace("family=DM+Sans", "family=Inter")
orig = orig.replace("font-family: 'DM Sans'", "font-family: 'Inter'")

js_new = """    const DISPLAY_COLUMNS = [
      'Rank', 'Address', 'Beds/Baths', 'List Price', 'Est. Rent/mo',
      '1% Ratio', 'Monthly Cash Flow', 'CoC Return', ''
    ];

    const NUMERIC_COLUMNS = [
      'Rank', 'List Price', 'Est. Rent/mo',
      '1% Ratio', 'Monthly Cash Flow', 'CoC Return'
    ];

    let rawData = [];
    let filteredData = [];
    let currentSort = { column: 'Rank', direction: 'asc' };

    async function init() {
      try {
        const res = await fetch(SHEET_CSV_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const text = await res.text();
        rawData = parseCSV(text);
        if (!rawData.length) throw new Error('No data found in sheet.');

        rawData.forEach((row, i) => {
          if (!row['Rank']) row['_calc_rank'] = i + 1;
        });

        populateCityFilter();
        updateStats();
        setLastUpdated();

        filteredData = [...rawData];
        sortData();
        renderHeaders();
        renderTable();

        document.getElementById('loading').style.display = 'none';
        document.getElementById('app').style.display = 'block';
        setupListeners();

      } catch (err) {
        document.getElementById('loading').innerHTML =
          '<div class="error-box"><strong>Could not load listings.</strong><br>Check the CSV URL or try again later.<br><small style="opacity:0.7">' + err.message + '</small></div>';
      }
    }

    function setLastUpdated() {
      const el = document.getElementById('last-updated');
      const sample = rawData[0] || {};
      const dateVal = sample['Last Updated'] || sample['last_updated'] || sample['LastUpdated'];
      if (dateVal) {
        el.textContent = 'Last updated: ' + dateVal;
      } else {
        el.textContent = 'Last updated: Current issue';
      }
    }

    function updateStats() {
      document.getElementById('stat-total').textContent = rawData.length;
      const cities = new Set(rawData.map(r => r['City'] || r['Location'] || r['ZIP'] || r['Zip'] || r['County'] || '').filter(Boolean));
      document.getElementById('stat-cities').textContent = cities.size;
      const prices = rawData.map(r => parseNumber(r['List Price'])).filter(n => !isNaN(n));
      if (prices.length) {
        const avg = prices.reduce((a,b) => a+b, 0) / prices.length;
        document.getElementById('stat-avg-price').textContent = '$' + Math.round(avg / 1000) + 'K';
      }
    }

    function setupListeners() {
      ['search','city','beds','min-ratio'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.addEventListener('input', applyFilters);
          el.addEventListener('change', applyFilters);
        }
      });
    }

    function populateCityFilter() {
      const sel = document.getElementById('city');
      const cities = new Set();
      rawData.forEach(r => {
        const loc = r['City'] || r['Location'] || r['ZIP'] || r['Zip'] || r['County'] || '';
        if (loc) cities.add(loc.trim());
      });
      Array.from(cities).sort().forEach(city => {
        const opt = document.createElement('option');
        opt.value = city; opt.textContent = city;
        sel.appendChild(opt);
      });
    }

    function applyFilters() {
      const q        = document.getElementById('search').value.toLowerCase().trim();
      const city     = document.getElementById('city').value;
      const beds     = document.getElementById('beds').value;
      
      const minRatioEl = document.getElementById('min-ratio');
      const minRatio = minRatioEl ? (parseFloat(minRatioEl.value) || 0) : 0;

      filteredData = rawData.filter(row => {
        const loc = row['City'] || row['Location'] || row['ZIP'] || row['Zip'] || row['County'] || '';

        if (q) {
          const addr = (row['Address'] || '').toLowerCase();
          const mls  = (row['MLS ID'] || row['MLS #'] || '').toLowerCase();
          if (!addr.includes(q) && !mls.includes(q)) return false;
        }
        if (city && loc.trim() !== city) return false;
        if (beds) {
          const bb = row['Beds/Baths'] || row['Beds'] || '';
          const bMatch = String(bb).match(/(\d+)/);
          const bNum = bMatch ? parseInt(bMatch[1]) : 0;
          if (beds === '4+') {
            if (bNum < 4) return false;
          } else {
            if (bNum !== parseInt(beds)) return false;
          }
        }
        if (minRatio > 0) {
          let r = parseNumber(row['1% Ratio']);
          if (!String(row['1% Ratio'] || '').includes('%') && r < 0.2) r *= 100;
          if (r < minRatio) return false;
        }
        return true;
      });

      sortData(); renderHeaders(); renderTable();
      const rc = document.getElementById('result-count');
      rc.innerHTML = `Showing <strong>${filteredData.length}</strong> of ${rawData.length} listings`;
    }

    function sortData() {
      const col = currentSort.column;
      const dir = currentSort.direction === 'asc' ? 1 : -1;
      const num = NUMERIC_COLUMNS.includes(col);
      filteredData.sort((a, b) => {
        let vA = getVal(a, col), vB = getVal(b, col);
        if (num) {
          let nA = parseNumber(vA), nB = parseNumber(vB);
          if (isNaN(nA)) nA = dir > 0 ? Infinity : -Infinity;
          if (isNaN(nB)) nB = dir > 0 ? Infinity : -Infinity;
          return (nA - nB) * dir;
        }
        return String(vA).localeCompare(String(vB)) * dir;
      });
    }

    function getVal(row, col) {
      if (col === 'Address')          return row['Address'] || '';
      if (col === 'Beds/Baths')       return row['Beds/Baths'] || (row['Beds'] ? `${row['Beds']}/${row['Baths'] || '?'}` : '');
      if (col === 'List Price')       return row['List Price'] || row['Price ($)'] || '';
      if (col === 'Est. Rent/mo')     return row['Est. Rent/mo'] || row['Est Rent/mo'] || row['Est. Monthly Rent'] || row['Est. Rent ($/mo)'] || '';
      if (col === '1% Ratio')         return row['1% Ratio'] || '';
      if (col === 'Monthly Cash Flow')return row['Monthly Cash Flow'] || row['Monthly CF'] || row['Net Cash Flow ($/mo)'] || '';
      if (col === 'CoC Return')       return row['CoC Return'] || row['Cash on Cash'] || '';
      if (col === 'Rank')             return row['Rank'] || row['_calc_rank'] || '';
      return row[col] || '';
    }

    function handleSort(col) {
      if (col === '') return;
      if (currentSort.column === col) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
      } else {
        currentSort.column = col;
        currentSort.direction = col === 'List Price' ? 'asc' : 'desc';
      }
      sortData(); renderHeaders(); renderTable();
    }

    function renderHeaders() {
      const thead = document.getElementById('table-head');
      thead.innerHTML = '';
      const tr = document.createElement('tr');
      DISPLAY_COLUMNS.forEach(col => {
        const th = document.createElement('th');
        if (col === '') {
          tr.appendChild(th);
          return;
        }
        if (col === 'Beds/Baths') th.className = 'hide-mobile';
        
        th.onclick = () => handleSort(col);
        const isSorted = currentSort.column === col;
        if (isSorted) th.classList.add('sorted');
        const arrow = isSorted
          ? `<span class="sort-arrow">${currentSort.direction === 'asc' ? '↑' : '↓'}</span>`
          : `<span class="sort-arrow" style="opacity:0.25">↕</span>`;
        th.innerHTML = col + arrow;
        tr.appendChild(th);
      });
      thead.appendChild(tr);
    }

    function renderTable() {
      const tbody = document.getElementById('table-body');
      tbody.innerHTML = '';

      if (!filteredData.length) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="${DISPLAY_COLUMNS.length}" style="text-align:center;padding:3rem;color:var(--text-muted)">No listings match your filters.</td>`;
        tbody.appendChild(tr);
        return;
      }

      let altCount = 0;
      filteredData.forEach((row, index) => {
        const tr = document.createElement('tr');
        tr.className = 'main-row ' + (altCount++ % 2 === 0 ? 'row-norm' : 'row-alt');
        
        const rank = parseNumber(row['Rank'] || row['_calc_rank']);
        const isTop3 = rank >= 1 && rank <= 3;
        if (isTop3) tr.classList.add('row-top3');

        DISPLAY_COLUMNS.forEach(col => {
          const td = document.createElement('td');
          if (col === '') {
            td.className = 'chevron-cell';
            td.innerHTML = '▸';
            tr.appendChild(td);
            return;
          }
          if (col === 'Beds/Baths') td.className = 'hide-mobile';

          let val = getVal(row, col);

          switch (col) {
            case 'Rank':
              td.innerHTML = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank;
              break;
            case 'Address':
              td.className = 'address-cell';
              td.textContent = val;
              break;
            case 'List Price':
              td.textContent = fmtPrice(val);
              break;
            case 'Est. Rent/mo':
              td.textContent = fmtRent(val);
              break;
            case '1% Ratio': {
              const num = parseRatio(val);
              const cls = num >= 1.0 ? 'ratio-pass' : num >= 0.9 ? 'ratio-close' : 'ratio-miss';
              td.innerHTML = `<span class="ratio-pill ${cls}">${isNaN(num) ? '—' : num.toFixed(2) + '%'}</span>`;
              break;
            }
            case 'Monthly Cash Flow':
              td.innerHTML = fmtCashFlow(val);
              break;
            case 'CoC Return':
              td.innerHTML = fmtCoC(val);
              break;
            default:
              td.textContent = val || '—';
          }
          tr.appendChild(td);
        });

        const detailTr = document.createElement('tr');
        detailTr.className = 'detail-row';
        
        const zip = row['ZIP'] || row['Zip'] || '—';
        const priceNum = parseNumber(getVal(row, 'List Price'));
        const dp = !isNaN(priceNum) ? fmtPrice(priceNum * 0.25) : '—';
        
        const hoaRaw = row['HOA Fee/mo'] || row['HOA/mo'] || row['HOA'] || '';
        const hoa = parseNumber(hoaRaw);
        const hoaStr = isNaN(hoa) ? '—' : '$' + hoa.toLocaleString('en-US', {maximumFractionDigits:0}) + '/mo';
        const hoaCls = hoa > 1000 ? 'hoa-high' : '';

        const score = row['Score'] || row['Total Score'] || '—';
        const lastUpd = row['Last Updated'] || row['last_updated'] || row['LastUpdated'] || '—';
        const url = row['Listing URL'] || row['Listing Link'] || row['MLS Link'] || '#';
        const urlBtn = url !== '#' ? `<a href="${url}" target="_blank" rel="noopener" class="view-btn">View Listing →</a>` : '';

        const detailHtml = `
          <td colspan="${DISPLAY_COLUMNS.length}">
            <div class="detail-card">
              <div class="detail-section">
                <div class="detail-item"><span class="detail-label">ZIP Code</span><span class="detail-value">${zip}</span></div>
                <div class="detail-item"><span class="detail-label">HOA/mo</span><span class="detail-value ${hoaCls}">${hoaStr}</span></div>
                <div class="detail-item"><span class="detail-label">Est. Down Payment (25%)</span><span class="detail-value">${dp}</span></div>
              </div>
              <div class="detail-section">
                <div class="detail-item"><span class="detail-label">Total Score</span><span class="detail-value">${score}</span></div>
                <div class="detail-item"><span class="detail-label">Last Updated</span><span class="detail-value">${lastUpd}</span></div>
                <div style="text-align:right">${urlBtn}</div>
              </div>
            </div>
          </td>
        `;
        detailTr.innerHTML = detailHtml;

        tr.onclick = () => {
          const wasOpen = detailTr.classList.contains('open');
          document.querySelectorAll('.detail-row.open').forEach(el => { el.classList.remove('open'); el.previousElementSibling.classList.remove('expanded'); });
          if (!wasOpen) {
            detailTr.classList.add('open');
            tr.classList.add('expanded');
          }
        };

        tbody.appendChild(tr);
        tbody.appendChild(detailTr);
      });

      const rc = document.getElementById('result-count');
      if (!rc.innerHTML) {
        rc.innerHTML = `Showing <strong>${filteredData.length}</strong> of ${rawData.length} listings`;
      }
    }

    function parseNumber(str) {
      if (!str && str !== 0) return NaN;
      if (typeof str === 'number') return str;
      return parseFloat(str.toString().replace(/[^0-9.-]+/g, ''));
    }

    function parseRatio(val) {
      let n = parseNumber(val);
      if (!String(val || '').includes('%') && n < 0.2) n *= 100;
      return n;
    }

    function fmtPrice(val) {
      const n = parseNumber(val);
      return isNaN(n) ? '—' : '$' + n.toLocaleString('en-US', {maximumFractionDigits:0});
    }

    function fmtRent(val) {
      const n = parseNumber(val);
      return isNaN(n) ? '—' : '$' + n.toLocaleString('en-US', {maximumFractionDigits:0}) + '/mo';
    }

    function fmtRatio(val) {
      const n = parseRatio(val);
      return isNaN(n) ? '—' : n.toFixed(2) + '%';
    }

    function fmtCashFlow(val) {
      const n = parseNumber(val);
      if (isNaN(n)) return '—';
      const f = '$' + Math.abs(n).toLocaleString('en-US', {maximumFractionDigits:0}) + '/mo';
      return n < 0 ? `<span class="cash-neg">−${f}</span>` : `<span class="cash-pos">+${f}</span>`;
    }

    function fmtCoC(val) {
      let n = parseNumber(val);
      if (!String(val || '').includes('%') && n < 0.2 && n > -0.2) n *= 100;
      if (isNaN(n)) return '—';
      const s = n.toFixed(1) + '%';
      return n < 0 ? `<span class="cash-neg">${s}</span>` : `<span class="cash-pos">${s}</span>`;
    }

    function parseCSV(text) {"""

start_idx = orig.find("    const DISPLAY_COLUMNS = [")
end_idx = orig.find("    function parseCSV(text) {")

if start_idx != -1 and end_idx != -1:
    orig = orig[:start_idx] + js_new + orig[end_idx:]

with open("condos.html", "w") as f:
    f.write(orig)

# Also fix fonts in index.html
with open("index.html", "r") as f:
    idx_orig = f.read()
    idx_orig = idx_orig.replace("family=DM+Sans", "family=Inter")
    idx_orig = idx_orig.replace("font-family: 'DM Sans'", "font-family: 'Inter'")
with open("index.html", "w") as f:
    f.write(idx_orig)
