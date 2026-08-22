/* 
  Script.js
  Interactive client-side JavaScript features and DOM event listeners
*/

// Hero Section
document.addEventListener('DOMContentLoaded', () => {
  const heroSection = document.querySelector('.hero-section');
  heroSection.classList.add('active');
  
  // Hero Image Slide
  const heroImages = document.querySelectorAll('.hero-image');
  heroImages.forEach((image, index) => {
    image.addEventListener('click', () => {
      heroImages.forEach((img) => img.classList.remove('active'));
      heroImages[index].classList.add('active');
    });
  });
  
  // Hero Text Slide
  const heroTexts = document.querySelectorAll('.hero-text');
  heroTexts.forEach((text, index) => {
    text.addEventListener('