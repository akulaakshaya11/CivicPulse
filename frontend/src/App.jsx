import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, CheckCircle2,
  ChevronDown, ChevronRight, Clock3, Download, ExternalLink, Filter, Gauge,
  LayoutDashboard, LifeBuoy, MapPin, Menu, MoreHorizontal, Search, Settings2,
  ShieldAlert, SlidersHorizontal, Sparkles, TrendingDown, TrendingUp, Waves,
  X, RefreshCw, CircleDot, CalendarDays, ClipboardList, Zap, Plus, BarChart3
} from 'lucide-react';
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
  BarChart, Bar, Cell
} from 'recharts';
import AnalyticsPage from './AnalyticsPage.jsx';

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const demoIssues = [
  { issue_id: 3, issue_type: 'Pothole', description: 'Deep pothole near school entrance', status: 'open', age_days: 12, total_complaints: 4, priority_score: 86, priority_level: 'critical', decline_detected: true, unresolved_review_flag: true, safety_risk: 5, physical_severity: 4, locality: 'Lakeview Road', updated: '12 min ago' },
  { issue_id: 8, issue_type: 'Streetlight', description: 'Streetlights not working along pedestrian stretch', status: 'open', age_days: 9, total_complaints: 8, priority_score: 79, priority_level: 'high', decline_detected: false, unresolved_review_flag: false, safety_risk: 4, physical_severity: 3, locality: 'Green Park Colony', updated: '28 min ago' },
  { issue_id: 1, issue_type: 'Road damage', description: 'Broken road surface affecting daily commute', status: 'in_progress', age_days: 16, total_complaints: 6, priority_score: 72, priority_level: 'high', decline_detected: false, unresolved_review_flag: false, safety_risk: 4, physical_severity: 4, locality: 'Market Junction', updated: '1 hr ago' },
  { issue_id: 5, issue_type: 'Drainage', description: 'Water stagnation after recent rainfall', status: 'open', age_days: 5, total_complaints: 3, priority_score: 63, priority_level: 'high', decline_detected: false, unresolved_review_flag: false, safety_risk: 3, physical_severity: 3, locality: 'Sai Nagar, Lane 4', updated: '2 hrs ago' },
  { issue_id: 2, issue_type: 'Waste collection', description: 'Overflowing community waste point', status: 'open', age_days: 3, total_complaints: 11, priority_score: 51, priority_level: 'medium', decline_detected: false, unresolved_review_flag: false, safety_risk: 2, physical_severity: 2, locality: 'Old Bus Depot', updated: '3 hrs ago' },
  { issue_id: 7, issue_type: 'Water supply', description: 'Intermittent water supply reported by residents', status: 'resolved', age_days: 7, total_complaints: 5, priority_score: 28, priority_level: 'low', decline_detected: false, unresolved_review_flag: false, safety_risk: 2, physical_severity: 2, locality: 'Sunrise Enclave', updated: 'Yesterday' }
];
const fmt = n => Number(n || 0).toLocaleString('en-IN');
const cap = s => String(s || 'unknown').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
function scoreOf(i) { return Number(i.priority_score ?? i.score ?? 0); }
function levelOf(i) {
  const n = scoreOf(i);
  return String(i.priority_level || (n >= 75 ? 'critical' : n >= 50 ? 'high' : n >= 25 ? 'medium' : 'low')).toLowerCase();
}
function App() {
  const [issues, setIssues] = useState(demoIssues);
  const [source, setSource] = useState('demo');
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeView, setActiveView] = useState('overview');
  const [toast, setToast] = useState('');
  const [trend, setTrend] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [populationExposure, setPopulationExposure] = useState(null);
  const [reportTrend, setReportTrend] = useState([]);
  const [categoryDistribution, setCategoryDistribution] = useState([]);
  const [totalReports, setTotalReports] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [showAddIssue, setShowAddIssue] = useState(false);
  const [submittingIssue, setSubmittingIssue] = useState(false);
  const [issueFormError, setIssueFormError] = useState('');
  const [statusUpdates, setStatusUpdates] = useState({});
  const [newIssue, setNewIssue] = useState({
    issue_type: '',
    description: '',
    latitude: '',
    longitude: '',
    physical_severity: '',
    safety_risk: ''
  });
  const [showEditIssue, setShowEditIssue] = useState(false);
  const [editingIssueId, setEditingIssueId] = useState(null);
  const [editIssue, setEditIssue] = useState({
    issue_type: '',
    description: '',
    latitude: '',
    longitude: '',
    physical_severity: '',
    safety_risk: ''
  });
  const [loadingEditCoordinates, setLoadingEditCoordinates] = useState(false);
  const [submittingEditIssue, setSubmittingEditIssue] = useState(false);
  const [editIssueError, setEditIssueError] = useState('');

  async function refresh() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/issues/priority-list`);
      if (!r.ok) throw new Error('API unavailable');
      const data = await r.json();
      const rows = (data.issues || []).map(i => ({
        ...i,
        original_issue_type: i.issue_type,
        issue_type: cap(i.issue_type),
        locality: i.locality || i.location_name || `Civic area ${i.issue_id}`,
        updated: 'Live from API',
        safety_risk: i.safety_risk ?? 3,
        physical_severity: i.physical_severity ?? 3
      }));
      setIssues(rows);
      setSource('live');
      setLastUpdated(new Date());

      // Load dashboard charts from PostgreSQL analytics endpoints.
      const [trendResponse, categoryResponse] = await Promise.all([
        fetch(`${API}/analytics/report-trend`),
        fetch(`${API}/analytics/category-distribution`)
      ]);

      if (trendResponse.ok) {
        const trendJson = await trendResponse.json();
        setReportTrend(Array.isArray(trendJson.data) ? trendJson.data : []);
      } else {
        setReportTrend([]);
      }

      if (categoryResponse.ok) {
        const categoryJson = await categoryResponse.json();
        setCategoryDistribution(
          (Array.isArray(categoryJson.data) ? categoryJson.data : []).map((item, index) => ({
            ...item,
            color: ['#4776e6', '#12a88a', '#f4a340', '#8c70df', '#e46f91', '#64748b'][index % 6]
          }))
        );
        setTotalReports(Number(categoryJson.total_reports || 0));
      } else {
        setCategoryDistribution([]);
        setTotalReports(0);
      }

      setToast('Live civic data synced');
      return true;
    } catch {
      setIssues(demoIssues);
      setSource('demo');
      setReportTrend([]);
      setCategoryDistribution([]);
      setTotalReports(0);
      setLastUpdated(new Date());
      setToast('Showing sample issue data — backend not connected');
      return false;
    } finally {
      setLoading(false);
      setTimeout(() => setToast(''), 3500);
    }
  }

  async function updateIssueStatus(issue, status) {
    if (status === issue.status || statusUpdates[issue.issue_id]) return;

    setStatusUpdates(current => ({
      ...current,
      [issue.issue_id]: status
    }));

    try {
      const response = await fetch(
        `${API}/issues/${issue.issue_id}/status`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status })
        }
      );
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        const detail = responseBody?.detail;
        throw new Error(
          typeof detail === 'string'
            ? detail
            : detail
              ? JSON.stringify(detail)
              : 'Could not update the issue status.'
        );
      }

      const refreshed = await refresh();
      setToast(
        refreshed
          ? 'Issue status updated and priority list refreshed'
          : 'Issue status updated, but the priority list could not be refreshed'
      );
    } catch (error) {
      setToast(error.message || 'Could not update the issue status. Please try again.');
      setTimeout(() => setToast(''), 3500);
    } finally {
      setStatusUpdates(current => {
        const next = { ...current };
        delete next[issue.issue_id];
        return next;
      });
    }
  }

  async function submitNewIssue(event) {
    event.preventDefault();
    setIssueFormError('');

    const issueType = newIssue.issue_type.trim();
    const description = newIssue.description.trim();
    const latitude = Number(newIssue.latitude);
    const longitude = Number(newIssue.longitude);
    const physicalSeverity = Number(newIssue.physical_severity);
    const safetyRisk = Number(newIssue.safety_risk);

    if (!issueType || !description || !newIssue.latitude || !newIssue.longitude ||
        !newIssue.physical_severity || !newIssue.safety_risk) {
      setIssueFormError('Complete all fields before submitting.');
      return;
    }
    if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
      setIssueFormError('Latitude must be between -90 and 90.');
      return;
    }
    if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
      setIssueFormError('Longitude must be between -180 and 180.');
      return;
    }
    if (!Number.isInteger(physicalSeverity) || physicalSeverity < 1 || physicalSeverity > 5) {
      setIssueFormError('Physical severity must be a whole number from 1 to 5.');
      return;
    }
    if (!Number.isInteger(safetyRisk) || safetyRisk < 1 || safetyRisk > 5) {
      setIssueFormError('Safety risk must be a whole number from 1 to 5.');
      return;
    }

    setSubmittingIssue(true);
    try {
      const response = await fetch(`${API}/issues`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          issue_type: issueType,
          description,
          latitude,
          longitude,
          physical_severity: physicalSeverity,
          safety_risk: safetyRisk
        })
      });
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        const detail = responseBody?.detail;
        throw new Error(typeof detail === 'string' ? detail : 'Could not create the issue.');
      }

      setShowAddIssue(false);
      setNewIssue({
        issue_type: '',
        description: '',
        latitude: '',
        longitude: '',
        physical_severity: '',
        safety_risk: ''
      });

      const refreshed = await refresh();
      setToast(
        refreshed
          ? 'Issue created and priority list refreshed'
          : 'Issue created, but the priority list could not be refreshed'
      );
    } catch (error) {
      setIssueFormError(error.message || 'Could not create the issue. Please try again.');
    } finally {
      setSubmittingIssue(false);
    }
  }

  async function openEditIssue(issue) {
    setEditingIssueId(issue.issue_id);
    setEditIssue({
      issue_type: issue.original_issue_type ?? issue.issue_type ?? '',
      description: issue.description || '',
      latitude: issue.latitude ?? '',
      longitude: issue.longitude ?? '',
      physical_severity: issue.physical_severity ?? '',
      safety_risk: issue.safety_risk ?? ''
    });
    setEditIssueError('');
    setShowEditIssue(true);

    // The priority-list response currently omits coordinates; this existing
    // endpoint returns them alongside its population exposure data.
    if (issue.latitude == null || issue.longitude == null) {
      setLoadingEditCoordinates(true);
      try {
        const response = await fetch(
          `${API}/issues/${issue.issue_id}/population-exposure`
        );
        const responseBody = await response.json().catch(() => null);
        if (!response.ok) {
          const detail = responseBody?.detail;
          throw new Error(
            typeof detail === 'string'
              ? detail
              : 'Could not load the saved issue coordinates.'
          );
        }

        const latitude = responseBody?.location?.latitude;
        const longitude = responseBody?.location?.longitude;
        setEditIssue(current => ({
          ...current,
          latitude: current.latitude === '' && latitude != null
            ? String(latitude)
            : current.latitude,
          longitude: current.longitude === '' && longitude != null
            ? String(longitude)
            : current.longitude
        }));
      } catch (error) {
        setEditIssueError(
          error.message || 'Could not load the saved issue coordinates.'
        );
      } finally {
        setLoadingEditCoordinates(false);
      }
    }
  }

  function resetEditIssue() {
    setEditingIssueId(null);
    setEditIssue({
      issue_type: '',
      description: '',
      latitude: '',
      longitude: '',
      physical_severity: '',
      safety_risk: ''
    });
    setEditIssueError('');
  }

  async function submitEditIssue(event) {
    event.preventDefault();
    setEditIssueError('');

    const issueType = editIssue.issue_type.trim();
    const description = editIssue.description.trim();
    const latitude = Number(editIssue.latitude);
    const longitude = Number(editIssue.longitude);
    const physicalSeverity = Number(editIssue.physical_severity);
    const safetyRisk = Number(editIssue.safety_risk);

    if (!issueType || !description || editIssue.latitude === '' ||
        editIssue.longitude === '' || editIssue.physical_severity === '' ||
        editIssue.safety_risk === '') {
      setEditIssueError('Complete all fields before submitting.');
      return;
    }
    if (description.length < 5) {
      setEditIssueError('Description must contain at least 5 characters.');
      return;
    }
    if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
      setEditIssueError('Latitude must be between -90 and 90.');
      return;
    }
    if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
      setEditIssueError('Longitude must be between -180 and 180.');
      return;
    }
    if (!Number.isInteger(physicalSeverity) || physicalSeverity < 1 || physicalSeverity > 5) {
      setEditIssueError('Physical severity must be a whole number from 1 to 5.');
      return;
    }
    if (!Number.isInteger(safetyRisk) || safetyRisk < 1 || safetyRisk > 5) {
      setEditIssueError('Safety risk must be a whole number from 1 to 5.');
      return;
    }

    setSubmittingEditIssue(true);
    try {
      const response = await fetch(`${API}/issues/${editingIssueId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          issue_type: issueType,
          description,
          latitude,
          longitude,
          physical_severity: physicalSeverity,
          safety_risk: safetyRisk
        })
      });
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        const detail = responseBody?.detail;
        throw new Error(
          typeof detail === 'string' ? detail : 'Could not update the issue.'
        );
      }

      setShowEditIssue(false);
      resetEditIssue();
      const refreshed = await refresh();
      setToast(
        refreshed
          ? 'Issue updated and priority list refreshed'
          : 'Issue updated, but the priority list could not be refreshed'
      );
    } catch (error) {
      setEditIssueError(error.message || 'Could not update the issue. Please try again.');
    } finally {
      setSubmittingEditIssue(false);
    }
  }

  useEffect(() => { refresh(); }, []);
  useEffect(() => {
    if (!selected || source !== 'live') {
      setTrend(null);
      setAnalytics(null);
      setPopulationExposure(null);
      return;
    }

  Promise.all([
    fetch(`${API}/issues/${selected.issue_id}/trend`)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null),

    fetch(`${API}/issues/${selected.issue_id}/analytics`)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null),

    fetch(`${API}/issues/${selected.issue_id}/population-exposure`)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null)
  ]).then(([t, a, p]) => {
    setTrend(t);
    setAnalytics(a);
    setPopulationExposure(p);
  });
}, [selected, source]);

  const filtered = useMemo(() => issues.filter(i => {
    const q = search.toLowerCase();
    const matches = [i.description, i.issue_type, i.original_issue_type, i.locality, i.issue_id].some(v => String(v ?? '').toLowerCase().includes(q));
    const matchesPriority = filter === 'all' || levelOf(i) === filter || (filter === 'review' && i.unresolved_review_flag);
    const matchesStatus = statusFilter === 'all' || String(i.status).toLowerCase() === statusFilter;
    return matches && matchesPriority && matchesStatus;
  }).sort((a,b) => scoreOf(b)-scoreOf(a)), [issues, search, filter, statusFilter]);
  const critical = issues.filter(i => levelOf(i) === 'critical').length;
  const openCount = issues.filter(i => !['resolved','closed'].includes(String(i.status).toLowerCase())).length;
  const reviewCount = issues.filter(i => i.unresolved_review_flag).length;
  const avgScore = issues.length ? Math.round(issues.reduce((s,i)=>s+scoreOf(i),0)/issues.length) : 0;
  function navigateToIssueList(nextFilter) {
    setFilter(nextFilter);
    setActiveView('overview');
    setSidebarOpen(false);
    requestAnimationFrame(() => requestAnimationFrame(() => {
      document.getElementById('issues-table')?.scrollIntoView({ behavior: 'smooth' });
    }));
  }
  function exportCsv() {
    const cols = ['rank','issue_id','issue_type','description','status','total_complaints','age_days','priority_score','priority_level','unresolved_review_flag'];
    const rows = filtered.map((i,n)=>[n+1,i.issue_id,i.issue_type,i.description,i.status,i.total_complaints,i.age_days,scoreOf(i),levelOf(i),!!i.unresolved_review_flag]);
    const csv = [cols,...rows].map(row=>row.map(v=>`"${String(v ?? '').replaceAll('"','""')}"`).join(',')).join('\n');
    const url = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8;'}));
    const a = document.createElement('a'); a.href=url; a.download='civicpulse-priority-list.csv'; a.click(); URL.revokeObjectURL(url);
    setToast('Priority list exported'); setTimeout(()=>setToast(''),2500);
  }
  return <div className="app-shell">
    <aside className={`sidebar ${sidebarOpen?'sidebar-open':''}`}>
      <div className="brand"><div className="brand-mark"><Waves size={22}/></div><div><b>CivicPulse</b><span>IMPACT INTELLIGENCE</span></div><button className="mobile-close icon-btn" onClick={()=>setSidebarOpen(false)}><X size={18}/></button></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="nav-list">
        <button className={`nav-item ${activeView === 'overview' ? 'active' : ''}`} onClick={()=>{setActiveView('overview');setSidebarOpen(false)}}><LayoutDashboard size={18}/><span>Overview</span>{activeView === 'overview'&&<span className="nav-active-dot"/>}</button>
        <button className="nav-item" onClick={()=>navigateToIssueList('all')}><ClipboardList size={18}/><span>Issue registry</span><span className="nav-count">{issues.length}</span></button>
        <button className="nav-item" onClick={()=>navigateToIssueList('review')}><ShieldAlert size={18}/><span>Signal watch</span>{reviewCount>0&&<span className="nav-count alert-count">{reviewCount}</span>}</button>
        <button className={`nav-item ${activeView === 'analytics' ? 'active' : ''}`} onClick={()=>{setActiveView('analytics');setSidebarOpen(false)}}><BarChart3 size={18}/><span>Analytics</span>{activeView === 'analytics'&&<span className="nav-active-dot"/>}</button>
      </nav>
      <div className="workspace-label section-label">MANAGE</div>
      <nav className="nav-list">
        <button className="nav-item" onClick={exportCsv}><Download size={18}/><span>Export reports</span></button>
        <button className="nav-item" onClick={()=>setToast('Settings are coming soon')}><Settings2 size={18}/><span>Settings</span></button>
        <button className="nav-item" onClick={()=>setToast('Connect the FastAPI backend to enable live support')}><LifeBuoy size={18}/><span>Help & support</span></button>
      </nav>
      <div className="sidebar-spacer"/>
      <div className="sidebar-note"><div className="note-icon"><Sparkles size={17}/></div><div><b>Impact over volume</b><p>Prioritize what puts people at risk, not just what gets reported most.</p></div></div>
      <div className="profile"><div className="avatar">CP</div><div className="profile-copy"><b>City Operations</b><span>Administrator workspace</span></div><MoreHorizontal size={19} className="muted"/></div>
    </aside>
    {sidebarOpen&&<button className="scrim" aria-label="Close menu" onClick={()=>setSidebarOpen(false)}/>}
    <main className="main-content">
      <header className="topbar">
        <div className="top-left"><button className="mobile-menu icon-btn" onClick={()=>setSidebarOpen(true)}><Menu size={20}/></button><div className="breadcrumbs">Workspace <ChevronRight size={14}/> <b>{activeView === 'analytics' ? 'Analytics' : 'Overview'}</b></div></div>
        <div className="top-actions"><div className={`connection-pill ${source==='live'?'live':'demo'}`}><span className="status-dot"/>{source==='live'?'Live data connected':'Preview mode'}</div><button className="icon-btn notification-btn" onClick={()=>navigateToIssueList('review')} title="View signal watch"><Bell size={18}/>{reviewCount>0&&<i/>}</button><div className="top-avatar">CO</div></div>
      </header>
      <div className="page">
        {activeView === 'analytics' ? <AnalyticsPage apiBaseUrl={API} /> : <>
        <section className="welcome-row">
  <div>
    <div className="eyebrow">
      <span className="eyebrow-line" />
      CIVIC OPERATIONS / OVERVIEW
    </div>

    <h1>
      Civic Impact Overview
      <span className="wave">✳</span>
    </h1>

    <p className="page-subtitle">
      Monitor civic issues, assess societal impact, and prioritize
      what needs attention first.
    </p>
  </div>

  <div className="header-actions">
    <div className="date-chip">
      <CalendarDays size={16} />
      {new Date().toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })}
    </div>

    <button className="primary-btn" onClick={refresh} disabled={loading}>
      <RefreshCw size={16} className={loading ? "spin" : ""} />
      {loading ? "Syncing…" : "Sync data"}
    </button>
  </div>
