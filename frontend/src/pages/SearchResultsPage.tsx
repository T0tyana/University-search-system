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
import { searchApi, getSearchHistoryApi } from '../services/search';
import type { SearchHistoryItem } from '../types';
import type { SearchResult as ApiSearchResult } from '../services/search';

interface SearchResult extends ApiSearchResult {
  id: string; 
}

export const SearchResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
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

  // Загружаем историю поиска
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await getSearchHistoryApi();
        const history: SearchHistoryItem[] = res.history.map((h) => ({
          id: h.query + h.timestamp,
          query: h.query,
          timestamp: h.timestamp,
          files_found: h.files_found,
          total_results: h.total_results,
        }));
        setSearchHistory(history);
      } catch (error) {
        console.error('Error fetching history:', error);
      }
    };
    fetchHistory();
  }, []);

  // Функция поиска
  const performSearch = useCallback(async (query: string, pageNum: number) => {
    if (!query.trim()) return;
    setLoading(true);
    
    try {
      const response = await searchApi(query, pageNum, 10); 
      
      const newResults: SearchResult[] = response.results.map(r => ({
        ...r,
        id: `${r.chunk_id}-${pageNum}`
      }));

      setResults(prev => pageNum === 1 ? newResults : [...prev, ...newResults]);
      
      // Проверяем, есть ли еще результаты
      setHasMore((pageNum * 10) < response.total);
      
    } catch (error: any) {
      console.error('Search error:', error);
      const errMsg = error.response?.data?.detail || 'Ошибка при выполнении поиска';
      setSnackbar({ open: true, message: errMsg, severity: 'error' });
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // Реагируем на изменение URL
  useEffect(() => {
    const queryFromUrl = getInitialQueryFromUrl();
    if (queryFromUrl) {
      setSearchQuery(queryFromUrl);
      setPage(1);
      setResults([]);
      performSearch(queryFromUrl, 1);
    }
  }, [location.search, performSearch]);

  // Обработчик нового поиска
  const handleSearch = (query: string) => {
    if (!query.trim()) return;
    
    setResults([]);
    setPage(1);
    setHasMore(true);
    
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

  const handleUploadClick = () => navigate('/home');
  const handleCloseSnackbar = () => setSnackbar(prev => ({ ...prev, open: false }));

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