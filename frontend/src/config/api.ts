const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export const API_ENDPOINTS = {
  CRAWLER: `${API_BASE_URL}/api/crawler/`,
  CRAWLER_STATUS: (taskId: string) => `${API_BASE_URL}/api/crawler/${taskId}/status/`,
  CRAWLER_RESULT: (taskId: string) => `${API_BASE_URL}/api/crawler/${taskId}/result/`,
};

export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8002';

export const WS_ENDPOINTS = {
  CRAWLER_STATUS: (taskId: string) => `${WS_BASE_URL}/ws/crawler/${taskId}/`,
};
