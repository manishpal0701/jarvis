import React from 'react';
import { Form, Field, Button } from 'react-hook-form';
import { v4 as uuidv4 } from 'uuid';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { TailwindConfig } from '@tailwindcss/tailwind-config';
import { lucideReact } from 'lucide-react';

const Contact = () => {
  const { register, handleSubmit } = React.useForm();
  const navigate = React.useNavigate();
  const { t } = useTranslation();

  const onSubmit = async (data) => {
    console.log(data);
    navigate('/thanks');
  };

  return (
    <div className="bg-slate-900 text-white">
      <Form
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-col items-center justify-center h-screen"
      >
        <h2 className="text-3xl font-bold mb-4">{t('Contact Me')}</h2>
        <div className="flex flex-col mb-4">
          <label
            htmlFor="name"
            className="block text-sm font-medium text-slate-300 mb-2"
          >
            {t('Name')}
          </label>
          <input
            type="text"
            id="name"
            name="name"
            className="block w-full p-2 pl-10 text-sm text-slate-300 border border-slate-400 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900"
            {...register('name')}
          />
        </div>
        <div className="flex flex-col mb-4">
          <label
            htmlFor="email"
            className="block text-sm font-medium text-slate-300 mb-2"
          >
            {t('Email')}
          </label>
          <input
            type="email"
            id="email"
            name="email"
            className="block w-full p-2 pl-10 text-sm text-slate-300 border border-slate-400 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900"
            {...register('email')}
          />
        </div>
        <div className="flex flex-col mb-4">
          <label
            htmlFor="message"
            className="block text-sm font-medium text-slate-300 mb-2"
          >
            {t('Message')}
          </label>
          <textarea
            id="message"
            name="message"
            className="block w-full p-2 pl-10 text-sm text-slate-300 border border-slate-400 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900"
            {...register('message')}
          />
        </div>
        <div className="flex justify-center mb-4">
          <Button
            type="submit"
            className="bg-emerald-400 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-900"
          >
            {t('Send')}
          </Button>
        </div>
      </Form>
    </div>
  );
};

export default Contact;