// script.js
const header = document.querySelector('header');
const hero = document.querySelector('.hero');
const about = document.querySelector('.about');
const featuresSkills = document.querySelector('.features-skills');
const projects = document.querySelector('.projects');
const contact = document.querySelector('.contact');
const footer = document.querySelector('footer');

header.addEventListener('click', () => {
  hero.classList.toggle('open');
});

about.addEventListener('click', () => {
  featuresSkills.classList.toggle('open');
});

contact.addEventListener('click', () => {
  projects.classList.toggle('open');
});

footer.addEventListener('click', () => {
  alert('Coming soon!');
});