'use client';

import { useState, useEffect } from 'react';
import { Layout, Form, Input, Button, Upload, Table, message, Card, Progress, Statistic, Row, Col, Spin, Select, Tooltip } from 'antd';
import { UploadOutlined, DashboardOutlined, CheckCircleOutlined, SyncOutlined, LoadingOutlined, CopyOutlined, DownloadOutlined, LinkOutlined } from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import type { UploadProps } from 'antd';
import { log } from 'console';
import { logger } from '../utils/logger';
import './table.css';

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
  progress?: number;
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
  const [processedAddressNetworks, setProcessedAddressNetworks] = useState<Set<string>>(new Set());

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/ws/task/${Date.now()}/`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const message = data.message as TaskProgress;
      
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
        setResults(prev => {
          const existingAddressNetworks = new Set(prev.map(item => `${item.address}-${item.network}`));
          if (existingAddressNetworks.has(`${newResult.address}-${newResult.network}`)) return prev;
          return [...prev, newResult];
        });
        
        // 更新进度
        setTaskProgress(prev => {
          if (!prev) return null;
          const current = (prev.current || 0) + 1;
          const total = prev.total || 0;
          return {
            ...prev,
            status: current >= total ? 'completed' : 'processing',
            current,
            progress: Math.round((current / total) * 100)
          };
        });
        
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
        setResults(prev => {
          const existingAddressNetworks = new Set(prev.map(item => `${item.address}-${item.network}`));
          if (existingAddressNetworks.has(`${newResult.address}-${newResult.network}`)) return prev;
          return [...prev, newResult];
        });
        
        // 更新进度
        setTaskProgress(prev => {
          if (!prev) return null;
          const current = (prev.current || 0) + 1;
          const total = prev.total || 0;
          return {
            ...prev,
            status: current >= total ? 'completed' : 'processing',
            current,
            progress: Math.round((current / total) * 100)
          };
        });
        
        setStats(prev => ({
          ...prev,
          error: prev.error + 1,
          inProgress: Math.max(0, prev.inProgress - 1)
        }));
      } else if (message.status === 'processing') {
        // 更新进度
        setTaskProgress(prev => {
          if (!prev) return message;
          return {
            ...prev,
            ...message,
            progress: message.progress || prev.progress
          };
        });
        
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

  const onSingleAddressSubmit = async (address: string) => {
    if (!form.getFieldValue('network')) {
      message.error('Please select a network first');
      return;
    }
    setLoading(true);
    try {
      const network = form.getFieldValue('network');
      console.log('Submitting single address:', { address, network });

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
      const response = await fetch(`${apiUrl}/api/crawler/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ 
          address: address,
          network: network
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
    } catch (error) {
      console.error('Task submission error:', error);
      message.error('Failed to submit task: Network error');
    } finally {
      setLoading(false);
    }
  };

  const onFinish = async (values: any) => {
    // This will only be called for batch file upload
    try {
      setLoading(true);
      console.log('Form Data:', values);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
      const response = await fetch(`${apiUrl}/api/crawler/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ 
          address: values.address,
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
          const [network, cleanAddress] = fullAddress.includes('/')
            ? fullAddress.split('/')
            : [form.getFieldValue('network'), fullAddress];
            
          console.log('Processing address:', {
            fullAddress,
            network,
            address: cleanAddress,
            result
          });

          return {
            key: cleanAddress,
            address: cleanAddress,
            network: network,
            status: result.success ? 'success' : 'error',
            result: {
              address: cleanAddress,
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
        
        // 更新结果列表，过滤掉重复地址
        setResults(prev => {
          const existingAddressNetworks = new Set(prev.map(item => `${item.address}-${item.network}`));
          const newUniqueAddresses = formattedAddresses.filter(
            item => !existingAddressNetworks.has(`${item.address}-${item.network}`)
          );
          return [...prev, ...newUniqueAddresses];
        });

        // 更新总任务数和状态
        setStats(prev => ({
          ...prev,
          total: prev.total + formattedAddresses.length,
          success: prev.success + formattedAddresses.filter(r => r.status === 'success').length,
          error: prev.error + formattedAddresses.filter(r => r.status === 'error').length
        }));

        // 更新任务进度
        setTaskProgress({
          status: 'processing',
          progress: 0,
          current: 0,
          total: results.length
        });
      } else if (info.file.status === 'error') {
        console.error('File upload error:', info.file);
        message.error(`${info.file.name} upload failed: ${info.file.error?.message || 'Unknown error'}`);
      }
    },
  };

  const handleExportTable = () => {
    try {
      // 准备导出数据
      const exportData = results.map((item, index) => ({
        'No.': index + 1,
        'Address': item.address,
        'Network': item.network,
        'Risk Level': item.result?.risk_level || 'N/A',
        'Risk Type': item.result?.risk_type || 'N/A',
        'Address/Risk Label': Array.isArray(item.result?.address_labels) 
          ? item.result.address_labels.join(', ') 
          : (item.result?.address_labels || 'N/A'),
        'Volume(USD)/%': item.result?.volume || 'N/A',
        'Status': item.status === 'error' ? `Error: ${item.error}` : 'Success'
      }));

      // 创建CSV内容
      const headers = Object.keys(exportData[0]);
      const csvContent = [
        headers.join(','),
        ...exportData.map(row => 
          headers.map(header => {
            const value = row[header];
            // 如果值包含逗号、引号或换行符，需要用引号包裹并处理引号
            return /[",\n]/.test(value) 
              ? `"${value.replace(/"/g, '""')}"` 
              : value
          }).join(',')
        )
      ].join('\n');

      // 创建Blob对象
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      
      // 创建下载链接
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `misttrack_address_results_${new Date().toISOString().slice(0,19).replace(/[:-]/g, '')}.csv`);
      document.body.appendChild(link);
      
      // 触发下载
      link.click();
      
      // 清理
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success('Table exported successfully');
    } catch (error) {
      console.error('Export error:', error);
      message.error('Failed to export table');
    }
  };

  const columns = [
    {
      title: '#',
      key: 'index',
      width: 60,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: 'Address',
      dataIndex: 'address',
      key: 'address',
      fixed: 'left',
      width: 420,
      sorter: (a, b) => a.address.localeCompare(b.address),
      render: (text: string, record: CrawlerResult) => {
        console.log('Rendering address column:', { text, record });
        
        if (!record.address) {
          console.warn('No address found for record:', record);
          return 'N/A';
        }
        
        if (record.status === 'error') {
          return <span style={{ color: 'red' }}>{record.address}</span>;
        }
        
        const handleCopy = () => {
          const rect = document.getElementById(`address-${record.address}`)?.getBoundingClientRect();
          navigator.clipboard.writeText(record.address)
            .then(() => {
              if (rect) {
                message.success({
                  content: 'copied',
                  duration: 1,
                  className: 'custom-message',
                  style: {
                    marginTop: '0px',
                    position: 'absolute',
                    left: `${rect.right + 30}px`,
                    top: `${rect.top}px`,
                  }
                });
              }
            })
            .catch(() => {
              message.error('Failed to copy');
            });
        };
        
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', position: 'relative', width: '100%' }}>
            <Tooltip title={record.address} overlayStyle={{ maxWidth: '500px' }}>
              <span 
                id={`address-${record.address}`}
                style={{ 
                  cursor: 'pointer',
                  fontFamily: 'monospace',
                  color: '#1f1f1f',
                  fontSize: '13px',
                  letterSpacing: '0.5px',
                  flexGrow: 1,
                  minWidth: 0,
                  whiteSpace: 'nowrap'
                }}
              >
                {record.address}
              </span>
            </Tooltip>
            <Button
              type="text"
              icon={<CopyOutlined style={{ color: '#8c8c8c' }} />}
              size="small"
              onClick={handleCopy}
              style={{ 
                padding: '0 4px',
                height: '24px',
                width: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            />
            <Button
              type="text"
              icon={<LinkOutlined style={{ color: '#8c8c8c' }} />}
              size="small"
              onClick={() => {
                const url = `https://misttrack.io/aml_risks/${record.network}/${record.address}`;
                window.open(url, '_blank');
              }}
              style={{ 
                padding: '0 4px',
                height: '24px',
                width: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            />
          </div>
        );
      }
    },
    {
      title: 'Network',
      dataIndex: 'network',
      key: 'network',
      width: 120,
      sorter: (a, b) => a.network.localeCompare(b.network),
      filters: [
        { text: 'BSC', value: 'BSC' },
        { text: 'ETH', value: 'ETH' },
        { text: 'SOL', value: 'SOL' },
      ],
      onFilter: (value: string, record) => record.network === value,
      render: (text: string) => text || <span style={{ color: '#d9d9d9' }}>N/A</span>
    },
    {
      title: 'Risk Level',
      dataIndex: ['result', 'risk_level'],
      key: 'risk_level',
      width: 130,
      sorter: (a, b) => {
        const levelA = a.result?.risk_level || '';
        const levelB = b.result?.risk_level || '';
        return levelA.localeCompare(levelB);
      },
      filters: [
        { text: 'Risky', value: 'Risky' },
        { text: 'Low', value: 'Low' },
      ],
      onFilter: (value: string, record) => record.result?.risk_level === value,
      render: (text: string) => {
        if (!text) return <span style={{ color: '#d9d9d9' }}>N/A</span>;
        const color = text.toLowerCase().includes('risky') ? 'red' : 
                     text.toLowerCase().includes('low') ? 'green' : 'inherit';
        return <span style={{ color }}>{text}</span>;
      }
    },
    {
      title: 'Risk Type',
      dataIndex: ['result', 'risk_type'],
      key: 'risk_type',
      sorter: (a, b) => {
        const typeA = a.result?.risk_type || '';
        const typeB = b.result?.risk_type || '';
        return typeA.localeCompare(typeB);
      },
      render: (text: string) => text || <span style={{ color: '#d9d9d9' }}>N/A</span>
    },
    {
      title: 'Address/Risk Label',
      dataIndex: ['result', 'address_labels'],
      key: 'address_labels',
      // width: 300,
      render: (labels: string[]) => {
        if (!labels || labels.length === 0) return <span style={{ color: '#d9d9d9' }}>N/A</span>;
        return Array.isArray(labels) ? labels.join(', ') : labels;
      }
    },
    {
      title: 'Volume(USD)/%',
      dataIndex: ['result', 'volume'],
      key: 'volume',
      sorter: (a, b) => {
        const volA = parseFloat(a.result?.volume?.replace(/[^0-9.-]+/g, '') || '0');
        const volB = parseFloat(b.result?.volume?.replace(/[^0-9.-]+/g, '') || '0');
        return volA - volB;
      },
      render: (text: string) => text || <span style={{ color: '#d9d9d9' }}>N/A</span>
    },
    {
      title: 'Status',
      key: 'status',
      sorter: (a, b) => a.status.localeCompare(b.status),
      filters: [
        { text: 'Success', value: 'success' },
        { text: 'Error', value: 'error' },
      ],
      width: 150,
      onFilter: (value: string, record) => record.status === value,
      render: (_: any, record: CrawlerResult) => {
        if (record.status === 'error') {
          return <span style={{ color: 'red' }}>Error: {record.error}</span>;
        }
        return <span style={{ color: 'green' }}>Success</span>;
      }
    }
  ];

  return (
    <Layout>
      <Header className="ant-layout-header flex items-center justify-between" style={{ 
        padding: '0 24px',
        height: 'auto',
        minHeight: '64px',
        position: 'relative',
        zIndex: 1
      }}>
        <div className="flex items-center justify-between w-full">
          <h1 className="text-2xl font-bold m-0" style={{
            color: '#ffffff',
            textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
            padding: '0.5rem 1rem',
            whiteSpace: 'nowrap',
            overflow: 'visible'
          }}>
            Misttrack Crawler Dashboard
          </h1>
          {/* <div className="text-white flex items-center" style={{
            background: 'rgba(255,255,255,0.1)',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            backdropFilter: 'blur(5px)'
          }}>
            <DashboardOutlined className="mr-2" />
            Task Monitor
          </div> */}
        </div>
      </Header>
      
      <Content className="p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="mb-6">
            <div className="mb-6">
              <h2 className="text-xl font-medium mb-4">Cryptocurrency Address Crawler</h2>
              <Form form={form} onFinish={onFinish}>
                <div className="bg-blue-50 p-4 rounded-lg mb-6">
                  <h3 className="text-lg font-medium mb-3 text-blue-700">Step 1: Select Network</h3>
                  <Form.Item
                    name="network"
                    rules={[{ required: true, message: 'Please select a network' }]}
                    className="mb-0"
                  >
                    <Select
                      placeholder="Select blockchain network"
                      style={{ width: '100%', maxWidth: '300px' }}
                      options={[
                        { value: 'BSC', label: 'Binance Smart Chain (BSC)' },
                        { value: 'ETH', label: 'Ethereum (ETH)' },
                        { value: 'SOL', label: 'Solana (SOL)' },
                      ]}
                    />
                  </Form.Item>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-medium mb-3 text-blue-700">Step 2: Input Address</h3>
                    <h3 className="text-lg font-medium mb-3">Option 1: Single</h3>
                    <Form.Item
                      name="address"
                      rules={[{ required: true, message: 'Please input an address' }]}
                      className="mb-3"
                    >
                      <Input.Search
                        placeholder="Enter cryptocurrency address"
                        enterButton={
                          <Button 
                            type="primary"
                            icon={<DashboardOutlined />}
                            loading={loading}
                          >
                            Start Crawling
                          </Button>
                        }
                        onSearch={(value) => onSingleAddressSubmit(value)}
                      />
                    </Form.Item>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-medium mb-3">Option 2: Batch</h3>
                    <Form.Item name="file" className="mb-3">
                      <Upload {...uploadProps} className="w-full">
                        <Button 
                          icon={<UploadOutlined />} 
                          style={{ width: '100%' }}
                          loading={loading}
                        >
                          Upload CSV File
                        </Button>
                      </Upload>
                    </Form.Item>
                    <div className="text-sm text-gray-500">
                      Supported format: CSV file with addresses in first column
                    </div>
                  </div>
                </div>
              </Form>
            </div>

            <AnimatePresence>
              {taskProgress && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-6"
                >
                  <div className="grid grid-cols-1 gap-4 mb-6">
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                      <h4 className="text-gray-600 mb-4">Task Progress</h4>
                      <div className="mb-4">
                        <Progress
                          percent={100}
                          success={{ percent: stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0 }}
                          trailColor="#ff4d4f"
                          showInfo={false}
                        />
                        <div className="flex justify-between text-sm mt-2">
                          <span className="text-green-500">Success: {stats.success} ({stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0}%)</span>
                          <span className="text-red-500">Failed: {stats.error} ({stats.total > 0 ? Math.round((stats.error / stats.total) * 100) : 0}%)</span>
                        </div>
                      </div>

                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="mt-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium">Crawling Results</h3>
              </div>
              <Table 
                dataSource={results}
                columns={columns}
                pagination={false}
                scroll={{ x: 1500 }}
                className="modern-table"
                style={{
                  background: '#fff',
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                }}
                rowClassName={(record) => record.status === 'error' ? 'error-row' : ''}
                title={() => (
                  results.length > 0 && (
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'flex-end', 
                      marginBottom: '2px',
                      paddingBottom: '1px'
                    }}>
                      <Button 
                        type="primary"
                        icon={<DownloadOutlined />}
                        onClick={handleExportTable}
                      >
                        Download Table
                      </Button>
                    </div>
                  )
                )}
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
