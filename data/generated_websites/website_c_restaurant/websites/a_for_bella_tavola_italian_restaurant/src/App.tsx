import React from 'react';
import { DynamicSpatialEnvironment } from './components/DynamicSpatialEnvironment';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Story } from './components/Story';
import { SignatureDishes } from './components/SignatureDishes';
import { Reservations } from './components/Reservations';
import { Footer } from './components/Footer';

export const App: React.FC = () => {
  return (
    <div className="bg-slate-950 text-slate-100 font-sans min-h-screen relative min-h-screen overflow-x-hidden">
      <DynamicSpatialEnvironment />
      <div className="relative z-10">
        <Navbar />
        <Hero />
        <Story />
        <SignatureDishes />
        <Reservations />
        <Footer />
      </div>
    </div>
  );
};

export default App;
