let sessionId = null;
let currentNextId = null;

// เริ่มเกม
async function startGame() {
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
    renderGame(data);
}

function renderGame(data) {
    const d = data.dialogue;
    const choices = data.choices;
    
    // ถ้าไม่มีข้อมูล dialogue (อาจจะจบเกมแล้ว หรือ error)
    if (!d) return;

    // 1. อัปเดตข้อความ และ สีชื่อตัวละคร [แก้ตรงนี้]
    const charNameElement = document.getElementById('char-name');
    charNameElement.innerText = d.char_name || '';
    // เพิ่ม: ถ้ามีโค้ดสี ให้เปลี่ยนสี ถ้าไม่มีให้เป็นสีขาว
    if (d.color_code) {
        charNameElement.style.color = d.color_code;
    } else {
        charNameElement.style.color = 'white'; 
    }

    document.getElementById('dialogue-text').innerText = d.text_content;

    // 2. อัปเดตตัวละคร (Sprite) [แก้ตรงนี้เยอะหน่อย]
    const sprite = document.getElementById('character-sprite');
    
    // เช็คว่ามีชื่อไฟล์รูปภาพส่งมาไหม (char_image_file ที่เราแก้ใน app.py)
    if (d.char_image_file) {
        // สั่งเปลี่ยน URL ของ background-image โดยตรง
        sprite.style.backgroundImage = `url('/static/images/${d.char_image_file}')`;
        sprite.classList.remove('hidden');
    } else {
        // ถ้าไม่มีรูป (เช่น บทบรรยาย) ให้ซ่อนและเคลียร์ภาพเก่า
        sprite.style.backgroundImage = 'none';
        sprite.classList.add('hidden');
    }
    // 3. อัปเดตพื้นหลัง (ถ้ามี)
    if (d.bg_image) {
        const gameScreen = document.getElementById('game-screen');
        gameScreen.style.backgroundImage = `url('/static/images/${d.bg_image}')`;
        gameScreen.style.backgroundSize = 'cover';
        gameScreen.style.backgroundPosition = 'center';
    }

    // 4. จัดการปุ่มตัวเลือก vs ปุ่มถัดไป
    const choicesBox = document.getElementById('choices-box');
    choicesBox.innerHTML = ''; 
    const nextIndicator = document.getElementById('next-indicator');

    if (choices.length > 0) {
        // มีตัวเลือก -> ซ่อนลูกศร, โชว์ช้อยส์
        nextIndicator.style.display = 'none';
        choices.forEach(c => {
            const btn = document.createElement('div');
            btn.className = 'choice-btn';
            btn.innerText = c.text_label;
            btn.onclick = () => selectChoice(c.id);
            choicesBox.appendChild(btn);
        });
    } else {
        // ไม่มีตัวเลือก -> โชว์ลูกศร (Next)
        nextIndicator.style.display = 'block';
        currentNextId = d.next_dialogue_id;
        
        // ถ้า next_id เป็น null แสดงว่าจบเกมจริงๆ (หลังฉากจบ)
        if(currentNextId === null) {
            nextIndicator.innerText = "END (Click to Menu)";
            nextIndicator.onclick = () => location.reload();
        } else {
            nextIndicator.innerText = "▼";
            nextIndicator.onclick = nextDialogue;
        }
    }
}

// เมื่อกดเลือก Choice
async function selectChoice(choiceId) {
    await fetch('/api/choose', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ session_id: sessionId, choice_id: choiceId })
    });
    updateState();
}

// เมื่อกดปุ่มลูกศร (Next)
async function nextDialogue() {
    if (!currentNextId) return;

    // [FIXED] เรียก /api/next แทน /api/choose
    await fetch('/api/next', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ session_id: sessionId })
    });
    updateState();
}

// ฟังก์ชันดู Credits (ถ้ามีปุ่มกด)
function showCredits() {
    alert("Game by You!");
}