function updatePagination() {
    const totalPages = Math.ceil(filteredPlayers.length / playersPerPage);
    const paginationContainer = document.getElementById('pagination-container');
    
    if (!paginationContainer) {
        const container = document.createElement('div');
        container.id = 'pagination-container';
        container.className = 'pagination';
        document.querySelector('.table-container').appendChild(container);
    }
    
    const paginationHTML = `
        <button class="pagination-btn" onclick="previousPage()" ${currentPage === 1 ? 'disabled' : ''}>
            Previous
        </button>
        <span class="pagination-info">
            Page ${currentPage} of ${totalPages}
        </span>
        <button class="pagination-btn" onclick="nextPage()" ${currentPage === totalPages ? 'disabled' : ''}>
            Next
        </button>
    `;
    
    document.getElementById('pagination-container').innerHTML = paginationHTML;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        displayPlayers();
        updatePagination();
    }
}

function nextPage() {
    const totalPages = Math.ceil(filteredPlayers.length / playersPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayPlayers();
        updatePagination();
    }
}