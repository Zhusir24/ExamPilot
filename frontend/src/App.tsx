import { Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Container, Box } from '@mui/material';
import HomePage from './pages/HomePage';
import QuestionPreviewPage from './pages/QuestionPreviewPage';
import AnsweringProgressPage from './pages/AnsweringProgressPage';
import LLMSettingsPage from './pages/LLMSettingsPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import SystemSettingsPage from './pages/SystemSettingsPage';
import HistoryPage from './pages/HistoryPage';
import HistoryDetailPage from './pages/HistoryDetailPage';

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ExamPilot - 智能自动答题系统
          </Typography>
          <Button color="inherit" component={Link} to="/">
            首页
          </Button>
          <Button color="inherit" component={Link} to="/history">
            历史记录
          </Button>
          <Button color="inherit" component={Link} to="/llm-settings">
            LLM设置
          </Button>
          <Button color="inherit" component={Link} to="/knowledge">
            知识库
          </Button>
          <Button color="inherit" component={Link} to="/settings">
            系统设置
          </Button>
        </Toolbar>
      </AppBar>

      <Container component="main" sx={{ flexGrow: 1, py: 4 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/preview" element={<QuestionPreviewPage />} />
          <Route path="/answering" element={<AnsweringProgressPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/history/:sessionId" element={<HistoryDetailPage />} />
          <Route path="/llm-settings" element={<LLMSettingsPage />} />
          <Route path="/knowledge" element={<KnowledgeBasePage />} />
          <Route path="/settings" element={<SystemSettingsPage />} />
        </Routes>
      </Container>

      <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: '#f5f5f5' }}>
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            © 2025 ExamPilot. All rights reserved.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}

export default App;

