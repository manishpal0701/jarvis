import Image from 'next/image';
import { useState } from 'react';
import { HeroSectionProps } from '../types';

const Hero: React.FC<HeroSectionProps> = ({ avatar, title, subtitle, button }) => {
  return (
    <section className="bg-gray-800 text-white">
      <div className="container mx-auto p-4 pt-6 md:p-6">
        <div className="flex flex-col items-center justify-center h-screen">
          <Image src={avatar} alt={title} width={200} height={200} />
          <h1 className="text-3xl font-bold">{title}</h1>
          <p className="text-lg">{subtitle}</p>
          <button className="bg-orange-500 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded">Get Started</button>
        </div>
      </div>
    </section>
  );
};

export default Hero;