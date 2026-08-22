import React from 'react';
import { Link } from 'react-router-dom';

const About = () => {
  return (
    <section className="bg-slate-900 text-white py-12">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold mb-4">About Me</h1>
        <p className="text-lg mb-8">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet nulla auctor, vestibulum magna sed, convallis ex.</p>
        <div className="flex flex-wrap justify-center mb-8">
          <div className="w-full lg:w-1/3 xl:w-1/3 px-4 mb-8">
            <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80" alt="Developer Profile Avatar" className="w-full h-full rounded-full" />
          </div>
          <div className="w-full lg:w-1/3 xl:w-1/3 px-4 mb-8">
            <h2 className="text-2xl font-bold mb-2">Project 1</h2>
            <p className="text-lg">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet nulla auctor, vestibulum magna sed, convallis ex.</p>
            <Link to="#" className="bg-emerald-400 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded">Learn More</Link>
          </div>
          <div className="w-full lg:w-1/3 xl:w-1/3 px-4 mb-8">
            <h2 className="text-2xl font-bold mb-2">Project 2</h2>
            <p className="text-lg">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet nulla auctor, vestibulum magna sed, convallis ex.</p>
            <Link to="#" className="bg-emerald-400 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded">Learn More</Link>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;