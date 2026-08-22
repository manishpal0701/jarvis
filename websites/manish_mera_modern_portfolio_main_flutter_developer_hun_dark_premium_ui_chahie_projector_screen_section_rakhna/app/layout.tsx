import Link from 'next/link';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useSession } from '../hooks/useSession';

function Layout({ children }: { children: React.ReactNode }) {
  const { data: session, error: errorSession } = useSession();

  if (errorSession) {
    return <div>Error: {errorSession.message}</div>;
  }

  return (
    <div className="font-sans text-lg min-h-screen">
      <Header />
      <main className="flex flex-col justify-center items-center">
        {children}
      </main>
      <Footer />
    </div>
  );
}

export default Layout;