import React, { useState } from 'react';
import {
  TextField,
  Button,
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
import { registerApi } from '../api/auth';
import '../styles/global.css';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleRegister = async () => {
    setError(null);
    setSuccess(null);

    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    setLoading(true);
    try {
      await registerApi({ username: login, password });
      setSuccess('Регистрация успешна! Перенаправляем на вход...');
      // Через секунду ведём на логин
      setTimeout(() => navigate('/login'), 1000);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.msg ||
        'Ошибка регистрации';
      setError(typeof msg === 'string' ? msg : 'Ошибка регистрации');
    } finally {
      setLoading(false);
    }
  };

  const handleClickShowPassword = () => setShowPassword(!showPassword);
  const handleClickShowConfirmPassword = () => setShowConfirmPassword(!showConfirmPassword);

  const isDisabled =
    !login || !password || !confirmPassword || password !== confirmPassword || loading;

  return (
    <Box className="auth-container">
      <Button
        onClick={() => navigate('/login')}
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
        Авторизация
      </Button>

      <Paper className="auth-paper" elevation={0}>
        <Typography variant="h5" component="h1" align="center" gutterBottom
          sx={{ fontWeight: 600, color: '#0288D1', mb: 4 }}>
          Регистрация
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <TextField
          fullWidth
          label="Ваш логин"
          variant="outlined"
          value={login}
          onChange={(e) => setLogin(e.target.value)}
          disabled={loading}
          sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
        />

        <TextField
          fullWidth
          label="Придумайте пароль"
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
          sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
        />

        <TextField
          fullWidth
          label="Повторите пароль"
          type={showConfirmPassword ? 'text' : 'password'}
          variant="outlined"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          disabled={loading}
          error={confirmPassword !== '' && password !== confirmPassword}
          helperText={
            confirmPassword !== '' && password !== confirmPassword
              ? 'Пароли не совпадают'
              : ''
          }
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={handleClickShowConfirmPassword} edge="end">
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
          sx={{ mb: 4, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
        />

        <Button
          fullWidth
          variant="contained"
          onClick={handleRegister}
          disabled={isDisabled}
          sx={{
            backgroundColor: '#08dad0',
            py: 1.5,
            borderRadius: 2,
            textTransform: 'none',
            fontSize: '16px',
            fontWeight: 600,
            '&:hover': { backgroundColor: '#07c4bc' },
          }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Зарегистрироваться'}
        </Button>
      </Paper>
    </Box>
  );
};