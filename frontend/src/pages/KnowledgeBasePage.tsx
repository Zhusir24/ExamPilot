import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Snackbar,
  AlertTitle,
} from '@mui/material';
import { Delete as DeleteIcon, CloudUpload as UploadIcon, Add as AddIcon, Visibility as ViewIcon, Settings as SettingsIcon } from '@mui/icons-material';
import { knowledgeApi, llmApi } from '@/api';
import type { KnowledgeDocument, KnowledgeChunk } from '@/types';

export default function KnowledgeBasePage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [textDialogOpen, setTextDialogOpen] = useState(false);
  const [textContent, setTextContent] = useState({ title: '', content: '' });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [hasEmbeddingConfig, setHasEmbeddingConfig] = useState<boolean>(false);

  // 查看分块相关状态
  const [chunksDialogOpen, setChunksDialogOpen] = useState(false);
  const [chunks, setChunks] = useState<KnowledgeChunk[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocument | null>(null);
  const [loadingChunks, setLoadingChunks] = useState(false);

  const checkEmbeddingConfig = async () => {
    try {
      const configs = await llmApi.getConfigs('embedding');
      const activeConfig = configs.find((c) => c.is_active);
      setHasEmbeddingConfig(!!activeConfig);
    } catch (err) {
      console.error('检查Embedding配置失败:', err);
      setHasEmbeddingConfig(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const data = await knowledgeApi.getDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    checkEmbeddingConfig();
    loadDocuments();
  }, []);

  const handleFileUpload = async () => {
    // 清除之前的验证错误
    setValidationError(null);
    
    if (!selectedFile) {
      setValidationError('请选择要上传的文件');
      return;
    }

    try {
      setLoading(true);
      await knowledgeApi.uploadDocument(selectedFile);
      
      // 成功后关闭对话框并刷新列表
      setUploadDialogOpen(false);
      setSelectedFile(null);
      setSuccessMessage('文档上传成功！');
      await loadDocuments();
    } catch (err: any) {
      setError(err.message || '上传文档失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleTextAdd = async () => {
    // 清除之前的验证错误
    setValidationError(null);
    
    // 表单验证
    if (!textContent.title.trim()) {
      setValidationError('请输入文档标题');
      return;
    }
    
    if (!textContent.content.trim()) {
      setValidationError('请输入文档内容');
      return;
    }

    try {
      setLoading(true);
      await knowledgeApi.addDocument({
        title: textContent.title.trim(),
        content: textContent.content.trim(),
      });
      
      // 成功后关闭对话框并刷新列表
      setTextDialogOpen(false);
      setTextContent({ title: '', content: '' });
      setSuccessMessage('文档添加成功！');
      await loadDocuments();
    } catch (err: any) {
      setError(err.message || '添加文档失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除此文档吗？')) return;

    try {
      await knowledgeApi.deleteDocument(id);
      loadDocuments();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleViewChunks = async (doc: KnowledgeDocument) => {
    try {
      setSelectedDocument(doc);
      setLoadingChunks(true);
      setChunksDialogOpen(true);
      const data = await knowledgeApi.getDocumentChunks(doc.id);
      setChunks(data);
    } catch (err: any) {
      setError(err.message || '获取分块信息失败');
      setChunksDialogOpen(false);
    } finally {
      setLoadingChunks(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">知识库管理</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setTextDialogOpen(true)}
            disabled={!hasEmbeddingConfig}
          >
            添加文本
          </Button>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
            disabled={!hasEmbeddingConfig}
          >
            上传文档
          </Button>
        </Box>
      </Box>

      {!hasEmbeddingConfig && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <AlertTitle>需要配置Embedding服务</AlertTitle>
          添加和上传文档需要Embedding服务来生成向量。请先在LLM设置中添加并激活一个Embedding配置。
          <Button
            size="small"
            startIcon={<SettingsIcon />}
            onClick={() => navigate('/llm-settings')}
            sx={{ mt: 1 }}
          >
            前往配置
          </Button>
        </Alert>
      )}

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
                <TableCell>标题</TableCell>
                <TableCell>文件名</TableCell>
                <TableCell>文件类型</TableCell>
                <TableCell>分块数</TableCell>
                <TableCell>创建时间</TableCell>
                <TableCell>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.title}</TableCell>
                  <TableCell>{doc.filename || '-'}</TableCell>
                  <TableCell>{doc.file_type || '-'}</TableCell>
                  <TableCell>{doc.total_chunks}</TableCell>
                  <TableCell>{new Date(doc.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <IconButton onClick={() => handleViewChunks(doc)} size="small" color="primary" title="查看分块">
                      <ViewIcon />
                    </IconButton>
                    <IconButton onClick={() => handleDelete(doc.id)} size="small" color="error" title="删除">
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 上传文件对话框 */}
      <Dialog open={uploadDialogOpen} onClose={() => {
        setUploadDialogOpen(false);
        setValidationError(null);
        setSelectedFile(null);
      }}>
        <DialogTitle>上传文档</DialogTitle>
        <DialogContent>
          {validationError && uploadDialogOpen && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {validationError}
            </Alert>
          )}
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              支持的格式：.txt, .md
            </Typography>
            <input
              type="file"
              accept=".txt,.md"
              onChange={(e) => {
                setSelectedFile(e.target.files?.[0] || null);
                setValidationError(null);
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setUploadDialogOpen(false);
            setValidationError(null);
            setSelectedFile(null);
          }} disabled={loading}>
            取消
          </Button>
          <Button 
            onClick={handleFileUpload} 
            variant="contained" 
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? '上传中...' : '上传'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 添加文本对话框 */}
      <Dialog open={textDialogOpen} onClose={() => {
        setTextDialogOpen(false);
        setValidationError(null);
        setTextContent({ title: '', content: '' });
      }} maxWidth="md" fullWidth>
        <DialogTitle>添加文本文档</DialogTitle>
        <DialogContent>
          {validationError && textDialogOpen && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {validationError}
            </Alert>
          )}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="标题"
              placeholder="请输入文档标题"
              value={textContent.title}
              onChange={(e) => {
                setTextContent({ ...textContent, title: e.target.value });
                setValidationError(null);
              }}
              fullWidth
              required
              error={validationError?.includes('标题')}
            />
            <TextField
              label="内容"
              placeholder="请输入文档内容"
              value={textContent.content}
              onChange={(e) => {
                setTextContent({ ...textContent, content: e.target.value });
                setValidationError(null);
              }}
              multiline
              rows={10}
              fullWidth
              required
              error={validationError?.includes('内容')}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setTextDialogOpen(false);
            setValidationError(null);
            setTextContent({ title: '', content: '' });
          }} disabled={loading}>
            取消
          </Button>
          <Button 
            onClick={handleTextAdd} 
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? '添加中...' : '添加'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 查看分块对话框 */}
      <Dialog 
        open={chunksDialogOpen} 
        onClose={() => {
          setChunksDialogOpen(false);
          setChunks([]);
          setSelectedDocument(null);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          文档分块详情 {selectedDocument && `- ${selectedDocument.title}`}
        </DialogTitle>
        <DialogContent>
          {loadingChunks ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                共 {chunks.length} 个分块
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {chunks.map((chunk) => (
                  <Card key={chunk.id} variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="subtitle2" color="primary">
                          分块 #{chunk.chunk_index + 1}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          位置: {chunk.start_pos} - {chunk.end_pos}
                        </Typography>
                      </Box>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          whiteSpace: 'pre-wrap',
                          backgroundColor: '#f5f5f5',
                          padding: 2,
                          borderRadius: 1,
                          maxHeight: '200px',
                          overflowY: 'auto'
                        }}
                      >
                        {chunk.content}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        长度: {chunk.content.length} 字符
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setChunksDialogOpen(false);
            setChunks([]);
            setSelectedDocument(null);
          }}>
            关闭
          </Button>
        </DialogActions>
      </Dialog>

      {/* 成功提示 */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccessMessage(null)} severity="success" sx={{ width: '100%' }}>
          {successMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}

