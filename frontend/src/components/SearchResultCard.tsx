import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

interface SearchResultCardProps {
  fileName: string;
  pageNumber: number;
  relevanceScore: number;
  textFragment: string;
  highlightedText?: string; // Текст с уже размеченными совпадениями
  searchQuery?: string; // Если нужно подсвечивать автоматически
}

export const SearchResultCard: React.FC<SearchResultCardProps> = ({
  fileName,
  pageNumber,
  relevanceScore,
  textFragment,
  highlightedText,
  searchQuery,
}) => {
  // Функция для подсветки совпадений, если не передан готовый highlightedText
  const highlightMatches = (text: string, query: string) => {
    if (!query.trim()) return text;

    const regex = new RegExp(`(${query.trim()})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <Box
          key={index}
          component="span"
          sx={{
            backgroundColor: '#fff278', 
            color: '#000000',
            padding: '0 2px',
            borderRadius: '2px',
            fontWeight: 500,
          }}
        >
          {part}
        </Box>
      ) : (
        part
      )
    );
  };

  return (
    <Paper
      sx={{
        width: '100%',
        mb: 2,
        p: 3,
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        display: 'flex',
        gap: 3,
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
        },
        // Адаптивность
        flexDirection: { xs: 'column', sm: 'row' },
      }}
    >
      {/* Левая часть - информация (1/4 ширины) */}
      <Box
        sx={{
          width: { xs: '100%', sm: '25%' },
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
          flexShrink: 0,
        }}
      >
        {/* Название файла */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: '#0078f0',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              fontSize: { xs: '12px', sm: '14px' },
            }}
            title={fileName}
          >
            {fileName}
          </Typography>
        </Box>

        {/* Номер страницы */}
        <Typography
          variant="caption"
          sx={{
            color: '#757575',
            fontSize: { xs: '11px', sm: '12px' },
          }}
        >
          Страница {pageNumber}
        </Typography>

        {/* Оценка релевантности */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mt: 'auto',
          }}
        >
          <Box
            sx={{
              width: '100%',
              height: '6px',
              backgroundColor: '#E3F2FD',
              borderRadius: '3px',
              overflow: 'hidden',
            }}
          >
            <Box
              sx={{
                width: `${relevanceScore}%`,
                height: '100%',
                backgroundColor: relevanceScore >= 70 ? '#a3ffa6' : relevanceScore >= 40 ? '#fed290' : '#ffaaa3',
                borderRadius: '3px',
                transition: 'width 0.3s ease',
              }}
            />
          </Box>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 600,
              color: '#424242',
              minWidth: '40px',
              fontSize: { xs: '10px', sm: '12px' },
            }}
          >
            {relevanceScore}%
          </Typography>
        </Box>
      </Box>

      {/* Правая часть - фрагмент текста (3/4 ширины) */}
      <Box
        sx={{
          width: { xs: '100%', sm: '75%' },
          flex: 1,
        }}
      >
        <Typography
          variant="body2"
          sx={{
            color: '#424242',
            lineHeight: 1.6,
            fontSize: { xs: '13px', sm: '14px' },
            textAlign: 'justify',
          }}
        >
          {highlightedText ? (
            <span dangerouslySetInnerHTML={{ __html: highlightedText }} />
          ) : searchQuery ? (
            highlightMatches(textFragment, searchQuery)
          ) : (
            textFragment
          )}
        </Typography>
      </Box>
    </Paper>
  );
};