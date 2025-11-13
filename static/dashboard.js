document.addEventListener('DOMContentLoaded', () => {
  const monthLabel = document.getElementById('month-label');
  const calendarBody = document.getElementById('calendar-body');
  const prev = document.getElementById('prev-month');
  const next = document.getElementById('next-month');
  const tabSchedule = document.getElementById('tab-schedule');
  const tabNotes = document.getElementById('tab-notes');
  const scheduleContent = document.getElementById('schedule');
  const notesContent = document.getElementById('notes');
  const scheduleList = document.getElementById('schedule-list');
  const notesList = document.getElementById('notes-list');
  const scheduleDate = document.getElementById('schedule-date');
  const notesDate = document.getElementById('notes-date');
  const noteInput = document.getElementById('noteInput');
  const addNoteBtn = document.getElementById('addNoteBtn');

  let cur = new Date();
  let selected = new Date();

  // вкладки
  tabSchedule.onclick = () => {
    tabSchedule.classList.add('active');
    tabNotes.classList.remove('active');
    scheduleContent.classList.add('active');
    notesContent.classList.remove('active');
  };
  tabNotes.onclick = () => {
    tabNotes.classList.add('active');
    tabSchedule.classList.remove('active');
    notesContent.classList.add('active');
    scheduleContent.classList.remove('active');
  };

  function iso(d) { return d.toISOString().slice(0, 10); }
  function nice(d) { return new Date(d).toLocaleDateString('ru-RU'); }

  function renderCalendar() {
    calendarBody.innerHTML = '';
    const y = cur.getFullYear(), m = cur.getMonth();
    monthLabel.textContent = cur.toLocaleString('ru-RU', { month: 'long', year: 'numeric' }).toUpperCase();
    const first = new Date(y, m, 1);
    const startIndex = (first.getDay() + 6) % 7; // Monday=0
    const daysInMonth = new Date(y, m + 1, 0).getDate();
    let day = 1 - startIndex;
    for (let r = 0; r < 6; r++) {
      const tr = document.createElement('tr');
      for (let c = 0; c < 7; c++, day++) {
        const td = document.createElement('td');
        const d = new Date(y, m, day);
        td.textContent = d.getDate();
        td.dataset.date = iso(d);
        if (d.getMonth() !== m) td.classList.add('other-month');
        if (iso(d) === iso(selected)) td.classList.add('active');
        td.onclick = () => {
          document.querySelectorAll('td.active').forEach(x => x.classList.remove('active'));
          td.classList.add('active');
          selected = new Date(td.dataset.date);
          loadDay();
        };
        tr.appendChild(td);
      }
      calendarBody.appendChild(tr);
    }
  }

  prev.onclick = () => { cur.setMonth(cur.getMonth() - 1); renderCalendar(); };
  next.onclick = () => { cur.setMonth(cur.getMonth() + 1); renderCalendar(); };

  async function loadDay() {
    const d = iso(selected);
    scheduleDate.textContent = 'Дата: ' + nice(d);
    notesDate.textContent = 'Дата: ' + nice(d);
    scheduleList.innerHTML = 'Загрузка...';
    notesList.innerHTML = 'Загрузка...';
    try {
      const res = await fetch('/api/day/' + d);
      const data = await res.json();
      scheduleList.innerHTML = '';
      if (data.items && data.items.length) {
        data.items.forEach(it => {
          const p = document.createElement('p');
          p.textContent = (it.time ? it.time + ' — ' : '') + it.text;
          scheduleList.appendChild(p);
        });
      } else {
        scheduleList.innerHTML = '<p>Нет событий</p>';
      }

      notesList.innerHTML = '';
      if (data.notes && data.notes.length) {
        data.notes.forEach(n => {
          const li = document.createElement('li');
          li.textContent = n.text;
          notesList.appendChild(li);
        });
      } else {
        notesList.innerHTML = '<li>Нет заметок</li>';
      }
    } catch (e) {
      scheduleList.innerHTML = '<p>Ошибка загрузки</p>';
      notesList.innerHTML = '<li>Ошибка загрузки</li>';
    }
  }

  addNoteBtn.onclick = async () => {
    const txt = noteInput.value.trim();
    if (!txt) return;
    const d = iso(selected);
    try {
      await fetch('/api/note', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: d, text: txt })
      });
      noteInput.value = '';
      loadDay();
    } catch (e) {
      alert('Ошибка добавления заметки');
    }
  };

  // первичная загрузка
  renderCalendar();
  selected = new Date();
  loadDay();
});
