import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  Checkbox,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  ExpandMore as ExpandIcon,
  GetApp as ExportIcon,
  Send as SendIcon,
  LibraryBooks as LibraryBooksIcon,
} from '@mui/icons-material';
import { historyApi } from '@/api';
import type { SessionDetail } from '@/types';

export default function HistoryDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
  const [editedAnswers, setEditedAnswers] = useState<Record<string, any>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    if (sessionId) {
      loadDetail(parseInt(sessionId));
    }
  }, [sessionId]);

  // 自动刷新（进行中状态时）
  useEffect(() => {
    if (!detail || detail.session.status !== 'in_progress') return;

    const intervalId = setInterval(() => {
      loadDetail(parseInt(sessionId!), true); // 静默刷新
    }, 2000); // 每2秒刷新一次

    return () => clearInterval(intervalId);
  }, [detail?.session.status, sessionId]);

  const loadDetail = async (id: number, silent = false) => {
    if (!silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const data = await historyApi.getSessionDetail(id);
      setDetail(data);
    } catch (err: any) {
      setError(err.message || '加载失败');
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const handleExport = async () => {
    if (!sessionId) return;
    try {
      const data = await historyApi.exportSession(parseInt(sessionId), 'json');
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

  const getConfidenceColor = (confidence?: number) => {
    if (confidence === undefined || confidence === null) return 'default';
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.5) return 'warning';
    return 'error';
  };

  const handleOpenSubmitDialog = () => {
    if (!detail) return;
    // 初始化编辑答案为当前答案
    const answers: Record<string, any> = {};
    detail.answers.forEach((item) => {
      if (item.answer !== null && item.answer !== undefined) {
        let answerValue = item.answer;

        // 如果答案格式是 "索引|文本"，提取文本部分
        if (typeof answerValue === 'string' && answerValue.includes('|')) {
          const parts = answerValue.split('|');
          if (parts.length > 1) {
            answerValue = parts.slice(1).join('|'); // 取"|"后面的所有内容
          }
        }

        answers[item.question_id] = answerValue;
      }
    });
    setEditedAnswers(answers);
    setSubmitDialogOpen(true);
  };

  const handleAnswerChange = (questionId: string, value: any) => {
    setEditedAnswers({
      ...editedAnswers,
      [questionId]: value,
    });
  };

  const handleSubmitAnswers = async () => {
    if (!sessionId) return;
    setSubmitting(true);
    setError(null);

    try {
      const result = await historyApi.submitSession(parseInt(sessionId), editedAnswers);

      if (result.success) {
        setSubmitSuccess(true);
        setSubmitDialogOpen(false);
        // 重新加载详情
        loadDetail(parseInt(sessionId));
      } else {
        setError(result.message || '提交失败');
      }
    } catch (err: any) {
      setError(err.message || '提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          加载中...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button
          variant="contained"
          startIcon={<BackIcon />}
          onClick={() => navigate('/history')}
          sx={{ mt: 2 }}
        >
          返回列表
        </Button>
      </Box>
    );
  }

  if (!detail) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>未找到数据</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* 头部 */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<BackIcon />}
            onClick={() => navigate('/history')}
          >
            返回
          </Button>
          <Typography variant="h5">
            {detail.questionnaire?.title || '答题详情'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {!detail.session.submitted && (detail.session.status === 'completed' || detail.session.status === 'failed') && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<SendIcon />}
              onClick={handleOpenSubmitDialog}
            >
              提交问卷
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={handleExport}
          >
            导出
          </Button>
        </Box>
      </Box>

      {submitSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSubmitSuccess(false)}>
          问卷提交成功！
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 会话信息 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            会话信息
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                答题模式
              </Typography>
              <Chip label={detail.session.mode_display} color="primary" sx={{ mt: 0.5 }} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                状态
              </Typography>
              <Chip 
                label={detail.session.status === 'completed' ? '已完成' : detail.session.status}
                color={detail.session.status === 'completed' ? 'success' : 'default'}
                sx={{ mt: 0.5 }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                题目进度
              </Typography>
              <Typography variant="body1" sx={{ mt: 0.5 }}>
                {detail.session.answered_questions} / {detail.session.total_questions}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                平均置信度
              </Typography>
              <Typography variant="body1" sx={{ mt: 0.5 }}>
                {detail.session.avg_confidence 
                  ? `${(detail.session.avg_confidence * 100).toFixed(1)}%` 
                  : '-'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                用时
              </Typography>
              <Typography variant="body1" sx={{ mt: 0.5 }}>
                {formatDuration(detail.session.duration)}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                开始时间
              </Typography>
              <Typography variant="body1" sx={{ mt: 0.5 }}>
                {formatDate(detail.session.start_time)}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                结束时间
              </Typography>
              <Typography variant="body1" sx={{ mt: 0.5 }}>
                {formatDate(detail.session.end_time)}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                提交状态
              </Typography>
              <Chip
                label={detail.session.submitted ? '已提交' : '未提交'}
                color={detail.session.submitted ? 'success' : 'default'}
                size="small"
                sx={{ mt: 0.5 }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 题目和答案列表 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          答题详情
        </Typography>
        {detail.session.status === 'in_progress' && (
          <Chip
            label="实时更新中..."
            size="small"
            color="info"
            sx={{ animation: 'pulse 2s infinite' }}
          />
        )}
      </Box>

      {detail.answers.length === 0 && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              {detail.session.status === 'in_progress'
                ? '正在答题中，请稍候...'
                : '暂无答案数据'}
            </Typography>
          </CardContent>
        </Card>
      )}

      {detail.answers.map((item, index) => {
        const hasAnswer = item.answer !== null && item.answer !== undefined;
        return (
          <Accordion
            key={item.question_id}
            defaultExpanded={index < 3}
            sx={{
              bgcolor: hasAnswer ? 'background.paper' : 'action.hover',
              opacity: hasAnswer ? 1 : 0.7,
            }}
          >
            <AccordionSummary expandIcon={<ExpandIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Typography variant="subtitle1">
                  {item.question.order}. {item.question.content.substring(0, 50)}
                  {item.question.content.length > 50 && '...'}
                </Typography>
                <Box sx={{ flexGrow: 1 }} />
                {!hasAnswer && (
                  <Chip
                    label="待答题"
                    size="small"
                    color="default"
                    variant="outlined"
                  />
                )}
                {hasAnswer && item.confidence !== undefined && (
                  <Chip
                    label={`${(item.confidence * 100).toFixed(0)}%`}
                    color={getConfidenceColor(item.confidence) as any}
                    size="small"
                  />
                )}
                <Chip
                  label={item.question.type}
                  size="small"
                  variant="outlined"
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Box>
                {/* 题目详情 */}
                <Typography variant="body1" gutterBottom>
                  <strong>题目：</strong>{item.question.content}
                </Typography>

                {/* 选项 */}
                {item.question.options && item.question.options.length > 0 && (
                  <Box sx={{ mt: 2, mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      选项：
                    </Typography>
                    {item.question.options.map((option, idx) => (
                      <Typography key={idx} variant="body2" sx={{ ml: 2 }}>
                        {idx}. {option}
                      </Typography>
                    ))}
                  </Box>
                )}

                <Divider sx={{ my: 2 }} />

                {/* 答案 */}
                <Box sx={{ bgcolor: hasAnswer ? 'action.hover' : 'background.default', p: 2, borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    AI答案：
                  </Typography>
                  <Typography variant="body1" sx={{ mt: 1 }}>
                    {hasAnswer
                      ? (item.answer_display || item.answer)
                      : '（等待AI回答中...）'}
                  </Typography>

                  {hasAnswer && item.confidence !== undefined && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        置信度：{(item.confidence * 100).toFixed(1)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={item.confidence * 100}
                        sx={{ mt: 1 }}
                        color={(() => {
                          const colorValue = getConfidenceColor(item.confidence);
                          // LinearProgress 不支持 'default'，用 'primary' 代替
                          return colorValue === 'default' ? 'primary' : colorValue;
                        })() as any}
                      />
                    </Box>
                  )}

                  {hasAnswer && item.reasoning && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        推理过程：
                      </Typography>
                      <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                        {item.reasoning}
                      </Typography>
                    </Box>
                  )}
                  
                  {/* 知识库引用信息 */}
                  {hasAnswer && item.knowledge_references && item.knowledge_references.length > 0 && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                        <LibraryBooksIcon fontSize="small" color="primary" />
                        <Typography variant="body2" color="primary" fontWeight="medium">
                          使用了 {item.knowledge_references.length} 个知识库引用
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {item.knowledge_references.map((ref: any, idx: number) => (
                          <Box key={idx} sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                            {idx > 0 && <Divider sx={{ mb: 2, mt: -1 }} />}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                              <Typography variant="subtitle2" color="text.primary">
                                引用 {idx + 1}: {ref.document_title}
                              </Typography>
                              <Chip 
                                label={`相似度: ${(ref.similarity * 100).toFixed(1)}%`}
                                size="small"
                                color={ref.similarity >= 0.7 ? 'success' : ref.similarity >= 0.5 ? 'primary' : 'warning'}
                              />
                              <Chip 
                                label={`分块 #${ref.chunk_index + 1}`}
                                size="small"
                                variant="outlined"
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ 
                              fontSize: '0.875rem',
                              lineHeight: 1.6,
                              whiteSpace: 'pre-wrap',
                            }}>
                              {ref.content.length > 200 
                                ? `${ref.content.substring(0, 200)}...` 
                                : ref.content
                              }
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
        );
      })}

      {/* 提交编辑弹框 */}
      <Dialog
        open={submitDialogOpen}
        onClose={() => setSubmitDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>编辑并提交答案</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 2 }}>
            您可以在下方编辑AI生成的答案，确认无误后点击提交按钮。
          </Typography>

          {detail?.answers.map((item) => {
            const answer = editedAnswers[item.question_id];
            const questionType = item.question.type;

            // 题型映射：支持中英文题型
            const isRadio = questionType === 'radio' || questionType === '单选';
            const isCheckbox = questionType === 'checkbox' || questionType === '多选';
            const isText = questionType === 'text' || questionType === '填空' || questionType === '单行文本';
            const isTextarea = questionType === 'textarea' || questionType === '多行文本' || questionType === '简答';

            return (
              <Box key={item.question_id} sx={{ mb: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Typography variant="subtitle1" gutterBottom>
                  {item.question.order}. {item.question.content}
                </Typography>

                {/* 单选题 */}
                {isRadio && item.question.options && item.question.options.length > 0 && (
                  <FormControl component="fieldset" sx={{ mt: 1 }}>
                    <RadioGroup
                      value={answer || ''}
                      onChange={(e) => handleAnswerChange(item.question_id, e.target.value)}
                    >
                      {item.question.options.map((option, idx) => (
                        <FormControlLabel
                          key={idx}
                          value={option}
                          control={<Radio />}
                          label={option}
                        />
                      ))}
                    </RadioGroup>
                  </FormControl>
                )}

                {/* 多选题 */}
                {isCheckbox && item.question.options && item.question.options.length > 0 && (
                  <FormControl component="fieldset" sx={{ mt: 1 }}>
                    {item.question.options.map((option, idx) => {
                      const selectedOptions = Array.isArray(answer) ? answer : [];
                      const isChecked = selectedOptions.includes(option);

                      return (
                        <FormControlLabel
                          key={idx}
                          control={
                            <Checkbox
                              checked={isChecked}
                              onChange={(e) => {
                                const newSelected = e.target.checked
                                  ? [...selectedOptions, option]
                                  : selectedOptions.filter((o: string) => o !== option);
                                handleAnswerChange(item.question_id, newSelected);
                              }}
                            />
                          }
                          label={option}
                        />
                      );
                    })}
                  </FormControl>
                )}

                {/* 填空题/文本题 */}
                {(isText || isTextarea) && (
                  <TextField
                    fullWidth
                    multiline={isTextarea}
                    rows={isTextarea ? 4 : 1}
                    value={answer || ''}
                    onChange={(e) => handleAnswerChange(item.question_id, e.target.value)}
                    sx={{ mt: 1 }}
                  />
                )}

                {/* 如果没有匹配任何类型，显示提示 */}
                {!isRadio && !isCheckbox && !isText && !isTextarea && (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    暂不支持该题型编辑（{questionType}）
                  </Alert>
                )}
              </Box>
            );
          })}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSubmitDialogOpen(false)} disabled={submitting}>
            取消
          </Button>
          <Button
            onClick={handleSubmitAnswers}
            variant="contained"
            disabled={submitting}
            startIcon={<SendIcon />}
          >
            {submitting ? '提交中...' : '确认提交'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

