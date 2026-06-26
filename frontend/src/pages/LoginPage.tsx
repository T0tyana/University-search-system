import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Checkbox,
  FormControlLabel,
  Typography,
  Paper,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    const savedLogin = localStorage.getItem('rememberedLogin');
    const savedPassword = localStorage.getItem('rememberedPassword');
    if (savedLogin) {
      setLogin(savedLogin);
      setRememberMe(true);
    }
    if (savedPassword) {
      setPassword(savedPassword);
    }
  }, []);

  const handleLogin = () => {
    if (rememberMe) {
      localStorage.setItem('rememberedLogin', login);
      localStorage.setItem('rememberedPassword', password);
    } else {
      localStorage.removeItem('rememberedLogin');
      localStorage.removeItem('rememberedPassword');
    }
    navigate('/home');
  };

  const handleClickShowPassword = () => setShowPassword(!showPassword);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#e6f4ff',
        position: 'relative',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        px: 2,
      }}
    >
      {/* Кнопка перехода на регистрацию */}
      <Button
        onClick={() => navigate('/register')}
        sx={{
          position: 'absolute',
          top: 20,
          right: 20,
          backgroundColor: '#ffffff',
          color: '#0288D1',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: '12px',
          textTransform: 'none',
          fontSize: '14px',
          fontWeight: 500,
          px: 3,
          py: 1,
          '&:hover': {
            backgroundColor: '#E3F2FD',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          },
        }}
      >
        Регистрация
      </Button>

      {/* Форма авторизации */}
      <Paper
        elevation={3}
        sx={{
          width: '100%',
          maxWidth: 400,
          p: 5,
          borderRadius: 4,
          backgroundColor: '#ffffff',
        }}
      >
        <Typography
          variant="h5"
          component="h1"
          align="center"
          gutterBottom
          sx={{
            fontWeight: 600,
            color: '#0288D1',
            mb: 4,
          }}
        >
          Авторизация
        </Typography>

        <TextField
          fullWidth
          label="Логин"
          variant="outlined"
          value={login}
          onChange={(e) => setLogin(e.target.value)}
          sx={{
            mb: 3,
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
            },
          }}
        />

        <TextField
          fullWidth
          label="Пароль"
          type={showPassword ? 'text' : 'password'}
          variant="outlined"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleClickShowPassword}
                    edge="end"
                    sx={{
                      color: '#757575',
                      '&:hover': {
                        color: '#0288D1',
                      },
                    }}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
          sx={{
            mb: 2,
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
            },
          }}
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              sx={{
                color: '#9e9e9e',
                '&.Mui-checked': {
                  color: '#757575',
                },
                '& .MuiSvgIcon-root': {
                  opacity: 0.6,
                },
              }}
            />
          }
          label="Запомнить меня"
          sx={{
            mb: 4,
            '& .MuiTypography-root': {
              fontSize: '14px',
              color: '#757575',
            },
          }}
        />

        <Button
          fullWidth
          variant="contained"
          onClick={handleLogin}
          disabled={!login || !password}
          sx={{
            backgroundColor: '#9969f7',
            color: '#ffffff',
            fontSize: '16px',
            fontWeight: 600,
            py: 1.5,
            borderRadius: 2,
            textTransform: 'none',
            boxShadow: '0 4px 12px rgba(153, 105, 247, 0.3)',
            '&:hover': {
              backgroundColor: '#8557e6',
              boxShadow: '0 6px 16px rgba(153, 105, 247, 0.4)',
            },
            '&:disabled': {
              backgroundColor: '#B0BEC5',
              boxShadow: 'none',
            },
          }}
        >
          Войти
        </Button>
      </Paper>
    </Box>
  );
};