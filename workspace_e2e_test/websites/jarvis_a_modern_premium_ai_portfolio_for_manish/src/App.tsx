import { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Hero } from '../components/Hero';
import { About } from '../components/About';
import { Skills } from '../components/Skills';
import { Projects } from '../components/Projects';
import { Experience } from '../components/Experience';
import { Contact } from '../components/Contact';
import { Footer } from '../components/Footer';

function App() {
  const [hero, setHero] = useState({
    title: 'Manish Website',
    subtitle: 'A modern premium AI portfolio website',
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80',
  });

  const [about, setAbout] = useState({
    title: 'About Manish',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet nulla auctor, vestibulum magna sed, convallis ex.',
  });

  const [skills, setSkills] = useState([
    { title: 'AI', description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.' },
    { title: 'Machine Learning', description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.' },
    { title: 'Deep Learning', description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.' },
  ]);

  const [projects, setProjects] = useState([
    {
      title: 'Project 1',
      description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
      image: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=800&q=80',
    },
    {
      title: 'Project 2',
      description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
      image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80',
    },
  ]);

  const [experience, setExperience] = useState([
    {
      title: 'Experience 1',
      description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
      date: '2022-01-01',
    },
    {
      title: 'Experience 2',
      description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
      date: '2022-02-01',
    },
  ]);

  const [contact, setContact] = useState({
    title: 'Contact Manish',
    email: 'manish@example.com',
    phone: '123-456-7890',
    address: '123 Main St, Anytown, USA',
  });

  return (
    <div className="bg-slate-900 text-white">
      <Navbar />
      <Hero {...hero} />
      <About {...about} />
      <Skills {...skills} />
      <Projects {...projects} />
      <Experience {...experience} />
      <Contact {...contact} />
      <Footer />
    </div>
  );
}

export default App;