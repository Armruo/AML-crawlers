'use client';

import { useState, useEffect } from 'react';
import { Layout, Form, Input, Button, Upload, Table, message, Card, Progress, Statistic, Row, Col, Spin, Select, Tooltip } from 'antd';
import { UploadOutlined, DashboardOutlined, CheckCircleOutlined, SyncOutlined, LoadingOutlined } from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import type { UploadProps } from 'antd';
import { log } from 'console';
import { logger } from '../utils/logger';

const { Header, Content } = Layout;

interface TaskProgress {
  status: 'processing' | 'completed' | 'error';
  address?: string;
  data?: {
    address: string;
    result?: {
      address?: string;
      input_address?: string;
      network?: string;
      risk_score?: string | number;
      risk_level?: string;
      risk_type?: string;
      address_labels?: string[];
      volume?: string;
      labels?: string[];
      transactions?: any[];
      related_addresses?: string[];
    }
  };
  error?: string;
  current?: number;
  total?: number;
}

interface CrawlerResult {
  key: string;
  address: string;
  network: string;
  status: 'success' | 'error';
  result?: {
    address: string;
    risk_score?: string | number;
    risk_level?: string;
    risk_type?: string;
    address_labels?: string[];
    volume?: string;
    labels?: string[];
    transactions?: any[];
    related_addresses?: string[];
  };
  error?: string;
}

