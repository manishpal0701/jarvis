import Image from 'next/image';

const Hero = () => {
  return (
    <section className="bg-[#333] py-12 text-white">
      <div className="container mx-auto p-4">
        <div className="flex flex-col items-center">
          <h1 className="text-5xl font-bold">Hero Section</h1>
          <div className="flex space-x-4">
            <div className="bg-[#333] p-4 rounded-md">
              <Image src={require('../assets/feature-image-1.jpg')} width={600} height={400} alt="Feature Image 1" />
            </div>
            <div className="bg-[#333] p