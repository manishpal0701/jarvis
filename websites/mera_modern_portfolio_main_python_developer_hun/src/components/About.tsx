import Image from 'next/image';
import { useState } from 'react';

const About = () => {
  const [showSkills, setShowSkills] = useState(false);
  const [showProjects, setShowProjects] = useState(false);

  return (
    <section className="text-gray-600 body-font">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold">About Me</h1>
        </div>
        <div className="flex flex-wrap justify-center -mx-4">
          <div className="w-full lg:w-1/3 px-4 mb-8 lg:mb-0">
            <Image
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"
              alt="Developer Profile Avatar"
              width={600}
              height={600}
            />
          </div>
          <div className="w-full lg:w-2/3 px-4">
            <p className="text-lg leading-relaxed">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet nulla auctor, vestibulum magna sed, convallis ex. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.
            </p>
            <button
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium leading-tight text-white rounded-md hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              onClick={() => setShowSkills(!showSkills)}
            >
              {showSkills ? 'Hide Skills' : 'Show Skills'}
            </button>
            <button
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium leading-tight text-white rounded-md hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              onClick={() => setShowProjects(!showProjects)}
            >
              {showProjects ? 'Hide Projects' : 'Show Projects'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;