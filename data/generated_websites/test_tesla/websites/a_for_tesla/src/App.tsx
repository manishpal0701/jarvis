import React from 'react';
import { DynamicSpatialEnvironment } from './components/DynamicSpatialEnvironment';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { PerformanceMetrics } from './components/PerformanceMetrics';
import { SpecsGrid } from './components/SpecsGrid';
import { Gallery } from './components/Gallery';
import { Contact } from './components/Contact';
import { Footer } from './components/Footer';

export const App: React.FC = () => {
  return (
    <div className="bg-slate-950 text-slate-100 font-sans min-h-screen relative min-h-screen overflow-x-hidden">
      <DynamicSpatialEnvironment />
      <div className="relative z-10">
        <Navbar />
        <Hero />
        <PerformanceMetrics />
        <SpecsGrid />
        <Gallery />
        <Contact />
        <Footer />
      </div>
    </div>
  );
};

export default App;
