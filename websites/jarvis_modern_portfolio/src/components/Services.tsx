import { useState, useEffect } from 'react';
import { Grid, Container } from '@tailwind/css';

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
      image: 'project_1',
    },
  ]);

  return (
    <Container maxW="lg" mx="auto" p={4}>
      <Grid
        gridTemplateColumns="repeat(3, 1fr)"
        gridTemplateRows="repeat(3, 1fr)"
        gap={4}
        className="grid gap-4"
      >
        {services.map((service) => (
          <Grid
            key={service.id}
            className="bg-slate-900 text-white rounded-lg shadow-md"
          >
            <img src={`/assets/${service.image}`} alt={service.name} />
            <h2 className="text-2xl font-bold">{service.name}</h2>
            <p className="text-lg">{service.description}</p>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default Services;