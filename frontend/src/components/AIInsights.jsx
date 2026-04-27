import { AlertTriangle } from 'lucide-react';
import InsightCard from './InsightCard';
import { useLanguage } from '../i18n';

export default function AIInsights({ report }) {
  const { t } = useLanguage();

  if (!report) {
    return (
      <div className="empty-state">
        <div className="empty-icon"><AlertTriangle size={48} /></div>
        <h3>{t.run_analyze_prompt}</h3>
      </div>
    );
  }

  const scorePct = (report.overall_score / 10) * 100;

  return (
    <div className="animate-fade-in">
      {/* Score + Summary */}
      <div className="grid-2" style={{ marginBottom: 'var(--space-xl)', alignItems: 'start' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-md)' }}>
          <div className="score-ring" style={{ '--score-pct': scorePct }}>
            <span className="score-value">{report.overall_score}</span>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800 }}>{report.overall_score}/10</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>{t.overall_score}</div>
          </div>
        </div>
        <div className="card">
          <div className="card-header"><h2>{t.exec_summary}</h2></div>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: 'var(--font-size-md)' }}>
            {report.summary}
          </p>
        </div>
      </div>

      {/* Key Insights */}
      <h2 style={{ marginBottom: 'var(--space-md)', fontSize: 'var(--font-size-xl)' }}>{t.key_insights}</h2>
      {report.key_insights.map((insight, i) => (
        <InsightCard key={i} insight={insight} />
      ))}

      {/* Anomalies */}
      {report.anomalies && report.anomalies.length > 0 && (
        <>
          <h2 style={{ margin: 'var(--space-xl) 0 var(--space-md)', fontSize: 'var(--font-size-xl)' }}>{t.anomalies}</h2>
          {report.anomalies.map((a, i) => (
            <div key={i} className="alert alert-warning" style={{ marginBottom: 'var(--space-sm)' }}>
              <AlertTriangle size={16} />
              <span>{a}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
