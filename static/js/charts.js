let chart = null;
let barChart = null;

function initializeCharts() {
    const chartContainer = document.getElementById('chart-container');
    const barChartContainer = document.getElementById('bar-chart-container');
    
    // Initialize line chart
    const lineData = {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Selected Metric'
    };
    
    const lineLayout = {
        title: 'Player Performance Over Time',
        xaxis: { title: 'Gameweek' },
        yaxis: { title: 'Value' },
        paper_bgcolor: '#2d3748',
        plot_bgcolor: '#2d3748',
        font: { color: '#f7fafc' },
        showlegend: true
    };
    
    // Initialize bar chart
    const barData = {
        type: 'bar',
        name: 'Current Value'
    };
    
    const barLayout = {
        title: 'Player Comparison',
        xaxis: { title: 'Players' },
        yaxis: { title: 'Value' },
        paper_bgcolor: '#2d3748',
        plot_bgcolor: '#2d3748',
        font: { color: '#f7fafc' },
        showlegend: true
    };
    
    Plotly.newPlot('chart-container', [lineData], lineLayout);
    Plotly.newPlot('bar-chart-container', [barData], barLayout);
    
    chart = document.getElementById('chart-container');
    barChart = document.getElementById('bar-chart-container');
}

function updateCharts(players, metric) {
    if (!players || players.length === 0) return;
    
    // Update line chart
    const traces = players.map(player => {
        const history = player.recent_matches || [];
        return {
            x: history.map(match => match.round),
            y: history.map(match => match[metric] || 0),
            type: 'scatter',
            mode: 'lines+markers',
            name: player.name
        };
    });
    
    const lineLayout = {
        title: `Player ${metric.replace(/_/g, ' ').toUpperCase()} Over Time`,
        xaxis: { title: 'Gameweek' },
        yaxis: { title: metric.replace(/_/g, ' ').toUpperCase() },
        paper_bgcolor: '#2d3748',
        plot_bgcolor: '#2d3748',
        font: { color: '#f7fafc' },
        showlegend: true
    };
    
    // Update bar chart
    const barData = [{
        x: players.map(p => p.name),
        y: players.map(p => p[metric] || 0),
        type: 'bar',
        name: metric.replace(/_/g, ' ').toUpperCase()
    }];
    
    const barLayout = {
        title: `Player ${metric.replace(/_/g, ' ').toUpperCase()} Comparison`,
        xaxis: { title: 'Players' },
        yaxis: { title: metric.replace(/_/g, ' ').toUpperCase() },
        paper_bgcolor: '#2d3748',
        plot_bgcolor: '#2d3748',
        font: { color: '#f7fafc' },
        showlegend: true
    };
    
    Plotly.react('chart-container', traces, lineLayout);
    Plotly.react('bar-chart-container', barData, barLayout);
}