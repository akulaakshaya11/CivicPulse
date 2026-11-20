import React, { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ClipboardList,
  RefreshCw,
  ShieldAlert,
  TrendingUp
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import './AnalyticsPage.css';

const PRIORITIES = [
  { key: 'critical', label: 'Critical', color: '#df6c62' },
  { key: 'high', label: 'High', color: '#e5a542' },
  { key: 'medium', label: 'Medium', color: '#8974d8' },
  { key: 'low', label: 'Low', color: '#48a888' }
];

const numberFormat = value => Number(value || 0).toLocaleString('en-IN');

function formatDate(value, fallback) {
  if (!value) return fallback || '';
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime())
    ? fallback || value
    : parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function formatCategory(value) {
  return String(value || 'Unspecified').replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase());
}

function ChartTooltip({ active, payload, label, category = false }) {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload || {};

  return (
    <div className="ap-tooltip">
      <strong>{category ? formatCategory(label) : (item.date ? formatDate(item.date, label) : label)}</strong>
      {category ? (
        <span>{numberFormat(item.count)} reports <b>·</b> {Number(item.value || 0).toLocaleString('en-IN')}%</span>
      ) : (
        <span>{numberFormat(item.reports)} reports</span>
      )}
    </div>
  );
}

function SectionState({ loading, error, empty, emptyTitle, emptyDetail }) {
  if (loading) {
    return (
      <div className="ap-state" role="status">
        <span className="ap-loader" />
        <strong>Loading data</strong>
        <span>Connecting to the civic data service…</span>
      </div>
    );
  }
  if (error) {
    return (
      <div className="ap-state ap-state-error" role="alert">
        <AlertCircle size={21} />
        <strong>Data could not be loaded</strong>
        <span>{error}</span>
      </div>
    );
  }
  if (empty) {
    return (
      <div className="ap-state">
        <BarChart3 size={22} />
        <strong>{emptyTitle}</strong>
        <span>{emptyDetail}</span>
      </div>
    );
  }
  return null;
}

function MetricCard({ icon: Icon, label, value, detail, tone, loading, error }) {
  return (
    <article className={`ap-metric ap-metric-${tone}`}>
      <div className="ap-metric-top">
        <span className="ap-metric-icon"><Icon size={18} strokeWidth={1.9} /></span>
        <span className="ap-metric-label">{label}</span>
      </div>
      <strong className="ap-metric-value">{loading ? <span className="ap-value-skeleton" /> : error ? '—' : numberFormat(value)}</strong>
      <span className="ap-metric-detail">{error ? 'Unavailable until the service responds' : detail}</span>
    </article>
  );
}

