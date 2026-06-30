import React, { useState, useEffect } from 'react';
import {
  Box,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Typography,
} from '@mui/material';
import { SearchBar } from '../components/SearchBar';
import { DragAndDropZone } from '../components/DragAndDropZone';
import { FileList } from '../components/FileList';
import { BackButton } from '../components/BackButton';
import { apiClient } from '../services/client';
import { getDocumentsApi, deleteDocumentApi } from '../services/documents';
import { getSearchHistoryApi } from '../services/search';
import type { UploadedFile, SearchHistoryItem } from '../types';
import { useNavigate } from 'react-router-dom';

export const HomePage: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);

  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({ open: false, message: '', severity: 'success' });

  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    fileName: string | null;
    fileId: string | null;
  }>({ open: false, fileName: null, fileId: null });

  // Загрузка данных при монтировании
  useEffect(() => {
    const fetchData = async () => {
      try {
        const docsRes = await getDocumentsApi();
        const files: UploadedFile[] = docsRes.documents.map((doc) => ({
          id: doc.file_name,
          name: doc.file_name,
          type: doc.file_name.split('.').pop()?.toLowerCase() as 'pdf' | 'docx',
          status: 'completed',
          progress: 100,
          uploadedAt: doc.upload_date,
        }));
        setUploadedFiles(files);

        const historyRes = await getSearchHistoryApi();
        const history: SearchHistoryItem[] = historyRes.history.map((h) => ({
          id: h.query + h.timestamp,
          query: h.query,
          timestamp: h.timestamp,
          files_found: h.files_found,
          total_results: h.total_results,
        }));
        setSearchHistory(history);
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };
    fetchData();
  }, []);

  // 🔥 Функция анимации индексации
  const animateIndexing = async (fileId: string) => {
    // Анимируем прогресс от 0% до 100%
    const totalDuration = 2000; // 2 секунды на всю анимацию
    const steps = 20; // 20 шагов
    const stepDuration = totalDuration / steps;
    const stepProgress = 100 / steps;

    for (let i = 1; i <= steps; i++) {
      await new Promise(resolve => setTimeout(resolve, stepDuration));
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === fileId 
            ? { ...f, progress: Math.min(i * stepProgress, 100) }
            : f
        )
      );
    }
  };

  // Загрузка файлов
  const handleFilesDrop = async (files: File[]) => {
    const newFiles: UploadedFile[] = files.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      type: file.name.split('.').pop()?.toLowerCase() as 'pdf' | 'docx',
      status: 'uploading',
      progress: 0,
    }));

    setUploadedFiles((prev) => [...newFiles, ...prev]);

    for (let i = 0; i < files.length; i++) {
      const fileObj = files[i];
      const fileId = newFiles[i].id;

      try {
        const formData = new FormData();
        formData.append('file', fileObj);

        // 1️⃣ ЭТАП ЗАГРУЗКИ (синий прогресс-бар)
        await apiClient.post('/api/v1/documents/upload', formData, {
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === fileId 
                    ? { ...f, progress: percentCompleted, status: 'uploading' } 
                    : f
                )
              );
            }
          },
        });

        // 2️⃣ ПЕРЕХОД К ИНДЕКСАЦИИ (фиолетовый прогресс-бар)
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? { ...f, status: 'indexing', progress: 0, uploadedAt: new Date() }
              : f
          )
        );

        // 🔥 ЗАПУСКАЕМ АНИМАЦИЮ ИНДЕКСАЦИИ
        await animateIndexing(fileId);

        // 3️⃣ ПОЛУЧАЕМ АКТУАЛЬНЫЙ СПИСОК ДОКУМЕНТОВ
        try {
          const docsRes = await getDocumentsApi();
          const updatedFile = docsRes.documents.find(d => d.file_name === fileObj.name);
          
          setUploadedFiles((prev) =>
            prev.map((f) =>
              f.id === fileId && updatedFile
                ? { 
                    ...f, 
                    status: 'completed', 
                    progress: 100, 
                    uploadedAt: updatedFile.upload_date 
                  }
                : f.id === fileId
                ? { ...f, status: 'completed', progress: 100, uploadedAt: new Date() }
                : f
            )
          );
        } catch (err) {
          console.error('Error fetching documents:', err);
          setUploadedFiles((prev) =>
            prev.map((f) =>
              f.id === fileId 
                ? { ...f, status: 'completed', progress: 100, uploadedAt: new Date() } 
                : f
            )
          );
        }

        setSnackbar({
          open: true,
          message: `Файл ${fileObj.name} успешно загружен и проиндексирован`,
          severity: 'success',
        });

      } catch (error: any) {
        console.error('Upload failed:', error);
        const errMsg = error.response?.data?.detail || 'Ошибка загрузки файла';

        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === fileId ? { ...f, status: 'error', progress: 100 } : f
          )
        );

        setSnackbar({
          open: true,
          message: `${fileObj.name}: ${errMsg}`,
          severity: 'error',
        });
      }
    }
  };

  // Обработка клика на удаление
  const handleDeleteClick = (fileName: string, fileId: string, needsApiCall: boolean) => {
    if (!needsApiCall) {
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
      setSnackbar({
        open: true,
        message: `Файл ${fileName} удален из списка`,
        severity: 'info',
      });
      return;
    }

    setDeleteDialog({ open: true, fileName, fileId });
  };

  // Подтверждение удаления
  const handleDeleteConfirm = async () => {
    if (!deleteDialog.fileName || !deleteDialog.fileId) return;
    const fileName = deleteDialog.fileName;
    const fileId = deleteDialog.fileId;

    setDeleteDialog({ open: false, fileName: null, fileId: null });

    setUploadedFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, status: 'deleting', progress: 100 } : f))
    );

    try {
      await deleteDocumentApi(fileName);

      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
      setSnackbar({
        open: true,
        message: `Файл ${fileName} удалён`,
        severity: 'success',
      });
    } catch (error: any) {
      console.error('Delete failed:', error);

      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: 'completed', progress: 100 } : f
        )
      );
      const errMsg = error.response?.data?.detail || 'Не удалось удалить файл';
      setSnackbar({
        open: true,
        message: `${fileName}: ${errMsg}`,
        severity: 'error',
      });
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, fileName: null, fileId: null });
  };

  const navigate = useNavigate();
  const handleSearch = (query: string) => {
    if (query.trim()) {
      navigate(`/search?query=${encodeURIComponent(query)}`);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#e6f4ff',
        position: 'relative',
        width: '100%',
        overflowX: 'hidden',
      }}
    >
      <BackButton />

      <Box
        sx={{
          width: '100%',
          px: { xs: 2, sm: 4, md: 6, lg: 10 },
          pt: 10,
          pb: 6,
          boxSizing: 'border-box',
        }}
      >
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
          <Box sx={{ width: '100%', maxWidth: '1100px' }}>
            <SearchBar onSearch={handleSearch} searchHistory={searchHistory} />
          </Box>
        </Box>

        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center' }}>
          <DragAndDropZone onFilesDrop={handleFilesDrop} />
        </Box>

        <FileList files={uploadedFiles} onDelete={handleDeleteClick} />
      </Box>

      {/* Диалог подтверждения удаления */}
      <Dialog open={deleteDialog.open} onClose={handleDeleteCancel}>
        <DialogTitle
          sx={{
            fontWeight: 700,
            color: '#212121',
            fontSize: '1.25rem',
          }}
        >
          Удалить файл?
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: '#424242', fontSize: '0.95rem' }}>
            Вы действительно хотите удалить файл{' '}
            <Typography
              component="strong"
              sx={{ color: '#FF9800', fontWeight: 600 }}
            >
              {deleteDialog.fileName}
            </Typography>{' '}
            из системы?
          </DialogContentText>
          <DialogContentText sx={{ color: '#757575', fontSize: '0.85rem', mt: 1 }}>
            Это действие нельзя отменить — файл будет безвозвратно удалён.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={handleDeleteCancel}
            sx={{
              color: '#757575',
              '&:hover': { backgroundColor: '#F5F5F5' },
            }}
          >
            Отмена
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            sx={{
              backgroundColor: '#FF9800',
              color: 'white',
              fontWeight: 500,
              '&:hover': {
                backgroundColor: '#F57C00',
                boxShadow: '0 4px 12px rgba(255, 152, 0, 0.3)',
              },
            }}
            autoFocus
          >
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};