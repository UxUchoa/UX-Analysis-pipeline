import { useMemo, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts';
import MetricCard from './MetricCard';
import { useLanguage } from '../i18n';
import { CheckCircle, XCircle, AlertCircle, Users, BarChart3, AlertTriangle, Pin, Search } from 'lucide-react';

const STATUS_COLORS = {
  'Com facilidade': '#2ed573',
  'Concluido': '#5b8def',
  'Com dificuldade': '#ff7f50',
  'Nao realizado': '#ff4757',
  'Comentario aberto': '#a78bfa',
  'Sem resposta': '#5a5a6e',
};

const STATUS_ORDER = ['Com facilidade', 'Concluido', 'Com dificuldade', 'Nao realizado', 'Comentario aberto', 'Sem resposta'];

export default function UsabilityPanel({ data }) {
  const { t } = useLanguage();
  const [selectedTask, setSelectedTask] = useState('');

  const records = data?.usability || [];
  const questions = data?.question_cols || [];
  const categorical = data?.usability_categorical || {};
  const profileEntries = Object.entries(categorical.profile || {}).filter(([, values]) => values.length > 0);
  const statusDistribution = categorical.status_distribution || [];
  const participantSummary = categorical.participant_summary || [];

  // Build aggregated data
  const { taskSummary, metrics, heatmapData, difficultyData, uniqueQuestions } = useMemo(() => {
    if (!records.length) return { taskSummary: [], metrics: {}, heatmapData: [], difficultyData: [], uniqueQuestions: [] };

    const total = records.length;
    const successStatuses = new Set(['Com facilidade', 'Concluido']);
    const successes = records.filter(r => successStatuses.has(r.status)).length;
    const difficulties = records.filter(r => r.status === 'Com dificuldade').length;
    const failures = records.filter(r => r.status === 'Nao realizado').length;
    const durations = records.map(r => r.time_min).filter(v => typeof v === 'number' && Number.isFinite(v));

    // Group by question_short for stacked bar chart
    const byQuestion = {};
    records.forEach(r => {
      const q = r.question_short;
      if (!byQuestion[q]) byQuestion[q] = { question: q };
      byQuestion[q][r.status] = (byQuestion[q][r.status] || 0) + 1;
    });

    // Unique questions preserving order
    const uqSet = new Set();
    const uq = [];
    records.forEach(r => {
      if (!uqSet.has(r.question_short)) {
        uqSet.add(r.question_short);
        uq.push(r.question_short);
      }
    });

    // Convert to percentages
    const taskSummaryData = uq.map(q => {
      const row = byQuestion[q];
      const rowTotal = STATUS_ORDER.reduce((s, st) => s + (row[st] || 0), 0);
      const pctRow = { question: q };
      STATUS_ORDER.forEach(st => {
        pctRow[st] = rowTotal > 0 ? Math.round((row[st] || 0) / rowTotal * 100) : 0;
      });
      return pctRow;
    });

    // Difficulty index
    const diffData = uq.map(q => {
      const row = byQuestion[q];
      const rowTotal = STATUS_ORDER.reduce((s, st) => s + (row[st] || 0), 0);
      const diffCount = (row['Com dificuldade'] || 0) + (row['Nao realizado'] || 0);
      return { question: q, difficulty: rowTotal > 0 ? Math.round(diffCount / rowTotal * 100) : 0 };
    }).sort((a, b) => b.difficulty - a.difficulty);

    return {
      taskSummary: taskSummaryData,
      metrics: {
        successRate: total > 0 ? Math.round(successes / total * 100) : 0,
        difficultyRate: total > 0 ? Math.round(difficulties / total * 100) : 0,
        failureRate: total > 0 ? Math.round(failures / total * 100) : 0,
        avgTime: durations.length ? (durations.reduce((sum, value) => sum + value, 0) / durations.length).toFixed(1) : 'N/A',
      },
      heatmapData: records,
      difficultyData: diffData,
      uniqueQuestions: uq,
    };
  }, [records]);

  if (!records.length) {
    return <div className="empty-state"><h3>{t.no_data}</h3></div>;
  }

  // Task detail
  const detailRecords = selectedTask
    ? records.filter(r => r.question_short === selectedTask)
    : [];

  return (
    <div className="animate-fade-in">
      {/* Metrics */}
      <div className="grid-4" style={{ marginBottom: 'var(--space-xl)' }}>
        <MetricCard icon={<CheckCircle size={18} />} value={`${metrics.successRate}%`} label={t.success_rate} className="stagger-1" />
        <MetricCard icon={<AlertCircle size={18} />} value={`${metrics.difficultyRate}%`} label={t.with_difficulty} className="stagger-2" />
        <MetricCard icon={<XCircle size={18} />} value={`${metrics.failureRate}%`} label={t.not_completed} className="stagger-3" />
        <MetricCard icon={<Users size={18} />} value={metrics.avgTime} label="Tempo médio (min)" className="stagger-4" />
      </div>

      {/* Stacked Bar Chart - Success Rate */}
      <div className="chart-container">
        <h3 className="chart-title"><BarChart3 size={18} /> {t.success_rate}</h3>
        <p className="chart-caption">% dos participantes por status em cada tarefa</p>
        <ResponsiveContainer width="100%" height={Math.max(300, taskSummary.length * 50)}>
          <BarChart data={taskSummary} layout="vertical" margin={{ left: 200 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis type="number" domain={[0, 100]} tick={{ fill: '#8b8b9e', fontSize: 12 }} />
            <YAxis type="category" dataKey="question" tick={{ fill: '#f0f0f5', fontSize: 11 }} width={190} />
            <Tooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }}
            />
            <Legend wrapperStyle={{ color: '#8b8b9e' }} />
            {STATUS_ORDER.map(st => (
              <Bar key={st} dataKey={st} stackId="a" fill={STATUS_COLORS[st]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Difficulty Index */}
      <div className="chart-container">
        <h3 className="chart-title"><AlertTriangle size={18} /> {t.difficulty_index}</h3>
        <ResponsiveContainer width="100%" height={Math.max(250, difficultyData.length * 40)}>
          <BarChart data={difficultyData} layout="vertical" margin={{ left: 200 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis type="number" domain={[0, 100]} tick={{ fill: '#8b8b9e', fontSize: 12 }} />
            <YAxis type="category" dataKey="question" tick={{ fill: '#f0f0f5', fontSize: 11 }} width={190} />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
            <Bar dataKey="difficulty" name="% Dificuldade/Falha" radius={[0, 4, 4, 0]}>
              {difficultyData.map((entry, i) => (
                <Cell key={i} fill={entry.difficulty > 50 ? '#ff4757' : entry.difficulty > 25 ? '#ff7f50' : '#2ed573'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Usability-specific categorical summaries */}
      {(profileEntries.length > 0 || statusDistribution.length > 0) && (
        <div className="chart-container">
          <h3 className="chart-title"><Pin size={18} /> Distribuições úteis para teste de usabilidade</h3>
          <p className="chart-caption">
            Recortes derivados dos metadados e da classificação das tarefas, sem tratar respostas abertas como categorias soltas.
          </p>
          <div className="grid-2">
            {statusDistribution.length > 0 && (
              <div>
                <h3>Status geral das tarefas</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={statusDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: '#8b8b9e', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#8b8b9e', fontSize: 12 }} />
                    <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {statusDistribution.map((entry, i) => (
                        <Cell key={i} fill={STATUS_COLORS[entry.name] || '#7c5cfc'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
            {profileEntries.map(([label, values]) => (
              <div key={label}>
                <h3>{label}</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={values}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: '#8b8b9e', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#8b8b9e', fontSize: 12 }} />
                    <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
                    <Bar dataKey="count" fill="#5b8def" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </div>
      )}

      {participantSummary.length > 0 && (
        <div className="chart-container">
          <h3 className="chart-title"><Users size={18} /> Participantes com mais fricção</h3>
          <p className="chart-caption">Ordenado por dificuldade e tarefas não realizadas.</p>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t.participants}</th>
                  <th>Sucesso</th>
                  <th>Dificuldade</th>
                  <th>Não realizado</th>
                  <th>Comentário aberto</th>
                </tr>
              </thead>
              <tbody>
                {participantSummary.slice(0, 12).map((row) => (
                  <tr key={row.participant}>
                    <td>{row.participant}</td>
                    <td>{row.success}</td>
                    <td>{row.difficulty}</td>
                    <td>{row.not_completed}</td>
                    <td>{row.open}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Task Detail */}
      <div className="chart-container">
        <h3 className="chart-title"><Search size={18} /> {t.task_detail}</h3>
        <select
          className="select"
          value={selectedTask}
          onChange={(e) => setSelectedTask(e.target.value)}
          style={{ marginBottom: 'var(--space-md)', maxWidth: 500 }}
        >
          <option value="">{t.select_task}</option>
          {uniqueQuestions.map(q => <option key={q} value={q}>{q}</option>)}
        </select>
        {detailRecords.length > 0 && (
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead><tr><th>{t.participants}</th><th>Status</th><th>Tempo</th><th>Observação</th></tr></thead>
              <tbody>
                {detailRecords.map((r, i) => (
                  <tr key={i}>
                    <td>{r.participant}</td>
                    <td><span style={{ color: STATUS_COLORS[r.status] || '#8b8b9e' }}>{r.status}</span></td>
                    <td>{typeof r.time_min === 'number' ? `${r.time_min.toFixed(1)} min` : 'N/A'}</td>
                    <td>{r.comment || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
