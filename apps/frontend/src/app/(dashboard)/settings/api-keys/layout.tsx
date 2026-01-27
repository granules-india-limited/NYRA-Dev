import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'API Keys | NYRA',
  description: 'Manage your API keys for programmatic access to NYRA',
  openGraph: {
    title: 'API Keys | NYRA',
    description: 'Manage your API keys for programmatic access to NYRA',
    type: 'website',
  },
};

export default async function APIKeysLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
