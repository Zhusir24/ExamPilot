import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon, Add as AddIcon } from '@mui/icons-material';
import { llmApi } from '@/api';
import type { LLMConfig } from '@/types';

export default function LLMSettingsPage() {
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<Partial<LLMConfig> | null>(null);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string } | null>(null);

  const loadConfigs = async () => {
    try {
      const data = await llmApi.getConfigs();
      setConfigs(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  const handleTestConnection = async () => {
    if (!editingConfig) return;

    // 验证必填字段
    if (!editingConfig.name || !editingConfig.base_url || !editingConfig.model || !editingConfig.config_type) {
      setError('请填写所有必填字段');
      return;
    }

    setValidating(true);
    setValidationResult(null);
    setError(null);

    try {
      const result = await llmApi.validateConfig(editingConfig);
      setValidationResult(result);
      if (!result.valid) {
        setError(result.message);
      }
    } catch (err: any) {
      setError(err.message);
      setValidationResult({ valid: false, message: err.message });
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async () => {
    if (!editingConfig) return;

    // 保存前强制验证
    if (!validationResult || !validationResult.valid) {
      setError('请先测试连接,确保配置有效后再保存');
      return;
    }

    try {
      if (editingConfig.id) {
        await llmApi.updateConfig(editingConfig.id, editingConfig);
      } else {
        await llmApi.createConfig(editingConfig);
      }
      setDialogOpen(false);
      setEditingConfig(null);
      setValidationResult(null);
      loadConfigs();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除此配置吗？')) return;

    try {
      await llmApi.deleteConfig(id);
      loadConfigs();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const openDialog = (config?: LLMConfig) => {
    setEditingConfig(config || {
      name: '',
      provider: 'DeepSeek',
      base_url: 'https://api.deepseek.com/v1',
      model: 'deepseek-chat',
      temperature: 0.7,
      config_type: 'llm',
      is_active: true,
    });
    setValidationResult(null);
    setError(null);
    setDialogOpen(true);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">LLM配置</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => openDialog()}
        >
          添加配置
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>名称</TableCell>
                <TableCell>供应商</TableCell>
                <TableCell>模型</TableCell>
                <TableCell>类型</TableCell>
                <TableCell>状态</TableCell>
                <TableCell>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {configs.map((config) => (
                <TableRow key={config.id}>
                  <TableCell>{config.name}</TableCell>
                  <TableCell>{config.provider}</TableCell>
                  <TableCell>{config.model}</TableCell>
                  <TableCell>
                    <Chip label={config.config_type} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={config.is_active ? '启用' : '禁用'}
                      size="small"
                      color={config.is_active ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton onClick={() => openDialog(config)} size="small">
                      <EditIcon />
                    </IconButton>
                    <IconButton onClick={() => handleDelete(config.id!)} size="small" color="error">
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingConfig?.id ? '编辑配置' : '添加配置'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="配置名称"
              value={editingConfig?.name || ''}
              onChange={(e) => {
                setEditingConfig({ ...editingConfig, name: e.target.value });
                setValidationResult(null);
              }}
              fullWidth
              required
            />
            <TextField
              label="供应商"
              value={editingConfig?.provider || ''}
              onChange={(e) => {
                setEditingConfig({ ...editingConfig, provider: e.target.value });
                setValidationResult(null);
              }}
              fullWidth
            />
            <TextField
              label="API密钥"
              type="password"
              value={editingConfig?.api_key || ''}
              onChange={(e) => {
                setEditingConfig({ ...editingConfig, api_key: e.target.value });
                setValidationResult(null);
              }}
              fullWidth
              helperText="某些API可能不需要密钥"
            />
            <TextField
              label="API地址"
              value={editingConfig?.base_url || ''}
              onChange={(e) => {
                setEditingConfig({ ...editingConfig, base_url: e.target.value });
                setValidationResult(null);
              }}
              fullWidth
              required
            />
            <TextField
              label="模型名称"
              value={editingConfig?.model || ''}
              onChange={(e) => {
                setEditingConfig({ ...editingConfig, model: e.target.value });
                setValidationResult(null);
              }}
              fullWidth
              required
            />
            <TextField
              label="温度"
              type="number"
              value={editingConfig?.temperature || 0.7}
              onChange={(e) => setEditingConfig({ ...editingConfig, temperature: parseFloat(e.target.value) })}
              inputProps={{ min: 0, max: 2, step: 0.1 }}
              fullWidth
            />
            <FormControl fullWidth required>
              <InputLabel>配置类型</InputLabel>
              <Select
                value={editingConfig?.config_type || 'llm'}
                onChange={(e) => {
                  setEditingConfig({ ...editingConfig, config_type: e.target.value });
                  setValidationResult(null);
                }}
                label="配置类型"
              >
                <MenuItem value="llm">LLM</MenuItem>
                <MenuItem value="embedding">Embedding</MenuItem>
                <MenuItem value="rerank">Rerank</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>状态</InputLabel>
              <Select
                value={editingConfig?.is_active ? 'true' : 'false'}
                onChange={(e) => setEditingConfig({ ...editingConfig, is_active: e.target.value === 'true' })}
                label="状态"
              >
                <MenuItem value="true">启用</MenuItem>
                <MenuItem value="false">禁用</MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info" sx={{ mt: 1 }}>
              每种类型(LLM/Embedding/Rerank)只能有一个激活的配置。保存前需要先测试连接。
            </Alert>

            <Button
              variant="outlined"
              onClick={handleTestConnection}
              disabled={validating}
              fullWidth
            >
              {validating ? '测试中...' : '测试连接'}
            </Button>

            {validationResult && (
              <Alert severity={validationResult.valid ? 'success' : 'error'}>
                {validationResult.message}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>取消</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={!validationResult || !validationResult.valid}
          >
            保存
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

