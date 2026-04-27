export default function MetricCard({ icon, value, label, className = '' }) {
  return (
    <div className={`metric-card animate-fade-in-up ${className}`}>
      {icon && <div className="metric-icon">{icon}</div>}
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
    </div>
  );
}
