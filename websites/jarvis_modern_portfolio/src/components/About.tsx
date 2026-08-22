import { useState } from 'react';
import { Link } from 'react-router-dom';

const About = () => {
  const [name, setName] = useState('John Doe');
  const [description, setDescription] = useState('Lorem ipsum dolor sit amet, consectetur adipiscing elit.');
  const [image, setImage] = useState('https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80');

  return (
    <section className="bg-slate-900 text-white">
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-4">About Me</h1>
        <p className="text-lg mb-8">{description}</p>
        <div className="flex justify-center mb-8">
          <img src={image} alt={name} className="w-1/2 rounded-full" />
        </div>
        <p className="text-lg">Get in touch with me at <Link to="mailto:john.doe@example.com">john.doe@example.com</Link> or call me at <Link to="tel:+1234567890">+1234567890</Link>.</p>
      </div>
    </section>
  );
};

export default About;