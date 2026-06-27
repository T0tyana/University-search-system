import React, { useState } from 'react';
import {
  TextField,
  Button,
  Typography,
  Paper,
  InputAdornment,
  IconButton,
  Box,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import '../styles/global.css';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleRegister = () => {
    if (password !== confirmPassword) {
      alert('Пароли не совпадают!');
      return;
    }
    navigate('/home');
  };

  const handleClickShowPassword = () => setShowPassword(!showPassword);
  const handleClickShowConfirmPassword = () => setShowConfirmPassword(!showConfirmPassword);

  return (
    <Box className="auth-container">
      {/* Кнопка перехода - возвращаем sx вместо className */}
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
          '&:hover': {
            backgroundColor: '#E3F2FD',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          },
        }}
      >
        Авторизация
      </Button>

      <Paper className="auth-paper" elevation={0}>
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
          Регистрация
        </Typography>

        <TextField
          fullWidth
          label="Ваш логин"
          variant="outlined"
          value={login}
          onChange={(e) => setLogin(e.target.value)}
          sx={{
            mb: 3,
            '& .MuiOutlinedInput-root': { borderRadius: 2 },
          }}
        />

        <TextField
          fullWidth
          label="Придумайте пароль"
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
                    sx={{ color: '#757575', '&:hover': { color: '#0288D1' } }}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
          sx={{
            mb: 3,
            '& .MuiOutlinedInput-root': { borderRadius: 2 },
          }}
        />

        <TextField
          fullWidth
          label="Повторите пароль"
          type={showConfirmPassword ? 'text' : 'password'}
          variant="outlined"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
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
                  <IconButton
                    onClick={handleClickShowConfirmPassword}
                    edge="end"
                    sx={{ color: '#757575', '&:hover': { color: '#0288D1' } }}
                  >
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
          sx={{
            mb: 4,
            '& .MuiOutlinedInput-root': { borderRadius: 2 },
          }}
        />

        <Button
          fullWidth
          variant="contained"
          onClick={handleRegister}
          disabled={!login || !password || !confirmPassword || password !== confirmPassword}
          sx={{
            backgroundColor: '#08dad0',
            color: '#ffffff',
            fontSize: '16px',
            fontWeight: 600,
            py: 1.5,
            borderRadius: 2,
            textTransform: 'none',
            boxShadow: '0 4px 12px rgba(8, 218, 208, 0.3)',
            '&:hover': {
              backgroundColor: '#07c4bc',
              boxShadow: '0 6px 16px rgba(8, 218, 208, 0.4)',
            },
            '&:disabled': { backgroundColor: '#B0BEC5', boxShadow: 'none' },
          }}
        >
          Зарегистрироваться
        </Button>
      </Paper>
    </Box>
  );
};