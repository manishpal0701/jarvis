import { useBreakpointValue } from '@rainbow-exploded/react';

const Navbar = () => {
  const [isMobile, setIsMobile] = useState(false);

  const mobileMenu = useBreakpointValue({
    visible: isMobile,
    hidden: !isMobile,
  });

  return (
    <nav
      className={`flex justify-between items-center py-4 bg-slate-900 text-white ${
        mobileMenu ? 'hidden' : 'flex'
      }`}
    >
      <a href="/">
        <a>
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"
            alt="Developer Profile Avatar"
            className="w-12 h-12 rounded-full"
          />
        </a>
      </a>
      <ul className="flex space-x-4">
        <li>
          <a href="/about">
            <a>About</a>
          </a>
        </li>
        <li>
          <a href="/skills">
            <a>Skills</a>
          </a>
        </li>
        <li>
          <a href="/projects">
            <a>Projects</a>
          </a>
        </li>
        <li>
          <a href="/experience">
            <a>Experience</a>
          </a>
        </li>
        <li>
          <a href="/contact">
            <a>Contact</a>
          </a>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;