'use client';

import React, { useState } from 'react';
import { Layout, Menu, theme, Typography } from 'antd';
import {
  DashboardOutlined,
  RadarChartOutlined,
  SettingOutlined,
  DatabaseOutlined,
  ApiOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: '/crawlers',
    icon: <RadarChartOutlined />,
    label: 'Crawlers',
    children: [
      {
        key: '/crawlers/misttrace',
        icon: <ApiOutlined />,
        label: 'Misttrace',
      },
      {
        key: '/crawlers/new',
        icon: <DatabaseOutlined />,
        label: 'Add New Crawler',
      },
    ],
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
  {
    key: '/team',
    icon: <TeamOutlined />,
    label: 'Team',
  },
];

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={(value) => setCollapsed(value)}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: 32, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <RadarChartOutlined style={{ fontSize: '1.5em', color: '#fff' }} />
        </div>
        <Menu
          theme="dark"
          defaultSelectedKeys={[pathname]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => {
            // Handle navigation here if needed
          }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header style={{ 
          padding: 0, 
          background: colorBgContainer,
          position: 'sticky',
          top: 0,
          zIndex: 1,
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          paddingLeft: 24
        }}>
          <Title level={4} style={{ margin: 0 }}>Web Crawler Management System</Title>
        </Header>
        <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
          <div
            style={{
              padding: 24,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              minHeight: 'calc(100vh - 112px)',
            }}
          >
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
