// Get the elements
const nav = document.querySelector('nav');
const hero = document.querySelector('.hero');

// Add event listener to the button
const button = document.querySelector('button');
button.addEventListener('click', () => {
  // Add animation to the section
  hero.classList.add('animate');

  // Animation duration
  setTimeout(() => {
    hero.classList.remove('animate');
  }, 500);
});