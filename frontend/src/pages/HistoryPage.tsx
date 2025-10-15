import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  MenuItem,
  Chip,
  LinearProgress,
  Alert,
  Pagination,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  GetApp as ExportIcon,
} from '@mui/icons-material';
import { historyApi } from '@/api';
import type { AnsweringSession } from '@/types';

export default function HistoryPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<AnsweringSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 分页
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [total, setTotal] = useState(0);
  
  // 筛选
  const [modeFilter, setModeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // 删除对话框
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<number | null>(null);

  useEffect(() => {
    loadSessions();
  }, [page, modeFilter, statusFilter]);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await historyApi.getSessions({
        page,
        page_size: pageSize,
        mode: modeFilter || undefined,
        status: statusFilter || undefined,
      });
      setSessions(response.items);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sessionId: number) => {
    try {
      await historyApi.deleteSession(sessionId);
      loadSessions(); // 重新加载
      setDeleteDialogOpen(false);
      setSessionToDelete(null);
    } catch (err: any) {
      setError(err.message || '删除失败');
    }
  };

  const handleExport = async (sessionId: number) => {
    try {
      const data = await historyApi.exportSession(sessionId, 'json');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `session-${sessionId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || '导出失败');
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'in_progress': return '进行中';
      case 'failed': return '失败';
      default: return status;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">历史记录</Typography>
        <Button variant="outlined" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </Box>

      {/* 筛选条件 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                fullWidth
                label="答题模式"
                value={modeFilter}
                onChange={(e) => setModeFilter(e.target.value)}
              >
                <MenuItem value="">全部</MenuItem>
                <MenuItem value="FULL_AUTO">全自动AI答题</MenuItem>
                <MenuItem value="USER_SELECT">用户勾选AI介入</MenuItem>
                <MenuItem value="PRESET_ANSWERS">预设答案填充</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                fullWidth
                label="状态"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">全部</MenuItem>
                <MenuItem value="completed">已完成</MenuItem>
                <MenuItem value="in_progress">进行中</MenuItem>
                <MenuItem value="failed">失败</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* 会话列表 */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {sessions.map((session) => (
          <Card key={session.id}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    {session.questionnaire?.title || '未知问卷'}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip label={session.mode_display} size="small" color="primary" />
                    <Chip 
                      label={getStatusText(session.status)} 
                      size="small" 
                      color={getStatusColor(session.status) as any}
                    />
                    {session.submitted && <Chip label="已提交" size="small" color="info" />}
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        题目进度
                      </Typography>
                      <Typography variant="body1">
                        {session.answered_questions}/{session.total_questions}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        平均置信度
                      </Typography>
                      <Typography variant="body1">
                        {session.avg_confidence ? `${(session.avg_confidence * 100).toFixed(0)}%` : '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        用时
                      </Typography>
                      <Typography variant="body1">
                        {formatDuration(session.duration)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        时间
                      </Typography>
                      <Typography variant="body1">
                        {formatDate(session.start_time)}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <IconButton
                    color="primary"
                    onClick={() => navigate(`/history/${session.id}`)}
                    title="查看详情"
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
                    color="info"
                    onClick={() => handleExport(session.id)}
                    title="导出"
                  >
                    <ExportIcon />
                  </IconButton>
                  <IconButton
                    color="error"
                    onClick={() => {
                      setSessionToDelete(session.id);
                      setDeleteDialogOpen(true);
                    }}
                    title="删除"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))}

        {!loading && sessions.length === 0 && (
          <Card>
            <CardContent>
              <Typography variant="body1" color="text.secondary" align="center">
                暂无历史记录
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>

      {/* 分页 */}
      {total > pageSize && (
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
          <Pagination
            count={Math.ceil(total / pageSize)}
            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <Typography>确定要删除这条历史记录吗？此操作不可恢复。</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button
            onClick={() => sessionToDelete && handleDelete(sessionToDelete)}
            color="error"
            variant="contained"
          >
            删除
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

