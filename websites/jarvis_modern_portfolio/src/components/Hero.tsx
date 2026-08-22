import Image from 'next/image';
import { HeroSection } from '../types';
import { useState } from 'react';

const Hero: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const handleToggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <section
      className={`bg-slate-900 text-white ${isDarkMode ? 'text-emerald-400' : 'text-cyan-400'}`}
      style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}
    >
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold">Welcome to my Portfolio</h1>
        <p className="text-lg">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded" onClick={handleToggleDarkMode}>
          Toggle Dark Mode
        </button>
        <Image src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80" alt="Developer Profile Avatar" />
      </div>
    </section>
  );
};

export default Hero;