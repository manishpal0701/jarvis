// script.js
(function() {
  'use strict';

  // Header Section
  const header = document.querySelector('header');
  header.innerHTML = `
    <nav class="navbar">
      <div class="logo">
        <h1>Your Name</h1>
        <h2>Your Title</h2>
      </div>
      <ul class="nav-links">
        <li><a href="#about">About</a></li>
        <li><a href="#features">Features</a></li>
        <li><a href="#projects">Projects</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
    </nav>
  `;

  //