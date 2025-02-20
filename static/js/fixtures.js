let allFixtures = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchFixtures();
});

async function fetchFixtures() {
    try {
        const response = await fetch('/api/fixtures');
        const data = await response.json();
        
        if (data.success) {
            allFixtures = data.fixtures;
            setupGameweekSelector(data.fixtures);
            displayFixtures(data.fixtures);
        } else {
            showError('Failed to load fixtures');
        }
    } catch (error) {
        console.error('Error fetching fixtures:', error);
        showError('Failed to load fixtures');
    }
}

function setupGameweekSelector(fixtures) {
    const selector = document.getElementById('gameweek-select');
    const gameweeks = [...new Set(fixtures.map(f => f.gameweek))].sort((a, b) => a - b);
    
    // Clear existing options except "All Gameweeks"
    selector.innerHTML = '<option value="all">All Gameweeks</option>';
    
    // Add gameweek options
    gameweeks.forEach(gw => {
        const option = document.createElement('option');
        option.value = gw;
        option.textContent = `Gameweek ${gw}`;
        selector.appendChild(option);
    });
    
    // Add event listener for gameweek selection
    selector.addEventListener('change', (e) => {
        const selectedGameweek = e.target.value;
        const filteredFixtures = selectedGameweek === 'all' 
            ? allFixtures 
            : allFixtures.filter(f => f.gameweek === parseInt(selectedGameweek));
        displayFixtures(filteredFixtures);
    });
}

function displayFixtures(fixtures) {
    const container = document.getElementById('fixtures-list');
    container.innerHTML = '';

    // Group fixtures by date
    const fixturesByDate = fixtures.reduce((acc, fixture) => {
        const [date] = fixture.kickoff_time.split(' | ');
        if (!acc[date]) {
            acc[date] = [];
        }
        acc[date].push(fixture);
        return acc;
    }, {});

    // Sort dates chronologically
    const sortedDates = Object.keys(fixturesByDate).sort((a, b) => {
        return new Date(a) - new Date(b);
    });

    sortedDates.forEach(date => {
        // Add date header with centered text
        const dateHeader = document.createElement('div');
        dateHeader.className = 'gameweek-header text-center';
        dateHeader.textContent = date;
        container.appendChild(dateHeader);

        // Sort fixtures by kickoff time
        const sortedFixtures = fixturesByDate[date].sort((a, b) => {
            return new Date(a.kickoff_time) - new Date(b.kickoff_time);
        });

        // Display fixtures for this date
        sortedFixtures.forEach(fixture => {
            const [, time] = fixture.kickoff_time.split(' | ');
            const fixtureElement = document.createElement('div');
            fixtureElement.className = 'fixture-item';
            fixtureElement.innerHTML = `
                <div class="fixture-date text-center">${time}</div>
                <div class="fixture-teams">
                    <div class="team home-team">
                        <img src="${fixture.team_h_logo}" alt="${fixture.team_h}" class="team-logo-small">
                        <span>${fixture.team_h}</span>
                    </div>
                    <div class="fixture-score">
                        ${fixture.started ? `${fixture.team_h_score} - ${fixture.team_a_score}` : 'vs'}
                    </div>
                    <div class="team away-team">
                        <img src="${fixture.team_a_logo}" alt="${fixture.team_a}" class="team-logo-small">
                        <span>${fixture.team_a}</span>
                    </div>
                </div>
            `;
            container.appendChild(fixtureElement);
        });
    });
}

function showError(message) {
    const container = document.getElementById('fixtures-list');
    container.innerHTML = `
        <div class="error-message">
            <p>${message}</p>
            <button onclick="fetchFixtures()">Try Again</button>
        </div>
    `;
}