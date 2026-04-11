const SHEET_ID = '1zf0lMcWQwOyJH5XT53_myO96Celb9SjvIKkxe7-oXTA';
const SHEET_NAME = '시트1'; // 필요시 변경 가능
const CSV_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:csv&sheet=${encodeURIComponent(SHEET_NAME)}`;

const studentNameInput = document.getElementById('studentName');
const searchBtn = document.getElementById('searchBtn');
const resultArea = document.getElementById('resultArea');
const errorArea = document.getElementById('errorArea');
const loadingArea = document.getElementById('loadingArea');
const displayName = document.getElementById('displayName');
const scoreValue = document.getElementById('scoreValue');
const errorMessage = document.getElementById('errorMessage');

let scoreData = [];

// 1. 구글 시트 데이터 로드
async function loadData() {
    showLoading(true);
    try {
        const response = await fetch(CSV_URL);
        const csvText = await response.text();
        scoreData = parseCSV(csvText);
        console.log('Loaded Data:', scoreData);
        showLoading(false);
    } catch (error) {
        console.error('Error loading sheet:', error);
        showError('데이터를 불러오는 데 실패했습니다. 시트 설정을 확인해 주세요.');
        showLoading(false);
    }
}

// 2. CSV 파싱 (간단한 구현)
function parseCSV(csvText) {
    const lines = csvText.split('\n');
    // 따옴표 제거 및 데이터 정리
    return lines.map(line => {
        return line.split(',').map(cell => cell.replace(/^"(.*)"$/, '$1').trim());
    }).filter(row => row.length >= 2); // 최소 이름, 점수 두 열은 있어야 함
}

// 3. 검색 로직
function searchScore() {
    const searchName = studentNameInput.value.trim();
    
    if (!searchName) {
        showError('이름을 입력해 주세요.');
        return;
    }

    if (scoreData.length === 0) {
        showError('데이터를 아직 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.');
        return;
    }

    // 첫 행(헤더)을 제외하고 검색하거나 전체 검색
    const student = scoreData.find(row => row[0] === searchName);

    if (student) {
        showResult(student[0], student[1]);
    } else {
        showError(`'${searchName}' 학생을 찾을 수 없습니다.`);
    }
}

// UI 제어 함수들
function showResult(name, score) {
    resultArea.classList.remove('hidden');
    errorArea.classList.add('hidden');
    displayName.textContent = `${name} 학생`;
    scoreValue.textContent = score;
}

function showError(msg) {
    resultArea.classList.add('hidden');
    errorArea.classList.remove('hidden');
    errorMessage.textContent = msg;
}

function showLoading(isLoading) {
    if (isLoading) {
        loadingArea.classList.remove('hidden');
        searchBtn.disabled = true;
    } else {
        loadingArea.classList.add('hidden');
        searchBtn.disabled = false;
    }
}

// 이벤트 리스너
searchBtn.addEventListener('click', searchScore);
studentNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchScore();
});

// 초기 데이터 로드
loadData();
