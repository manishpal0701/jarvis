import { useState, useEffect } from 'react';
import { Grid, Card, CardBody, CardTitle, CardText } from 'reactstrap';
import { Link } from 'react-router-dom';

const Projects = () => {
  const [projects, setProjects] = useState([
    {
      id: 1,
      title: 'Project 1',
      description: 'This is the first project',
      image: 'project_1',
    },
    {
      id: 2,
      title: 'Project 2',
      description: 'This is the second project',
      image: 'project_2',
    },
  ]);

  return (
    <Grid className="grid-container">
      {projects.map((project) => (
        <Card key={project.id} className="card">
          <CardBody>
            <CardTitle className="text-lg">{project.title}</CardTitle>
            <CardText className="text-sm">{project.description}</CardText>
            <img src={`/assets/${project.image}`} alt={project.title} />
          </CardBody>
        </Card>
      ))}
    </Grid>
  );
};

export default Projects;