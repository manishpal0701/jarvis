import { useState } from 'react';
import { Form, Field, Button } from 'react-hook-form';
import { useToast } from '@use-toast-notifier/core';

const Contact = () => {
  const [toast, setToast] = useToast();

  const onSubmit = async (data) => {
    try {
      // Send form data to server
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        setToast({
          title: 'Thank you for your message!',
          description: 'We will get back to you soon.',
          type: 'success',
        });
      } else {
        setToast({
          title: 'Error sending message',
          description: 'Please try again later.',
          type: 'error',
        });
      }
    } catch (error) {
      setToast({
        title: 'Error sending message',
        description: 'Please try again later.',
        type: 'error',
      });
    }
  };

  return (
    <Form
      onSubmit={onSubmit}
      form={Form}
      render={({ register, handleSubmit, errors }) => (
        <form>
          <Field
            name="name"
            type="text"
            placeholder="Your Name"
            register={register}
            required
          />
          <Field
            name="email"
            type="email"
            placeholder="Your Email"
            register={register}
            required
          />
          <Field
            name="message"
            type="text"
            placeholder="Your Message"
            register={register}
            required
          />
          <Button type="submit">Send Message</Button>
        </form>
      )}
    />
  );
};

export default Contact;