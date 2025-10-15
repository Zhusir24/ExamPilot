import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSnapshot } from 'valtio';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  FormControl,
  RadioGroup,
  FormControlLabel,
  Radio,
  Checkbox,
  Chip,
  Divider,
  Alert,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  Slider,
  Switch,
} from '@mui/material';
import { appState, setAnsweringMode, toggleQuestionSelection, setAnswering, setPresetAnswers, setKnowledgeConfig, toggleKnowledgeEnabled, toggleDocumentSelection } from '@/store';
import { knowledgeApi } from '@/api';
import type { AnsweringMode, KnowledgeDocument } from '@/types';

export default function QuestionPreviewPage() {
  const snap = useSnapshot(appState);
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  // 加载知识库文档列表
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoadingDocs(true);
        const docs = await knowledgeApi.getDocuments();
        setDocuments(docs);
      } catch (error) {
        console.error('加载知识库文档失败:', error);
      } finally {
        setLoadingDocs(false);
      }
    };
    loadDocuments();
  }, []);

  if (!snap.questionnaire) {
    return (
      <Alert severity="warning">
        请先解析问卷
        <Button onClick={() => navigate('/')}>返回首页</Button>
      </Alert>
    );
  }

  // 判断是否应该显示知识库配置（全自动或用户勾选模式）
  const showKnowledgeConfig = snap.mode === 'FULL_AUTO' || snap.mode === 'USER_SELECT';

  // 处理预设答案变化
  const handlePresetAnswerChange = (index: number, value: string) => {
    const newAnswers = [...snap.presetAnswers];
    // 确保数组足够长
    while (newAnswers.length <= index) {
      newAnswers.push('');
    }
    newAnswers[index] = value;
    setPresetAnswers(newAnswers);
  };

  const handleStartAnswering = () => {
    setAnswering(true);
    navigate('/answering');
  };

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            {snap.questionnaire.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {snap.questionnaire.description}
          </Typography>
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip label={`平台: ${snap.questionnaire.platform}`} size="small" />
            <Chip label={`类型: ${snap.questionnaire.template_type}`} size="small" />
            <Chip label={`题目数: ${snap.questionnaire.total_questions}`} size="small" color="primary" />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            选择答题模式
          </Typography>
          <FormControl component="fieldset">
            <RadioGroup
              value={snap.mode}
              onChange={(e) => setAnsweringMode(e.target.value as AnsweringMode)}
            >
              <FormControlLabel
                value="FULL_AUTO"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">全自动AI答题</Typography>
                    <Typography variant="caption" color="text.secondary">AI自动回答所有题目</Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="USER_SELECT"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">用户勾选AI介入</Typography>
                    <Typography variant="caption" color="text.secondary">选择需要AI回答的题目</Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="PRESET_ANSWERS"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">预设答案自动填充</Typography>
                    <Typography variant="caption" color="text.secondary">按顺序使用预设答案</Typography>
                  </Box>
                }
              />
            </RadioGroup>
          </FormControl>
        </CardContent>
      </Card>

      {/* 知识库配置 - 在全自动AI答题或用户勾选AI介入模式时显示 */}
      {showKnowledgeConfig && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                知识库辅助答题
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={snap.knowledgeConfig.enabled}
                    onChange={toggleKnowledgeEnabled}
                    color="primary"
                  />
                }
                label={snap.knowledgeConfig.enabled ? '已启用' : '已禁用'}
              />
            </Box>

            {snap.knowledgeConfig.enabled && (
              <>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    启用知识库后，AI会在答题时参考选中文档中的相关内容，提高答案准确性。
                  </Typography>
                </Alert>

                {loadingDocs ? (
                  <Typography variant="body2" color="text.secondary">
                    加载知识库文档...
                  </Typography>
                ) : documents.length === 0 ? (
                  <Alert severity="warning">
                    知识库中还没有文档，请先在"知识库管理"页面添加文档。
                  </Alert>
                ) : (
                  <>
                    {/* 文档选择 */}
                    <Typography variant="subtitle2" gutterBottom>
                      选择文档（{snap.knowledgeConfig.document_ids.length} / {documents.length}）
                    </Typography>
                    <Box sx={{ mb: 3, display: 'flex', flexDirection: 'column', gap: 1, maxHeight: '200px', overflowY: 'auto', p: 1, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                      {documents.map((doc) => (
                        <FormControlLabel
                          key={doc.id}
                          control={
                            <Checkbox
                              checked={snap.knowledgeConfig.document_ids.includes(doc.id)}
                              onChange={() => toggleDocumentSelection(doc.id)}
                            />
                          }
                          label={
                            <Box>
                              <Typography variant="body2">{doc.title}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {doc.total_chunks} 个分块 · {new Date(doc.created_at).toLocaleDateString()}
                              </Typography>
                            </Box>
                          }
                        />
                      ))}
                    </Box>

                    {/* 使用前N个分块 */}
                    <Typography variant="subtitle2" gutterBottom>
                      使用前 {snap.knowledgeConfig.top_k} 个最相关的分块
                    </Typography>
                    <Box sx={{ mb: 3, px: 1 }}>
                      <Slider
                        value={snap.knowledgeConfig.top_k}
                        onChange={(_, value) => setKnowledgeConfig({ top_k: value as number })}
                        min={1}
                        max={10}
                        step={1}
                        marks
                        valueLabelDisplay="auto"
                      />
                      <Typography variant="caption" color="text.secondary">
                        建议：3-5个分块可以提供足够的上下文，又不会让AI接收过多信息
                      </Typography>
                    </Box>

                    {/* 相似度阈值 */}
                    <Typography variant="subtitle2" gutterBottom>
                      相似度阈值：{snap.knowledgeConfig.score_threshold.toFixed(2)}
                    </Typography>
                    <Box sx={{ px: 1 }}>
                      <Slider
                        value={snap.knowledgeConfig.score_threshold}
                        onChange={(_, value) => setKnowledgeConfig({ score_threshold: value as number })}
                        min={0.0}
                        max={1.0}
                        step={0.05}
                        marks={[
                          { value: 0.0, label: '0.0' },
                          { value: 0.3, label: '0.3' },
                          { value: 0.5, label: '0.5' },
                          { value: 0.7, label: '0.7' },
                          { value: 1.0, label: '1.0' },
                        ]}
                        valueLabelDisplay="auto"
                      />
                      <Typography variant="caption" color="text.secondary">
                        阈值越高，只使用高度相关的内容；阈值越低，允许更多候选内容
                      </Typography>
                    </Box>
                  </>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {snap.mode === 'USER_SELECT' && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              选择需要AI回答的题目
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              已选择 {snap.selectedQuestions.length} / {snap.questions.length} 题
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {snap.questions.map((q) => (
                <FormControlLabel
                  key={q.id}
                  control={
                    <Checkbox
                      checked={snap.selectedQuestions.includes(q.id)}
                      onChange={() => toggleQuestionSelection(q.id)}
                    />
                  }
                  label={`${q.order}. ${q.content.substring(0, 50)}${q.content.length > 50 ? '...' : ''}`}
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {snap.mode === 'PRESET_ANSWERS' && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              设置预设答案
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>填写说明：</strong>
              </Typography>
              <Typography variant="body2">
                • 单选题：输入选项索引（0, 1, 2...）或完整选项文本
              </Typography>
              <Typography variant="body2">
                • 多选题：输入多个索引，用逗号分隔（如 0,1,2）
              </Typography>
              <Typography variant="body2">
                • 填空题/简答题：直接输入文本内容
              </Typography>
            </Alert>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {snap.questions.map((q, index) => (
                <Box key={q.id}>
                  <Typography variant="subtitle2" gutterBottom>
                    {q.order}. {q.content}
                    <Chip label={q.type} size="small" sx={{ ml: 1 }} />
                  </Typography>
                  
                  {/* 显示选项（如果有） */}
                  {q.options && q.options.length > 0 && (
                    <Box sx={{ mb: 1, ml: 2, fontSize: '0.875rem', color: 'text.secondary' }}>
                      {q.options.map((opt, optIdx) => (
                        <Typography key={optIdx} variant="caption" display="block">
                          {optIdx}. {opt}
                        </Typography>
                      ))}
                    </Box>
                  )}
                  
                  {/* 单选题：下拉选择 */}
                  {q.type === '单选题' && q.options && q.options.length > 0 ? (
                    <FormControl fullWidth size="small">
                      <InputLabel>选择答案</InputLabel>
                      <Select
                        value={snap.presetAnswers[index] || ''}
                        onChange={(e) => handlePresetAnswerChange(index, e.target.value)}
                        label="选择答案"
                      >
                        <MenuItem value="">
                          <em>不填写</em>
                        </MenuItem>
                        {q.options.map((opt, optIdx) => (
                          <MenuItem key={optIdx} value={String(optIdx)}>
                            {optIdx}. {opt}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  ) : (
                    /* 其他题型：文本输入 */
                    <TextField
                      fullWidth
                      size="small"
                      placeholder={
                        q.type === '多选题' 
                          ? '输入选项索引，用逗号分隔（如 0,1,2）' 
                          : '输入答案内容'
                      }
                      value={snap.presetAnswers[index] || ''}
                      onChange={(e) => handlePresetAnswerChange(index, e.target.value)}
                      multiline={q.type === '简答题' || q.type === '填空题'}
                      rows={q.type === '简答题' ? 3 : 1}
                    />
                  )}
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            题目列表
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {snap.questions.map((q, index) => (
              <Box key={q.id}>
                {index > 0 && <Divider sx={{ my: 2 }} />}
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    {q.order}. {q.content}
                  </Typography>
                  <Chip label={q.type} size="small" color="primary" sx={{ mr: 1 }} />
                  {q.required && <Chip label="必答" size="small" color="error" />}
                  
                  {q.options && q.options.length > 0 && (
                    <Box sx={{ mt: 1, ml: 2 }}>
                      {q.options.map((opt, idx) => (
                        <Typography key={idx} variant="body2" color="text.secondary">
                          {idx}. {opt}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button variant="outlined" onClick={() => navigate('/')}>
          返回首页
        </Button>
        <Button variant="contained" size="large" onClick={handleStartAnswering}>
          开始答题
        </Button>
      </Box>
    </Box>
  );
}

