import { useState } from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <nav
      className="bg-slate-900 text-white flex justify-between items-center py-4"
      role="navigation"
    >
      <div className="flex items-center">
        <Link to="/" className="text-lg font-bold">
          Client
        </Link>
        <button onClick={handleToggle} className="text-sm">
          {isOpen ? 'Close' : 'Menu'}
        </button>
      </div>
      <div className={`hidden ${isOpen ? 'block' : 'none'}`}>
        <ul>
          <li>
            <Link to="/about" className="text-sm">
              About
            </Link>
          </li>
          <li>
            <Link to="/skills" className="text-sm">
              Skills
            </Link>
          </li>
          <li>
            <Link to="/projects" className="text-sm">
              Projects
            </Link>
          </li>
          <li>
            <Link to="/experience" className="text-sm">
              Experience
            </Link>
          </li>
          <li>
            <Link to="/contact" className="text-sm">
              Contact
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;