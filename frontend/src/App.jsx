import { useState, useEffect, useCallback } from 'react';
import {
  Microscope,
  Wifi,
  WifiOff,
  Sparkles,
  Search,
  FlaskConical,
  MessagesSquare,
  BarChart3,
  Languages,
} from 'lucide-react';
import { LanguageProvider, useLanguage } from './i18n';
import { uploadFile, analyzeData, getVisualizationData, healthCheck } from './api';
import FileUpload from './components/FileUpload';
import DataOverview from './components/DataOverview';
import AIInsights from './components/AIInsights';
import UsabilityPanel from './components/UsabilityPanel';
import ContextPanel from './components/ContextPanel';
import QuantitativePanel from './components/QuantitativePanel';
import ExportPanel from './components/ExportPanel';

function AppContent() {
  const { lang, setLang, t } = useLanguage();

  // State
  const [ollamaOk, setOllamaOk] = useState(false);
  const [uploadData, setUploadData] = useState(null);
  const [report, setReport] = useState(null);
  const [visData, setVisData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [context, setContext] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [visType, setVisType] = useState('auto');

  // Health check on mount and after backend/Ollama restarts
  useEffect(() => {
    let cancelled = false;
    const checkOllama = () => {
      healthCheck()
        .then(r => {
          if (!cancelled) setOllamaOk(Boolean(r.ollama_connected && (r.model_available ?? true)));
        })
        .catch(() => {
          if (!cancelled) setOllamaOk(false);
        });
    };

    checkOllama();
    const interval = window.setInterval(checkOllama, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  // Handle file upload
  const handleFileUpload = useCallback(async (file) => {
    setUploading(true);
    setError(null);
    try {
      const data = await uploadFile(file);
      setUploadData(data);
      setReport(null);
      setVisData(null);
      // Fetch visualization data
      const vis = await getVisualizationData();
      setVisData(vis);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }, []);

  // Handle analysis
  const handleAnalyze = useCallback(async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const result = await analyzeData(context);
      setReport(result);
      setActiveTab('insights');
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  }, [context]);

  // Handle vis type change
  const handleVisTypeChange = useCallback(async (type) => {
    setVisType(type);
    if (uploadData) {
      try {
        const dsType = type === 'auto' ? null : type;
        const vis = await getVisualizationData(dsType);
        setVisData(vis);
      } catch (err) {
        setError(err.message);
      }
    }
  }, [uploadData]);

  const tabs = [
    { id: 'overview', label: t.tab_overview },
    { id: 'insights', label: t.tab_insights },
    { id: 'visualizations', label: t.tab_visualizations },
    { id: 'export', label: t.tab_export },
  ];

  const dsType = visData?.dataset_type || 'generic';
  const visualizationOptions = [
    { id: 'auto', label: `${t.vis_auto} (${dsType})`, icon: Search },
    { id: 'usability', label: t.vis_usability, icon: FlaskConical },
    { id: 'context', label: t.vis_context, icon: MessagesSquare },
    { id: 'generic', label: t.vis_generic, icon: BarChart3 },
  ];

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon"><Microscope size={18} color="white" /></div>
          UX Analyzer
        </div>

        {/* Language */}
        <div className="sidebar-section">
          <div className="lang-toggle">
            <button className={lang === 'PT' ? 'active' : ''} onClick={() => setLang('PT')}><Languages size={14} /> PT</button>
            <button className={lang === 'EN' ? 'active' : ''} onClick={() => setLang('EN')}><Languages size={14} /> EN</button>
          </div>
        </div>

        {/* Ollama Status */}
        <div className="sidebar-section">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', fontSize: 'var(--font-size-xs)', color: ollamaOk ? 'var(--severity-low)' : 'var(--severity-critical)' }}>
            {ollamaOk ? <Wifi size={14} /> : <WifiOff size={14} />}
            {ollamaOk ? t.ollama_connected : t.ollama_disconnected}
          </div>
        </div>

        {/* Upload */}
        <div className="sidebar-section">
          <h3>{t.upload_header}</h3>
          <FileUpload
            onFileSelected={handleFileUpload}
            isLoaded={!!uploadData}
            filename={uploadData?.filename}
          />
          {uploading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
              <div className="spinner" />
              {t.upload_help}
            </div>
          )}
        </div>

        {/* Analysis */}
        {uploadData && (
          <div className="sidebar-section">
            <h3>{t.analysis_header}</h3>
            <div className="input-group">
              <label>{t.context_label}</label>
              <textarea
                className="textarea"
                placeholder={t.context_placeholder}
                value={context}
                onChange={(e) => setContext(e.target.value)}
              />
            </div>
            <button
              className="btn btn-primary btn-full"
              onClick={handleAnalyze}
              disabled={analyzing || !ollamaOk}
            >
              {analyzing ? <><div className="spinner" />{t.analyzing_spinner}</> : <><Sparkles size={16} />{t.analyze_btn}</>}
            </button>
          </div>
        )}

        {/* Visualization Type */}
        {uploadData && (
          <div className="sidebar-section">
            <h3>{t.vis_type_label}</h3>
            <div className="vis-type-list" role="radiogroup" aria-label={t.vis_type_label}>
              {visualizationOptions.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  role="radio"
                  aria-checked={visType === id}
                  className={`vis-type-option ${visType === id ? 'active' : ''}`}
                  onClick={() => handleVisTypeChange(id)}
                >
                  <Icon size={16} />
                  <span>{label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <div className="page-header">
          <h1>{t.page_title}</h1>
          <p>{t.description}</p>
        </div>

        {error && (
          <div className="alert alert-warning" style={{ marginBottom: 'var(--space-lg)' }}>
            <span>{error}</span>
          </div>
        )}

        {!uploadData ? (
          <div className="empty-state" style={{ marginTop: '15vh' }}>
            <Microscope size={64} className="empty-icon" />
            <h3>{t.upload_prompt}</h3>
          </div>
        ) : (
          <>
            {/* Tabs */}
            <div className="tabs">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && <DataOverview uploadData={uploadData} />}
            {activeTab === 'insights' && <AIInsights report={report} />}
            {activeTab === 'visualizations' && visData && (
              <>
                {dsType === 'usability' && <UsabilityPanel data={visData} />}
                {dsType === 'context' && <ContextPanel data={visData} />}
                {dsType === 'generic' && <QuantitativePanel data={visData} />}
              </>
            )}
            {activeTab === 'export' && <ExportPanel hasReport={!!report} />}
          </>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}
