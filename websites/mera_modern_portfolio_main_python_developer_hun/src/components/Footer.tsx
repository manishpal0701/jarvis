import Link from 'next/link';
import { useState } from 'react';
import { TailwindConfig } from 'tailwindcss';

const Footer: React.FC = () => {
  const [year, setYear] = useState(new Date().getFullYear());

  return (
    <footer className="bg-gray-800 text-white py-12">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm font-medium text-gray-300">
              &copy; {year} <Link href="/about">About</Link> | <Link href="/contact">Contact</Link>
            </p>
          </div>
          <div>
            <ul className="flex space-x-4">
              <li>
                <Link href="/projects">
                  <a className="text-gray-300 hover:text-white">Projects</a>
                </Link>
              </li>
              <li>
                <Link href="/experience">
                  <a className="text-gray-300 hover:text-white">Experience</a>
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;