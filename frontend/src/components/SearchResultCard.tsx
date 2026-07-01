import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

interface SearchResultCardProps {
  fileName: string;
  pageNumber: number;
  relevanceScore: number;
  textFragment: string;
  highlightedText?: string[]; // 🔥 Теперь это массив строк от бэкенда
  searchQuery?: string;
}

export const SearchResultCard: React.FC<SearchResultCardProps> = ({
  fileName,
  pageNumber,
  relevanceScore,
  textFragment,
  highlightedText,
  searchQuery,
}) => {
  // Функция для рендеринга highlighted_text от бэкенда
  // Бэкенд возвращает массив фрагментов с тегами <mark>...</mark>
  const renderHighlightedText = (highlights: string[]): React.ReactNode => {
    // Объединяем все фрагменты через "..." (как это обычно делают поисковики)
    const combinedText = highlights.join(' ... ');

    // Заменяем <mark> и </mark> на стилизованные span'ы
    const styledHtml = combinedText
      .replace(/<mark>/gi, '<span style="background-color:#fff278;color:#000000;padding:0 2px;border-radius:2px;font-weight:500;">')
      .replace(/<\/mark>/gi, '</span>');

    return (
      <span dangerouslySetInnerHTML={{ __html: styledHtml }} />
    );
  };

  // Фолбэк: если бэкенд не вернул highlighted_text, используем старую подсветку
  const highlightMatches = (text: string, query: string): React.ReactNode => {
    if (!query?.trim()) return text;

    const words = query
      .trim()
      .replace(/[().]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length > 0);

    if (!words.length) return text;

    const uniqueWords = [...new Set(words)].sort((a, b) => b.length - a.length);
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let keyIndex = 0;

    const allMatches: Array<{ start: number; end: number; text: string }> = [];

    uniqueWords.forEach(word => {
      const escapedWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escapedWord, 'giu');
      let match;
      while ((match = regex.exec(text)) !== null) {
        allMatches.push({
          start: match.index,
          end: match.index + match[0].length,
          text: match[0]
        });
      }
    });

    allMatches.sort((a, b) => a.start - b.start);
    const filteredMatches = allMatches.filter((match, i, arr) => {
      if (i === 0) return true;
      return match.start >= arr[i - 1].end;
    });

    filteredMatches.forEach(match => {
      if (match.start > lastIndex) {
        parts.push(text.slice(lastIndex, match.start));
      }
      parts.push(
        <Box
          key={keyIndex++}
          component="span"
          sx={{
            backgroundColor: '#fff278',
            color: '#000000',
            padding: '0 2px',
            borderRadius: '2px',
            fontWeight: 500,
          }}
        >
          {match.text}
        </Box>
      );
      lastIndex = match.end;
    });

    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return <>{parts}</>;
  };

  // Расчет релевантности (процент найденных слов из запроса)
  const calculateRelevancePercent = (text: string, query: string): number => {
    if (!query.trim()) return 0;

    const cleanQuery = query
      .trim()
      .toLowerCase()
      .replace(/[^\w\sа-яА-ЯёЁ0-9]/g, ' ');

    const queryWords = cleanQuery.split(/\s+/).filter(w => w.length > 0);
    if (queryWords.length === 0) return 0;

    const textLower = text.toLowerCase();
    let foundCount = 0;

    queryWords.forEach(word => {
      if (textLower.includes(word.toLowerCase())) {
        foundCount++;
      }
    });

    return Math.round((foundCount / queryWords.length) * 100);
  };

  const displayRelevance = searchQuery
    ? calculateRelevancePercent(textFragment, searchQuery)
    : Math.round(relevanceScore);

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
        flexDirection: { xs: 'column', sm: 'row' },
      }}
    >
      {/* Левая часть */}
      <Box
        sx={{
          width: { xs: '100%', sm: '25%' },
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
          flexShrink: 0,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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

        <Typography
          variant="caption"
          sx={{
            color: '#757575',
            fontSize: { xs: '11px', sm: '12px' },
          }}
        >
          Страница {pageNumber}
        </Typography>

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
                width: `${displayRelevance}%`,
                height: '100%',
                backgroundColor:
                  displayRelevance >= 70
                    ? '#a3ffa6'
                    : displayRelevance >= 40
                    ? '#fed290'
                    : '#ffaaa3',
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
            {displayRelevance}%
          </Typography>
        </Box>
      </Box>

      {/* Правая часть - текст с подсветкой */}
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
          {/* highlighted_text от бэкенда > ручная подсветка > обычный текст */}
          {highlightedText && highlightedText.length > 0 ? (
            renderHighlightedText(highlightedText)
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