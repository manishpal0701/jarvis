// script.js

// Header Section
document.addEventListener('DOMContentLoaded', function () {
  const header = document.querySelector('.header');
  header.addEventListener('click', function () {
    const nav = document.querySelector('.nav');
    nav.classList.toggle('open');
  });
});

// Hero Section
document.addEventListener('DOMContentLoaded', function () {
  const hero = document.querySelector('.hero');
  hero.addEventListener('click', function () {
    const overlay = document.querySelector('.overlay');
    overlay.classList.toggle('open');
  });
});

// About Section
document.addEventListener('DOMContentLoaded', function () {
  const about = document.querySelector('.about');
  about.addEventListener('click', function () {
    const modal = document.querySelector('.modal');
    modal.classList.toggle('open');
  });