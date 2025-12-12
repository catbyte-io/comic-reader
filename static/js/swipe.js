let startX;
let prevUrl = document.getElementById('prev').dataset.prev;
let nextUrl = document.getElementById('next').dataset.next;


const SWIPE_THRESHOLD = 300;

const touchStart = (event) => {
    startX = event.touches[0].clientX;
};

const touchEnd = (event) => {
    const endX = event.changedTouches[0].clientX;

    // Calculates distance
    const distanceX = endX - startX;

    if (distanceX > SWIPE_THRESHOLD) {
        window.location.href = prevUrl;
    } else if (distanceX < -SWIPE_THRESHOLD) {
        window.location.href = nextUrl;
    }
};

document.getElementById('toonLayer').addEventListener('touchstart', touchStart);
document.getElementById('toonLayer').addEventListener('touchend', touchEnd);
