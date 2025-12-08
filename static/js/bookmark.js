document.getElementById('bookmarkButton').addEventListener('click', function() {
    let buttonIcon = this.querySelector('i');
    
    // Toggle the icon immediately
    if (buttonIcon.classList.contains('bi-bookmark')) {
        buttonIcon.classList.remove('bi-bookmark');
        buttonIcon.classList.add('bi-bookmark-fill');
    } else {
        buttonIcon.classList.remove('bi-bookmark-fill');
        buttonIcon.classList.add('bi-bookmark');
    }
});