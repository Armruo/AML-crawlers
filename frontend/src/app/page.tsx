'use client';

import { useState, useEffect } from 'react';
import { Layout, Form, Input, Button, Upload, Table, message, Card, Progress, Statistic, Row, Col, Spin, Select } from 'antd';
import { UploadOutlined, DashboardOutlined, CheckCircleOutlined, SyncOutlined, LoadingOutlined } from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import type { UploadProps } from 'antd';
import { log } from 'console';
import { logger } from '../utils/logger';

const { Header, Content } = Layout;

interface TaskProgress {
  status: 'processing' | 'completed' | 'error';
  progress: number;
  address?: string;
  result?: any;
  error?: string;
  current?: number;
  total?: number;
}

export default function Home() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [taskProgress, setTaskProgress] = useState<TaskProgress | null>(null);
  const [stats, setStats] = useState({
    total: 0,
    success: 0,
    error: 0,
    inProgress: 0
  });

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/ws/task/${Date.now()}/`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const message = data.message as TaskProgress;
      setTaskProgress(message);
      
      if (message.status === 'completed' && message.result) {
        setResults(prev => [...prev, {
          address: message.address,
          status: 'success',
          result: message.result
        }]);
        setStats(prev => ({
          ...prev,
          success: prev.success + 1,
          inProgress: Math.max(0, prev.inProgress - 1)
        }));
      } else if (message.status === 'error') {
        setResults(prev => [...prev, {
          address: message.address,
          status: 'error',
          error: message.error
        }]);
        setStats(prev => ({
          ...prev,
          error: prev.error + 1,
          inProgress: Math.max(0, prev.inProgress - 1)
        }));
      } else if (message.status === 'processing') {
        setStats(prev => ({
          ...prev,
          inProgress: prev.inProgress + 1
        }));
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      logger.info('API URL:', apiUrl);
      const response = await fetch(`${apiUrl}/api/crawler/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ 
          address: values.url,
          network: values.network 
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Task submission failed:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });
        message.error(`Failed to submit task: ${JSON.stringify(errorData.error || errorData)}`);
        return;
      }
      
      const result = await response.json();
      console.log('Task submitted successfully:', result);
      message.success('Task submitted successfully');
      setStats(prev => ({
        ...prev,
        total: prev.total + 1
      }));
    } catch (error) {
      console.error('Task submission error:', error);
      message.error('Failed to submit task: Network error');
    } finally {
      setLoading(false);
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    action: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/crawler/upload_file/`,
    headers: {
      'Accept': 'application/json',
    },
    onChange(info) {
      if (info.file.status === 'done') {
        console.log('Upload response:', info.file.response);
        message.success(`${info.file.name} uploaded successfully`);
        const addresses = info.file.response.results || [];
        setResults(prev => [...prev, ...addresses]);
        setStats(prev => ({
          ...prev,
          total: prev.total + addresses.length
        }));
      } else if (info.file.status === 'error') {
        console.error('File upload error:', info.file);
        message.error(`${info.file.name} upload failed: ${info.file.error?.message || 'Unknown error'}`);
      }
    },
  };

  const columns = [
    {
      title: 'Address',
      dataIndex: 'address',
      key: 'address',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ color: status === 'success' ? '#52c41a' : '#f5222d' }}
        >
          {status === 'success' ? 'Success' : 'Failed'}
        </motion.span>
      ),
    },
    {
      title: 'Result',
      dataIndex: 'result',
      key: 'result',
      render: (result: any) => (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.3 }}
        >
          {result ? (
            <pre style={{ maxHeight: '100px', overflow: 'auto' }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          ) : '-' }
        </motion.div>
      ),
    },
  ];

  return (
    <Layout className="min-h-screen">
      <Header className="flex items-center justify-between">
        <motion.h1 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-white text-xl"
        >
          Misttrack Crawler Dashboard
        </motion.h1>
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-white"
        >
          <DashboardOutlined className="mr-2" />
          Task Monitor
        </motion.div>
      </Header>
      
      <Content className="p-8">
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <motion.div whileHover={{ scale: 1.02 }} transition={{ type: "spring" }}>
              <Card>
                <Statistic
                  title="Total Tasks"
                  value={stats.total}
                  prefix={<DashboardOutlined />}
                />
              </Card>
            </motion.div>
          </Col>
          <Col span={6}>
            <motion.div whileHover={{ scale: 1.02 }} transition={{ type: "spring" }}>
              <Card>
                <Statistic
                  title="Successful Tasks"
                  value={stats.success}
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Card>
            </motion.div>
          </Col>
          <Col span={6}>
            <motion.div whileHover={{ scale: 1.02 }} transition={{ type: "spring" }}>
              <Card>
                <Statistic
                  title="Failed Tasks"
                  value={stats.error}
                  valueStyle={{ color: '#cf1322' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Card>
            </motion.div>
          </Col>
          <Col span={6}>
            <motion.div whileHover={{ scale: 1.02 }} transition={{ type: "spring" }}>
              <Card>
                <Statistic
                  title="Tasks in Progress"
                  value={stats.inProgress}
                  prefix={<SyncOutlined spin />}
                />
              </Card>
            </motion.div>
          </Col>
        </Row>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="mt-4">
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Card>
                  <div className="text-center">
                    <div className="text-lg mb-2">Task Status Distribution</div>
                    <Progress type="circle" percent={stats.total > 0 ? (stats.success / stats.total) * 100 : 0} />
                    <div className="mt-4">
                      <div>Success Rate: {stats.total > 0 ? ((stats.success / stats.total) * 100).toFixed(1) : 0}%</div>
                      <div>Failure Rate: {stats.total > 0 ? ((stats.error / stats.total) * 100).toFixed(1) : 0}%</div>
                    </div>
                  </div>
                </Card>
              </Col>
              <Col span={16}>
                <Card>
                  <div className="text-lg mb-4">Task Status Overview</div>
                  <div className="flex justify-around">
                    <Progress 
                      type="dashboard"
                      percent={stats.total > 0 ? (stats.success / stats.total) * 100 : 0}
                      status="success"
                      format={() => `${stats.success} Success`}
                    />
                    <Progress 
                      type="dashboard"
                      percent={stats.total > 0 ? (stats.error / stats.total) * 100 : 0}
                      status="exception"
                      format={() => `${stats.error} Failed`}
                    />
                    <Progress 
                      type="dashboard"
                      percent={stats.total > 0 ? (stats.inProgress / stats.total) * 100 : 0}
                      status="active"
                      format={() => `${stats.inProgress} In Progress`}
                    />
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="mt-4">
            <Form form={form} onFinish={onFinish} layout="vertical">
              <Form.Item
                label="Network"
                name="network"
                rules={[{ required: true, message: 'Please select a network' }]}
              >
                <Select placeholder="Select a network">
                  <Select.Option value="ETH">ETH</Select.Option>
                  <Select.Option value="BSC">BSC</Select.Option>
                  <Select.Option value="Solana">Solana</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item
                label="Address"
                name="url"
                rules={[{ required: true, message: 'Please enter an address' }]}
              >
                <Input placeholder="Enter the address to crawl" />
              </Form.Item>
              
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Start Crawling
                </Button>
              </Form.Item>
            </Form>

            <div className="mt-4">
              <Upload {...uploadProps}>
                <Button icon={<UploadOutlined />}>Upload Batch Task File</Button>
              </Upload>
            </div>

            <AnimatePresence>
              {taskProgress && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4"
                >
                  <Progress
                    percent={taskProgress.progress}
                    status={taskProgress.status === 'error' ? 'exception' : 
                           taskProgress.status === 'completed' ? 'success' : 'active'}
                  />
                  <div className="text-sm text-gray-500 mt-2">
                    {taskProgress.current && taskProgress.total && 
                     `Progress: ${taskProgress.current}/${taskProgress.total}`}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="mt-4">
              <Table 
                columns={columns} 
                dataSource={results}
                rowKey="address"
                pagination={{ pageSize: 10 }}
              />
            </div>
          </Card>
        </motion.div>
      </Content>
    </Layout>
  );
}
