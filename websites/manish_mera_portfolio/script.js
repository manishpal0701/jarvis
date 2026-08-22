// Get all elements with the class "header", "nav", and "logo"
const header = document.querySelector('.header');
const nav = document.querySelector('.nav');
const logo = document.querySelector('.logo');

// Add event listener to the logo to toggle the navigation
logo.addEventListener('click', () => {
    nav.classList.toggle('open');
});

// Get all elements with the class "nav-link"
const navLinks = document.querySelectorAll('.nav-link');

// Add event listener to each nav-link to navigate to the corresponding section
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        const sectionId = link.getAttribute('href');
        const section = document