import { useState, useEffect } from 'react';
import { Grid, Card, CardBody, CardTitle, CardText } from 'reactstrap';
import { Link } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import lucide from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useMediaQuery } from 'react-use';

const Services = () => {
  const [services, setServices] = useState([
    {
      id: 1,
      name: 'Service 1',
      description: 'This is service 1',
      image: 'project_1',
    },
    {
      id: 2,
      name: 'Service 2',
      description: 'This is service 2',
      image: 'project_2',
    },
    {
      id: 3,
      name: 'Service 3',
      description: 'This is service 3',
      image: 'project_3',
    },
  ]);

  const { t } = useTranslation();
  const navigate = useNavigate();
  const isMobile = useMediaQuery('(max-width: 768px)');

  return (
    <Grid className="grid-container">
      {services.map((service) => (
        <Card key={service.id} className="card">
          <CardBody>
            <CardTitle>
              <Link to={`/services/${service.id}`}>
                {service.name}
              </Link>
            </CardTitle>
            <CardText>
              {service.description}
            </CardText>
            <img
              src={`https://images.unsplash.com/${service.image}`}
              alt={service.name}
              className="img-fluid"
            />
          </CardBody>
        </Card>
      ))}
    </Grid>
  );
};

export default Services;