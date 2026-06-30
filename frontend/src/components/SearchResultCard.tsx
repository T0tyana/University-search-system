import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

interface SearchResultCardProps {
  fileName: string;
  pageNumber: number;
  relevanceScore: number;
  textFragment: string;
  highlightedText?: string;
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
  const highlightMatches = (
    text: string,
    query: string
  ): React.ReactNode => {
    if (!query?.trim()) return text;

    const words = query
      .trim()
      .replace(/[().]/g, ' ')
      .split(/\s+/)
      .filter(Boolean);

    if (!words.length) return text;

    const uniqueWords = [...new Set(words)].sort(
      (a, b) => b.length - a.length
    );

    const matches: Array<{
      start: number;
      end: number;
      text: string;
    }> = [];

    uniqueWords.forEach((word) => {
      const escapedWord = word.replace(
        /[.*+?^${}()|[\]\\]/g,
        '\\$&'
      );

      const regex = new RegExp(
        `(^|[^\\p{L}\\p{N}])(${escapedWord})(?=[^\\p{L}\\p{N}]|$)`,
        'giu'
      );

      let match: RegExpExecArray | null;

      while ((match = regex.exec(text)) !== null) {
        const prefixLength = match[1]?.length ?? 0;

        const start = match.index + prefixLength;
        const end = start + match[2].length;

        matches.push({
          start,
          end,
          text: match[2],
        });
      }
    });

    if (!matches.length) {
      return text;
    }

    matches.sort((a, b) => {
      if (a.start !== b.start) {
        return a.start - b.start;
      }

      return b.end - a.end;
    });

    const filteredMatches: typeof matches = [];

    for (const match of matches) {
      const last = filteredMatches[filteredMatches.length - 1];

      if (!last || match.start >= last.end) {
        filteredMatches.push(match);
      }
    }

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    filteredMatches.forEach((match, index) => {
      if (match.start > lastIndex) {
        parts.push(text.slice(lastIndex, match.start));
      }

      parts.push(
        <Box
          key={`highlight-${index}`}
          component="span"
          sx={{
            backgroundColor: '#fff278',
            color: '#000000',
            padding: '0 2px',
            borderRadius: '2px',
            fontWeight: 500,
          }}
        >
          {text.slice(match.start, match.end)}
        </Box>
      );

      lastIndex = match.end;
    });

    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return <>{parts}</>;
  };

  const calculateRelevancePercent = (
    text: string,
    query: string
  ): number => {
    if (!query.trim()) return 0;

    const cleanQuery = query
      .trim()
      .toLowerCase()
      .replace(/[^\w\sа-яА-ЯёЁ0-9]/g, ' ');

    const queryWords = cleanQuery
      .split(/\s+/)
      .filter(Boolean);

    if (queryWords.length === 0) return 0;

    const textLower = text.toLowerCase();

    let foundCount = 0;

    queryWords.forEach((word) => {
      const escapedWord = word.replace(
        /[.*+?^${}()|[\]\\]/g,
        '\\$&'
      );

      const regex = new RegExp(
        `(^|[^\\p{L}\\p{N}])${escapedWord}(?=[^\\p{L}\\p{N}]|$)`,
        'iu'
      );

      if (regex.test(textLower)) {
        foundCount++;
      }
    });

    return Math.round(
      (foundCount / queryWords.length) * 100
    );
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