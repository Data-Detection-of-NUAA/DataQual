/**
 * 数据类型工具函数
 * 用于统一处理多模态数据类型的显示
 */

export const getDataTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    image: '图片',
    audio: '音频',
    text: '文本',
    multimodal: '多模态',
  };
  return labels[type] || type;
};

export const getDataTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    image: 'success',
    audio: 'warning',
    text: 'info',
    multimodal: 'primary',
  };
  return colors[type] || '';
};

export const getDataTypeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    image: 'Picture',
    audio: 'Microphone',
    text: 'Document',
    multimodal: 'Grid',
  };
  return icons[type] || 'Document';
};

export const getDefectTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    annotation_error: 'danger',
    distribution_shift: 'warning',
    adversarial_vulnerability: 'info',
  };
  return colors[type] || '';
};

export const getDefectTypeName = (type: string): string => {
  const names: Record<string, string> = {
    annotation_error: '标注错误',
    distribution_shift: '分布偏移',
    adversarial_vulnerability: '对抗脆弱',
  };
  return names[type] || type;
};
