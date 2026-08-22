import Link from 'next/link';
import { useState } from 'react';

const Footer = () => {
  const [year, setYear] = useState(new Date().getFullYear());

  return (
    <footer className="bg-slate-900 text-white">
      <div className="container mx-auto p-4">
        <div className="flex justify-between items-center">
          <div>
            <Link href="/">
              <a>Home</a>
            </Link>
            <Link href="/about">
              <a>About</a>
            </Link>
            <Link href="/skills">
              <a>Skills</a>
            </Link>
            <Link href="/projects">
              <a>Projects</a>
            </Link>
            <Link href="/experience">
              <a>Experience</a>
            </Link>
            <Link href="/contact">
              <a>Contact</a>
            </Link>
          </div>
          <div>
            &copy; {year} Developed by <span>Client</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;