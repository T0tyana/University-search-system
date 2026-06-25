import React, { useState } from 'react';
import { Box } from '@mui/material';
import { SearchBar } from '../components/SearchBar';
import { DragAndDropZone } from '../components/DragAndDropZone';
import { FileList } from '../components/FileList';
import { BackButton } from '../components/BackButton';
import type { UploadedFile, SearchHistoryItem } from '../types';

export const HomePage: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);

  const handleFilesDrop = (files: File[]) => {
    const newFiles: UploadedFile[] = files.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      type: file.name.split('.').pop()?.toLowerCase() as 'pdf' | 'docx' | 'txt',
      status: 'uploading',
      progress: 0,
    }));

    setUploadedFiles((prev) => [...newFiles, ...prev]);

    newFiles.forEach((file) => {
      simulateUpload(file.id);
    });
  };

  const simulateUpload = (fileId: string) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadedFiles((prev) =>
        prev.map((file) =>
          file.id === fileId ? { ...file, progress } : file
        )
      );

      if (progress >= 100) {
        clearInterval(interval);
        setTimeout(() => {
          simulateIndexing(fileId);
        }, 500);
      }
    }, 200);
  };

  const simulateIndexing = (fileId: string) => {
    setUploadedFiles((prev) =>
      prev.map((file) =>
        file.id === fileId ? { ...file, status: 'indexing', progress: 0 } : file
      )
    );

    let progress = 0;
    const interval = setInterval(() => {
      progress += 15;
      setUploadedFiles((prev) =>
        prev.map((file) =>
          file.id === fileId ? { ...file, progress } : file
        )
      );

      if (progress >= 100) {
        clearInterval(interval);
        setUploadedFiles((prev) =>
          prev.map((file) =>
            file.id === fileId
              ? { ...file, status: 'completed', progress: 100, uploadedAt: new Date() }
              : file
          )
        );
      }
    }, 300);
  };

  const handleSearch = (query: string) => {
    const newHistoryItem: SearchHistoryItem = {
      id: Math.random().toString(36).substr(2, 9),
      query,
      timestamp: new Date(),
    };

    setSearchHistory((prev) => {
      const filtered = prev.filter((item) => item.query !== query);
      return [newHistoryItem, ...filtered].slice(0, 10);
    });

    console.log('Search query:', query);
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

      {/* Основной контейнер — на всю ширину с небольшими отступами */}
      <Box
        sx={{
          width: '100%',
          px: { xs: 2, sm: 4, md: 6, lg: 10 }, // боковые отступы
          pt: 10, // отступ сверху (чтобы не наезжать на кнопку)
          pb: 6,
          boxSizing: 'border-box',
        }}
      >
        {/* Поисковая строка — почти на всю ширину */}
        <Box sx={{ mb: 3 }}>
          <SearchBar onSearch={handleSearch} searchHistory={searchHistory} />
        </Box>

        {/* Drag-and-drop зона — широкая и низкая */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center' }}>
          <DragAndDropZone onFilesDrop={handleFilesDrop} />
        </Box>

        {/* Лента файлов */}
        <FileList files={uploadedFiles} />
      </Box>
    </Box>
  );
};