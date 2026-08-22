import React from 'react';
import { Hero, About, Skills, Projects, Experience, Contact } from './components';

const App = () => {
  return (
    <div className="max-w-7xl mx-auto p-4">
      <Hero />
      <About />
      <Skills />
      <Projects />
      <Experience />
      <Contact />
    </div>
  );
};

export default App;