</section>

        <section className="hero-banner"><div className="hero-text"><div className="hero-kicker"><Sparkles size={14}/> THE COMMUNITY PULSE</div><h2>Turn reports into<br/><em>meaningful action.</em></h2><p>Bring safety, severity, persistence and resident reports together to help teams focus on what needs attention first.</p><button className="hero-link" onClick={()=>document.getElementById('issues-table')?.scrollIntoView({behavior:'smooth'})}>Explore priority queue <ChevronRight size={16}/></button></div><div className="hero-visual" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="hero-pin pin-a"><MapPin size={17}/></div><div className="hero-pin pin-b"><AlertTriangle size={16}/></div><div className="hero-pin pin-c"><Activity size={16}/></div><div className="hero-center"><Waves size={35}/></div><div className="visual-label label-a"><span/> Safety signal <b>Elevated</b></div><div className="visual-label label-b"><span/> Issue coverage <b>Active</b></div></div><div className="hero-foot"><span><span className="tiny-dot"/> Evidence-led prioritization</span><span>Built for community outcomes <ArrowUpRight size={13}/></span></div></section>

        <section className="section-heading"><div><h2>At a glance</h2><p>What the current issue register is telling us</p></div><span className="muted-small">Updated {lastUpdated.toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'})}</span></section>
        <section className="stats-grid">
          <Stat icon={<ClipboardList size={18}/>} label="Tracked issues" value={fmt(issues.length)} foot="In the current register" accent="blue" />
          <Stat icon={<AlertTriangle size={18}/>} label="Need attention" value={fmt(openCount)} foot={`${issues.length?Math.round(openCount/issues.length*100):0}% currently unresolved`} accent="orange" />
          <Stat icon={<ShieldAlert size={18}/>} label="Signals to review" value={fmt(reviewCount)} foot="Declining reports, still unresolved" accent="purple" />
          <Stat icon={<Gauge size={18}/>} label="Average impact score" value={`${avgScore}/100`} foot="Provisional baseline score" accent="green" />
        </section>

        <section className="analytics-grid">
          <div className="panel trend-panel"><div className="panel-heading"><div><div className="panel-kicker">REPORTING ACTIVITY</div><h3>Community signal</h3><p>Actual complaint reports across the last 7 days</p></div><button className="soft-btn" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div><div className="trend-summary"><div><strong>{fmt(reportTrend.reduce((sum, item) => sum + Number(item.reports || 0), 0))}</strong><span>reports in last 7 days</span></div><span className="trend-change"><Activity size={15}/> PostgreSQL data</span></div><div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={reportTrend} margin={{top:8,right:4,left:-25,bottom:0}}><defs><linearGradient id="reportFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4776e6" stopOpacity={0.2}/><stop offset="95%" stopColor="#4776e6" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#edf0f6" vertical={false}/><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fontSize:11,fill:'#8b93a7'}} dy={8}/><YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{fontSize:11,fill:'#8b93a7'}}/><Tooltip contentStyle={{border:'1px solid #e7ebf2',borderRadius:12,fontSize:12,boxShadow:'0 8px 24px #25385812'}}/><Area type="monotone" dataKey="reports" name="Reports" stroke="#4776e6" strokeWidth={2.5} fill="url(#reportFill)" activeDot={{r:5,strokeWidth:0}}/></AreaChart></ResponsiveContainer></div><div className="chart-foot"><span><span className="legend-dot blue-dot"/> Reports received</span><span className="chart-disclaimer">{reportTrend.length ? 'Live database series' : 'No trend data available'}</span></div></div>
          <div className="panel category-panel"><div className="panel-heading"><div><div className="panel-kicker">ISSUE DISTRIBUTION</div><h3>Where attention goes</h3><p>Share of complaints by reported category</p></div><button className="icon-btn subtle"><MoreHorizontal size={19}/></button></div><div className="category-total"><strong>{fmt(totalReports)}</strong><span>complaints in database</span></div><div className="category-bars">{categoryDistribution.map(c=><div className="category-row" key={c.name}><div className="category-meta"><span><i style={{background:c.color}}/>{cap(c.name)}</span><b>{Number(c.value || 0)}%</b></div><div className="bar-track"><div style={{width:`${Math.min(Number(c.value || 0), 100)}%`,background:c.color}}/></div><span className="cell-sub">{fmt(c.count)} reports</span></div>)}{categoryDistribution.length===0&&<div className="empty-state"><b>No category data yet</b><span>Submit complaints to populate this chart.</span></div>}</div><div className="category-foot"><span className="foot-check"><CheckCircle2 size={15}/> Categories help teams spot patterns</span></div></div>
        </section>

        <section className="signal-strip"><div className="signal-symbol"><ShieldAlert size={20}/></div><div className="signal-copy"><b>Signal watch <span className="signal-number">{reviewCount}</span></b><p>{reviewCount ? 'At least one unresolved issue has a drop in reporting activity. A drop is a review signal — not evidence that the problem is fixed.' : 'No unresolved decline signals in the current list.'}</p></div><button className="signal-action" onClick={()=>{setFilter('review');document.getElementById('issues-table')?.scrollIntoView({behavior:'smooth'})}}>Review signals <ChevronRight size={16}/></button></section>

        <section className="panel table-panel" id="issues-table"><div className="table-title-row"><div><div className="panel-kicker">ACTION QUEUE</div><h3>Priority issue register</h3><p>Ranked by the current provisional impact score, not complaint count alone.</p></div><div><button className="outline-btn" onClick={()=>setShowAddIssue(true)}><Plus size={15}/> Add New Issue</button> <button className="outline-btn" onClick={exportCsv}><Download size={15}/> Export CSV</button></div></div>
          <div className="table-toolbar"><div className="search-box"><Search size={16}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search issues, categories or locations…"/>{search&&<button onClick={()=>setSearch('')}><X size={14}/></button>}</div><button className={`filter-btn ${showFilters?'selected':''}`} onClick={()=>setShowFilters(!showFilters)}><SlidersHorizontal size={15}/> Filters <ChevronDown size={14}/></button><div className="result-count">{filtered.length} results</div></div>
          {showFilters&&<div className="filter-row">{[['all','All issues'],['critical','Critical'],['high','High'],['medium','Medium'],['low','Low'],['review','Signal watch']].map(([v,l])=><button key={v} className={`filter-chip ${filter===v?'chosen':''}`} onClick={()=>setFilter(v)}>{l}</button>)}<select className="filter-btn" aria-label="Filter by issue status" value={statusFilter} onChange={event=>setStatusFilter(event.target.value)}><option value="all">All Statuses</option><option value="open">Open</option><option value="in_progress">In Progress</option><option value="resolved">Resolved</option></select></div>}
          <div className="table-scroll"><table><thead><tr><th>ISSUE / LOCATION</th><th>STATUS</th><th>REPORTS</th><th>AGE</th><th>IMPACT SCORE</th><th>PRIORITY</th><th>ACTIONS</th></tr></thead><tbody>{filtered.map((issue,index)=><tr key={issue.issue_id} onClick={()=>setSelected(issue)} className="issue-row"><td><div className="issue-cell"><div className={`issue-icon issue-${levelOf(issue)}`}><MapPin size={16}/></div><div><b>{issue.description || cap(issue.issue_type)}</b><span>{cap(issue.issue_type)} <i>·</i> {issue.locality || `Civic area ${issue.issue_id}`} <i>·</i> ID #{issue.issue_id}</span>{issue.unresolved_review_flag&&<small className="review-inline"><AlertTriangle size={11}/> Reporting decline — review</small>}</div></div></td>
          <td>
            <select
              className={`status-badge status-${String((statusUpdates[issue.issue_id] ?? issue.status)).toLowerCase()}`}
              value={statusUpdates[issue.issue_id] ?? issue.status}
              disabled={Boolean(statusUpdates[issue.issue_id])}
              aria-label={`Update status for issue ${issue.issue_id}`}
              onClick={event => event.stopPropagation()}
              onChange={event => {
                event.stopPropagation();
                updateIssueStatus(issue, event.target.value);
              }}
            >
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
            </select>
          </td><td><span className="report-count">{fmt(issue.total_complaints)}</span><span className="cell-sub">linked reports</span></td><td><b className="age-value">{fmt(issue.age_days)}d</b><span className="cell-sub">unresolved age</span></td><td><div className="score-cell"><div className="score-number">{Math.round(scoreOf(issue))}<span>/100</span></div><div className="score-track"><div style={{width:`${Math.min(scoreOf(issue),100)}%`}} className={`score-fill fill-${levelOf(issue)}`}/></div></div></td><td><span className={`priority-badge priority-${levelOf(issue)}`}><i/>{cap(levelOf(issue))}</span></td><td><button
  type="button"
  className="outline-btn"
  onClick={event => {
    event.stopPropagation();
    openEditIssue(issue);
  }}
>
  Edit
</button><button className="row-open" aria-label="View issue" onClick={e=>{e.stopPropagation();setSelected(issue)}}><ChevronRight size={17}/></button></td></tr>)}</tbody></table>{filtered.length===0&&<div className="empty-state"><Search size={24}/><b>No matching issues</b><span>Try a different search or filter.</span><button className="soft-btn" onClick={()=>{setSearch('');setFilter('all')}}>Clear filters</button></div>}</div>
          <div className="table-footer"><span>Showing <b>{filtered.length}</b> of <b>{issues.length}</b> issues</span><span>Ranking: provisional rule-based baseline <CircleDot size={12}/></span></div>
        </section>
        <footer className="footer"><div className="footer-brand"><div className="mini-brand"><Waves size={15}/></div><b>CivicPulse</b><span>·</span><span>Make every report count.</span></div><div><span className="footer-status"><span className="status-dot"/> {source==='live'?'API connected':'Demo preview'}</span><span className="footer-sep">·</span><span>Impact Intelligence v1.0</span></div></footer>
        </>}
      </div>
    </main>
    {selected&&<><button className="drawer-scrim" onClick={()=>setSelected(null)} aria-label="Close details"/><aside className="detail-drawer"><div className="drawer-header"><div><div className="panel-kicker">ISSUE DETAILS · #{selected.issue_id}</div><h2>Issue overview</h2></div><button className="icon-btn" onClick={()=>setSelected(null)}><X size={19}/></button></div><div className={`drawer-priority-banner banner-${levelOf(selected)}`}><div className="drawer-score"><span>Impact score</span><strong>{Math.round(scoreOf(selected))}<small>/100</small></strong></div><span className={`priority-badge priority-${levelOf(selected)}`}><i/>{cap(levelOf(selected))} priority</span></div><div className="drawer-issue-title"><span className="issue-type-label">{cap(selected.issue_type)}</span><h3>{selected.description || cap(selected.issue_type)}</h3><p><MapPin size={14}/>{selected.locality || `Civic area ${selected.issue_id}`}</p></div><div className="drawer-metrics"><div><span>Linked reports</span><b>{selected.total_complaints||0}</b></div><div><span>Issue age</span><b>{selected.age_days||0} days</b></div><div><span>Safety risk</span><b>{selected.safety_risk ?? '—'}<small> / 5</small></b></div><div><span>Severity</span><b>{selected.physical_severity ?? '—'}<small> / 5</small></b></div></div><div className="drawer-section"><h4><Activity size={16}/> Reporting trend</h4>{source==='live'&&trend?<><div className="trend-compare"><div><span>Last 7 days</span><b>{trend.complaints_last_7_days}</b></div><ArrowDownRight size={18}/><div><span>Previous 7 days</span><b>{trend.complaints_previous_7_days}</b></div></div><p className="drawer-note">{trend.message}</p></>:<div className="drawer-note"><AlertTriangle size={15}/> {selected.unresolved_review_flag?'Reports have declined while this issue remains unresolved. Review is recommended.':'Connect the API to view the live 14-day reporting trend.'}</div>}</div><div className="drawer-section">
  <h4><MapPin size={16}/> Nearby population exposure</h4>
  {source !== 'live' ? (
    <div className="drawer-note">
      <AlertTriangle size={15}/>
      Connect the backend to view WorldPop population estimates.
    </div>
  ) : populationExposure?.population_exposure ? (
    <>
      <div className="population-grid">
        {[
          { label: '250 metres', key: '250m' },
          { label: '500 metres', key: '500m' },
          { label: '1 kilometre', key: '1000m' }
        ].map(radius => {
          const data = populationExposure.population_exposure[radius.key];

          return (
            <div className="population-card" key={radius.key}>
              <span>{radius.label}</span>
              <b>
                {data?.population != null
                  ? Number(data.population).toLocaleString('en-IN', {
                      maximumFractionDigits: 2
                    })
                  : '—'}
              </b>
              <small>Estimated persons</small>
              <div className="population-coverage">
                Coverage: {data?.coverage_percent ?? '—'}%
              </div>
            </div>
          );
        })}
      </div>
      <p className="population-source">
        Source: {populationExposure.data_source || 'WorldPop'} · Reference year: {populationExposure.reference_year || 2025}
      </p>
      <p className="population-disclaimer">
        These figures estimate the residential population within each surrounding buffer. They do not represent confirmed affected persons.
      </p>
    </>
  ) : (
    <div className="drawer-note">
      <Activity size={15}/>
      Population exposure is unavailable. Check the backend endpoint and try again.
    </div>
  )}
</div>
<div className="drawer-section"><h4><Clock3 size={16}/> Current assessment</h4><div className="assessment-line"><span>Status</span><b className={`status-badge status-${String(selected.status).toLowerCase()}`}>{cap(selected.status)}</b></div><div className="assessment-line"><span>Review signal</span><b className={selected.unresolved_review_flag?'text-warning':'text-ok'}>{selected.unresolved_review_flag?'Needs review':'No decline flag'}</b></div><div className="assessment-line"><span>Scoring method</span><b>Rule-based baseline</b></div></div><div className="drawer-disclaimer"><ShieldAlert size={17}/><p><b>Decision support, not an automatic verdict.</b> The score is provisional. Validate field conditions and use independent expert assessments before treating this ranking as ground truth.</p></div><button className="primary-btn drawer-done" onClick={()=>setSelected(null)}>Done <CheckCircle2 size={16}/></button></aside></>}
    {showAddIssue && (
      <div
        role="presentation"
        onMouseDown={event => {
          if (event.target === event.currentTarget && !submittingIssue) {
            setShowAddIssue(false);
            setIssueFormError('');
          }
        }}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20,
          background: 'rgba(20, 30, 50, 0.48)'
        }}
      >
        <section
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-issue-title"
          style={{
            width: 'min(100%, 560px)',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: 24,
            borderRadius: 16,
            background: '#fff',
            boxShadow: '0 20px 60px rgba(20, 30, 50, 0.24)'
          }}
        >
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">ISSUE REGISTRY</div>
              <h3 id="add-issue-title">Add New Issue</h3>
              <p>Enter the issue details and location.</p>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Close dialog"
              disabled={submittingIssue}
              onClick={() => {
                setShowAddIssue(false);
                setIssueFormError('');
              }}
            >
              <X size={19} />
            </button>
          </div>

          <form onSubmit={submitNewIssue}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              {[
                { key: 'issue_type', label: 'Issue type', type: 'text', full: true },
                { key: 'description', label: 'Description', type: 'text', full: true },
                { key: 'latitude', label: 'Latitude', type: 'number', min: -90, max: 90, step: 'any' },
                { key: 'longitude', label: 'Longitude', type: 'number', min: -180, max: 180, step: 'any' },
                { key: 'physical_severity', label: 'Physical severity (1–5)', type: 'number', min: 1, max: 5, step: 1 },
                { key: 'safety_risk', label: 'Safety risk (1–5)', type: 'number', min: 1, max: 5, step: 1 }
              ].map(field => (
                <label
                  key={field.key}
                  style={{
                    display: 'grid',
                    gap: 6,
                    gridColumn: field.full ? '1 / -1' : undefined,
                    fontSize: 13,
                    fontWeight: 600
                  }}
                >
                  {field.label}
                  <input
                    required
                    type={field.type}
                    min={field.min}
                    max={field.max}
                    step={field.step}
                    value={newIssue[field.key]}
                    onChange={event => setNewIssue(current => ({
                      ...current,
                      [field.key]: event.target.value
                    }))}
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '11px 12px',
                      border: '1px solid #dfe4ed',
                      borderRadius: 9,
                      font: 'inherit'
                    }}
                  />
                </label>
              ))}
            </div>

            {issueFormError && (
              <p role="alert" className="drawer-note">{issueFormError}</p>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button
                type="button"
                className="outline-btn"
                disabled={submittingIssue}
                onClick={() => {
                  setShowAddIssue(false);
                  setIssueFormError('');
                }}
              >
                Cancel
              </button>
              <button type="submit" className="primary-btn" disabled={submittingIssue}>
                {submittingIssue ? 'Submitting…' : 'Create issue'}
              </button>
            </div>
          </form>
        </section>
      </div>
    )}
    {showEditIssue && (
      <div
        role="presentation"
        onMouseDown={event => {
          if (event.target === event.currentTarget && !submittingEditIssue && !loadingEditCoordinates) {
            setShowEditIssue(false);
            resetEditIssue();
          }
        }}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20,
          background: 'rgba(20, 30, 50, 0.48)'
        }}
      >
        <section
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-issue-title"
          style={{
            width: 'min(100%, 560px)',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: 24,
            borderRadius: 16,
            background: '#fff',
            boxShadow: '0 20px 60px rgba(20, 30, 50, 0.24)'
          }}
        >
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">ISSUE REGISTRY</div>
              <h3 id="edit-issue-title">Edit Issue</h3>
              <p>Update the issue details and location.</p>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Close dialog"
              disabled={submittingEditIssue || loadingEditCoordinates}
              onClick={() => {
                setShowEditIssue(false);
                resetEditIssue();
              }}
            >
              <X size={19} />
            </button>
          </div>

          <form onSubmit={submitEditIssue}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              {[
                { key: 'issue_type', label: 'Issue type', type: 'text', full: true },
                { key: 'description', label: 'Description', type: 'text', full: true },
                { key: 'latitude', label: 'Latitude', type: 'number', min: -90, max: 90, step: 'any' },
                { key: 'longitude', label: 'Longitude', type: 'number', min: -180, max: 180, step: 'any' },
                { key: 'physical_severity', label: 'Physical severity (1–5)', type: 'number', min: 1, max: 5, step: 1 },
                { key: 'safety_risk', label: 'Safety risk (1–5)', type: 'number', min: 1, max: 5, step: 1 }
              ].map(field => (
                <label
                  key={field.key}
                  style={{
                    display: 'grid',
                    gap: 6,
                    gridColumn: field.full ? '1 / -1' : undefined,
                    fontSize: 13,
                    fontWeight: 600
                  }}
                >
                  {field.label}
                  <input
                    required
                    type={field.type}
                    min={field.min}
                    max={field.max}
                    step={field.step}
                    value={editIssue[field.key]}
                    onChange={event => setEditIssue(current => ({
                      ...current,
                      [field.key]: event.target.value
                    }))}
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '11px 12px',
                      border: '1px solid #dfe4ed',
                      borderRadius: 9,
                      font: 'inherit'
                    }}
                  />
                </label>
              ))}
            </div>

            {loadingEditCoordinates && (
              <p className="drawer-note">Loading saved coordinates…</p>
            )}
            {editIssueError && (
              <p role="alert" className="drawer-note">{editIssueError}</p>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button
                type="button"
                className="outline-btn"
                disabled={submittingEditIssue || loadingEditCoordinates}
                onClick={() => {
                  setShowEditIssue(false);
                  resetEditIssue();
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="primary-btn"
                disabled={submittingEditIssue || loadingEditCoordinates}
              >
                {loadingEditCoordinates
                  ? 'Loading…'
                  : submittingEditIssue
                    ? 'Saving…'
                    : 'Save changes'}
              </button>
            </div>
          </form>
        </section>
      </div>
    )}
    {toast&&<div className="toast"><CheckCircle2 size={17}/>{toast}</div>}
  </div>;
}
function Stat({ icon, label, value, foot, accent }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${accent}`}>{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-foot">
        <span className={`stat-foot-dot ${accent}`} />
        {foot}
      </div>
      <div className="stat-card-glow" />
    </div>
  );
}
export default App;