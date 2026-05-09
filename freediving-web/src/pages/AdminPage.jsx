import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import { Link } from 'react-router-dom';
import './AdminPage.css';

const AdminPage = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  
  const [activeTab, setActiveTab] = useState('announcements');
  const [announcements, setAnnouncements] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [applications, setApplications] = useState([]);

  // Form states
  const [annForm, setAnnForm] = useState({ title: '', content: '' });
  const [schedForm, setSchedForm] = useState({ date: '', time: '', location: '', max_capacity: 4 });

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  const fetchData = async () => {
    const { data: anns } = await supabase.from('fd_announcements').select('*').order('created_at', { ascending: false });
    if (anns) setAnnouncements(anns);

    const { data: scheds } = await supabase.from('fd_schedules').select('*').order('schedule_date', { ascending: true }).order('schedule_time', { ascending: true });
    if (scheds) setSchedules(scheds);

    const { data: apps } = await supabase.from('fd_applications').select('*').order('created_at', { ascending: true });
    if (apps) setApplications(apps);
  };

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === 'admin1234') {
      setIsAuthenticated(true);
    } else {
      alert('비밀번호가 틀렸습니다.');
    }
  };

  const handleAddAnnouncement = async (e) => {
    e.preventDefault();
    if (!annForm.title || !annForm.content) return alert('모두 입력해주세요');
    
    const { error } = await supabase.from('fd_announcements').insert([{ title: annForm.title, content: annForm.content }]);
    if (error) return alert(error.message);
    
    alert('공지가 등록되었습니다! (카카오톡 알림 발송됨 - 시뮬레이션)');
    setAnnForm({ title: '', content: '' });
    fetchData();
  };

  const handleDeleteAnnouncement = async (id) => {
    if (!window.confirm('삭제하시겠습니까?')) return;
    await supabase.from('fd_announcements').delete().eq('id', id);
    fetchData();
  };

  const handleAddSchedule = async (e) => {
    e.preventDefault();
    if (!schedForm.date || !schedForm.time || !schedForm.location) return alert('모두 입력해주세요');
    
    const { error } = await supabase.from('fd_schedules').insert([{
      schedule_date: schedForm.date,
      schedule_time: schedForm.time,
      location: schedForm.location,
      max_capacity: schedForm.max_capacity
    }]);
    
    if (error) return alert(error.message);
    alert('일정이 등록되었습니다!');
    setSchedForm({ date: '', time: '', location: '', max_capacity: 4 });
    fetchData();
  };

  const handleDeleteSchedule = async (id) => {
    if (!window.confirm('삭제하시겠습니까? (관련 신청 내역도 모두 삭제됩니다)')) return;
    await supabase.from('fd_schedules').delete().eq('id', id);
    fetchData();
  };

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <h2>🔐 관리자 로그인</h2>
        <form onSubmit={handleLogin} className="login-form">
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            placeholder="비밀번호 입력"
          />
          <button type="submit">로그인</button>
        </form>
        <Link to="/" style={{marginTop: '20px', display: 'block'}}>사용자 페이지로 돌아가기</Link>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <header className="admin-header">
        <h1>⚙️ 브로시스 관리자 대시보드</h1>
        <Link to="/" className="home-link">👉 사용자 웹앱(메인화면)으로 바로가기</Link>
      </header>

      <div className="tabs">
        <button className={activeTab === 'announcements' ? 'active' : ''} onClick={() => setActiveTab('announcements')}>📢 공지사항 관리</button>
        <button className={activeTab === 'schedules' ? 'active' : ''} onClick={() => setActiveTab('schedules')}>🗓️ 교육 일정 관리</button>
        <button className={activeTab === 'applications' ? 'active' : ''} onClick={() => setActiveTab('applications')}>👥 예약자 현황 (상세)</button>
      </div>

      <div className="tab-content">
        {activeTab === 'announcements' && (
          <div>
            <h3>새 공지사항 작성</h3>
            <form onSubmit={handleAddAnnouncement} className="admin-form">
              <input type="text" placeholder="공지 제목" value={annForm.title} onChange={e => setAnnForm({...annForm, title: e.target.value})} />
              <textarea placeholder="공지 내용" value={annForm.content} onChange={e => setAnnForm({...annForm, content: e.target.value})} rows="4"></textarea>
              <div className="info-box">💡 카카오톡/문자 자동 알림 발송은 외부 API 연동이 필요합니다. 현재는 가상의 발송 로직만 실행됩니다.</div>
              <button type="submit">공지 등록하기 및 알림 발송</button>
            </form>
            
            <hr/>
            <h3>등록된 공지사항 목록</h3>
            {announcements.map(a => (
              <div key={a.id} className="list-item">
                <div>
                  <strong>{a.title}</strong> ({new Date(a.created_at).toLocaleDateString()})
                  <p>{a.content}</p>
                </div>
                <button onClick={() => handleDeleteAnnouncement(a.id)} className="delete-btn">삭제</button>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'schedules' && (
          <div>
            <h3>새 교육 일정 등록</h3>
            <form onSubmit={handleAddSchedule} className="admin-form">
              <div className="form-row">
                <input type="date" value={schedForm.date} onChange={e => setSchedForm({...schedForm, date: e.target.value})} required/>
                <input type="time" value={schedForm.time} onChange={e => setSchedForm({...schedForm, time: e.target.value})} required/>
              </div>
              <input type="text" placeholder="교육 장소 (예: 올림픽 수영장 다이빙풀)" value={schedForm.location} onChange={e => setSchedForm({...schedForm, location: e.target.value})} required/>
              <input type="number" placeholder="최대 인원" min="1" max="20" value={schedForm.max_capacity} onChange={e => setSchedForm({...schedForm, max_capacity: parseInt(e.target.value)})} required/>
              <button type="submit">일정 등록하기</button>
            </form>

            <hr/>
            <h3>등록된 교육 일정 목록</h3>
            {schedules.map(s => (
              <div key={s.id} className="list-item">
                <div>
                  <strong>📅 {s.schedule_date} {s.schedule_time.substring(0,5)}</strong> | 📍 {s.location} | 최대 {s.max_capacity}명
                </div>
                <button onClick={() => handleDeleteSchedule(s.id)} className="delete-btn">삭제</button>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'applications' && (
          <div>
            <h3>날짜별 교육 예약 현황</h3>
            {schedules.map(s => {
              const schedApps = applications.filter(a => a.schedule_id === s.id);
              return (
                <div key={s.id} className="admin-sched-card">
                  <h4>📅 {s.schedule_date} {s.schedule_time.substring(0,5)} - {s.location} (현재 {schedApps.length}/{s.max_capacity}명)</h4>
                  {schedApps.length === 0 ? (
                    <p>아직 신청자가 없습니다.</p>
                  ) : (
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>신청일시</th>
                          <th>이름</th>
                          <th>생년월일</th>
                          <th>면책동의</th>
                          <th>대여장비</th>
                        </tr>
                      </thead>
                      <tbody>
                        {schedApps.map(a => (
                          <tr key={a.id}>
                            <td>{new Date(a.created_at).toLocaleString()}</td>
                            <td>{a.name}</td>
                            <td>{a.birthdate}</td>
                            <td>{a.liability_consent ? '✅ 동의' : '❌ 미동의'}</td>
                            <td>{a.rental_equipment || '없음'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPage;
