import Image from 'next/image';
import { useState } from 'react';

const Page = () => {
  const [count, setCount] = useState(0);

  return (
    <div className="flex justify-center items-center h-screen">
      <div className="bg-white rounded-lg shadow-md p-4">
        <h1 className="text-3xl font-bold">Page Title</h1>
        <p className="text-lg font-medium">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
        <button
          className="bg-orange-500 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded"
          onClick={() => setCount(count + 1)}
        >