let sessionId = null;
let currentNextId = null;
let currentDay = null;

// เริ่มเกม
async function startGame() {

    // --- เล่นเพลงพื้นหลัง ---
    const bgm = document.getElementById("bgm");
    if (bgm) {
        bgm.volume = 0.5; // ปรับความดัง (0.0 - 1.0)
        bgm.play().catch(() => {
            console.log("Autoplay ถูกบล็อก ต้องกดก่อนถึงจะเล่นเพลงได้");
        });
    }

    try {
        const res = await fetch('/api/start', { method: 'POST' });
        const data = await res.json();
        sessionId = data.session_id;
        
        document.getElementById('start-screen').classList.add('hidden');
        document.getElementById('game-screen').classList.remove('hidden');
        
        updateState();
    } catch (e) {
        console.error("Error starting game:", e);
        alert("ไม่สามารถเริ่มเกมได้ กรุณาลองใหม่อีกครั้ง");
    }
}

// อัปเดตหน้าจอ
async function updateState() {
    if (!sessionId) return;
    
    const res = await fetch(`/api/state/${sessionId}`);
    if (!res.ok) {
        alert("เกิดข้อผิดพลาดในการโหลดข้อมูล");
        return;
    }

    const data = await res.json();
    applyGameData(data);
}

// ตรวจสอบวันก่อนแสดงผล
function applyGameData(data) {
    const d = data.dialogue;
    const scene = data.scene;

    if (!d || !scene) {
        renderGame(data);
        return;
    }

    // ถ้าเป็นครั้งแรกของเกม
    if (currentDay === null) {
        currentDay = scene.day;
        showDayTransition(scene.day, () => {
            renderGame(data);
        });
        return;
    }

    // ถ้าวันเปลี่ยน
    if (scene.day !== currentDay && scene.day !== 0) {
        currentDay = scene.day;

        showDayTransition(scene.day, () => {
            renderGame(data);
        });
    } 
    else {
        renderGame(data);
    }
}

// แสดงหน้าจอ DAY
function showDayTransition(day, callback) {
    let overlay = document.getElementById('day-overlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'day-overlay';
        document.body.appendChild(overlay);
    }

    overlay.innerText = "- DAY " + day + " -";
    overlay.classList.add('show');

    const uiBar = document.querySelector('.ui-bar');
    if (uiBar) uiBar.style.visibility = 'hidden';

    setTimeout(() => {
        overlay.classList.remove('show');

        if (uiBar) uiBar.style.visibility = 'visible';

        setTimeout(callback, 1000);
    }, 2500);
}

// แสดงเกม
function renderGame(data) {
    const d = data.dialogue;

    let stickerContainer = document.getElementById('sticker-container');
    if (!stickerContainer) {
        stickerContainer = document.createElement('div');
        stickerContainer.id = 'sticker-container';
        document.getElementById('game-screen').appendChild(stickerContainer);
    }
    stickerContainer.innerHTML = ''; 

    // เช็คเงื่อนไข: ถ้าเป็นตัวละครบรรยาย (ID 99) และมีรูปภาพประกอบ
    if (d.character_id === 99 && d.char_image_file) {
        const img = document.createElement('img');
        img.src = `/static/images/${d.char_image_file}`;
        img.className = 'sticker-img';
        stickerContainer.appendChild(img);
        
        // ซ่อน Sprite ตัวละครปกติ (ถ้ามีค้างอยู่)
        document.getElementById('character-sprite').classList.add('hidden');
    } else {
        // ถ้าไม่ใช่บทที่มีสติ๊กเกอร์ ให้จัดการ Sprite ตัวละครตามปกติ
        if (d.char_image_file) {
            const sprite = document.getElementById('character-sprite');
            sprite.style.backgroundImage = `url('/static/images/${d.char_image_file}')`;
            sprite.classList.remove('hidden');
        }
    }
    
    const choices = data.choices;

    if (!d) return;

    // --- Character Name ---
    const charNameElement = document.getElementById('char-name');
    charNameElement.innerText = d.char_name || '';

    if (d.color_code) {
        charNameElement.style.color = d.color_code;
    } else {
        charNameElement.style.color = 'white';
    }

    // --- Dialogue ---
    document.getElementById('dialogue-text').innerText = d.text_content;

    // --- Character Sprite ---
    const sprite = document.getElementById('character-sprite');

    if (d.char_image_file) {
        sprite.style.backgroundImage = `url('/static/images/${d.char_image_file}')`;
        sprite.classList.remove('hidden');
    } else {
        sprite.style.backgroundImage = 'none';
        sprite.classList.add('hidden');
    }

    // --- Background ---
    if (d.bg_image) {
        const gameScreen = document.getElementById('game-screen');

        gameScreen.style.backgroundImage = `url('/static/images/${d.bg_image}')`;
        gameScreen.style.backgroundSize = 'cover';
        gameScreen.style.backgroundPosition = 'center';
    }

    // --- Choices ---
    const choicesBox = document.getElementById('choices-box');
    choicesBox.innerHTML = '';

    const nextIndicator = document.getElementById('next-indicator');

    if (choices.length > 0) {
        nextIndicator.style.display = 'none';

        choices.forEach(c => {
            const btn = document.createElement('div');
            btn.className = 'choice-btn';
            btn.innerText = c.text_label;
            btn.onclick = () => selectChoice(c.id);
            choicesBox.appendChild(btn);
        });

    } else {

        nextIndicator.style.display = 'block';
        currentNextId = d.next_dialogue_id;

        if (currentNextId === null) {
            nextIndicator.innerText = "END (Click to Menu)";
            nextIndicator.onclick = () => location.reload();
        } else {
            nextIndicator.innerText = "▼";
            nextIndicator.onclick = nextDialogue;
        }
    }
}

// เลือก choice
async function selectChoice(choiceId) {
    await fetch('/api/choose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            choice_id: choiceId
        })
    });

    updateState();
}

// กด next
async function nextDialogue() {

    if (!currentNextId) return;

    await fetch('/api/next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId
        })
    });

    updateState();
}

// เครดิต
function showCredits() {
    alert("This game is created by 68051299 & 68051317");
}