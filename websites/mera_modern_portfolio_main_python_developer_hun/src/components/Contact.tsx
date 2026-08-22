import React from 'react';
import { Form, Field, Button } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { v4 as uuidv4 } from 'uuid';

interface ContactFormValues {
  name: string;
  email: string;
  message: string;
}

const Contact: React.FC = () => {
  const { t } = useTranslation();
  const { register, handleSubmit } = React Hook Form.useForm();

  const onSubmit = async (data: ContactFormValues) => {
    console.log(data);
  };

  return (
    <Form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col justify-center items-center w-full h-screen"
    >
      <h2 className="text-3xl font-bold mb-4">{t('Contact Us')}</h2>
      <div className="flex flex-col space-y-4">
        <Field
          name="name"
          type="text"
          placeholder={t('Your Name')}
          className="w-full p-4 mb-2 border-2 border-gray-400 rounded"
        />
        <Field
          name="email"
          type="email"
          placeholder={t('Your Email')}
          className="w-full p-4 mb-2 border-2 border-gray-400 rounded"
        />
        <Field
          name="message"
          type="textarea"
          placeholder={t('Your Message')}
          className="w-full p-4 border-2 border-gray-400 rounded"
        />
      </div>
      <Button
        type="submit"
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      >
        {t('Send Message')}
      </Button>
    </Form>
  );
};

export default Contact;