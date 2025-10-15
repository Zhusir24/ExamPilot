import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSnapshot } from 'valtio';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Button,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import { appState, updateAnswer, updateAnsweringProgress, setAnswering } from '@/store';
import { answeringWs } from '@/utils/websocket';

export default function AnsweringProgressPage() {
  const snap = useSnapshot(appState);
  const navigate = useNavigate();
  const [status, setStatus] = useState<'connecting' | 'answering' | 'completed' | 'error'>('connecting');
  const [statusMessage, setStatusMessage] = useState('正在连接...');
  const [submitResult, setSubmitResult] = useState<any>(null);
  const hasStartedRef = useRef(false);

  useEffect(() => {
    if (!snap.questionnaire) {
      navigate('/');
      return;
    }

    // 连接WebSocket
    answeringWs.connect();

    // 监听事件
    answeringWs.on('connected', () => {
      // 防止重复开始答题（例如服务重启后重连）
      if (hasStartedRef.current) {
        console.log('答题已经开始，跳过重复启动');
        return;
      }
      
      hasStartedRef.current = true;
      setStatus('answering');
      setStatusMessage('开始答题...');
      
      // 发送开始命令（包括知识库配置）
      answeringWs.startAnswering(
        snap.questionnaire!.id,
        snap.mode,
        [...snap.selectedQuestions],
        [...snap.presetAnswers],
        snap.knowledgeConfig.enabled ? {
          enabled: snap.knowledgeConfig.enabled,
          document_ids: [...snap.knowledgeConfig.document_ids],
          top_k: snap.knowledgeConfig.top_k,
          score_threshold: snap.knowledgeConfig.score_threshold,
        } : undefined
      );
    });

    answeringWs.on('progress', (data) => {
      updateAnswer(data.question_id, data.answer);
      updateAnsweringProgress(data.current, data.total);
      setStatusMessage(`正在回答第 ${data.current}/${data.total} 题...`);
    });

    answeringWs.on('complete', () => {
      setStatus('completed');
      setStatusMessage('答题完成！');
    });

    answeringWs.on('error', (data) => {
      setStatus('error');
      setStatusMessage(data.message || '发生错误');
    });

    answeringWs.on('submit_result', (result) => {
      setSubmitResult(result);
    });

    return () => {
      answeringWs.disconnect();
      setAnswering(false);
    };
  }, []);

  const handleSubmit = () => {
    answeringWs.submitAnswers();
    setStatusMessage('正在提交答案...');
  };

  const progress = snap.answeringProgress.total > 0
    ? (snap.answeringProgress.current / snap.answeringProgress.total) * 100
    : 0;

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            答题进度
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {statusMessage}
          </Typography>
          
          {status === 'answering' && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress variant="determinate" value={progress} />
              <Typography variant="body2" align="center" sx={{ mt: 1 }}>
                {snap.answeringProgress.current} / {snap.answeringProgress.total}
              </Typography>
            </Box>
          )}

          {status === 'connecting' && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <CircularProgress />
            </Box>
          )}

          {status === 'completed' && !submitResult && (
            <Box sx={{ mt: 2 }}>
              {(() => {
                const failedCount = Object.values(snap.answers).filter(
                  (a: any) => a.status === '失败' || a.status === 'FAILED'
                ).length;
                const totalCount = Object.keys(snap.answers).length;

                return failedCount > 0 ? (
                  <>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      答题完成，但有 {failedCount}/{totalCount} 个答案验证失败！请检查并修正后再提交。
                    </Alert>
                    <Button variant="outlined" onClick={handleSubmit} color="warning">
                      仍然提交答案（不推荐）
                    </Button>
                  </>
                ) : (
                  <>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      所有题目已答完！
                    </Alert>
                    <Button variant="contained" onClick={handleSubmit}>
                      提交答案
                    </Button>
                  </>
                );
              })()}
            </Box>
          )}

          {submitResult && (
            <Alert severity={submitResult.success ? 'success' : 'error'} sx={{ mt: 2 }}>
              {submitResult.message}
            </Alert>
          )}

          {status === 'error' && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {statusMessage}
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            答案列表
          </Typography>
          <List>
            {Object.entries(snap.answers).map(([questionId, answer]: [string, any]) => {
              const question = snap.questions.find(q => q.id === questionId);
              return (
                <ListItem key={questionId} divider>
                  <ListItemText
                    primary={`${question?.order}. ${question?.content.substring(0, 50)}...`}
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2">
                          答案: {(() => {
                            // 如果答案格式是"索引|内容"，只显示内容部分
                            const answerStr = String(answer.content);
                            if (answerStr.includes('|')) {
                              const parts = answerStr.split('|');
                              return parts.length > 1 ? parts[1] : answerStr;
                            }
                            return answerStr;
                          })()}
                        </Typography>
                        <Box sx={{ mt: 0.5 }}>
                          <Chip
                            label={answer.status}
                            size="small"
                            color={
                              answer.status === '失败' || answer.status === 'FAILED'
                                ? 'error'
                                : answer.status === 'AI生成'
                                ? 'primary'
                                : 'default'
                            }
                            sx={{ mr: 1 }}
                          />
                          {answer.confidence !== undefined && (
                            <Chip
                              label={`置信度: ${(answer.confidence * 100).toFixed(0)}%`}
                              size="small"
                              color={answer.confidence >= 0.7 ? 'success' : 'warning'}
                            />
                          )}
                        </Box>

                        {/* 显示验证错误或失败原因 */}
                        {(answer.status === '失败' || answer.status === 'FAILED') && answer.reasoning && (
                          <Alert severity="error" sx={{ mt: 1 }}>
                            {answer.reasoning}
                          </Alert>
                        )}
                        
                        {/* 知识库引用信息 */}
                        {answer.knowledge_references && answer.knowledge_references.length > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Accordion>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <LibraryBooksIcon fontSize="small" color="primary" />
                                  <Typography variant="body2" color="primary">
                                    使用了 {answer.knowledge_references.length} 个知识库引用
                                  </Typography>
                                </Box>
                              </AccordionSummary>
                              <AccordionDetails>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                  {answer.knowledge_references.map((ref: any, idx: number) => (
                                    <Box key={idx}>
                                      {idx > 0 && <Divider sx={{ mb: 2 }} />}
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
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
                                        bgcolor: 'grey.50', 
                                        p: 1.5, 
                                        borderRadius: 1,
                                        border: '1px solid',
                                        borderColor: 'grey.200',
                                        fontSize: '0.875rem',
                                        lineHeight: 1.6,
                                      }}>
                                        {ref.content.length > 200 
                                          ? `${ref.content.substring(0, 200)}...` 
                                          : ref.content
                                        }
                                      </Typography>
                                    </Box>
                                  ))}
                                </Box>
                              </AccordionDetails>
                            </Accordion>
                          </Box>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              );
            })}
          </List>
        </CardContent>
      </Card>

      {(status === 'completed' || status === 'error') && (
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
          <Button variant="outlined" onClick={() => navigate('/')}>
            返回首页
          </Button>
        </Box>
      )}
    </Box>
  );
}

