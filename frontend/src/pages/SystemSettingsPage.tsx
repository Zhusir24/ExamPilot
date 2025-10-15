import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Divider,
} from '@mui/material';
import { settingsApi } from '@/api';

export default function SystemSettingsPage() {
  const [settings, setSettings] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await settingsApi.getAll();
      const settingsMap: Record<string, any> = {};
      data.forEach((s) => {
        settingsMap[s.key] = s.value;
      });
      setSettings(settingsMap);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // 更新每个设置
      for (const [key, value] of Object.entries(settings)) {
        const valueType = typeof value === 'boolean' ? 'bool' : typeof value === 'number' ? 'float' : 'str';
        await settingsApi.update(key, { key, value, value_type: valueType });
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInitDefaults = async () => {
    try {
      await settingsApi.initDefaults();
      loadSettings();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const updateSetting = (key: string, value: any) => {
    setSettings({ ...settings, [key]: value });
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">系统设置</Typography>
        <Button variant="outlined" onClick={handleInitDefaults}>
          初始化默认设置
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          设置保存成功！
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            答题设置
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="置信度阈值"
              type="number"
              value={settings.confidence_threshold || 0.7}
              onChange={(e) => updateSetting('confidence_threshold', parseFloat(e.target.value))}
              inputProps={{ min: 0, max: 1, step: 0.1 }}
              helperText="低于此值的答案需要人工确认"
              fullWidth
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.use_knowledge_base || false}
                  onChange={(e) => updateSetting('use_knowledge_base', e.target.checked)}
                />
              }
              label="使用知识库辅助答题"
            />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            时间模拟设置
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>时间策略</InputLabel>
              <Select
                value={settings.timing_strategy || 'none'}
                onChange={(e) => updateSetting('timing_strategy', e.target.value)}
                label="时间策略"
              >
                <MenuItem value="none">无停顿（最快速度）</MenuItem>
                <MenuItem value="uniform">均匀分布</MenuItem>
                <MenuItem value="normal">正态分布</MenuItem>
                <MenuItem value="segmented">分段停顿</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="最小答题时间（秒）"
              type="number"
              value={settings.timing_min_time || 2.0}
              onChange={(e) => updateSetting('timing_min_time', parseFloat(e.target.value))}
              inputProps={{ min: 0.5, step: 0.5 }}
              fullWidth
            />

            <TextField
              label="最大答题时间（秒）"
              type="number"
              value={settings.timing_max_time || 10.0}
              onChange={(e) => updateSetting('timing_max_time', parseFloat(e.target.value))}
              inputProps={{ min: 1, step: 0.5 }}
              fullWidth
            />
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSave}
          disabled={loading}
        >
          {loading ? '保存中...' : '保存设置'}
        </Button>
      </Box>
    </Box>
  );
}

