/**
 * Global game state
 * - sessionId: current session from backend
 * - currentNextId: id of the next dialogue (used for "next" button)
 * - currentDay: used to detect day changes for transitions
 */
let sessionId = null;
let currentNextId = null;
let currentDay = null;


/**
 * Starts the game
 * - requests a new session from backend
 * - plays background music (if allowed)
 * - switches from start screen to game screen
 */
async function startGame() {

    // --- play background music ---
    const bgm = document.getElementById("bgm");
    if (bgm) {
        bgm.volume = 0.5; // adjust volume here
        bgm.play().catch(() => {
            // some browsers block autoplay until user interacts
            console.log("Autoplay was blocked. Please click first to play the music.");
        });
    }

    try {
        // create a new session
        const res = await fetch('/api/start', { method: 'POST' });
        const data = await res.json();
        sessionId = data.session_id;
        
        // switch UI screens
        document.getElementById('start-screen').classList.add('hidden');
        document.getElementById('game-screen').classList.remove('hidden');
        
        // load initial state
        updateState();
    } catch (e) {
        console.error("Error starting game:", e);
        alert("Unable to start the game. Please try again.");
    }
}


/**
 * Fetches the latest game state from backend
 * and passes it to the renderer
 */
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


/**
 * Checks if the day has changed before rendering
 * If so, shows a day transition first
 */
function applyGameData(data) {
    const d = data.dialogue;
    const scene = data.scene;

    // fallback if something is missing
    if (!d || !scene) {
        renderGame(data);
        return;
    }

    // first time entering the game
    if (currentDay === null) {
        currentDay = scene.day;
        showDayTransition(scene.day, () => {
            renderGame(data);
        });
        return;
    }

    // day changed → show transition
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


/**
 * Displays "- DAY X -" overlay
 * then continues to the actual scene
 */
function showDayTransition(day, callback) {
    let overlay = document.getElementById('day-overlay');

    // create overlay if it doesn't exist yet
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'day-overlay';
        document.body.appendChild(overlay);
    }

    overlay.innerText = "- DAY " + day + " -";
    overlay.classList.add('show');

    // temporarily hide UI bar
    const uiBar = document.querySelector('.ui-bar');
    if (uiBar) uiBar.style.visibility = 'hidden';

    setTimeout(() => {
        overlay.classList.remove('show');

        if (uiBar) uiBar.style.visibility = 'visible';

        // small delay for smoother transition
        setTimeout(callback, 1000);
    }, 2500);
}


/**
 * Renders everything on screen:
 * - character / sticker
 * - name
 * - dialogue text
 * - background
 * - choices or next button
 */
function renderGame(data) {
    const d = data.dialogue;

    // --- sticker container (for narrator visuals) ---
    let stickerContainer = document.getElementById('sticker-container');
    if (!stickerContainer) {
        stickerContainer = document.createElement('div');
        stickerContainer.id = 'sticker-container';
        document.getElementById('game-screen').appendChild(stickerContainer);
    }
    stickerContainer.innerHTML = ''; 

    // narrator (id 99) uses sticker instead of sprite
    if (d.character_id === 99 && d.char_image_file) {
        const img = document.createElement('img');
        img.src = `/static/images/${d.char_image_file}`;
        img.className = 'sticker-img';
        stickerContainer.appendChild(img);
        
        document.getElementById('character-sprite').classList.add('hidden');
    } else {
        // normal character sprite handling
        if (d.char_image_file) {
            const sprite = document.getElementById('character-sprite');
            sprite.style.backgroundImage = `url('/static/images/${d.char_image_file}')`;
            sprite.classList.remove('hidden');
        }
    }

    const choices = data.choices;

    if (!d) return;

    // --- character name ---
    const charNameElement = document.getElementById('char-name');
    charNameElement.innerText = d.char_name || '';

    // apply color if provided
    if (d.color_code) {
        charNameElement.style.color = d.color_code;
    } else {
        charNameElement.style.color = 'white';
    }

    // --- dialogue text ---
    document.getElementById('dialogue-text').innerText = d.text_content;

    // --- sprite ---
    const sprite = document.getElementById('character-sprite');

    if (d.char_image_file) {
        sprite.style.backgroundImage = `url('/static/images/${d.char_image_file}')`;
        sprite.classList.remove('hidden');
    } else {
        sprite.style.backgroundImage = 'none';
        sprite.classList.add('hidden');
    }

    // --- background ---
    if (d.bg_image) {
        const gameScreen = document.getElementById('game-screen');

        gameScreen.style.backgroundImage = `url('/static/images/${d.bg_image}')`;
        gameScreen.style.backgroundSize = 'cover';
        gameScreen.style.backgroundPosition = 'center';
    }

    // --- choices / next ---
    const choicesBox = document.getElementById('choices-box');
    choicesBox.innerHTML = '';

    const nextIndicator = document.getElementById('next-indicator');

    if (choices.length > 0) {
        // show choices
        nextIndicator.style.display = 'none';

        choices.forEach(c => {
            const btn = document.createElement('div');
            btn.className = 'choice-btn';
            btn.innerText = c.text_label;
            btn.onclick = () => selectChoice(c.id);
            choicesBox.appendChild(btn);
        });

    } else {
        // fallback to next button
        nextIndicator.style.display = 'block';
        currentNextId = d.next_dialogue_id;

        if (currentNextId === null) {
            // end of game
            showStats();
            nextIndicator.innerText = "Back to Menu";
            nextIndicator.onclick = () => location.reload();
        } else {
            nextIndicator.innerText = "▼";
            nextIndicator.onclick = nextDialogue;
        }
    }
}


/**
 * Sends selected choice to backend
 * then refreshes the game state
 */
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


/**
 * Moves to the next dialogue (no choice case)
 */
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


/**
 * Shows game credits
 */
function showCredits() {
    alert("This game is created by 68051299 & 68051317");
}


/**
 * Displays player's choice history and score impact
 */
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


/**
 * "What If" mode:
 * shows an alternative timeline based on unchosen options
 */
function showWhatIf() {
    
    document.getElementById("stats-container").classList.remove("hidden");

    fetch(`/api/what_if/${sessionId}`)
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById("stats-list");
            
            if (data.length === 0) {
                list.innerHTML = "<h3 style='color:white;'>What If Timeline</h3><p style='color:white;'>You haven't reached any choice points yet. Try playing a bit further!</p>";

                list.innerHTML += `<div style="text-align: center; margin-top: 15px;"><button onclick="document.getElementById('stats-container').classList.add('hidden')" style="background-color: #ff4d4d; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer;">Close Window</button></div>`;
                return;
            }

            const missedChoice = data[0].missed_choice;

            list.innerHTML = `<h3 style='color:white; margin-top:0;'>Parallel Universe: What if you had chosen...<br><span style='color:#ff9fb2'>"${missedChoice}"</span></h3>`;
            
            data.forEach(item => {
                list.innerHTML += `
                    <p style='color:white; margin: 5px 0; border-left: 3px solid #ff9fb2; padding-left: 10px;'>
                        <b>[${item.step}]</b> ${item.text_content}
                    </p>
                `;
            });

            list.innerHTML += `
                <div style="text-align: center; margin-top: 15px;">
                    <button onclick="document.getElementById('stats-container').classList.add('hidden')" style="background-color: #ff4d4d; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                        Close Window
                    </button>
                </div>
            `;
        })
        .catch(err => console.error("Error:", err));
}