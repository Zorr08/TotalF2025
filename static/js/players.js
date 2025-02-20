let allPlayers = [];
let teams = new Set();
let currentSortColumn = 3; // Default sort by total points
let sortDirections = {}; // Initialize empty sort directions
let currentPage = 1;
let playersPerPage = 10;
let filteredPlayers = [];

document.addEventListener('DOMContentLoaded', () => {
    setupJsonEndpointButton();
    setupModal();
    setupFilters();
    fetchPlayers();
});

async function fetchPlayers() {
    try {
        const response = await fetch('/api/players');
        const data = await response.json();
        
        if (data.success) {
            allPlayers = data.players;
            filteredPlayers = [...allPlayers];
            updateTeamFilter();
            updatePagination();
            displayPlayers();
            updateLastUpdated(data.last_updated);
            setupSorting();
            sortTable(3); // Default sort by total points column
            sortTable(currentSortColumn);
        }
    } catch (error) {
        console.error('Error fetching players:', error);
        showError('Failed to load player data');
    }
}

function applyFilters() {
    const position = document.getElementById('position-filter').value;
    const team = document.getElementById('team-filter').value;
    const maxPrice = parseFloat(document.getElementById('price-range').value);
    const minPoints = parseInt(document.getElementById('min-points').value);

    filteredPlayers = allPlayers.filter(player => {
        const positionMatch = !position || player.position === position;
        const teamMatch = !team || player.team === team;
        const priceMatch = !maxPrice || parseFloat(player.price) <= maxPrice;
        const pointsMatch = !minPoints || parseInt(player.total_points) >= minPoints;
        return positionMatch && teamMatch && priceMatch && pointsMatch;
    });

    currentPage = 1;
    sortTable(currentSortColumn);
    updatePagination();
}

function setupFilters() {
    const positionFilter = document.getElementById('position-filter');
    const teamFilter = document.getElementById('team-filter');
    const priceRange = document.getElementById('price-range');
    const priceValue = document.getElementById('price-value');
    const minPoints = document.getElementById('min-points');

    positionFilter.addEventListener('change', () => applyFilters());
    teamFilter.addEventListener('change', () => applyFilters());
    priceRange.addEventListener('input', (e) => {
        priceValue.textContent = `£${e.target.value}m`;
        applyFilters();
    });
    minPoints.addEventListener('input', () => applyFilters());
}

