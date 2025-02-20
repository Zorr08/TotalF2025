document.addEventListener("DOMContentLoaded", function() {
    // Select all table cells in the players table with the player-name class
    var playerNameCells = document.querySelectorAll("#players-table td.player-name");
    
    playerNameCells.forEach(function(cell) {
        var name = cell.textContent.trim();
        var words = name.split(" ");
        // If there are more than 2 words, display only the first and the last word (FPL style)
        if (words.length > 2) {
            cell.textContent = words[0] + " " + words[words.length - 1];
        }
    });
}); 