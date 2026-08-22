import { useState, useEffect } from "react";

const Services = () => {
  const [services, setServices] = useState([
    "Services 1",
    "Services 2",
    "Services 3",
    "Services 4",
    "Services 5",
  ]);

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-3xl font-bold mb-4">Our Services</h2>
      <ul>
        {services.map((service, index) => (
          <li key={index}>
            <span className="text-gray-600">{service}</span>
          </li>
        ))}
      </ul>
    </div>