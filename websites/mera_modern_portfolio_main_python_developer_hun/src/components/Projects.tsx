import { useState, useEffect } from 'react';
import { Grid, Card, Image } from '@tailwind/css';
import { Project } from '../types/project';

const Projects = () => {
  const [projects, setProjects] = useState<Project[]>([
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
          className="bg-white rounded shadow-md"
        >
          <Image
            src={`/assets/${project.image}`}
            alt={project.name}
            className="w-full h-48 object-cover"
          />
          <div className="p-4">
            <h2 className="text-lg font-bold">{project.name}</h2>
            <p className="text-gray-600">{project.description}</p>
          </div>
        </Card>
      ))}
    </Grid>
  );
};

export default Projects;