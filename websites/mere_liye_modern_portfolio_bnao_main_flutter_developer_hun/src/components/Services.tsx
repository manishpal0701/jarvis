import { useState, useEffect } from 'react';
import { Grid, Card, Image } from '@tailwind/css';
import { Link } from 'react-router-dom';

const Services = () => {
  const [services, setServices] = useState([
    {
      id: 1,
      name: 'Service 1',
      description: 'Description 1',
      image: 'project_1',
    },
    {
      id: 2,
      name: 'Service 2',
      description: 'Description 2',
      image: 'project_2',
    },
    {
      id: 3,
      name: 'Service 3',
      description: 'Description 3',
      image: 'project_3',
    },
  ]);

  return (
    <Grid
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      items={services}
    >
      {services.map((service) => (
        <Card
          key={service.id}
          className="bg-slate-900 text-white rounded-lg shadow-md"
        >
          <Image
            src={`/assets/${service.image}`}
            alt={service.name}
            className="w-full h-48 object-cover"
          />
          <div className="p-4">
            <h2 className="text-lg font-bold">{service.name}</h2>
            <p className="text-sm">{service.description}</p>
          </div>
          <Link
            to={`/services/${service.id}`}
            className="bg-emerald-400 hover:bg-emerald-500 text-white py-2 px-4 rounded"
          >
            Learn More
          </Link>
        </Card>
      ))}
    </Grid>
  );
};

export default Services;