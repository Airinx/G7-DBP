let sessionId = null;
let currentNextId = null;
let currentDay = null;

// Start the game
async function startGame() {

// --- Play background music ---
    const bgm = document.getElementById("bgm");
    if (bgm) {
        bgm.volume = 0.5; // Adjust volume (0.0 - 1.0)
        bgm.play().catch(() => {
            console.log("Autoplay was blocked. Please click first to play the music.");
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
        alert("Unable to start the game. Please try again.");
    }
}

// Update the screen
async function updateState() {
    if (!sessionId) return;
    
    const res = await fetch(`/api/state/${sessionId}`);
    if (!res.ok) {
        alert("An error occurred while loading the data");
        return;
    }

    const data = await res.json();
    applyGameData(data);
}

// Check the day before displaying
function applyGameData(data) {
    const d = data.dialogue;
    const scene = data.scene;

    if (!d || !scene) {
        renderGame(data);
        return;
    }

// If this is the first time starting the game
    if (currentDay === null) {
        currentDay = scene.day;
        showDayTransition(scene.day, () => {
            renderGame(data);
        });
        return;
    }

  // If the day changes
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

// Show the DAY screen
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

// Show the game
function renderGame(data) {
    const d = data.dialogue;

    let stickerContainer = document.getElementById('sticker-container');
    if (!stickerContainer) {
        stickerContainer = document.createElement('div');
        stickerContainer.id = 'sticker-container';
        document.getElementById('game-screen').appendChild(stickerContainer);
    }
    stickerContainer.innerHTML = ''; 

// Check condition: if the narrator character (ID 99) has an accompanying image
    if (d.character_id === 99 && d.char_image_file) {
        const img = document.createElement('img');
        img.src = `/static/images/${d.char_image_file}`;
        img.className = 'sticker-img';
        stickerContainer.appendChild(img);
        
        // Hide the normal character sprite (if one is still visible)
        document.getElementById('character-sprite').classList.add('hidden');
    } else {
       // If this scene does not use a sticker, handle the character sprite normally
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
            showStats();
            nextIndicator.innerText = "Back to Menu";;
            nextIndicator.onclick = () => location.reload();
        } else {
            nextIndicator.innerText = "▼";
            nextIndicator.onclick = nextDialogue;
        }
    }
}

// select choice
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

//press next
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

// credit
function showCredits() {
    alert("This game is created by 68051299 & 68051317");
}

function showStats() {

    document.getElementById("stats-container").classList.remove("hidden");

    fetch(`/api/stats/${sessionId}`)
        .then(res => res.json())
        .then(data => {

            const list = document.getElementById("stats-list");
            list.innerHTML = "";

            data.forEach(item => {

                const row = document.createElement("div");

                row.innerHTML =
                    "<b>Turn " + item.turn_number + "</b>: "
                    + item.text_label +
                    " (Score " + item.score_impact + ")";

                list.appendChild(row);
            });

        });
}