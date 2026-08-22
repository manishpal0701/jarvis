import { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@lucide-react/core';

const Footer = () => {
  const [active, setActive] = useState(0);

  const handleNav = (index: number) => {
    setActive(index);
  };

  return (
    <footer className="bg-slate-900 text-white">
      <div className="container mx-auto px-4 py-12">
        <div className="flex justify-between items-center">
          <div>
            <a href="/">
              <a>Manish</a>
            </a>
            <p>&copy; 2023 Manish</p>
          </div>
          <div>
            <ChevronLeftIcon className="w-6 h-6" />
            <ChevronRightIcon className="w-6 h-6" />
          </div>
        </div>
        <div className="flex flex-wrap justify-center mt-4">
          <a href="#about" onClick={() => handleNav(1)}>
            <a>About</a>
          </a>
          <a href="#skills" onClick={() => handleNav(2)}>
            <a>Skills</a>
          </a>
          <a href="#projects" onClick={() => handleNav(3)}>
            <a>Projects</a>
          </a>
          <a href="#experience" onClick={() => handleNav(4)}>
            <a>Experience</a>
          </a>
          <a href="#contact" onClick={() => handleNav(5)}>
            <a>Contact</a>
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;