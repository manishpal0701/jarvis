import Link from 'next/link';

const Footer = () => {
  return (
    <footer className="bg-zinc-900 text-white py-4">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center">
          <div>
            <p>&copy; 2023 ek modern portfolio</p>
          </div>
          <div>
            <ul>
              <li>
                <Link href="https://example.com">
                  <a target="_blank" rel="noopener noreferrer">
                    LinkedIn
                  </a>
                </Link>
              </li>
              <li>
                <Link href="https://example.com">
                  <a target="_blank" rel="noopener noreferrer">
                    GitHub
                  </a>
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