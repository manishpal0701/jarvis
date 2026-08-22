import Image from 'next/image';
import { useState } from 'react';
import { HeroSection } from '../styles';

const Hero = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  return (
    <HeroSection
      className={`bg-slate-900 text-white transition duration-500 ${
        isDarkMode ? 'text-emerald-400' : 'text-cyan-400'
      }`}
    >
      <Image
        src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"
        alt="Developer Profile Avatar"
        width={600}
        height={400}
      />
      <h1 className="text-3xl font-bold">ek modern portfolio</h1>
      <p className="text-lg font-medium">ek modern portfolio</p>
      <button
        className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
        onClick={() => setIsDarkMode(!isDarkMode)}
      >
        Toggle Dark Mode
      </button>
    </HeroSection>
  );
};

export default Hero;