function AnalyticsPage({ apiBaseUrl }) {
  const [trend, setTrend] = useState({ loading: true, error: '', data: [] });
  const [categories, setCategories] = useState({ loading: true, error: '', data: [], total: 0 });
  const [priority, setPriority] = useState({ loading: true, error: '', data: [], metrics: null });
  const controllerRef = useRef(null);

  async function loadEndpoint(path, signal) {
    const response = await fetch(`${apiBaseUrl}${path}`, { signal });
    if (!response.ok) throw new Error(`Request failed with status ${response.status}.`);
    return response.json();
  }

  function refresh() {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setTrend(current => ({ ...current, loading: true, error: '' }));
    setCategories(current => ({ ...current, loading: true, error: '' }));
    setPriority(current => ({ ...current, loading: true, error: '' }));

    const isCurrent = () => controllerRef.current === controller && !controller.signal.aborted;

    loadEndpoint('/analytics/report-trend', controller.signal)
      .then(result => {
        if (!isCurrent()) return;
        const data = Array.isArray(result?.data) ? result.data : [];
        setTrend({
          loading: false,
          error: '',
          data: data
            .map(item => ({
              ...item,
              reports: Number(item.reports),
              label: formatDate(item.date, item.day)
            }))
            .sort((left, right) => String(left.date || '').localeCompare(String(right.date || '')))
        });
      })
      .catch(error => {
        if (!isCurrent()) return;
        setTrend({ loading: false, error: error.message || 'The report trend is unavailable.', data: [] });
      });

    loadEndpoint('/analytics/category-distribution', controller.signal)
      .then(result => {
        if (!isCurrent()) return;
        setCategories({
          loading: false,
          error: '',
          total: Number(result?.total_reports || 0),
          data: Array.isArray(result?.data) ? result.data.map(item => ({
            ...item,
            name: formatCategory(item.name),
            value: Number(item.value),
            count: Number(item.count)
          })) : []
        });
      })
      .catch(error => {
        if (!isCurrent()) return;
        setCategories({ loading: false, error: error.message || 'Category data is unavailable.', data: [], total: 0 });
      });

    loadEndpoint('/issues/priority-list', controller.signal)
      .then(result => {
        if (!isCurrent()) return;
        const issues = Array.isArray(result?.issues) ? result.issues : [];
        const counts = PRIORITIES.map(level => ({
          ...level,
          count: issues.filter(issue => String(issue.priority_level || '').toLowerCase() === level.key).length
        }));
        setPriority({
          loading: false,
          error: '',
          data: counts,
          metrics: {
            total: Number(result?.total_issues ?? issues.length),
            unresolved: issues.filter(issue => ['open', 'in_progress'].includes(String(issue.status || '').toLowerCase())).length,
            resolved: issues.filter(issue => String(issue.status || '').toLowerCase() === 'resolved').length,
            urgent: issues.filter(issue => ['critical', 'high'].includes(String(issue.priority_level || '').toLowerCase())).length,
            priorityCount: issues.filter(issue => PRIORITIES.some(level => String(issue.priority_level || '').toLowerCase() === level.key)).length
          }
        });
      })
      .catch(error => {
        if (!isCurrent()) return;
        setPriority({ loading: false, error: error.message || 'Issue priority data is unavailable.', data: [], metrics: null });
      });
  }

  useEffect(() => {
    refresh();
    return () => controllerRef.current?.abort();
  }, []);

  const issueLoading = priority.loading;
  const issueError = priority.error;
  const metrics = priority.metrics;
  const categoryChartHeight = Math.max(250, categories.data.length * 38);
  const trendIsEmpty = !trend.data.length || trend.data.every(item => !Number.isFinite(item.reports));
  const categoryIsEmpty = !categories.data.length;
  const priorityIsEmpty = !priority.data.some(item => item.count > 0);

  return (
    <div className="analytics-page">
      <section className="ap-header">
        <div>
          <div className="ap-eyebrow"><span /> CIVIC OPERATIONS / INSIGHTS</div>
          <h1>Analytics</h1>
          <p>Understand report patterns and issue priority across the current civic register.</p>
        </div>
        <div className="ap-header-actions">
          <span className="ap-period"><TrendingUp size={15} /> Reports · last 7 calendar days</span>
          <button type="button" className="ap-refresh" onClick={refresh} disabled={trend.loading || categories.loading || priority.loading}>
            <RefreshCw size={15} className={trend.loading || categories.loading || priority.loading ? 'ap-spin' : ''} />
            {trend.loading || categories.loading || priority.loading ? 'Refreshing…' : 'Refresh analytics'}
          </button>
        </div>
      </section>

      <section className="ap-metrics" aria-label="Issue overview metrics">
        <MetricCard icon={ClipboardList} label="Total issues" value={metrics?.total} detail="In the current priority list" tone="blue" loading={issueLoading} error={issueError} />
        <MetricCard icon={AlertTriangle} label="Unresolved issues" value={metrics?.unresolved} detail="Open and in progress" tone="amber" loading={issueLoading} error={issueError} />
        <MetricCard icon={CheckCircle2} label="Resolved issues" value={metrics?.resolved} detail="Marked resolved in the register" tone="green" loading={issueLoading} error={issueError} />
        <MetricCard icon={ShieldAlert} label="Critical + high" value={metrics?.urgent} detail="Priority levels from the API" tone="coral" loading={issueLoading} error={issueError} />
      </section>

      {issueError && (
        <div className="ap-inline-error" role="alert"><AlertCircle size={16} /> Issue metrics and priority distribution are unavailable. {issueError}</div>
      )}

      <section className="ap-chart-grid" aria-label="Civic reports analytics">
        <article className="ap-panel ap-trend-panel">
          <div className="ap-panel-heading">
            <div><span className="ap-kicker">REPORTING ACTIVITY</span><h2>Reports over time</h2><p>Daily reports received during the last seven calendar days.</p></div>
            <span className="ap-heading-icon ap-blue-icon"><TrendingUp size={18} /></span>
          </div>
          <div className="ap-chart-area ap-trend-chart">
            {trend.loading || trend.error || trendIsEmpty ? (
              <SectionState loading={trend.loading} error={trend.error} empty={trendIsEmpty} emptyTitle="No trend data available" emptyDetail="No daily report counts were returned for this period." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend.data} margin={{ top: 10, right: 12, left: -18, bottom: 0 }}>
                  <defs><linearGradient id="analyticsTrendFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4776e6" stopOpacity={0.19} /><stop offset="95%" stopColor="#4776e6" stopOpacity={0.015} /></linearGradient></defs>
                  <CartesianGrid stroke="#edf1f7" vertical={false} />
                  <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#8490a4' }} dy={9} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#8490a4' }} width={34} />
                  <Tooltip content={<ChartTooltip />} cursor={{ stroke: '#cbd6ed', strokeDasharray: '4 4' }} />
                  <Area type="monotone" dataKey="reports" name="Reports" stroke="#4776e6" strokeWidth={2.5} fill="url(#analyticsTrendFill)" activeDot={{ r: 5, strokeWidth: 0 }} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="ap-chart-foot"><span><i className="ap-legend-dot ap-legend-blue" /> Daily reports</span><span>{trend.data.length ? `${trend.data.length} days returned` : 'Source: report trend API'}</span></div>
        </article>

        <article className="ap-panel ap-category-panel">
          <div className="ap-panel-heading">
            <div><span className="ap-kicker">REPORTED CATEGORY</span><h2>Complaint distribution</h2><p>Reports and share by resident-reported category.</p></div>
            <span className="ap-heading-icon ap-violet-icon"><BarChart3 size={18} /></span>
          </div>
          <div className="ap-category-summary"><strong>{categories.loading ? '—' : categories.error ? '—' : numberFormat(categories.total)}</strong><span>total reports</span></div>
          <div className="ap-chart-area ap-category-chart" style={{ height: categoryChartHeight }}>
            {categories.loading || categories.error || categoryIsEmpty ? (
              <SectionState loading={categories.loading} error={categories.error} empty={categoryIsEmpty} emptyTitle="No category data available" emptyDetail="No report categories were returned by the service." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categories.data} layout="vertical" margin={{ top: 2, right: 18, left: 3, bottom: 0 }} barCategoryGap={10}>
                  <CartesianGrid stroke="#edf1f7" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} unit="%" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#8490a4' }} />
                  <YAxis type="category" dataKey="name" width={112} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#59667d' }} />
                  <Tooltip content={<ChartTooltip category />} cursor={{ fill: '#f5f7fb' }} />
                  <Bar dataKey="value" name="Share" radius={[0, 5, 5, 0]} maxBarSize={17}>
                    {categories.data.map((item, index) => <Cell key={`${item.name}-${index}`} fill={['#4776e6', '#18a88a', '#e5a542', '#8974d8', '#df6c87', '#6384a8'][index % 6]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="ap-chart-foot"><span><i className="ap-legend-dot ap-legend-violet" /> Share of reports</span><span>Counts and percentages from API</span></div>
        </article>
      </section>

      <section className="ap-panel ap-priority-panel">
        <div className="ap-panel-heading">
          <div><span className="ap-kicker">CURRENT ISSUE REGISTER</span><h2>Priority distribution</h2><p>Issues grouped by the priority level assigned by the backend.</p></div>
          <span className="ap-priority-total">{issueLoading || issueError ? '—' : numberFormat(metrics?.priorityCount)} <small>classified issues</small></span>
        </div>
        <div className="ap-priority-content">
          <div className="ap-priority-chart">
            {priority.loading || priority.error || priorityIsEmpty ? (
              <SectionState loading={priority.loading} error={priority.error} empty={priorityIsEmpty} emptyTitle="No priority values available" emptyDetail="The issue list contains no recognized priority levels to visualize." />
            ) : (
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={priority.data} margin={{ top: 8, right: 22, left: -17, bottom: 0 }} barCategoryGap={20}>
                  <CartesianGrid stroke="#edf1f7" vertical={false} />
                  <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#69758a' }} dy={9} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#8490a4' }} width={36} />
                  <Tooltip formatter={(value, _name, item) => [numberFormat(value), `${item.payload.label} issues`]} cursor={{ fill: '#f7f8fb' }} />
                  <Bar dataKey="count" name="Issues" radius={[5, 5, 0, 0]} maxBarSize={46}>
                    {priority.data.map(item => <Cell key={item.key} fill={item.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="ap-priority-legend" aria-label="Priority counts">
            {priority.data.map(item => (
              <div className="ap-priority-row" key={item.key}>
                <span className="ap-priority-name"><i style={{ backgroundColor: item.color }} />{item.label}</span>
                <strong>{issueLoading || issueError ? '—' : numberFormat(item.count)}</strong>
              </div>
            ))}
            {!priority.loading && !priority.error && !priorityIsEmpty && (
              <p className="ap-priority-note">Priority levels are shown as returned; no score thresholds are applied in this view.</p>
            )}
          </div>
        </div>
      </section>

      <footer className="ap-footer"><span><span className="ap-footer-mark"><BarChart3 size={13} /></span><b>CivicPulse</b><i>·</i>Operational analytics</span><span><span className="ap-footer-dot" /> Each data section loads independently</span></footer>
    </div>
  );
}

export default AnalyticsPage;
