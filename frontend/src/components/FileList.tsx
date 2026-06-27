import React from 'react';
import { Box, Typography, LinearProgress, IconButton, Tooltip } from '@mui/material';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import type { UploadedFile } from '../types';
import DescriptionIcon from '@mui/icons-material/Description';

interface FileListProps {
  files: UploadedFile[];
  onDelete?: (fileName: string, fileId: string, needsApiCall: boolean) => void;
}

export const FileList: React.FC<FileListProps> = ({ files, onDelete }) => {
  const getStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'completed':
        return '#08dad0';
      case 'error':
        return '#EF5350'; 
      case 'uploading':
        return '#64B5F6';
      case 'indexing':
        return '#9969f7';
      case 'deleting':
        return '#FF9800';
      default:
        return '#B0BEC5';
    }
  };

  const getStatusText = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return 'Загрузка...';
      case 'indexing':
        return 'Индексация...';
      case 'completed':
        return 'Загружен';
      case 'error':
        return 'Ошибка загрузки';
      case 'deleting':
        return 'Удаление...';
      default:
        return '';
    }
  };

  const getFileIcon = (type: string) => {
    const colors = {
      pdf: '#F44336',
      docx: '#2196F3',
    };
    return colors[type as keyof typeof colors] || '#757575';
  };

  // Кнопка удаления активна только для завершенных или ошибочных файлов
  const canDelete = (status: UploadedFile['status']) =>
    status === 'completed' || status === 'error';

  // Обработчик клика на удаление
  const handleDeleteClick = (file: UploadedFile) => {
    if (!onDelete) return;

    // Если файл с ошибкой загрузки — удаляем сразу без API (needsApiCall = false)
    // Если файл загружен — показываем диалог и шлем запрос (needsApiCall = true)
    const needsApiCall = file.status !== 'error';
    onDelete(file.name, file.id, needsApiCall);
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <Box sx={{ width: '100%', mt: 4 }}>
      <Box
        sx={{
          display: 'flex',
          gap: 3,
          overflowX: 'auto',
          pb: 3,
          pt: 1,
          '&::-webkit-scrollbar': { height: '8px' },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'rgba(255, 255, 255, 0.3)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0, 0, 0, 0.2)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.3)',
          },
        }}
      >
        {files.map((file) => (
          <Box key={file.id} sx={{ minWidth: '280px', maxWidth: '280px', flexShrink: 0 }}>
            <Box sx={{ height: '20px', mb: 0.5 }}>
              {file.uploadedAt && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: 'block', textAlign: 'center', fontSize: '12px' }}
                >
                  {new Date(file.uploadedAt).toLocaleDateString('ru-RU')}
                </Typography>
              )}
            </Box>

            <Box
              sx={{
                p: 2,
                backgroundColor: '#ffffff',
                border: `2px solid ${getStatusColor(file.status)}`,
                borderRadius: '12px',
                position: 'relative',
                transition: 'opacity 0.3s ease',
                opacity: file.status === 'deleting' ? 0.6 : 1,
              }}
            >
              {/* Кнопка удаления */}
              {onDelete && (
                <Tooltip
                  title={
                    canDelete(file.status)
                      ? file.status === 'error'
                        ? 'Удалить из списка'
                        : 'Удалить файл'
                      : 'Дождитесь окончания обработки'
                  }
                >
                  <span>
                    <IconButton
                      size="small"
                      disabled={!canDelete(file.status)}
                      onClick={() => handleDeleteClick(file)}
                      sx={{
                        position: 'absolute',
                        top: 4,
                        right: 4,
                        color: '#EF5350',
                        padding: '4px',
                        '&:hover': { backgroundColor: '#FFEBEE' },
                        '&.Mui-disabled': { color: '#E0E0E0' },
                      }}
                    >
                      <DeleteOutlinedIcon sx={{ fontSize: 18 }} />
                    </IconButton>
                  </span>
                </Tooltip>
              )}

              <Box sx={{ display: 'flex', alignItems: 'center', pr: 3 }}>
                <DescriptionIcon
                  sx={{
                    color: getFileIcon(file.type),
                    mr: 1,
                    fontSize: 28,
                  }}
                />
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 500,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flex: 1,
                    color: '#212121',
                  }}
                >
                  {file.name}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ mt: 1, mb: 1 }}>
              {(file.status === 'uploading' ||
                file.status === 'indexing' ||
                file.status === 'completed' ||
                file.status === 'error' ||
                file.status === 'deleting') && (
                <LinearProgress
                  variant="determinate"
                  value={file.status === 'deleting' ? 100 : file.progress}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: 'rgba(255, 255, 255, 0.5)',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getStatusColor(file.status),
                      borderRadius: 3,
                    },
                  }}
                />
              )}
            </Box>

            <Typography
              variant="caption"
              sx={{
                display: 'block',
                textAlign: 'center',
                color: getStatusColor(file.status),
                fontWeight: 500,
                fontSize: '12px',
              }}
            >
              {getStatusText(file.status)}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
};