export default function Home() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<CrawlerResult[]>([]);
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
      
      console.log('Raw WebSocket message:', data);
      
      if (message.status === 'completed' && message.data) {
        // Extract address and result
        const inputAddress = message.data.address || '';
        const [network, cleanAddress] = inputAddress.includes('/')
          ? inputAddress.split('/')
          : ['BSC', inputAddress];
          
        // Get the final address from all possible sources
        const address = cleanAddress || 
                       message.data.result?.address ||
                       message.data.result?.input_address ||
                       message.address;

        if (!address) {
          console.error('No address found in message:', message);
          return;
        }

        console.log('Processing completed message:', {
          inputAddress,
          network,
          address,
          result: message.data.result
        });

        const newResult: CrawlerResult = {
          key: address,
          address: address,
          network: network,
          status: 'success',
          result: {
            address: address,
            ...message.data.result,
          }
        };

        console.log('Adding new result:', newResult);
        setResults(prev => [...prev, newResult]);
        
        setStats(prev => ({
          ...prev,
          success: prev.success + 1,
          inProgress: Math.max(0, prev.inProgress - 1)
        }));
      } else if (message.status === 'error') {
        const inputAddress = message.data?.address || '';
        const [network, address] = inputAddress.includes('/')
          ? inputAddress.split('/')
          : ['BSC', inputAddress];

        if (!address) {
          console.error('No address found in error message:', message);
          return;
        }

        console.log('Processing error message:', {
          inputAddress,
          network,
          address,
          error: message.data?.error
        });

        const newResult: CrawlerResult = {
          key: address,
          address: address,
          network: network,
          status: 'error',
          error: message.data?.error || 'Unknown error'
        };

        console.log('Adding error result:', newResult);
        setResults(prev => [...prev, newResult]);
        
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
    accept: '.csv',
    action: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/crawler/upload_file/`,
    headers: {
      'Accept': 'application/json',
    },
    data: (file) => {
      const network = form.getFieldValue('network');
      return {
        network: network || 'ETH'  // 默认使用ETH网络
      };
    },
    beforeUpload: (file) => {
      const network = form.getFieldValue('network');
      if (!network) {
        message.error('Please select a network before uploading a file');
        return false;
      }
      
      const isCSV = file.type === 'text/csv' || file.name.endsWith('.csv');
      if (!isCSV) {
        message.error('You can only upload CSV files!');
        return false;
      }
      return true;
    },
    onChange(info) {
      console.log('File upload info:', info);
      if (info.file.status === 'uploading') {
        message.loading('Uploading file...');
      } else if (info.file.status === 'done') {
        console.log('Upload response:', info.file.response);
        message.success(`${info.file.name} uploaded successfully`);
        
        // 从响应中获取结果数组
        const results = info.file.response.results || [];
        console.log('Raw results:', results);
        
        // 格式化地址数据
        const formattedAddresses = results.map((result: any) => {
          // 从data中提取地址信息
          const fullAddress = result.data?.address || '';
          const [network, address] = fullAddress.includes('/')
            ? fullAddress.split('/')
            : ['BSC', fullAddress];
            
          console.log('Processing address:', {
            fullAddress,
            network,
            address,
            result
          });

          return {
            key: address,
            address: address,  // 只使用地址部分，不包含网络前缀
            network: network,
            status: result.success ? 'success' : 'error',
            result: {
              address: address,
              risk_score: result.data?.risk_score,
              risk_level: result.data?.risk_level,
              risk_type: result.data?.risk_type,
              address_labels: typeof result.data?.address_labels === 'string' 
                ? [result.data.address_labels] 
                : result.data?.address_labels || [],
              volume: result.data?.volume,
              labels: result.data?.labels || [],
              transactions: result.data?.transactions || [],
              related_addresses: result.data?.related_addresses || []
            }
          };
        });

        console.log('Formatted addresses:', formattedAddresses);
        
        // 更新结果列表和统计信息
        setResults(prev => [...prev, ...formattedAddresses]);
        setStats(prev => ({
          ...prev,
          total: prev.total + results.length,
          success: prev.success + results.filter((r: any) => r.success).length,
          error: prev.error + results.filter((r: any) => !r.success).length
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
      fixed: 'left',
      width: 400,
      render: (text: string, record: CrawlerResult) => {
        console.log('Rendering address column:', { text, record });
        
        if (!record.address) {
          console.warn('No address found for record:', record);
          return 'N/A';
        }
        
        if (record.status === 'error') {
          return <span style={{ color: 'red' }}>{record.address}</span>;
        }
        
        return (
          <Tooltip title={record.address}>
            <span style={{ 
              cursor: 'pointer',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              display: 'block',
              fontFamily: 'monospace',
              maxWidth: '380px'
            }}>
              {record.address}
            </span>
          </Tooltip>
        );
      }
    },
    {
      title: 'Network',
      dataIndex: 'network',
      key: 'network',
    },
    {
      title: 'Risk Level',
      dataIndex: ['result', 'risk_level'],
      key: 'risk_level',
      render: (text: string) => {
        if (!text) return 'N/A';
        const color = text.toLowerCase().includes('risky') ? 'red' : 'inherit';
        return <span style={{ color }}>{text}</span>;
      }
    },
    {
      title: 'Risk Score',
      dataIndex: ['result', 'risk_score'],
      key: 'risk_score',
      render: (text: string) => text || 'N/A'
    },
    {
      title: 'Risk Type',
      dataIndex: ['result', 'risk_type'],
      key: 'risk_type',
      render: (text: string) => text || 'N/A'
    },
    {
      title: 'Volume',
      dataIndex: ['result', 'volume'],
      key: 'volume',
      render: (text: string) => text || 'N/A'
    },
    {
      title: 'Address Labels',
      dataIndex: ['result', 'address_labels'],
      key: 'address_labels',
      render: (labels: string[]) => {
        if (!labels || labels.length === 0) return 'N/A';
        return labels.join(', ');
      }
    },
    {
      title: 'Labels',
      dataIndex: ['result', 'labels'],
      key: 'labels',
      render: (labels: string[]) => {
        if (!labels || labels.length === 0) return 'N/A';
        return labels.join(', ');
      }
    },
    {
      title: 'Related Addresses',
      dataIndex: ['result', 'related_addresses'],
      key: 'related_addresses',
      render: (addresses: string[]) => {
        if (!addresses || addresses.length === 0) return 'N/A';
        return addresses.slice(0, 3).join(', ') + (addresses.length > 3 ? '...' : '');
      }
    },
    {
      title: 'Status',
      key: 'status',
      render: (_: any, record: CrawlerResult) => {
        if (record.status === 'error') {
          return <span style={{ color: 'red' }}>Error: {record.error}</span>;
        }
        return <span style={{ color: 'green' }}>Success</span>;
      }
    }
  ];

  return (
    <Layout className="min-h-screen">
      <Header className="flex items-center justify-between">
        <motion.h1
          className="text-3xl font-bold mb-8"
          style={{
            color: '#ffffff',  
            textShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)',  
            background: 'linear-gradient(45deg, #1a1a1a, #2d2d2d)',  
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            display: 'inline-block'
          }}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
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
            <Form form={form} onFinish={onFinish} layout="inline" className="mb-4">
              <Form.Item
                name="network"
                label="Network"
                rules={[{ required: true, message: 'Please select a network' }]}
              >
                <Select style={{ width: 120 }}>
                  <Select.Option value="ETH">ETH</Select.Option>
                  <Select.Option value="BSC">BSC</Select.Option>
                  <Select.Option value="SOL">SOL</Select.Option>
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
              <div className="text-sm text-gray-500 mt-2">
                Please upload a CSV file with an "address" column. The file should be encoded in UTF-8 or GBK.
              </div>
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

            <div className="mt-6">
              <h3 className="text-lg font-medium mb-4">Crawling Results</h3>
              <Table 
                columns={columns} 
                dataSource={results}
                rowKey="key"
                pagination={{ pageSize: 10 }}
                className="shadow-sm"
                scroll={{ x: true }}  
              />
              {results.length > 0 && (
                <div className="mt-4 bg-gray-50 p-4 rounded">
                  <h4 className="text-md font-medium mb-2">Latest Result Details</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Risk Score: {results[results.length - 1]?.result?.risk_score || 'N/A'}</p>
                      <p className="text-sm text-gray-600">Risk Level: {results[results.length - 1]?.result?.risk_level || 'N/A'}</p>
                      <p className="text-sm text-gray-600">Risk Type: {results[results.length - 1]?.result?.risk_type || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Network: {results[results.length - 1]?.network || 'N/A'}</p>
                      <p className="text-sm text-gray-600">Labels: {results[results.length - 1]?.result?.address_labels?.join(', ') || 'None'}</p>
                      <p className="text-sm text-gray-600">Volume: {results[results.length - 1]?.result?.volume || 'N/A'}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </motion.div>
      </Content>
    </Layout>
  );
}
