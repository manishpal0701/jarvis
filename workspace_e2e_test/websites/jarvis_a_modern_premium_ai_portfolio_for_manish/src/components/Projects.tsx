import { useState, useEffect } from 'react';
import { Grid, Card, CardBody, CardTitle, CardText } from 'tailwindcss';

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
    <Grid className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <Card key={project.id} className="bg-slate-900 text-white">
          <CardBody>
            <CardTitle className="text-2xl font-bold">{project.name}</CardTitle>
            <CardText className="text-slate-300">{project.description}</CardText>
            <img src={`/assets/${project.image}`} alt={project.name} className="w-full h-48 object-cover" />
          </CardBody>
        </Card>
      ))}
    </Grid>
  );
};

export default Projects;