import React from 'react';
import Image from 'next/image';

const About = () => {
  const subjectName = 'Your Subject Name';
  const businessName = 'Your Business Name';
  const roles = ['Your Role 1', 'Your Role 2'];
  const products = ['Your Product 1', 'Your Product 2'];

  return (
    <main className="max-w-7xl mx-auto p-4 text-center">
      <header>
        <h1 className="text-3xl font-bold">{subjectName}</h1>
      </header>
      <section>
        <h2 className="text-2xl font-bold mb-4">Business Overview</h2>
        <p