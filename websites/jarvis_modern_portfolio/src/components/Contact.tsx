import { useState } from 'react';
import { Form, Field, Button } from 'react-hook-form';
import { useToast } from '@use-toast-notifications';

const Contact = () => {
  const [toast, setToast] = useToast();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (data) => {
    try {
      // Send data to server
      setToast('Message sent successfully', {
        type: 'success',
        duration: 3000,
      });
    } catch (error) {
      setToast('Error sending message', {
        type: 'error',
        duration: 3000,
      });
    }
  };

  return (
    <Form
      onSubmit={handleSubmit}
      // Add form validation and styles as needed
    >
      <Field
        type="text"
        name="name"
        placeholder="Your Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Field
        type="email"
        name="email"
        placeholder="Your Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <Field
        type="textarea"
        name="message"
        placeholder="Your Message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <Button type="submit">Send Message</Button>
    </Form>
  );
};

export default Contact;