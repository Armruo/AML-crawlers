import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ConfigProvider, App } from 'antd';
import MainLayout from '../components/layout/MainLayout';
import StyledComponentsRegistry from '../lib/AntdRegistry';
import { metadata } from './metadata';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <StyledComponentsRegistry>
          <ConfigProvider>
            <App>
              <MainLayout>{children}</MainLayout>
            </App>
          </ConfigProvider>
        </StyledComponentsRegistry>
      </body>
    </html>
  );
}