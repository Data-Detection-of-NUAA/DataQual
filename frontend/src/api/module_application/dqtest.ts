import { httpRequest } from '@/utils/request' // ✅ 改为 httpRequest

export interface DqtestTaskConfig {
  name: string
  dataset: any
  model: any
  strategy: any
  parameters: any
  metrics: any
}

export interface DqtestTask {
  id: number
  name: string
  status: 'idle' | 'running' | 'completed' | 'failed'
  progress: number
  config: DqtestTaskConfig
  result?: any
  created_time: string
  updated_time: string
}

export class DqtestApi {
  private static readonly BASE_URL = '/dqtest'

  // 创建dqtest任务
  static async createTask(config: DqtestTaskConfig): Promise<ApiResponse<DqtestTask>> {
    return httpRequest({ // ✅ 使用 httpRequest 而不是 request
      url: `${this.BASE_URL}/tasks`,
      method: 'POST',
      data: config
    })
  }

  // 获取dqtest任务详情
  static async getTask(taskId: number): Promise<ApiResponse<DqtestTask>> {
    return httpRequest({ // ✅ 使用 httpRequest
      url: `${this.BASE_URL}/tasks/${taskId}`,
      method: 'GET'
    })
  }

  // 获取dqtest任务列表
  static async getTaskList(): Promise<ApiResponse<DqtestTask[]>> {
    return httpRequest({ // ✅ 使用 httpRequest
      url: `${this.BASE_URL}/tasks`,
      method: 'GET'
    })
  }

  // 上传dqtest数据文件
  static async uploadFile(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData()
    formData.append('file', file)
    
    return httpRequest({ // ✅ 使用 httpRequest
      url: `${this.BASE_URL}/upload`,
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }

  // 下载dqtest报告
  static async downloadReport(taskId: number, filename: string): Promise<Blob> {
    const response = await httpRequest({ // ✅ 使用 httpRequest
      url: `${this.BASE_URL}/tasks/${taskId}/artifact`,
      method: 'GET',
      params: { path: filename },
      responseType: 'blob'
    })
    return response.data
  }

  // dqtest任务WebSocket地址
  static getWebSocketUrl(taskId: number): string {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${wsProtocol}//${host}/api/v1/dqtest/ws/${taskId}`
  }
}