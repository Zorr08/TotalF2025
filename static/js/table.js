document.addEventListener('DOMContentLoaded', () => {
    fetchLeagueTable();
    setupSorting();
});

let currentSortColumn = 9; // Default sort by points
let sortDirections = {9: true}; // Initialize points column to sort descending

async function fetchLeagueTable() {
    try {
        const response = await fetch('/api/table');
        const data = await response.json();
        
        if (data.success) {
            displayTable(data.table);
            sortTable(currentSortColumn); // Sort by default column
        } else {
            showError('Failed to load league table');
        }
    } catch (error) {
        console.error('Error fetching league table:', error);
        showError('Failed to load league table');
    }
}

function displayTable(tableData) {
    const tbody = document.querySelector('#league-table tbody');
    tbody.innerHTML = '';

    tableData.forEach((team, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>
                <div class="team-info">
                    <img src="${team.logo}" alt="${team.name}" class="team-logo-small">
                    <span>${team.name}</span>
                </div>
            </td>
            <td>${team.played}</td>
            <td>${team.won}</td>
            <td>${team.drawn}</td>
            <td>${team.lost}</td>
            <td>${team.goals_for}</td>
            <td>${team.goals_against}</td>
            <td>${team.goal_difference}</td>
            <td>${team.points}</td>
        `;
        tbody.appendChild(row);
    });
}

function setupSorting() {
    const headers = document.querySelectorAll('#league-table th');
    headers.forEach((header, index) => {
        if (index !== 1) { // Skip team name column
            header.style.cursor = 'pointer';
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
        }
    });
}

function sortTable(columnIndex) {
    const table = document.getElementById('league-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        let aValue = a.cells[columnIndex].textContent;
        let bValue = b.cells[columnIndex].textContent;
        
        // Convert to numbers for numeric columns
        if (columnIndex !== 1) {
            aValue = parseInt(aValue);
            bValue = parseInt(bValue);
        }
        
        const direction = sortDirections[columnIndex] ? -1 : 1;
        return (aValue - bValue) * direction;
    });
    
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
    
    // Update position numbers after sorting
    rows.forEach((row, index) => {
        row.cells[0].textContent = index + 1;
    });
}

function updateSortIndicator(columnIndex) {
    const headers = document.querySelectorAll('#league-table th');
    headers.forEach((header, index) => {
        header.classList.remove('sorted-asc', 'sorted-desc');
        if (index === columnIndex) {
            header.classList.add(sortDirections[index] ? 'sorted-desc' : 'sorted-asc');
        }
    });
}

function showError(message) {
    const tbody = document.querySelector('#league-table tbody');
    tbody.innerHTML = `
        <tr>
            <td colspan="10" class="error-message">
                <p>${message}</p>
                <button onclick="fetchLeagueTable()">Try Again</button>
            </td>
        </tr>
    `;
}