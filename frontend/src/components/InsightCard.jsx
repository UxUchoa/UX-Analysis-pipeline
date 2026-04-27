import { useLanguage } from '../i18n';

export default function InsightCard({ insight }) {
  const { t } = useLanguage();
  const sev = (insight.severity || 'medium').toLowerCase();

  return (
    <div className={`insight-card ${sev} animate-fade-in-up`}>
      <div className="insight-header">
        <span className="insight-category">{insight.category}</span>
        <span className={`severity-badge ${sev}`}>{insight.severity}</span>
      </div>
      <div className="insight-field">
        <strong>{t.finding}:</strong> {insight.finding}
      </div>
      <div className="insight-field">
        <strong>{t.evidence}:</strong> {insight.evidence}
      </div>
      {insight.recommendation && (
        <div className="insight-field">
          <strong>{t.recommendation}:</strong> {insight.recommendation}
        </div>
      )}
    </div>
  );
}
