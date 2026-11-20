import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, CheckCircle2,
  ChevronDown, ChevronRight, Clock3, Download, ExternalLink, Filter, Gauge,
  LayoutDashboard, LifeBuoy, MapPin, Menu, MoreHorizontal, Search, Settings2,
  ShieldAlert, SlidersHorizontal, Sparkles, TrendingDown, TrendingUp, Waves,
  X, RefreshCw, CircleDot, CalendarDays, ClipboardList, Zap
} from 'lucide-react';
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
  BarChart, Bar, Cell
} from 'recharts';

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
  const [selected, setSelected] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState('');
  const [trend, setTrend] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [populationExposure, setPopulationExposure] = useState(null);
  const [reportTrend, setReportTrend] = useState([]);
  const [categoryDistribution, setCategoryDistribution] = useState([]);
  const [totalReports, setTotalReports] = useState(0);
  const [showFilters, setShowFilters] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/issues/priority-list`);
      if (!r.ok) throw new Error('API unavailable');
      const data = await r.json();
      const rows = (data.issues || []).map(i => ({
        ...i,
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
    } catch {
      setIssues(demoIssues);
      setSource('demo');
      setReportTrend([]);
      setCategoryDistribution([]);
      setTotalReports(0);
      setLastUpdated(new Date());
      setToast('Showing sample issue data — backend not connected');
    } finally {
      setLoading(false);
      setTimeout(() => setToast(''), 3500);
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
    const matches = [i.description, i.issue_type, i.locality, i.issue_id].some(v => String(v ?? '').toLowerCase().includes(q));
    return matches && (filter === 'all' || levelOf(i) === filter || (filter === 'review' && i.unresolved_review_flag));
  }).sort((a,b) => scoreOf(b)-scoreOf(a)), [issues, search, filter]);
  const critical = issues.filter(i => levelOf(i) === 'critical').length;
  const openCount = issues.filter(i => !['resolved','closed'].includes(String(i.status).toLowerCase())).length;
  const reviewCount = issues.filter(i => i.unresolved_review_flag).length;
  const avgScore = issues.length ? Math.round(issues.reduce((s,i)=>s+scoreOf(i),0)/issues.length) : 0;
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
        <button className="nav-item active"><LayoutDashboard size={18}/><span>Overview</span><span className="nav-active-dot"/></button>
        <button className="nav-item" onClick={()=>{setFilter('all');document.getElementById('issues-table')?.scrollIntoView({behavior:'smooth'});setSidebarOpen(false)}}><ClipboardList size={18}/><span>Issue registry</span><span className="nav-count">{issues.length}</span></button>
        <button className="nav-item" onClick={()=>{setFilter('review');document.getElementById('issues-table')?.scrollIntoView({behavior:'smooth'});setSidebarOpen(false)}}><ShieldAlert size={18}/><span>Signal watch</span>{reviewCount>0&&<span className="nav-count alert-count">{reviewCount}</span>}</button>
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
        <div className="top-left"><button className="mobile-menu icon-btn" onClick={()=>setSidebarOpen(true)}><Menu size={20}/></button><div className="breadcrumbs">Workspace <ChevronRight size={14}/> <b>Overview</b></div></div>
        <div className="top-actions"><div className={`connection-pill ${source==='live'?'live':'demo'}`}><span className="status-dot"/>{source==='live'?'Live data connected':'Preview mode'}</div><button className="icon-btn notification-btn" onClick={()=>{setFilter('review');document.getElementById('issues-table')?.scrollIntoView({behavior:'smooth'})}} title="View signal watch"><Bell size={18}/>{reviewCount>0&&<i/>}</button><div className="top-avatar">CO</div></div>
      </header>
      <div className="page">
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

        <section className="panel table-panel" id="issues-table"><div className="table-title-row"><div><div className="panel-kicker">ACTION QUEUE</div><h3>Priority issue register</h3><p>Ranked by the current provisional impact score, not complaint count alone.</p></div><button className="outline-btn" onClick={exportCsv}><Download size={15}/> Export CSV</button></div>
          <div className="table-toolbar"><div className="search-box"><Search size={16}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search issues, categories or locations…"/>{search&&<button onClick={()=>setSearch('')}><X size={14}/></button>}</div><button className={`filter-btn ${showFilters?'selected':''}`} onClick={()=>setShowFilters(!showFilters)}><SlidersHorizontal size={15}/> Filters <ChevronDown size={14}/></button><div className="result-count">{filtered.length} results</div></div>
          {showFilters&&<div className="filter-row">{[['all','All issues'],['critical','Critical'],['high','High'],['medium','Medium'],['low','Low'],['review','Signal watch']].map(([v,l])=><button key={v} className={`filter-chip ${filter===v?'chosen':''}`} onClick={()=>setFilter(v)}>{l}</button>)}</div>}
          <div className="table-scroll"><table><thead><tr><th>ISSUE / LOCATION</th><th>STATUS</th><th>REPORTS</th><th>AGE</th><th>IMPACT SCORE</th><th>PRIORITY</th><th></th></tr></thead><tbody>{filtered.map((issue,index)=><tr key={issue.issue_id} onClick={()=>setSelected(issue)} className="issue-row"><td><div className="issue-cell"><div className={`issue-icon issue-${levelOf(issue)}`}><MapPin size={16}/></div><div><b>{issue.description || cap(issue.issue_type)}</b><span>{cap(issue.issue_type)} <i>·</i> {issue.locality || `Civic area ${issue.issue_id}`} <i>·</i> ID #{issue.issue_id}</span>{issue.unresolved_review_flag&&<small className="review-inline"><AlertTriangle size={11}/> Reporting decline — review</small>}</div></div></td><td><span className={`status-badge status-${String(issue.status).toLowerCase()}`}><i/>{cap(issue.status)}</span></td><td><span className="report-count">{fmt(issue.total_complaints)}</span><span className="cell-sub">linked reports</span></td><td><b className="age-value">{fmt(issue.age_days)}d</b><span className="cell-sub">unresolved age</span></td><td><div className="score-cell"><div className="score-number">{Math.round(scoreOf(issue))}<span>/100</span></div><div className="score-track"><div style={{width:`${Math.min(scoreOf(issue),100)}%`}} className={`score-fill fill-${levelOf(issue)}`}/></div></div></td><td><span className={`priority-badge priority-${levelOf(issue)}`}><i/>{cap(levelOf(issue))}</span></td><td><button className="row-open" aria-label="View issue" onClick={e=>{e.stopPropagation();setSelected(issue)}}><ChevronRight size={17}/></button></td></tr>)}</tbody></table>{filtered.length===0&&<div className="empty-state"><Search size={24}/><b>No matching issues</b><span>Try a different search or filter.</span><button className="soft-btn" onClick={()=>{setSearch('');setFilter('all')}}>Clear filters</button></div>}</div>
          <div className="table-footer"><span>Showing <b>{filtered.length}</b> of <b>{issues.length}</b> issues</span><span>Ranking: provisional rule-based baseline <CircleDot size={12}/></span></div>
        </section>
        <footer className="footer"><div className="footer-brand"><div className="mini-brand"><Waves size={15}/></div><b>CivicPulse</b><span>·</span><span>Make every report count.</span></div><div><span className="footer-status"><span className="status-dot"/> {source==='live'?'API connected':'Demo preview'}</span><span className="footer-sep">·</span><span>Impact Intelligence v1.0</span></div></footer>
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