function setupJsonEndpointButton() {
    const jsonEndpointBtn = document.getElementById('json-endpoint-btn');
    const jsonModal = document.getElementById('json-modal');
    const closeBtn = jsonModal.querySelector('.close');
    const copyBtn = document.getElementById('copy-url-btn');
    const apiUrl = document.getElementById('api-url');
    const sampleJson = document.getElementById('sample-json');
    
    jsonEndpointBtn.addEventListener('click', async () => {
        // Get current filters
        const position = document.getElementById('position-filter').value;
        const team = document.getElementById('team-filter').value;
        const maxPrice = document.getElementById('price-range').value;
        const minPoints = document.getElementById('min-points').value;
        
        // Get current sorting
        const sortColumn = currentSortColumn;
        const sortDirection = sortDirections[currentSortColumn];
        
        // Get current page info
        const startIndex = (currentPage - 1) * playersPerPage;
        const endIndex = startIndex + playersPerPage;
        
        // Apply sorting to filtered players
        const sortedPlayers = [...filteredPlayers];
        sortedPlayers.sort((a, b) => {
            let aValue, bValue;
            
            switch (sortColumn) {
                case 0: // Player name
                    aValue = a.name;
                    bValue = b.name;
                    break;
                case 1: // Team
                    aValue = a.team;
                    bValue = b.team;
                    break;
                case 2: // Price
                    aValue = parseFloat(a.price);
                    bValue = parseFloat(b.price);
                    break;
                case 3: // Total Points
                    aValue = parseInt(a.total_points);
                    bValue = parseInt(b.total_points);
                    break;
                case 4: // Event Points
                    aValue = parseInt(a.event_points || 0);
                    bValue = parseInt(b.event_points || 0);
                    break;
                case 5: // Minutes played
                    aValue = parseInt(a.minutes);
                    bValue = parseInt(b.minutes);
                    break;
                default:
                    aValue = a[getColumnKey(sortColumn)] || 0;
                    bValue = b[getColumnKey(sortColumn)] || 0;
            }
            
            const direction = sortDirection ? -1 : 1;
            if (typeof aValue === 'number' && typeof bValue === 'number') {
                return (aValue - bValue) * direction;
            }
            return aValue.toString().localeCompare(bValue.toString()) * direction;
        });
        
        const currentlyDisplayedPlayers = sortedPlayers.slice(startIndex, endIndex);
        
        // Build query parameters
        const params = new URLSearchParams({
            page: currentPage,
            per_page: playersPerPage,
            position: position || '',
            team: team || '',
            max_price: maxPrice || '',
            min_points: minPoints || '',
            sort_column: sortColumn,
            sort_direction: sortDirection
        });
        
        const apiEndpoint = '/api/players/json';
        const fullUrl = `${window.location.origin}${apiEndpoint}?${params.toString()}`;
        
        apiUrl.textContent = fullUrl;
        sampleJson.textContent = 'Loading sample response...';
        jsonModal.style.display = 'block';
        
        // Format the sample response to match exactly what's shown in the table
        const formattedData = {
            success: true,
            players: currentlyDisplayedPlayers.map(player => ({
                name: player.name,
                position: player.position,
                team: player.team,
                price: player.price,
                total_points: player.total_points,
                event_points: player.event_points || 0,
                minutes: player.minutes,
                goals_scored: player.goals_scored,
                assists: player.assists,
                clean_sheets: player.clean_sheets,
                goals_conceded: player.goals_conceded,
                own_goals: player.own_goals,
                penalties_saved: player.penalties_saved,
                penalties_missed: player.penalties_missed,
                yellow_cards: player.yellow_cards,
                red_cards: player.red_cards,
                saves: player.saves,
                bonus: player.bonus,
                bps: player.bps,
                influence: player.influence,
                creativity: player.creativity,
                threat: player.threat,
                ict_index: player.ict_index,
                selected_by_percent: player.selected_by_percent
            })),
            pagination: {
                current_page: currentPage,
                per_page: playersPerPage,
                total_players: sortedPlayers.length,
                total_pages: Math.ceil(sortedPlayers.length / playersPerPage)
            }
        };
        
        sampleJson.textContent = JSON.stringify(formattedData, null, 2);
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

function setupModal() {
    const modal = document.getElementById('player-modal');
    const closeBtn = modal.querySelector('.close');

    closeBtn.onclick = () => modal.style.display = "none";
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    };
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

function displayPlayers() {
    const tbody = document.querySelector('#players-table tbody');
    tbody.innerHTML = '';

    const startIndex = (currentPage - 1) * playersPerPage;
    const endIndex = startIndex + playersPerPage;
    const playersToShow = filteredPlayers.slice(startIndex, endIndex);

    playersToShow.forEach(player => {
        const row = document.createElement('tr');
        row.setAttribute('data-player-id', player.id);
        row.innerHTML = `
            <td>
                <div class="player-info-cell">
                    <img src="${player.photo_url}" alt="${player.name}" class="player-photo-small">
                    <span>${player.name}</span>
                </div>
            </td>
            <td>
                <img src="${player.team_logo}" alt="Team logo" class="team-logo-small">
            </td>
            <td>£${player.price}m</td>
            <td>${player.total_points}</td>
            <td>${player.form || '0.0'}</td>
            <td>${player.event_points || 0}</td>
            <td>${player.minutes}</td>
            <td>${player.goals_scored}</td>
            <td>${player.assists}</td>
            <td>${player.expected_goals?.toFixed(2) || '0.00'}</td>
            <td>${player.expected_assists?.toFixed(2) || '0.00'}</td>
            <td>${player.clean_sheets}</td>
            <td>${player.goals_conceded}</td>
            <td>${player.expected_goals_conceded?.toFixed(2) || '0.00'}</td>
            <td>${player.own_goals}</td>
            <td>${player.penalties_saved}</td>
            <td>${player.penalties_missed}</td>
            <td>${player.yellow_cards}</td>
            <td>${player.red_cards}</td>
            <td>${player.saves}</td>
            <td>${player.bonus}</td>
            <td>${player.bps}</td>
            <td>${player.influence}</td>
            <td>${player.creativity}</td>
            <td>${player.threat}</td>
            <td>${player.ict_index}</td>
            <td>${player.selected_by_percent}%</td>
        `;
        
        row.addEventListener('click', async () => {
            try {
                const response = await fetch(`/api/player/${player.id}/details`);
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Failed to load player details');
                }
                
                const modal = document.getElementById('player-modal');
                const modalContent = document.getElementById('modal-content');
                
                const history = data.history || [];
                const fixtures = data.fixtures || [];
                
                modalContent.innerHTML = `
                    <div class="player-details">
                        <div class="player-header">
                            <div class="player-photo-container">
                                <img src="${player.photo_url}" alt="${player.name}" class="player-photo-large">
                                <h2 class="player-name">${player.name}</h2>
                            </div>
                            <div class="player-info">
                                <div class="player-info-grid">
                                    <div class="info-row">
                                        <img src="${player.team_logo}" alt="Team logo" class="team-logo-small">
                                        <span>${player.team}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Position:</span>
                                        <span>${player.position}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Price:</span>
                                        <span>£${player.price}m</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Total Points:</span>
                                        <span>${player.total_points}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Matchweek Points:</span>
                                        <span>${player.event_points || 0}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Minutes Played:</span>
                                        <span>${player.minutes}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Selected by:</span>
                                        <span>${player.selected_by_percent}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="recent-matches">
                            <h3>Recent Matches</h3>
                            <table class="history-table">
                                <thead>
                                    <tr>
                                        <th>GW</th>
                                        <th>OPP</th>
                                        <th>Result</th>
                                        <th>Pts</th>
                                        <th>MP</th>
                                        <th>GS</th>
                                        <th>A</th>
                                        <th>CS</th>
                                        <th>BP</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${history.map(match => `
                                        <tr>
                                            <td>${match.round}</td>
                                            <td>${match.opponent}</td>
                                            <td class="result-${match.result.toLowerCase()}">${match.result}</td>
                                            <td>${match.total_points}</td>
                                            <td>${match.minutes}</td>
                                            <td>${match.goals_scored}</td>
                                            <td>${match.assists}</td>
                                            <td>${match.clean_sheets}</td>
                                            <td>${match.bonus}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        <div class="upcoming-fixtures">
                            <h3>Upcoming Fixtures</h3>
                            <table class="fixtures-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>GW</th>
                                        <th>Opponent</th>
                                        <th>FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${fixtures.map(fixture => `
                                        <tr>
                                            <td>${fixture.formatted_date}</td>
                                            <td>${fixture.event}</td>
                                            <td>${fixture.opponent_name}</td>
                                            <td>${fixture.difficulty}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
                
                modal.style.display = "block";
            } catch (error) {
                console.error('Error loading player details:', error);
                const modal = document.getElementById('player-modal');
                const modalContent = document.getElementById('modal-content');
                modalContent.innerHTML = `
                    <div class="error-message">
                        <p>Failed to load player details. Please try again later.</p>
                    </div>
                `;
                modal.style.display = "block";
            }
        });
        tbody.appendChild(row);
    });
}

async function showPlayerDetails(player) {
    const modal = document.getElementById('player-modal');
    const modalContent = document.getElementById('modal-content');
    
    try {
        const response = await fetch(`/api/player/${player.id}/details`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load player details');
        }
        
        const history = data.history || [];
        const fixtures = data.fixtures || [];
        
        modalContent.innerHTML = `
            <div class="player-details">
                <div class="player-header">
                    <img src="${player.photo_url}" alt="${player.name}" class="player-photo-large">
                    <div class="player-info">
                        <h2>${player.name}</h2>
                        <p class="team-name"><img src="${player.team_logo}" alt="Team logo" class="team-logo-small"></p>
                        <p class="price">Price: £${player.price}m</p>
                        <p class="form">Form: ${player.form}</p>
                        <p class="points">Points/Match: ${player.points_per_match}</p>
                        <p class="total-points">Total Points: ${player.total_points}</p>
                        <p class="bonus">Total Bonus: ${player.total_bonus}</p>
                        <p class="ict">ICT Index: ${player.ict_index}</p>
                        <p class="selected">Selected by: ${player.selected_by_percent}%</p>
                    </div>
                </div>
                <div class="recent-matches">
                    <h3>Recent Matches</h3>
                    <table class="history-table">
                        <thead>
                            <tr>
                                <th>GW</th>
                                <th>OPP</th>
                                <th>Form</th>
                                <th>Pts</th>
                                <th>MP</th>
                                <th>GS</th>
                                <th>A</th>
                                <th>CS</th>
                                <th>BP</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${history.map(match => `
                                <tr>
                                    <td>${match.round}</td>
                                    <td>${match.opponent}</td>
                                    <td class="result-${match.result.toLowerCase()}">${match.result}</td>
                                    <td>${match.total_points}</td>
                                    <td>${match.minutes}</td>
                                    <td>${match.goals_scored}</td>
                                    <td>${match.assists}</td>
                                    <td>${match.clean_sheets}</td>
                                    <td>${match.bonus}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="upcoming-fixtures">
                    <h3>Upcoming Fixtures</h3>
                    <table class="fixtures-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>GW</th>
                                <th>Opponent</th>
                                <th>FDR</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${fixtures.map(fixture => `
                                <tr>
                                    <td>${fixture.formatted_date}</td>
                                    <td>${fixture.event}</td>
                                    <td>${fixture.opponent_name}</td>
                                    <td>${fixture.difficulty}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error fetching player details:', error);
        modalContent.innerHTML = `
            <div class="error-message">
                <p>Failed to load player details. Please try again later.</p>
            </div>
        `;
    }
    
    modal.style.display = "block";
}

function setupSorting() {
    const headers = document.querySelectorAll('#players-table th');
    headers.forEach((header, index) => {
        header.addEventListener('click', () => {
            if (currentSortColumn === index) {
                sortDirections[index] = !sortDirections[index];
            } else {
                currentSortColumn = index;
                sortDirections[index] = true; // Start with descending
            }
            sortTable(index);
            updateSortIndicator(index);
        });
    });
}

function getColumnKey(columnIndex) {
    const columnKeys = {
        6: 'goals_scored',
        7: 'assists',
        8: 'expected_goals',
        9: 'expected_assists',
        10: 'clean_sheets',
        11: 'goals_conceded',
        12: 'expected_goals_conceded',
        13: 'own_goals',
        14: 'penalties_saved',
        15: 'penalties_missed',
        16: 'yellow_cards',
        17: 'red_cards',
        18: 'saves',
        19: 'bonus',
        20: 'bps',
        21: 'influence',
        22: 'creativity',
        23: 'threat',
        24: 'ict_index',
        25: 'selected_by_percent'
    };
    return columnKeys[columnIndex];
}

function sortTable(columnIndex) {
    // Initialize sort direction to descending if not set
    if (!(columnIndex in sortDirections)) {
        sortDirections[columnIndex] = true; // true means descending
    }

    filteredPlayers.sort((a, b) => {
        let aValue, bValue;
        
        // Special handling for different columns
        switch (columnIndex) {
            case 0: // Player name
                aValue = a.name;
                bValue = b.name;
                break;
            case 1: // Team
                aValue = a.team;
                bValue = b.team;
                break;
            case 2: // Price
                aValue = parseFloat(a.price);
                bValue = parseFloat(b.price);
                break;
            case 3: // Total Points
                aValue = parseInt(a.total_points);
                bValue = parseInt(b.total_points);
                break;
            case 4: // Form
                aValue = parseFloat(a.form || 0);
                bValue = parseFloat(b.form || 0);
                break;
            case 5: // GW Points
                aValue = parseInt(a.event_points || 0);
                bValue = parseInt(b.event_points || 0);
                break;
            case 6: // Minutes played
                aValue = parseInt(a.minutes || 0);
                bValue = parseInt(b.minutes || 0);
                break;
            case 7: // Goals scored
                aValue = parseInt(a.goals_scored || 0);
                bValue = parseInt(b.goals_scored || 0);
                break;
            case 8: // Assists
                aValue = parseInt(a.assists || 0);
                bValue = parseInt(b.assists || 0);
                break;
            case 9: // Expected goals
                aValue = parseFloat(a.expected_goals || 0);
                bValue = parseFloat(b.expected_goals || 0);
                break;
            case 10: // Expected assists
                aValue = parseFloat(a.expected_assists || 0);
                bValue = parseFloat(b.expected_assists || 0);
                break;
            case 11: // Clean sheets
                aValue = parseInt(a.clean_sheets || 0);
                bValue = parseInt(b.clean_sheets || 0);
                break;
            case 12: // Goals conceded
                aValue = parseInt(a.goals_conceded || 0);
                bValue = parseInt(b.goals_conceded || 0);
                break;
            case 13: // Expected goals conceded
                aValue = parseFloat(a.expected_goals_conceded || 0);
                bValue = parseFloat(b.expected_goals_conceded || 0);
                break;
            case 14: // Own goals
                aValue = parseInt(a.own_goals || 0);
                bValue = parseInt(b.own_goals || 0);
                break;
            case 15: // Penalties saved
                aValue = parseInt(a.penalties_saved || 0);
                bValue = parseInt(b.penalties_saved || 0);
                break;
            case 16: // Penalties missed
                aValue = parseInt(a.penalties_missed || 0);
                bValue = parseInt(b.penalties_missed || 0);
                break;
            case 17: // Yellow cards
                aValue = parseInt(a.yellow_cards || 0);
                bValue = parseInt(b.yellow_cards || 0);
                break;
            case 18: // Red cards
                aValue = parseInt(a.red_cards || 0);
                bValue = parseInt(b.red_cards || 0);
                break;
            case 19: // Saves
                aValue = parseInt(a.saves || 0);
                bValue = parseInt(b.saves || 0);
                break;
            case 20: // Bonus
                aValue = parseInt(a.bonus || 0);
                bValue = parseInt(b.bonus || 0);
                break;
            case 21: // BPS
                aValue = parseInt(a.bps || 0);
                bValue = parseInt(b.bps || 0);
                break;
            case 22: // Influence
                aValue = parseFloat(a.influence || 0);
                bValue = parseFloat(b.influence || 0);
                break;
            case 23: // Creativity
                aValue = parseFloat(a.creativity || 0);
                bValue = parseFloat(b.creativity || 0);
                break;
            case 24: // Threat
                aValue = parseFloat(a.threat || 0);
                bValue = parseFloat(b.threat || 0);
                break;
            case 25: // ICT index
                aValue = parseFloat(a.ict_index || 0);
                bValue = parseFloat(b.ict_index || 0);
                break;
            case 26: // Selected by percent
                aValue = parseFloat(a.selected_by_percent || 0);
                bValue = parseFloat(b.selected_by_percent || 0);
                break;
            case 27: // Selected by percent
                aValue = parseFloat(a.selected_by_percent || 0);
                bValue = parseFloat(b.selected_by_percent || 0);
                break;
            default:
                aValue = 0;
                bValue = 0;
        }
        
        const direction = sortDirections[columnIndex] ? -1 : 1;
        if (typeof aValue === 'number' && typeof bValue === 'number') {
            // Handle NaN values
            if (isNaN(aValue)) aValue = -Infinity;
            if (isNaN(bValue)) bValue = -Infinity;
            return (aValue - bValue) * direction;
        }
        return aValue.toString().localeCompare(bValue.toString()) * direction;
    });
    
    displayPlayers();
}

function updateSortIndicator(columnIndex) {
    const headers = document.querySelectorAll('#players-table th');
    headers.forEach((header, index) => {
        header.classList.remove('sorted-asc', 'sorted-desc');
        if (index === columnIndex) {
            header.classList.add(sortDirections[index] ? 'sorted-desc' : 'sorted-asc');
        }
    });
}

function updateLastUpdated(timestamp) {
    const element = document.getElementById('last-updated');
    if (element && timestamp) {
        const date = new Date(timestamp);
        element.textContent = `Last updated: ${date.toLocaleString()}`;
    }
}

function showError(message) {
    const tbody = document.querySelector('#players-table tbody');
    tbody.innerHTML = `
        <tr>
            <td colspan="10" class="error-message">
                <p>${message}</p>
                <button onclick="fetchPlayers()">Try Again</button>
            </td>
        </tr>
    `;
}