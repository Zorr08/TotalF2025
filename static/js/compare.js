let selectedPlayers = [];
let allPlayers = [];
let teams = new Set();
let currentSearchIndex = -1;

document.addEventListener('DOMContentLoaded', () => {
    fetchPlayers();
    setupSearchAndFilters();
    setupJsonModal();
    initializeCharts();
});

function setupJsonModal() {
    const jsonEndpointBtn = document.getElementById('compare-json-btn');
    const jsonModal = document.getElementById('json-modal');
    const closeBtn = jsonModal.querySelector('.close');
    const copyBtn = document.getElementById('copy-url-btn');
    const apiUrl = document.getElementById('api-url');
    const sampleJson = document.getElementById('sample-json');
    
    jsonEndpointBtn.addEventListener('click', () => {
        const playerIds = selectedPlayers.map(player => player.id);
        const params = new URLSearchParams({
            player_ids: playerIds.join(',')
        });
        
        const fullUrl = `${window.location.origin}/api/players/compare?${params.toString()}`;
        apiUrl.textContent = fullUrl;
        
        const sampleResponse = {
            success: true,
            players: selectedPlayers.map(player => ({
                id: player.id,
                name: player.name,
                team: player.team,
                position: player.position,
                price: player.price,
                total_points: player.total_points,
                form: player.form,
                points_per_match: player.points_per_match,
                selected_by_percent: player.selected_by_percent
            }))
        };
        
        sampleJson.textContent = JSON.stringify(sampleResponse, null, 2);
        jsonModal.style.display = 'block';
    });
    
    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(apiUrl.textContent)
            .then(() => {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy URL:', err);
            });
    });
    
    closeBtn.onclick = () => jsonModal.style.display = "none";
    window.onclick = (event) => {
        if (event.target === jsonModal) {
            jsonModal.style.display = "none";
        }
    };
}

async function fetchPlayers() {
    try {
        const response = await fetch('/api/players');
        const data = await response.json();
        
        if (data.success) {
            allPlayers = data.players;
            updateTeamFilter();
        } else {
            console.error('Failed to load player data');
        }
    } catch (error) {
        console.error('Error fetching players:', error);
    }
}

function setupSearchAndFilters() {
    const searchInput = document.getElementById('player-search');
    const searchResults = document.getElementById('search-results');
    const positionFilter = document.getElementById('position-filter');
    const teamFilter = document.getElementById('team-filter');
    const priceRange = document.getElementById('price-range');
    const priceValue = document.getElementById('price-value');
    const metricSelect = document.getElementById('metric-select');

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        currentSearchIndex = -1;
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        const position = positionFilter.value;
        const team = teamFilter.value;
        const maxPrice = parseFloat(priceRange.value);

        const filteredPlayers = allPlayers.filter(player => {
            const nameMatch = player.name.toLowerCase().includes(query);
            const positionMatch = !position || player.position === position;
            const teamMatch = !team || player.team === team;
            const priceMatch = player.price <= maxPrice;
            return nameMatch && positionMatch && teamMatch && priceMatch;
        }).slice(0, 5);

        displaySearchResults(filteredPlayers, searchResults);
    });

    metricSelect.addEventListener('change', () => {
        const selectedMetric = metricSelect.value;
        updateCharts(selectedPlayers, selectedMetric);
    });

    searchInput.addEventListener('keydown', (e) => {
        const results = document.querySelectorAll('.search-result-item');
        if (!results.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            currentSearchIndex = Math.min(currentSearchIndex + 1, results.length - 1);
            updateSearchSelection(results);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            currentSearchIndex = Math.max(currentSearchIndex - 1, 0);
            updateSearchSelection(results);
        } else if (e.key === 'Enter' && currentSearchIndex >= 0) {
            e.preventDefault();
            results[currentSearchIndex].click();
        }
    });

    priceRange.addEventListener('input', (e) => {
        priceValue.textContent = `£${e.target.value}m`;
    });

    document.addEventListener('click', (e) => {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.style.display = 'none';
        }
    });
}

function updateSearchSelection(results) {
    results.forEach((result, index) => {
        if (index === currentSearchIndex) {
            result.classList.add('selected');
            result.focus();
        } else {
            result.classList.remove('selected');
        }
    });
}

function updateTeamFilter() {
    const teamFilter = document.getElementById('team-filter');
    const teams = [...new Set(allPlayers.map(player => player.team))].sort();
    
    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        teamFilter.appendChild(option);
    });
}

