const items = document.querySelectorAll('.timeline-item');
const buttons = document.querySelectorAll('.read-more-btn');

function showOnScroll() {
    const triggerBottom = window.innerHeight * 0.85;

    items.forEach(item => {
        const boxTop = item.getBoundingClientRect().top;

        if (boxTop < triggerBottom) {
            item.classList.add('active');
        }
    });
}

window.addEventListener('scroll', showOnScroll);
showOnScroll();

/* Expand Interaction */
buttons.forEach(button => {
    button.addEventListener('click', () => {
        const content = button.parentElement;
        content.classList.toggle('expanded');

        if (button.innerText === "View Details") {
            button.innerText = "Hide Details";
        } else {
            button.innerText = "View Details";
        }
    });
});