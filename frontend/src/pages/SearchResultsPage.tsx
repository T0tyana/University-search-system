import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Tooltip,
  CircularProgress,
  Snackbar,
  Alert,
} from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import { useNavigate, useLocation } from 'react-router-dom';
import { SearchBar } from '../components/SearchBar';
import { SearchResultCard } from '../components/SearchResultCard';
import type { SearchHistoryItem } from '../types';

interface SearchResult {
  id: string;
  chunk_id: string;
  file_name: string;
  page: number;
  text: string;
  score: number;
}

export const SearchResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // ✅ ЧИТАЕМ QUERY ИЗ URL СРАЗУ ПРИ ИНИЦИАЛИЗАЦИИ
  const getInitialQueryFromUrl = () => {
    const params = new URLSearchParams(location.search);
    const queryFromUrl = params.get('query');
    return queryFromUrl ? decodeURIComponent(queryFromUrl) : '';
  };
  
  const [searchQuery, setSearchQuery] = useState(getInitialQueryFromUrl());
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({ open: false, message: '', severity: 'info' });

  const observerTarget = useRef<HTMLDivElement>(null);

  // Инициализация истории поиска
  useEffect(() => {
    const mockHistory: SearchHistoryItem[] = [
      { 
        id: '1', 
        query: 'машинное обучение', 
        timestamp: new Date().toISOString(), 
        files_found: ['lecture_ml.pdf', 'ai_intro.pdf'],
        total_results: 15 
      },
      { 
        id: '2', 
        query: 'базы данных', 
        timestamp: new Date().toISOString(), 
        files_found: ['db_lecture.pdf'],
        total_results: 8 
      },
    ];
    setSearchHistory(mockHistory);
  }, []);

  // Функция поиска
  const performSearch = useCallback(async (query: string, pageNum: number) => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const mockResults: SearchResult[] = Array.from({ length: 10 }, (_, i) => ({
        id: `${pageNum}-${i}`,
        chunk_id: `chunk_${i}`,
        file_name: `document_${pageNum}_${i}.pdf`,
        page: Math.floor(Math.random() * 20) + 1,
        text: `Это пример текста из документа. Здесь содержится информация о "${query}". 
               Данный фрагмент демонстрирует, как будет выглядеть результат поиска в системе. 
               Система нашла это совпадение в контексте учебного материала.`,
        score: Math.floor(Math.random() * 40) + 60,
      }));

      setResults(prev => pageNum === 1 ? mockResults : [...prev, ...mockResults]);
      setHasMore(pageNum < 5);
    } catch (error) {
      console.error('Search error:', error);
      setSnackbar({ open: true, message: 'Ошибка при выполнении поиска', severity: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  // ✅ ТЕПЕРЬ USE EFFECT ТОЛЬКО ДЛЯ ЗАПУСКА ПОИСКА
  useEffect(() => {
    if (searchQuery) {
      performSearch(searchQuery, 1);
    }
  }, [searchQuery, performSearch]);

  // Отслеживание изменений URL (если пользователь меняет URL вручную)
  useEffect(() => {
    const queryFromUrl = getInitialQueryFromUrl();
    if (queryFromUrl && queryFromUrl !== searchQuery) {
      setSearchQuery(queryFromUrl);
    }
  }, [location.search]);

  const handleSearch = (query: string) => {
    if (!query.trim()) return;
    
    setSearchQuery(query);
    setResults([]);
    setPage(1);
    setHasMore(true);
    // performSearch вызывается в useEffect при изменении searchQuery
    navigate(`/search?query=${encodeURIComponent(query)}`, { replace: true });
  };

  // Бесконечный скролл
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading && searchQuery) {
          const nextPage = page + 1;
          setPage(nextPage);
          performSearch(searchQuery, nextPage);
        }
      },
      { threshold: 0.5 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [page, hasMore, loading, searchQuery, performSearch]);

  const handleUploadClick = () => {
    navigate('/home');
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
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
      <Tooltip title="Загрузить документы" placement="right">
        <IconButton
          onClick={handleUploadClick}
          sx={{
            position: 'absolute',
            top: 20,
            left: 20,
            backgroundColor: '#ffffff',
            color: '#1976D2',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            zIndex: 1000,
            '&:hover': {
              backgroundColor: '#E3F2FD',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            },
          }}
        >
          <AttachFileIcon sx={{ fontSize: 24 }} />
        </IconButton>
      </Tooltip>

      <Box
        sx={{
          width: '100%',
          px: { xs: 2, sm: 4, md: 6, lg: 10 },
          pt: 10,
          pb: 6,
          boxSizing: 'border-box',
        }}
      >
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center' }}>
          <Box sx={{ width: '100%', maxWidth: '1100px' }}>
            {/* ✅ ТЕПЕРЬ initialQuery сразу содержит значение из URL */}
            <SearchBar 
              key={searchQuery}
              onSearch={handleSearch} 
              searchHistory={searchHistory} 
              initialQuery={searchQuery} 
            />
          </Box>
        </Box>

        {searchQuery && (
          <Box sx={{ maxWidth: '1100px', margin: '0 auto' }}>
            <Typography
              variant="h6"
              sx={{
                mb: 3,
                color: '#424242',
                fontWeight: 600,
                fontSize: { xs: '16px', sm: '18px' },
              }}
            >
              Результаты поиска по запросу: "{searchQuery}"
              {results.length > 0 && (
                <Typography
                  component="span"
                  sx={{
                    ml: 2,
                    color: '#757575',
                    fontWeight: 400,
                    fontSize: '14px',
                  }}
                >
                  ({results.length} найдено)
                </Typography>
              )}
            </Typography>

            {results.map((result) => (
              <SearchResultCard
                key={result.id}
                fileName={result.file_name}
                pageNumber={result.page}
                relevanceScore={result.score}
                textFragment={result.text}
                searchQuery={searchQuery}
              />
            ))}

            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress sx={{ color: '#1976D2' }} />
              </Box>
            )}

            {!loading && results.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 8, px: 2 }}>
                <Typography sx={{ color: '#757575', fontSize: { xs: '14px', sm: '16px' }, mb: 1 }}>
                  По вашему запросу ничего не найдено
                </Typography>
                <Typography sx={{ color: '#9E9E9E', fontSize: { xs: '12px', sm: '14px' } }}>
                  Попробуйте изменить формулировку
                </Typography>
              </Box>
            )}

            <div ref={observerTarget} style={{ height: '20px' }} />

            {!hasMore && results.length > 0 && (
              <Typography sx={{ textAlign: 'center', color: '#9E9E9E', py: 3, fontSize: '14px' }}>
                Больше результатов нет
              </Typography>
            )}
          </Box>
        )}

        {!searchQuery && (
          <Box sx={{ textAlign: 'center', py: 12, px: 2 }}>
            <Typography sx={{ color: '#757575', fontSize: { xs: '14px', sm: '16px' } }}>
              Введите поисковый запрос выше, чтобы найти документы
            </Typography>
          </Box>
        )}
      </Box>

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