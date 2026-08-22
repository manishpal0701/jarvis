import { useState } from 'react';
import { useTheme } from 'next-themes';

const About = () => {
  const { theme } = useTheme();
  const [show, setShow] = useState(false);

  return (
    <div className={`container mx-auto p-4 pt-6 md:p-6 lg:p-12 xl:p-24`}>
      <div className="text-lg leading-loose font-bold text-slate-900">
        <h1 className="text-3xl">About Me</h1>
      </div>
      <div className="text-lg leading-loose font-bold text-slate-900">
        <p className="text-2xl">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet nulla auctor, vestibulum magna sed, convallis ex.</p>
      </div>
      <div className="flex justify-center">
        <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"
          alt="Developer Profile Avatar"
          width={200}
          height={200}
          className="rounded-full shadow-md"
         />
      </div>
      <div className="mt-4">
        <button
          className={`bg-zinc-900 hover:bg-zinc-900 text-white transition duration-300 ease-in-out rounded-md py-2 px-4`}
          onClick={() => setShow(!show)}
        >
          {show ? 'Hide' : 'Show Contact Info'}
        </button>
        {show && (
          <div className="mt-4">
            <p className="text-lg leading-loose font-bold text-slate-900">
              <a href="mailto:manish@example.com">
                <a className="text-white">manish@example.com</a>
              </a>
            </p>
            <p className="text-lg leading-loose font-bold text-slate-900">
              <a href="tel:1234567890">
                <a className="text-white">1234567890</a>
              </a>
            </p>
            <p className="text-lg leading-loose font-bold text-slate-900">
              <a href="https://www.example.com">
                <a className="text-white">https://www.example.com</a>
              </a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default About;