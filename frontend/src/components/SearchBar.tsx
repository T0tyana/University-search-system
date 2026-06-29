import React, { useState, useRef, useEffect } from 'react';
import { Box, InputBase, IconButton, List, ListItemButton, ListItemText, Paper, Typography } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import type { SearchHistoryItem } from '../types';

interface SearchBarProps {
  onSearch: (query: string) => void;
  searchHistory: SearchHistoryItem[];
  initialQuery?: string; // <-- Добавляем этот пропс
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, searchHistory, initialQuery = '' }) => {
  const [query, setQuery] = useState(initialQuery);
  const [isFocused, setIsFocused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Синхронизируем локальный стейт с пропсом initialQuery
  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      // setQuery(''); // Убираем очистку, чтобы запрос оставался в поле
      setIsFocused(false);
    }
  };

  const handleHistoryClick = (historyQuery: string) => {
    setQuery(historyQuery);
    onSearch(historyQuery);
    setIsFocused(false);
  };

  return (
    <Box ref={containerRef} sx={{ position: 'relative', width: '100%', maxWidth: '1100px' }}>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
          width: '100%',
          backgroundColor: '#ffffff',
          boxShadow: isFocused ? '0 4px 12px rgba(0,0,0,0.15)' : '0 2px 4px rgba(0,0,0,0.1)',
          borderRadius: '8px',
          border: isFocused ? '2px solid #4FC3F7' : '2px solid #E3F2FD',
        }}
      >
        <InputBase
          sx={{ ml: 2, flex: 1, fontSize: '16px' }}
          placeholder="Найти..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
        />
        <IconButton type="submit" sx={{ p: '10px', color: '#0288D1' }} aria-label="search">
          <SearchIcon />
        </IconButton>
      </Paper>

      {isFocused && (
          <Paper
            sx={{
              position: 'absolute',
              top: '100%',
              left: 0,
              width: '33%',          
              mt: 1,
              maxHeight: '300px',
              overflow: 'auto',
              zIndex: 1000,
              backgroundColor: 'rgba(200, 200, 200, 0.3)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              borderRadius: '8px',
              backdropFilter: 'blur(10px)',
            }}
          >
          {searchHistory.length > 0 ? (
            <List sx={{ py: 0 }}>
              {searchHistory.map((item) => (
                <ListItemButton
                  key={item.id}
                  onClick={() => handleHistoryClick(item.query)}
                  sx={{
                    py: 1,
                    px: 2,
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    },
                  }}
                >
                  <ListItemText
                    primary={
                      <Typography
                        variant="body2"
                        sx={{
                          fontSize: '14px',
                          color: '#424242',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {item.query}
                      </Typography>
                    }
                  />
                </ListItemButton>
              ))}
            </List>
          ) : (
            <Box sx={{ p: 2, textAlign: 'center', color: '#757575', fontSize: '14px' }}>
              История поиска пуста
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};