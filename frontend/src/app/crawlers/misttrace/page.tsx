'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Card, Form, Input, Button, Table, Tag, Space, message, App } from 'antd';
import {
  SearchOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { API_ENDPOINTS, WS_ENDPOINTS } from '../../../config/api';

const MisttracePage = () => {
  const { message: messageApi } = App.useApp();
  const [form] = Form.useForm();
  const wsRef = useRef<WebSocket | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  const columns = [
    {
      title: 'Address',
      dataIndex: 'address',
      key: 'address',
      render: (text: string) => (
        <a href={`https://etherscan.io/address/${text}`} target="_blank" rel="noopener noreferrer">
          {text}
        </a>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
          completed: { color: 'success', icon: <CheckCircleOutlined /> },
          processing: { color: 'processing', icon: <SyncOutlined spin /> },
          failed: { color: 'error', icon: <CloseCircleOutlined /> },
        };
        return (
          <Tag icon={statusConfig[status].icon} color={statusConfig[status].color}>
            {status.toUpperCase()}
          </Tag>
        );
      },
    },
    {
      title: 'Created At',
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button type="link" onClick={() => console.log('View details', record)}>
            View Details
          </Button>
          <Button type="link" danger onClick={() => console.log('Delete', record)}>
            Delete
          </Button>
        </Space>
      ),
    },
  ];

  const demoData = [
    {
      key: '1',
      address: '0x28c6c06298d514db089934071355e5743bf21d60',
      status: 'completed',
      createdAt: '2024-02-25 10:00:00',
    },
    {
      key: '2',
      address: '0x1234567890abcdef1234567890abcdef12345678',
      status: 'processing',
      createdAt: '2024-02-25 10:05:00',
    },
  ];

  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      const response = await fetch(API_ENDPOINTS.CRAWLER, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        throw new Error('Failed to submit task');
      }

      const data = await response.json();
      setCurrentTaskId(data.task_id);

      // 连接WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }

      const ws = new WebSocket(WS_ENDPOINTS.CRAWLER_STATUS(data.task_id));
      wsRef.current = ws;

      ws.onopen = () => {
        messageApi.success('Connected to task status updates');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        switch (message.status) {
          case 'started':
            messageApi.info('Task started');
            break;
          case 'completed':
            messageApi.success('Task completed');
            setLoading(false);
            // 更新任务列表
            break;
          case 'error':
            messageApi.error(`Task failed: ${message.error}`);
            setLoading(false);
            break;
        }
      };

      ws.onerror = () => {
        messageApi.error('WebSocket connection error');
        setLoading(false);
      };

      ws.onclose = () => {
        messageApi.info('Disconnected from task status updates');
        setLoading(false);
      };

    } catch (error) {
      setLoading(false);
      messageApi.error('Failed to submit task');
      console.error('Task submission error:', error);
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <div>
      <Card title="Submit New Task" style={{ marginBottom: 16 }}>
        <Form
          name="misttrace_form"
          onFinish={onFinish}
          layout="inline"
          style={{ gap: 16 }}
        >
          <Form.Item
            name="url"
            rules={[
              { required: true, message: 'Please input an Ethereum address!' },
              {
                pattern: /^0x[a-fA-F0-9]{40}$/,
                message: 'Please input a valid Ethereum address!',
              },
            ]}
            style={{ flex: 1 }}
          >
            <Input
              prefix={<SearchOutlined />}
              placeholder="Enter Ethereum Address (0x...)"
              allowClear
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              Submit
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Task History">
        <Table
          columns={columns}
          dataSource={demoData}
          pagination={{
            total: 50,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>
    </div>
  );
};

export default MisttracePage;
