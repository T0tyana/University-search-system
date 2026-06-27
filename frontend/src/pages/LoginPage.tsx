import React, { useState, useEffect } from 'react';
import {
  TextField,
  Button,
  Checkbox,
  FormControlLabel,
  Typography,
  Paper,
  InputAdornment,
  IconButton,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { loginApi } from '../api/auth';
import '../styles/global.css';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedLogin = localStorage.getItem('rememberedLogin');
    if (savedLogin) {
      setLogin(savedLogin);
      setRememberMe(true);
    }

    const savedPassword = localStorage.getItem('rememberedPassword');
    if (savedPassword) setPassword(savedPassword);
  }, []);

  const handleLogin = async () => {
    setError(null);

    // Запоминаем логин, если нужно
    if (rememberMe) {
      localStorage.setItem('rememberedLogin', login);
      localStorage.setItem('rememberedPassword', password);
    } else {
      localStorage.removeItem('rememberedLogin');
      localStorage.removeItem('rememberedPassword');
    }

    setLoading(true);
    try {
      const data = await loginApi({ username: login, password });
      // Сохраняем JWT токен — он будет автоматически подставляться во все запросы
      localStorage.setItem('access_token', data.access_token);
      navigate('/home');
    } catch (err: any) {
      // axios кладёт ответ сервера в err.response
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.msg ||
        'Неверный логин или пароль';
      setError(typeof msg === 'string' ? msg : 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  const handleClickShowPassword = () => setShowPassword(!showPassword);

  return (
    <Box className="auth-container">
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
          '&:hover': { backgroundColor: '#E3F2FD' },
        }}
      >
        Регистрация
      </Button>

      <Paper className="auth-paper" elevation={0}>
        <Typography variant="h5" component="h1" align="center" gutterBottom
          sx={{ fontWeight: 600, color: '#0288D1', mb: 4 }}>
          Авторизация
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Логин"
          variant="outlined"
          value={login}
          onChange={(e) => setLogin(e.target.value)}
          disabled={loading}
          sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
        />

        <TextField
          fullWidth
          label="Пароль"
          type={showPassword ? 'text' : 'password'}
          variant="outlined"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={handleClickShowPassword} edge="end">
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
          sx={{ mb: 2, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              disabled={loading}
            />
          }
          label="Запомнить меня"
          sx={{ mb: 4 }}
        />

        <Button
          fullWidth
          variant="contained"
          onClick={handleLogin}
          disabled={!login || !password || loading}
          sx={{
            backgroundColor: '#9969f7',
            py: 1.5,
            borderRadius: 2,
            textTransform: 'none',
            fontSize: '16px',
            fontWeight: 600,
            '&:hover': { backgroundColor: '#8557e6' },
          }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Войти'}
        </Button>
      </Paper>
    </Box>
  );
};