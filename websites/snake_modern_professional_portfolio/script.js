// script.js

// Header Section
let header = document.createElement('header');
header.innerHTML = `
  <nav class="main-nav">
    <ul>
      <li><a href="#about">About</a></li>
      <li><a href="#features">Features</a></li>
      <li><a href="#projects">Projects</a></li>
      <li><a href="#contact">Contact</a></li>
    </ul>
  </nav>
`;

document.body.insertAdjacentElement('beforeend', header);

// Hero Section
let hero = document.createElement('section');
hero.innerHTML = `
  <div class="hero">
    <h1>Welcome to my Modern Professional Portfolio</h1>