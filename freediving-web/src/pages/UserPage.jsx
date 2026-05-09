import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';
import './UserPage.css';

const UserPage = () => {
  const [announcements, setAnnouncements] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [applications, setApplications] = useState([]);
  
  // Form states
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    birthdate: '',
    rental_equipment: '',
    liability_consent: false
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    // 공지사항 로드
    const { data: anns } = await supabase
      .from('fd_announcements')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(3);
    if (anns) setAnnouncements(anns);

    // 일정 로드
    const { data: scheds } = await supabase
      .from('fd_schedules')
      .select('*')
      .order('schedule_date', { ascending: true })
      .order('schedule_time', { ascending: true });
    if (scheds) setSchedules(scheds);

    // 신청 내역 로드
    const { data: apps } = await supabase
      .from('fd_applications')
      .select('*')
      .order('created_at', { ascending: true });
    if (apps) setApplications(apps);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e, scheduleId) => {
    e.preventDefault();
    if (!formData.name || !formData.birthdate) {
      alert("이름과 생년월일을 모두 입력해주세요.");
      return;
    }
    if (!formData.liability_consent) {
      alert("면책 동의에 체크해주셔야 예약이 가능합니다.");
      return;
    }

    try {
      const { error } = await supabase
        .from('fd_applications')
        .insert([{
          schedule_id: scheduleId,
          name: formData.name,
          birthdate: formData.birthdate,
          rental_equipment: formData.rental_equipment,
          liability_consent: formData.liability_consent
        }]);

      if (error) throw error;
      
      alert("예약이 완료되었습니다!");
      setFormData({ name: '', birthdate: '', rental_equipment: '', liability_consent: false });
      setSelectedSchedule(null);
      fetchData(); // 데이터 리로드
    } catch (error) {
      alert("예약 중 오류가 발생했습니다: " + error.message);
    }
  };

  return (
    <div className="user-container">
      <header className="main-header">
        <h1>🌊 브로시스 프리다이빙</h1>
        <p>초보자도 쉽고 즐겁게 프리다이빙을 배울 수 있는 공간입니다. 아래에서 공지를 확인하고 교육을 예약하세요!</p>
        <Link to="/admin" className="admin-link">관리자 페이지로 이동</Link>
      </header>

      <section className="section">
        <h2>📢 최근 공지사항</h2>
        {announcements.length === 0 ? (
          <p className="empty-state">등록된 공지사항이 없습니다.</p>
        ) : (
          announcements.map(ann => (
            <div key={ann.id} className="announce-card">
              <h3>{ann.title}</h3>
              <span className="date-badge">{format(new Date(ann.created_at), 'yyyy-MM-dd HH:mm')}</span>
              <p>{ann.content}</p>
            </div>
          ))
        )}
      </section>

      <section className="section">
        <h2>🗓️ 교육 일정 및 예약</h2>
        {schedules.length === 0 ? (
          <p className="empty-state">현재 열려있는 교육 일정이 없습니다.</p>
        ) : (
          schedules.map(sched => {
            const schedApps = applications.filter(a => a.schedule_id === sched.id);
            const currentCount = schedApps.length;
            const isFull = currentCount >= sched.max_capacity;
            const isExpanded = selectedSchedule === sched.id;

            return (
              <div key={sched.id} className="sched-card">
                <div 
                  className="sched-header" 
                  onClick={() => setSelectedSchedule(isExpanded ? null : sched.id)}
                >
                  <div className="sched-info">
                    <span className="sched-date">{sched.schedule_date} {sched.schedule_time.substring(0, 5)}</span>
                    <span className="sched-location">📍 {sched.location}</span>
                  </div>
                  <div className="sched-status">
                    {isFull ? (
                      <span className="status-badge full">🔴 마감</span>
                    ) : (
                      <span className="status-badge available">🟢 {currentCount}/{sched.max_capacity}명</span>
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="sched-details">
                    <div className="app-list">
                      <h4>👥 현재 신청자 현황</h4>
                      {currentCount === 0 ? (
                        <p className="text-muted">아직 신청자가 없습니다. 첫 번째로 신청해보세요!</p>
                      ) : (
                        <ul>
                          {schedApps.map(a => (
                            <li key={a.id}>
                              <strong>{a.name}</strong>님 | 
                              장비: {a.rental_equipment || '없음'} | 
                              동의: {a.liability_consent ? '✅' : '❌'}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {!isFull && (
                      <div className="booking-form">
                        <h4>📝 예약 신청하기</h4>
                        <form onSubmit={(e) => handleSubmit(e, sched.id)}>
                          <div className="form-group">
                            <label>이름</label>
                            <input type="text" name="name" value={formData.name} onChange={handleInputChange} placeholder="홍길동" required />
                          </div>
                          <div className="form-group">
                            <label>생년월일 (관리자만 볼 수 있습니다)</label>
                            <input type="text" name="birthdate" value={formData.birthdate} onChange={handleInputChange} placeholder="YYYY-MM-DD" required />
                          </div>
                          <div className="form-group">
                            <label>대여 필요 장비 (없으면 비워두세요)</label>
                            <input type="text" name="rental_equipment" value={formData.rental_equipment} onChange={handleInputChange} placeholder="예: 마스크, 오리발(260mm)" />
                          </div>
                          <div className="consent-box">
                            <strong>면책 동의서</strong>
                            <p className="consent-text">본인은 프리다이빙 교육 중 발생할 수 있는 위험성을 인지하며, 본인의 과실로 인한 사고에 대해 강사에게 책임을 묻지 않을 것에 동의합니다.</p>
                            <label className="checkbox-label">
                              <input type="checkbox" name="liability_consent" checked={formData.liability_consent} onChange={handleInputChange} />
                              위 면책 동의서 내용을 확인하였으며 동의합니다.
                            </label>
                          </div>
                          <button type="submit" className="submit-btn">예약 신청하기</button>
                        </form>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </section>
    </div>
  );
};

export default UserPage;
