import { Metadata } from 'next';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Worker Conversation | NYRA',
  description: 'Interactive Worker conversation powered by NYRA',
  openGraph: {
    title: 'Worker Conversation | NYRA',
    description: 'Interactive Worker conversation powered by NYRA',
    type: 'website',
  },
};

export default async function AgentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