function displaySearchResults(players, searchResults) {
    searchResults.innerHTML = '';
    
    if (players.length === 0) {
        searchResults.style.display = 'none';
        return;
    }

    players.forEach((player, index) => {
        const div = document.createElement('div');
        div.className = 'search-result-item';
        div.setAttribute('tabindex', index);
        div.innerHTML = `
            <img src="${player.photo_url}" alt="${player.name}" class="player-photo-small">
            <div class="search-result-details">
                <div class="search-result-name">${player.name}</div>
                <div class="search-result-info">${player.team} | ${player.position} | £${player.price}m</div>
            </div>
        `;

        div.addEventListener('click', () => {
            if (selectedPlayers.length < 5 && !selectedPlayers.find(p => p.id === player.id)) {
                addPlayerToComparison(player);
            }
            searchResults.style.display = 'none';
        });

        searchResults.appendChild(div);
    });

    searchResults.style.display = 'block';
}

async function addPlayerToComparison(player) {
    try {
        const response = await fetch(`/api/player/${player.id}/details`);
        const data = await response.json();
        
        if (data.success) {
            player.recent_matches = data.history || [];
            player.upcoming_fixtures = data.fixtures || [];
            selectedPlayers.push(player);
            updateSelectedPlayers();
            updateComparisonTable();
            updateCharts(selectedPlayers, document.getElementById('metric-select').value);
        } else {
            console.error('Failed to fetch player details');
        }
    } catch (error) {
        console.error('Error fetching player details:', error);
    }
}

function removePlayerFromComparison(playerId) {
    selectedPlayers = selectedPlayers.filter(p => p.id !== playerId);
    updateSelectedPlayers();
    updateComparisonTable();
    updateCharts(selectedPlayers, document.getElementById('metric-select').value);
}

function updateSelectedPlayers() {
    const container = document.getElementById('selected-players');
    container.innerHTML = '';

    selectedPlayers.forEach(player => {
        const card = document.createElement('div');
        card.className = 'player-card';
        card.innerHTML = `
            <button class="remove-player" onclick="removePlayerFromComparison(${player.id})">×</button>
            <div class="player-card-header">
                <img src="${player.photo_url}" alt="${player.name}" class="player-card-photo">
                <div>
                    <div class="player-card-name">${player.name}</div>
                    <div class="player-card-info">${player.team} | ${player.position}</div>
                </div>
            </div>
            <div class="player-card-stats">
                <div>Price: £${player.price}m</div>
                <div>Total Points: ${player.total_points}</div>
            </div>
        `;
        container.appendChild(card);
    });
}

function updateComparisonTable() {
    const container = document.getElementById('comparison-table');
    if (selectedPlayers.length === 0) {
        container.innerHTML = '';
        return;
    }

    const metrics = [
        { key: 'form', label: 'Form', format: v => v || '0' },
        { key: 'total_points', label: 'Total Points', format: v => v || '0' },
        { key: 'price', label: 'Price', format: v => `£${v || '0'}m` },
        { key: 'points_per_match', label: 'Points/Match', format: v => v || '0' },
        { key: 'minutes', label: 'Minutes Played', format: v => v || '0' },
        { key: 'goals_scored', label: 'Goals', format: v => v || '0' },
        { key: 'assists', label: 'Assists', format: v => v || '0' },
        { key: 'clean_sheets', label: 'Clean Sheets', format: v => v || '0' },
        { key: 'goals_conceded', label: 'Goals Conceded', format: v => v || '0' },
        { key: 'own_goals', label: 'Own Goals', format: v => v || '0' },
        { key: 'penalties_saved', label: 'Penalties Saved', format: v => v || '0' },
        { key: 'penalties_missed', label: 'Penalties Missed', format: v => v || '0' },
        { key: 'yellow_cards', label: 'Yellow Cards', format: v => v || '0' },
        { key: 'red_cards', label: 'Red Cards', format: v => v || '0' },
        { key: 'saves', label: 'Saves', format: v => v || '0' },
        { key: 'bonus', label: 'Bonus Points', format: v => v || '0' },
        { key: 'bps', label: 'Bonus Points System', format: v => v || '0' },
        { key: 'influence', label: 'Influence', format: v => v || '0' },
        { key: 'creativity', label: 'Creativity', format: v => v || '0' },
        { key: 'threat', label: 'Threat', format: v => v || '0' },
        { key: 'ict_index', label: 'ICT Index', format: v => v || '0' },
        { key: 'selected_by_percent', label: 'Selected By', format: v => `${v || '0'}%` }
    ];

    let html = `
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    ${selectedPlayers.map(p => `<th>${p.name || 'Unknown Player'}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    metrics.forEach(metric => {
        html += `
            <tr>
                <td>${metric.label}</td>
                ${selectedPlayers.map(player => {
                    const value = player[metric.key];
                    return `<td>${metric.format(value)}</td>`;
                }).join('')}
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}