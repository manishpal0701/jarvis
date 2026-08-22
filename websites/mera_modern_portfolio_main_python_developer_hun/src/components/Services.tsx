import { useState, useEffect } from 'react';
import { Grid, GridItem, Flex, Box } from 'tailwindcss';

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
    <Grid
      templateColumns="repeat(3, 1fr)"
      gap={4}
      justify="center"
      className="max-w-4xl mx-auto"
    >
      {services.map((service) => (
        <GridItem key={service.id} className="bg-white rounded shadow-md p-4">
          <Flex
            direction="column"
            className="flex-1 justify-center items-center"
          >
            <Box
              className="text-lg font-bold text-gray-600"
              dangerouslySetInnerHTML={{ __html: service.name }}
            />
            <Box
              className="text-base text-gray-600"
              dangerouslySetInnerHTML={{ __html: service.description }}
            />
            <Box
              className="mt-4"
              dangerouslySetInnerHTML={{ __html: `<img src="${services[0].image}" alt="${service.name}" />` }}
            />
          </Flex>
        </GridItem>
      ))}
    </Grid>
  );
};

export default Services;