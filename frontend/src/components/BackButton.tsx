import React from 'react';
import { IconButton, Tooltip } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useNavigate, useLocation } from 'react-router-dom';

export const BackButton: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleClick = () => {
    // Если мы на главной странице, идем на login
    if (location.pathname === '/home' || location.pathname === '/') {
      navigate('/login');
    } else {
      navigate(-1);
    }
  };

  // Не показываем кнопку на страницах авторизации/регистрации
  if (location.pathname === '/login' || location.pathname === '/register') {
    return null;
  }

  return (
    <Tooltip title="Назад" placement="right">
      <IconButton
        onClick={handleClick}
        sx={{
          position: 'absolute',
          top: 20,
          left: 20,
          backgroundColor: '#ffffff',
          color: '#0288D1',
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
        <ArrowBackIcon sx={{ fontSize: 24 }} />
      </IconButton>
    </Tooltip>
  );
};