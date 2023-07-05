function ToggleModeNoturn(){
    var darkModeIcon = document.getElementById("manage_noturnmode");
    console.log("Clique no ícone de modo escuro");
    var currentIcon = darkModeIcon.textContent.trim();

    if (currentIcon === "dark_mode") {
        darkModeIcon.textContent = 'light_mode';
    } else {
        darkModeIcon.textContent = 'dark_mode';
    }
}