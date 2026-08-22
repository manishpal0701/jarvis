import { useState, useEffect } from 'react';
import { Grid, Card, Image, Heading, Text } from '@tailwind/css';

const Projects = () => {
  const [projects, setProjects] = useState([
    {
      id: 1,
      name: 'Project 1',
      description: 'This is project 1',
      image: 'project_1',
    },
    {
      id: 2,
      name: 'Project 2',
      description: 'This is project 2',
      image: 'project_2',
    },
  ]);

  return (
    <Grid
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      {projects.map((project) => (
        <Card
          key={project.id}
          className="bg-slate-900 text-white rounded-lg shadow-md"
        >
          <Image
            src={`/assets/${project.image}`}
            alt={project.name}
            className="w-full h-48 object-cover"
          />
          <Heading
            as="h2"
            className="text-lg font-bold leading-tight"
          >
            {project.name}
          </Heading>
          <Text
            as="p"
            className="text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: project.description }}
          />
        </Card>
      ))}
    </Grid>
  );
};

export default Projects;