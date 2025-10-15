import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSnapshot } from 'valtio';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { questionnaireApi } from '@/api';
import { appState, setQuestionnaire, setLoading, setError } from '@/store';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const snap = useSnapshot(appState);
  const navigate = useNavigate();

  const handleParse = async () => {
    if (!url.trim()) {
      setError('请输入问卷URL');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await questionnaireApi.parse(url);
      setQuestionnaire(
        {
          id: result.questionnaire_id,
          url: result.url,
          platform: result.platform,
          template_type: result.template_type,
          title: result.title,
          description: result.description,
          total_questions: result.total_questions,
        },
        result.questions
      );
      navigate('/preview');
    } catch (error: any) {
      setError(error.message || '解析失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom align="center">
        欢迎使用 ExamPilot
      </Typography>
      <Typography variant="subtitle1" gutterBottom align="center" color="text.secondary">
        智能自动答题系统
      </Typography>

      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            开始答题
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            请输入问卷星的问卷链接，系统将自动解析题目
          </Typography>

          <TextField
            fullWidth
            label="问卷URL"
            placeholder="https://www.wjx.cn/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={snap.loading}
            sx={{ mb: 2 }}
          />

          {snap.error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {snap.error}
            </Alert>
          )}

          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleParse}
            disabled={snap.loading}
            startIcon={snap.loading && <CircularProgress size={20} />}
          >
            {snap.loading ? '解析中...' : '解析问卷'}
          </Button>
        </CardContent>
      </Card>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          功能特性
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                🤖 智能答题
              </Typography>
              <Typography variant="body2" color="text.secondary">
                集成LLM模型进行智能答题
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                📚 知识库检索
              </Typography>
              <Typography variant="body2" color="text.secondary">
                支持文档上传和向量检索
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                🎯 多种模式
              </Typography>
              <Typography variant="body2" color="text.secondary">
                全自动、用户勾选、预设答案
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                ⏱️ 时间模拟
              </Typography>
              <Typography variant="body2" color="text.secondary">
                人性化答题时间模拟
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
}

