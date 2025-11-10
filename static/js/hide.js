document.addEventListener('click', function() {
    const bannerDiv = document.getElementById('navBanner');
    bannerDiv.classList.remove('hide'); // Show the message

    // Set a timer to hide the message after 3 seconds
    setTimeout(function() {
        bannerDiv.classList.add('hide'); // Hide the message
    }, 3000);
});