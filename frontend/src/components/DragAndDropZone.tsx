import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Paper } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

interface DragAndDropZoneProps {
  onFilesDrop: (files: File[]) => void;
}

export const DragAndDropZone: React.FC<DragAndDropZoneProps> = ({ onFilesDrop }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onFilesDrop(acceptedFiles);
  }, [onFilesDrop]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 10,
  });

  return (
    <Paper
      {...getRootProps()}
      sx={{
        width: '100%',
        maxWidth: '700px',
        minHeight: '300px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 4,
        cursor: 'pointer',
        border: isDragActive ? '3px dashed #0288D1' : '3px dashed rgba(255,255,255,0.6)',
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        transition: 'all 0.3s ease',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        '&:hover': {
          backgroundColor: '#FAFAFA',
          borderColor: '#4FC3F7',
          boxShadow: '0 6px 16px rgba(0,0,0,0.12)',
        },
      }}
    >
      <input {...getInputProps()} />
      
      <CloudUploadIcon
        sx={{
          fontSize: 70,
          color: isDragActive ? '#0288D1' : '#81D4FA',
          mb: 3,
        }}
      />

      {/* Синий текст заголовка */}
      <Typography
        variant="h6"
        align="center"
        sx={{
          mb: 2,
          color: '#1565C0', // синий цвет
          fontWeight: 600,
        }}
      >
        {isDragActive
          ? 'Отпустите файлы здесь...'
          : 'Перетащите сюда ваши файлы или нажмите чтобы выбрать'}
      </Typography>

      <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
        Поддерживаемые форматы: PDF и DOCX
      </Typography>

      {/* Перекрывающиеся иконки файлов */}
      <Box
        sx={{
          position: 'relative',
          width: '120px',
          height: '80px',
          mt: 2,
        }}
      >
        {/* PDF иконка (сзади) */}
        <Box
          sx={{
            position: 'absolute',
            left: '10px',
            top: '0',
            width: '60px',
            height: '70px',
            border: '3px solid #F44336',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#FFEBEE',
            transform: 'rotate(-5deg)',
            zIndex: 1,
          }}
        >
          <Typography
            sx={{
              color: '#F44336',
              fontWeight: 'bold',
              fontSize: '14px',
            }}
          >
            PDF
          </Typography>
        </Box>

        {/* DOCX иконка (спереди) */}
        <Box
          sx={{
            position: 'absolute',
            left: '50px',
            top: '10px',
            width: '60px',
            height: '70px',
            border: '3px solid #2196F3',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#E3F2FD',
            transform: 'rotate(5deg)',
            zIndex: 2,
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
          }}
        >
          <Typography
            sx={{
              color: '#2196F3',
              fontWeight: 'bold',
              fontSize: '14px',
            }}
          >
            DOCX
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};