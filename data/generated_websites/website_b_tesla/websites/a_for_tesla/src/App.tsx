import React from 'react';
import { DynamicSpatialEnvironment } from './components/DynamicSpatialEnvironment';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { About } from './components/About';
import { Services } from './components/Services';
import { Projects } from './components/Projects';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';

export const App: React.FC = () => {
  return (
    <div className="bg-slate-950 text-slate-100 font-sans min-h-screen relative min-h-screen overflow-x-hidden">
      <DynamicSpatialEnvironment />
      <div className="relative z-10">
        <Navbar />
        <Hero />
        <About />
        <Services />
        <Projects />
        <Contact />
        <Footer />
      </div>
    </div>
  );
};

export default App;
