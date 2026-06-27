import React from 'react';
import { IconButton, Tooltip } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import { useNavigate, useLocation } from 'react-router-dom';

export const BackButton: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  // Не показываем кнопку на страницах авторизации/регистрации
  if (location.pathname === '/login' || location.pathname === '/register') {
    return null;
  }

  return (
    <Tooltip title="Выйти" placement="right">
      <IconButton
        onClick={handleLogout}
        sx={{
          position: 'absolute',
          top: 20,
          left: 20,
          backgroundColor: '#ffffff',
          color: '#EF5350',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          width: '44px',
          height: '44px',
          borderRadius: '12px',
          zIndex: 1000,
          '&:hover': {
            backgroundColor: '#FFEBEE',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          },
        }}
      >
        <LogoutIcon sx={{ fontSize: 24 }} />
      </IconButton>
    </Tooltip>
  );
};